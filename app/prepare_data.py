"""Build the small, compressed datasets the Streamlit app reads.

Run once after notebooks 01, 03 and 05 have produced their outputs in files/:

    python app/prepare_data.py

Inputs (git-ignored, from Kaggle and the notebooks):
    files/train.csv, stores.csv, transactions.csv, oil.csv, holidays_events.csv
    files/train_sales_transactions_oil_holidays_merged.csv   (Part 1)
    files/preparation_checkpoint.pkl                         (Part 3)
    files/model_ready_data.pkl, feature_columns.txt          (Part 5)

Outputs: app/data/*.parquet and app/data/summary.json (a few MB in total).
Only aggregates and a small random sample of rows are written.
"""
import json
import time
from datetime import date as date_type
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

ROOT = Path(__file__).resolve().parents[1]
FILES = ROOT / "files"
OUT = ROOT / "app" / "data"
OUT.mkdir(parents=True, exist_ok=True)
summary = {}


def save(df, name):
    df.to_parquet(OUT / f"{name}.parquet", index=False, compression="zstd")
    print(f"  {name}: {df.shape}")


def run_model(model, records):
    """Validate records with a Pydantic model; return (checked, errors, seconds, first error)."""
    start = time.perf_counter()
    errors, first = 0, None
    for row in records:
        try:
            model(**row)
        except ValidationError as error:
            errors += 1
            first = first or str(error)[:300]
    return {"checked": len(records), "errors": errors,
            "seconds": round(time.perf_counter() - start, 2), "first_error": first}


def model_rules(model):
    rows = []
    for name, field in model.model_fields.items():
        rules = []
        for item in field.metadata:
            for key in ("ge", "gt", "le", "lt", "min_length", "allow_inf_nan"):
                value = getattr(item, key, None)
                if value is not None:
                    rules.append(f"{key}={value}")
        annotation = getattr(field.annotation, "__name__", str(field.annotation)).replace("datetime.", "")
        rows.append({"field": name, "type": annotation, "rules": ", ".join(rules) or "type only"})
    return rows


# ------------------------------------------------------------------ raw inputs
print("Raw tables")
train = pd.read_csv(FILES / "train.csv", parse_dates=["date"])
stores = pd.read_csv(FILES / "stores.csv")
transactions = pd.read_csv(FILES / "transactions.csv", parse_dates=["date"])
oil = pd.read_csv(FILES / "oil.csv", parse_dates=["date"])
holidays = pd.read_csv(FILES / "holidays_events.csv", parse_dates=["date"])

save(stores, "raw_stores")
save(oil, "raw_oil")
save(holidays, "raw_holidays")
save(train.sample(n=150_000, random_state=7).sort_values("id"), "raw_train_sample")

raw = {}
for name, table in [("train", train), ("stores", stores), ("transactions", transactions),
                    ("oil", oil), ("holidays_events", holidays)]:
    raw[name] = {
        "rows": int(len(table)), "columns": int(table.shape[1]),
        "dtypes": {c: str(t) for c, t in table.dtypes.items()},
        "missing": {c: int(v) for c, v in table.isna().sum().items()},
        "duplicates": int(table.duplicated().sum()),
    }
s = train["sales"]
raw["train"]["sales"] = {
    "mean": float(s.mean()), "median": float(s.median()), "max": float(s.max()),
    "skew": float(s.skew()), "zero_share": float((s == 0).mean()), "zero_rows": int((s == 0).sum()),
    "p": {str(q): float(s.quantile(q)) for q in (0.5, 0.75, 0.9, 0.95, 0.99, 0.999)},
    "total": float(s.sum()),
}
raw["train"]["date_min"] = str(train["date"].min().date())
raw["train"]["date_max"] = str(train["date"].max().date())
raw["train"]["dates"] = int(train["date"].nunique())
raw["train"]["stores"] = int(train["store_nbr"].nunique())
raw["train"]["families"] = int(train["family"].nunique())
raw["train"]["promo_share"] = float((train["onpromotion"] > 0).mean())
all_days = pd.date_range(train["date"].min(), train["date"].max())
raw["train"]["missing_calendar_days"] = [str(d.date()) for d in all_days.difference(train["date"].unique())]
oil_days = pd.date_range(oil["date"].min(), oil["date"].max())
raw["oil"]["calendar_days_without_row"] = int(len(oil_days.difference(oil["date"])))
raw["oil"]["date_min"], raw["oil"]["date_max"] = str(oil["date"].min().date()), str(oil["date"].max().date())
raw["transactions"]["date_min"] = str(transactions["date"].min().date())
raw["transactions"]["date_max"] = str(transactions["date"].max().date())
raw["holidays_events"]["types"] = holidays["type"].value_counts().to_dict()
raw["holidays_events"]["locales"] = holidays["locale"].value_counts().to_dict()
raw["holidays_events"]["transferred"] = int(holidays["transferred"].sum())
summary["raw"] = raw

# family zero share / store-family never sold (raw facts)
family_raw = train.groupby("family").agg(
    total_sales=("sales", "sum"), mean_sales=("sales", "mean"), median_sales=("sales", "median"),
    zero_share=("sales", lambda x: (x == 0).mean()), promo_share=("onpromotion", lambda x: (x > 0).mean()),
    mean_promotions=("onpromotion", "mean"),
).reset_index()
save(family_raw, "family_summary")

# log-scale histogram of all sales rows (exact counts, not a sample)
edges = np.concatenate([[0, 1e-9], np.logspace(0, np.log10(s.max() + 1), 60)])
counts, _ = np.histogram(s, bins=edges)
save(pd.DataFrame({"left": edges[:-1], "right": edges[1:], "rows": counts}), "sales_histogram")

# ------------------------------------------------------------------ merge (ETL) facts
print("Merged data (before cleaning)")
merged = pd.read_csv(FILES / "train_sales_transactions_oil_holidays_merged.csv",
                     parse_dates=["date"], dtype={"holiday_transferred": "object"}, low_memory=False)
summary["merged"] = {
    "rows": int(len(merged)), "columns": int(merged.shape[1]),
    "missing": {c: int(v) for c, v in merged.isna().sum().items()},
}
summary["etl_steps"] = [
    {"step": "train", "rows": int(len(train)), "columns": 6, "join": "base table", "key": "id"},
    {"step": "+ stores", "rows": int(len(merged)), "columns": 10, "join": "left, many-to-one", "key": "store_nbr"},
    {"step": "+ transactions", "rows": int(len(merged)), "columns": 11, "join": "left, many-to-one", "key": "date + store_nbr"},
    {"step": "+ oil", "rows": int(len(merged)), "columns": 12, "join": "left", "key": "date"},
    {"step": "+ holidays/events", "rows": int(len(merged)), "columns": 17, "join": "left, many-to-one (aggregated per store-day)", "key": "date + store_nbr"},
]

# ------------------------------------------------------------------ cleaned data
print("Cleaned checkpoint")
clean = pd.read_pickle(FILES / "preparation_checkpoint.pkl")
assert len(clean) == len(merged)
clean["transactions_original"] = merged["transactions"].values
clean["oil_original"] = merged["oil_price"].values
clean["zero_sale"] = (clean["sales"] == 0).astype("int16")

first_sales = clean[clean["sales"] > 0].groupby("store_nbr")["date"].min()

store_day = (
    clean.groupby(["date", "store_nbr"], observed=True)
    .agg(
        sales=("sales", "sum"),
        transactions=("transactions", "first"),
        transactions_original=("transactions_original", "first"),
        fill_method=("transactions_fill_method", "first"),
        promotions=("onpromotion", "sum"),
        zero_families=("zero_sale", "sum"),
        extreme_rows=("sales_extreme_flag", "sum"),
        oil_price=("oil_price", "first"),
        is_holiday=("is_holiday", "max"), is_national_holiday=("is_national_holiday", "max"),
        is_regional_holiday=("is_regional_holiday", "max"), is_local_holiday=("is_local_holiday", "max"),
        is_event=("is_event", "max"), is_work_day=("is_work_day", "max"),
        is_earthquake_period=("is_earthquake_period", "max"),
        is_weekend=("is_weekend", "first"), is_payday=("is_payday", "first"),
        city=("city", "first"), state=("state", "first"), store_type=("type", "first"),
        cluster=("cluster", "first"),
    )
    .reset_index()
)
store_day["fill_method"] = store_day["fill_method"].astype(str)
for c in ["city", "state", "store_type"]:
    store_day[c] = store_day[c].astype(str)
store_day["cluster"] = store_day["cluster"].astype(int)
store_day["store_open"] = (store_day["date"] >= store_day["store_nbr"].map(first_sales)).astype("int8")
store_day["year"] = store_day["date"].dt.year
store_day["month"] = store_day["date"].dt.month
store_day["weekday"] = store_day["date"].dt.day_name()
store_day["sales_per_transaction"] = np.where(store_day["transactions"] > 0,
                                              store_day["sales"] / store_day["transactions"], np.nan)
save(store_day, "store_day")

family_day = (
    clean.groupby(["date", "family"], observed=True)
    .agg(sales=("sales", "sum"), promotions=("onpromotion", "sum"),
         zero_stores=("zero_sale", "sum"), extreme_rows=("sales_extreme_flag", "sum"))
    .reset_index()
)
family_day["family"] = family_day["family"].astype(str)
save(family_day, "family_day")

store_family = (
    clean.groupby(["store_nbr", "family"], observed=True)
    .agg(total_sales=("sales", "sum"), mean_sales=("sales", "mean"),
         zero_share=("zero_sale", "mean"), mean_promotions=("onpromotion", "mean"),
         extreme_rows=("sales_extreme_flag", "sum"))
    .reset_index()
)
store_family["family"] = store_family["family"].astype(str)
save(store_family, "store_family")

daily = (
    store_day.groupby("date")
    .agg(sales=("sales", "sum"), transactions=("transactions", "sum"),
         transactions_observed=("transactions_original", "sum"),
         promotions=("promotions", "sum"), zero_families=("zero_families", "sum"),
         stores_selling=("sales", lambda x: int((x > 0).sum())),
         filled_store_days=("fill_method", lambda x: int((x != "observed").sum())),
         oil_price=("oil_price", "first"),
         is_national_holiday=("is_national_holiday", "max"), is_event=("is_event", "max"),
         stores_with_holiday=("is_holiday", "sum"),
         is_earthquake_period=("is_earthquake_period", "max"),
         is_weekend=("is_weekend", "first"), is_payday=("is_payday", "first"))
    .reset_index()
)
oil_orig = clean.drop_duplicates("date").set_index("date")["oil_original"]
daily["oil_original"] = daily["date"].map(oil_orig)
daily["year"] = daily["date"].dt.year
daily["month"] = daily["date"].dt.month
daily["weekday"] = daily["date"].dt.day_name()
save(daily, "daily")

# clean sample rows for distributions
sample_cols = ["date", "store_nbr", "family", "sales", "sales_log1p", "onpromotion", "transactions",
               "oil_price", "type", "city", "cluster", "is_holiday", "is_weekend", "sales_extreme_flag"]
clean_sample = clean[sample_cols].sample(n=150_000, random_state=7).copy()
for c in ["family", "type", "city"]:
    clean_sample[c] = clean_sample[c].astype(str)
clean_sample["cluster"] = clean_sample["cluster"].astype(int)
save(clean_sample, "clean_sample")

summary["clean"] = {
    "rows": int(len(clean)), "columns": int(clean.shape[1] - 3),
    "missing": {c: int(v) for c, v in clean.drop(columns=["transactions_original", "oil_original", "zero_sale"]).isna().sum().items()},
    "fill_method_rows": clean["transactions_fill_method"].astype(str).value_counts().to_dict(),
    "fill_method_store_days": store_day["fill_method"].value_counts().to_dict(),
    "oil_filled_dates": int(daily["oil_original"].isna().sum()),
    "extreme_rows": int(clean["sales_extreme_flag"].sum()),
    "flags": {c: int(clean[c].sum()) for c in ["is_holiday", "is_national_holiday", "is_regional_holiday",
                                              "is_local_holiday", "is_event", "is_work_day",
                                              "is_earthquake_period", "is_weekend", "is_payday"]},
    "skew_sales": float(clean["sales"].skew()), "skew_log": float(clean["sales_log1p"].skew()),
    "first_sales": {int(k): str(v.date()) for k, v in first_sales.items()},
}

# integrity checks (same as notebook 04 section 16.2)
known_t = merged["transactions"].notna()
known_o = merged["oil_price"].notna()
summary["integrity"] = [
    ["Same number of rows", bool(len(clean) == len(merged))],
    ["Same row order (id)", bool((clean["id"].values == merged["id"].values).all())],
    ["Same dates, stores and families", bool((clean["date"].values == merged["date"].values).all()
                                             and (clean["store_nbr"].values == merged["store_nbr"].values).all()
                                             and (clean["family"].astype(str).values == merged["family"].values).all())],
    ["Sales unchanged", bool((clean["sales"].values == merged["sales"].values).all())],
    ["Promotions unchanged", bool((clean["onpromotion"].values == merged["onpromotion"].values).all())],
    ["Known transactions unchanged", bool((clean.loc[known_t, "transactions"].values == merged.loc[known_t, "transactions"].values).all())],
    ["transactions_missing matches original gaps", bool((clean["transactions_missing"].values == merged["transactions"].isna().values).all())],
    ["Known oil prices unchanged", bool((clean.loc[known_o, "oil_price"].values == merged.loc[known_o, "oil_price"].values).all())],
    ["oil_price_missing matches original gaps", bool((clean["oil_price_missing"].values == merged["oil_price"].isna().values).all())],
    ["No duplicate date/store/family keys", bool(not clean.duplicated(["date", "store_nbr", "family"]).any())],
    ["No missing values after cleaning", bool(clean.drop(columns=["transactions_original", "oil_original"]).isna().sum().sum() == 0)],
]

# ------------------------------------------------------------------ Pydantic validation (real runs)
print("Pydantic validation")


class StoreDayTransactions(BaseModel):
    store_nbr: int = Field(ge=1, le=54)
    transactions: int = Field(ge=0)
    transactions_missing: int = Field(ge=0, le=1)


class OilDay(BaseModel):
    date: date_type
    oil_price: float = Field(gt=0, allow_inf_nan=False)


class CleanSalesRow(BaseModel):
    id: int = Field(ge=0)
    date: date_type
    store_nbr: int = Field(ge=1, le=54)
    family: str = Field(min_length=1)
    sales: float = Field(ge=0, allow_inf_nan=False)
    onpromotion: int = Field(ge=0)
    city: str = Field(min_length=1)
    state: str = Field(min_length=1)
    type: str = Field(min_length=1)
    cluster: int = Field(ge=1)
    transactions: int = Field(ge=0)
    transactions_missing: int = Field(ge=0, le=1)
    oil_price: float = Field(gt=0, allow_inf_nan=False)
    oil_price_missing: int = Field(ge=0, le=1)
    is_holiday: int = Field(ge=0, le=1)
    is_event: int = Field(ge=0, le=1)
    is_work_day: int = Field(ge=0, le=1)
    sales_log1p: float = Field(ge=0, allow_inf_nan=False)
    sales_extreme_flag: int = Field(ge=0, le=1)
    is_earthquake_period: int = Field(ge=0, le=1)
    month: int = Field(ge=1, le=12)
    day_of_week: int = Field(ge=0, le=6)
    is_weekend: int = Field(ge=0, le=1)
    is_payday: int = Field(ge=0, le=1)


sd = clean[["date", "store_nbr", "transactions", "transactions_missing"]].drop_duplicates()
od = clean[["date", "oil_price"]].drop_duplicates()
od["date"] = od["date"].dt.date
rows = clean[list(CleanSalesRow.model_fields)].sample(n=100_000, random_state=42)
rows["date"] = rows["date"].dt.date
rows = rows.astype(object)

model_ready = pd.read_pickle(FILES / "model_ready_data.pkl")
feature_columns = (FILES / "feature_columns.txt").read_text(encoding="utf-8").split("\n")


class ModelRow(BaseModel):
    store_nbr: int = Field(ge=1, le=54)
    family_code: int = Field(ge=0, le=32)
    sales_log1p: float = Field(ge=0, allow_inf_nan=False)
    sales_lag_16: float = Field(ge=0, allow_inf_nan=False)
    sales_lag_364: float = Field(ge=-1, allow_inf_nan=False)
    sales_rolling_mean_7: float = Field(ge=0, allow_inf_nan=False)
    transactions_lag_16: float = Field(ge=0, allow_inf_nan=False)
    oil_price_change_7: float = Field(gt=-1, allow_inf_nan=False)
    month_sin: float = Field(ge=-1, le=1)
    days_to_christmas: int = Field(ge=0, le=365)
    is_holiday: int = Field(ge=0, le=1)
    store_open: int = Field(ge=0, le=1)


mr = model_ready[list(ModelRow.model_fields)].sample(n=100_000, random_state=42)

summary["pydantic"] = []
for model, level, records, notebook in [
    (StoreDayTransactions, "one row per store-day", sd.to_dict("records"), "03 · 15.8 / 04 · 16.4"),
    (OilDay, "one row per date", od.to_dict("records"), "03 · 15.9.1 / 04 · 16.4"),
    (CleanSalesRow, "random sample of cleaned rows", rows.to_dict("records"), "03 · 15.14"),
    (ModelRow, "random sample of model-ready rows", mr.to_dict("records"), "05 · 17.13"),
]:
    result = run_model(model, records)
    result.update({"model": model.__name__, "level": level, "notebook": notebook,
                   "fields": model_rules(model), "population": {
                       "StoreDayTransactions": len(sd), "OilDay": len(od),
                       "CleanSalesRow": len(clean), "ModelRow": len(model_ready)}[model.__name__]})
    summary["pydantic"].append(result)
    print(f"  {model.__name__}: {result['checked']:,} checked, {result['errors']} errors")

# coverage: which cleaned columns are protected by which check
covered = {}
for result in summary["pydantic"][:3]:
    for f in result["fields"]:
        covered.setdefault(f["field"], []).append(result["model"])
summary["coverage"] = [
    {"column": c, "pydantic": covered.get(c, []), "pandas": True}
    for c in clean.drop(columns=["transactions_original", "oil_original", "zero_sale"]).columns
]

# ------------------------------------------------------------------ features
print("Model-ready features")
fs = model_ready.sample(n=200_000, random_state=11)
corr = fs[feature_columns].corrwith(fs["sales_log1p"]).sort_values(key=np.abs, ascending=False)
groups = []
for c in feature_columns:
    g = ("sales history" if c.startswith("sales_") else "one-hot family" if c.startswith("family_") and c != "family_code"
         else "one-hot store type" if c.startswith("store_type_") else "transactions" if "transaction" in c
         else "promotion" if "promotion" in c else "oil" if "oil" in c
         else "holiday / event" if c.startswith(("is_holiday", "is_national", "is_regional", "is_local", "is_event", "is_work", "is_day_", "is_earthquake"))
         else "codes" if c.endswith("_code") or c == "store_nbr" else "calendar")
    groups.append({"feature": c, "group": g, "corr_with_target": float(corr.get(c, np.nan))})
save(pd.DataFrame(groups), "features")
summary["model_ready"] = {
    "rows": int(len(model_ready)), "columns": int(model_ready.shape[1]),
    "features": len(feature_columns), "first_date": str(model_ready["date"].min().date()),
    "removed_rows": int(len(clean) - len(model_ready)),
    "missing": int(model_ready[feature_columns].isna().sum().sum()),
}

(OUT / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
total = sum(p.stat().st_size for p in OUT.iterdir())
print(f"Done. {len(list(OUT.iterdir()))} files, {total / 1024**2:.1f} MB in {OUT}")
