import time
from datetime import date as date_type

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pydantic import BaseModel, Field, ValidationError

from lib import data, theme

DOWNLOADS = "https://github.com/MuhammadTahirHussain-Official/PAI-Sales-DataAnalysis/raw/main/downloads/"
S = data.summary()
M = S["merged"]["missing"]
C = S["clean"]

theme.flow_top("views/cleaning.py")
theme.page_title("Technical overview", "<em>Cleaning</em> and validation",
                 "Which rule filled each gap, how many rows it touched, and how every rule was then checked with pandas and Pydantic.")

theme.chapter("4.0", "Before and after", "Every column that had empty values, and what cleaning did to it.")
miss = pd.DataFrame([
    {"column": k, "before": v, "after": C["missing"].get(k, 0)} for k, v in M.items() if v > 0
]).sort_values("before")
view = st.segmented_control("Show", ["Before cleaning", "Before and after"], default="Before and after")
fig = go.Figure()
fig.add_trace(go.Bar(y=miss["column"], x=miss["before"], orientation="h", name="before cleaning", marker_color=theme.PERSIMMON,
                     hovertemplate="%{y}: %{x:,} empty rows before<extra></extra>"))
if view == "Before and after":
    fig.add_trace(go.Bar(y=miss["column"], x=miss["after"], orientation="h", name="after cleaning", marker_color=theme.MOSS,
                         hovertemplate="%{y}: %{x:,} empty rows after<extra></extra>"))
fig.update_layout(barmode="group", xaxis_title="Empty rows (of 3,000,888)", yaxis_title="")
theme.chart(fig, height=360)
theme.figcap("3.2", "Grouped bar chart", "How many empty values each column had, before and after cleaning.",
             "The five holiday columns are empty on 91% of rows simply because most days are not holidays. Oil is empty on weekends (928,422 rows), and transactions on 7,448 store-days (245,784 rows). After cleaning every column is complete.",
             "a longer bar means more empty rows; orange is before, green is after.")

# ------------------------------------------------------------------ cleaning ledger
theme.chapter("3.3", "Every cleaning rule", "Every cleaning rule, in order, and how many rows it changed.")
fr = C["fill_method_rows"]
theme.ledger(
    ["Step", "Rule", "Rows affected", "Validation"],
    [["15.5 Quality", "no duplicate keys or ids, no negative sales or promotions", "0 problems", "assert"],
     ["15.6 Transactions", "missing on a store-day whose total sales are 0 → 0", f"{fr.get('zero_sales_store_day', 0):,} rows · 7,330 store-days", "only those cells changed"],
     ["15.7 Transactions", "missing with positive sales → total sales × median(transactions / sales) of that store and weekday", f"{fr.get('ratio_estimate', 0):,} rows · 118 store-days", "no gaps left; known values unchanged"],
     ["15.8 Pydantic", "whole number ≥ 0, one value per store-day", "90,936 store-days", "0 errors"],
     ["15.9 Oil", "forward fill from the last trading day, at most 7 days", "926,640 rows · 520 dates", "known prices unchanged"],
     ["15.9.2 Oil", "first date (no earlier price) ← next trading day", "1,782 rows · 2013-01-01", "flag kept"],
     ["15.10 Holidays", "0/1 flags from the original records; transferred-away days are not holidays; Work Day is not a holiday", f"{C['flags']['is_holiday']:,} holiday rows", "row count unchanged"],
     ["15.10.1 Holidays", "empty text → \"No Event\"", "2,733,291 rows per column", "existing text unchanged"],
     ["15.11 Sales", "keep zeros; add log1p; flag (never delete) values above Q3 + 3·IQR inside each store-family", f"{C['extreme_rows']:,} rows flagged", "sales unchanged"],
     ["15.12 – 15.13", "date parts, weekend, payday; category data types", "21 new columns", "memory 2.1 → 1.1 GB"]],
    numeric_cols=(2,))

# ------------------------------------------------------------------ transactions before / after
theme.chapter("3.4", "Transactions: what was filled, and with what")
sd = data.load("store_day")
c1, c2 = st.columns([1, 1.4])
with c1:
    fm = pd.Series(C["fill_method_store_days"]).rename_axis("source").reset_index(name="store_days")
    fig = px.pie(fm, names="source", values="store_days", hole=.62,
                 color="source", color_discrete_map={"observed": theme.TEAL, "zero_sales_store_day": theme.SAND, "ratio_estimate": theme.PERSIMMON})
    fig.update_traces(textinfo="percent", hovertemplate="%{label}: %{value:,} store-days<extra></extra>", sort=False,
                      marker=dict(line=dict(color=theme.PAPER, width=2)))
    fig.update_layout(showlegend=True, legend=dict(orientation="v", y=.5, x=1.02),
                      annotations=[dict(text="90,936<br>store-days", showarrow=False, font=dict(family=theme.FONT_DISPLAY, size=20))])
    theme.chart(fig, height=330)
with c2:
    est = sd[sd["fill_method"] == "ratio_estimate"]
    fig = px.scatter(sd[sd["fill_method"] == "observed"].sample(8000, random_state=1), x="sales", y="transactions",
                     opacity=.25, color_discrete_sequence=[theme.SAND], render_mode="webgl")
    fig.add_trace(go.Scatter(x=est["sales"], y=est["transactions"], mode="markers", name="estimated (118)",
                             marker=dict(color=theme.PERSIMMON, size=7, line=dict(width=1, color=theme.PAPER)),
                             customdata=est[["store_nbr", "date"]], hovertemplate="store %{customdata[0]}, %{customdata[1]|%d %b %Y}<br>sales %{x:,.0f}<br>estimated %{y:,.0f} transactions<extra></extra>"))
    fig.data[0].name = "observed (sample)"
    fig.data[0].showlegend = True
    fig.update_layout(xaxis_title="Total sales of the store-day", yaxis_title="Transactions", xaxis_type="log", yaxis_type="log")
    theme.chart(fig, height=330)
theme.figcap("3.4", "Donut and scatter charts",
             "Left: where each customer count comes from. Right: estimated days (orange) on top of 8,000 real days (grey).",
             "92% of the counts are real. The 118 estimates sit among the real days, which shows the rule gave believable numbers. Most are from 2 to 4 January 2016, when records were missing for 53 stores.",
             "the right chart uses a log scale on both sides; point at an orange dot to see its store and day.")

# ------------------------------------------------------------------ oil before / after
theme.chapter("3.5", "Oil: forward fill, never interpolation",
              "On a Saturday the latest price is still Friday's. Copying it forward uses only the past, so no future information gets in.")
daily = data.load("daily")
yr = st.select_slider("Year", options=sorted(daily["year"].unique()), value=2015)
d = daily[daily["year"] == yr]
fig = go.Figure()
fig.add_trace(go.Scatter(x=d["date"], y=d["oil_price"], mode="lines", line=dict(color=theme.RULE, width=6), name="cleaned",
                         hovertemplate="%{x|%a %d %b}<br>%{y:.2f} USD<extra>cleaned</extra>"))
fig.add_trace(go.Scatter(x=d["date"], y=d["oil_original"], mode="markers", marker=dict(color=theme.TEAL, size=5), name="original price",
                         hovertemplate="%{x|%a %d %b}<br>%{y:.2f} USD<extra>original</extra>"))
filled = d[d["oil_original"].isna()]
fig.add_trace(go.Scatter(x=filled["date"], y=filled["oil_price"], mode="markers", name="filled",
                         marker=dict(color=theme.PERSIMMON, size=6, symbol="diamond"),
                         hovertemplate="%{x|%a %d %b}<br>%{y:.2f} USD (copied from the last trading day)<extra>filled</extra>"))
fig.update_layout(yaxis_title="USD per barrel")
theme.chart(fig, height=400)
theme.figcap("3.5", "Line with markers",
             f"Oil price in {yr}. Blue dots are original prices and orange diamonds were filled in.",
             "Each filled point repeats the last known price, so every weekend looks like a short flat step. No new prices were made up.",
             "change the year with the slider; point at a diamond to see its price.")

# ------------------------------------------------------------------ flags
theme.chapter("3.6", "Clear yes or no holiday columns")
fl = pd.Series(C["flags"]).rename(data.label).rename_axis("flag").reset_index(name="rows").sort_values("rows")
fig = px.bar(fl, x="rows", y="flag", orientation="h", color_discrete_sequence=[theme.OCHRE], text="rows")
fig.update_traces(texttemplate="%{text:,}", textposition="outside", hovertemplate="%{y}: %{x:,} rows<extra></extra>", cliponaxis=False)
fig.update_layout(xaxis_title="Rows with the flag = 1", yaxis_title="")
theme.chart(fig, height=380)
theme.figcap("3.6", "Bar chart", "How many of the 3,000,888 rows are marked yes for each new flag.",
             "Only 5% of rows fall on a real holiday for that store. 12,837 rows whose holiday was moved away now count as normal days, and Work Days are kept apart from holidays.", "")

# ------------------------------------------------------------------ validation
theme.chapter("Validation", "Every rule, checked",
              "Cleaning can only be trusted if it is tested. Automatic checks cover all three million rows, and Pydantic rules describe what a valid row looks like and reject anything else.")
checked = sum(p["checked"] for p in S["pydantic"])
errors = sum(p["errors"] for p in S["pydantic"])
theme.stats([
    (f"{sum(ok for _, ok in S['integrity'])}/{len(S['integrity'])}", "integrity checks pass", "cleaned vs original data"),
    (str(len(S["pydantic"])), "Pydantic models", "store-day, date, row, model row"),
    (f"{checked:,}", "records validated", "in the last recorded run"),
    (str(errors), "validation errors", "", errors == 0),
])

# ------------------------------------------------------------------ integrity
theme.chapter("4.1", "Did cleaning keep the original data intact?",
              "Each line compares the cleaned table with the original. Cleaning may add information, but it must never change a real value.")
theme.ledger(["Check", "Result"],
             [[name, '<span class="ok">PASS</span>' if ok else '<span class="fail">FAIL</span>'] for name, ok in S["integrity"]])

# ------------------------------------------------------------------ models
theme.chapter("4.2", "The Pydantic models",
              "Each set of rules lists the columns and what values they may hold. "
              "<code>ge</code> means this number or more, <code>gt</code> more than this number, and <code>le</code> this number or less. "
              "A value such as 12.5 transactions, −3 sales or an empty oil price is rejected.")
for p in S["pydantic"]:
    with st.expander(f"{p['model']}  ·  {p['level']}  ·  {p['checked']:,} checked  ·  {p['errors']} errors", expanded=p["model"] == "StoreDayTransactions"):
        a, b, c, d = st.columns(4)
        a.markdown(theme.card("Records checked", f"{p['checked']:,}", f"of {p['population']:,} in the table"), unsafe_allow_html=True)
        b.markdown(theme.card("Errors", str(p["errors"]), "rows that broke a rule"), unsafe_allow_html=True)
        c.markdown(theme.card("Time", f"{p['seconds']} s", "for the whole loop"), unsafe_allow_html=True)
        d.markdown(theme.card("Notebook", p["notebook"], "where it runs"), unsafe_allow_html=True)
        theme.ledger(["Field", "Type", "Rules"], [[f"<code>{f['field']}</code>", f["type"], f["rules"]] for f in p["fields"]])

# ------------------------------------------------------------------ coverage matrix
theme.chapter("4.3", "Which check protects which column",
              "Every column is covered by automatic checks. This grid shows which ones also have Pydantic rules of their own.")
cov = pd.DataFrame(S["coverage"])
models = ["StoreDayTransactions", "OilDay", "CleanSalesRow"]
z = [[1 if m in r["pydantic"] else 0 for m in models] + [1] for _, r in cov.iterrows()]
fig = go.Figure(go.Heatmap(z=z, x=models + ["pandas checks"], y=cov["column"], colorscale=[[0, theme.PAPER_2], [1, theme.MOSS]],
                           showscale=False, xgap=3, ygap=2,
                           hovertemplate="%{y} · %{x}: %{z}<extra></extra>"))
fig.update_layout(yaxis=dict(autorange="reversed", tickfont=dict(family=theme.FONT_MONO, size=11)), xaxis=dict(side="top"))
theme.chart(fig, height=820)
covered = int((cov["pydantic"].str.len() > 0).sum())
theme.figcap("4.3", "Coverage matrix",
             f"{covered} of {len(cov)} columns have Pydantic rules, and all {len(cov)} are covered by automatic checks.",
             "The 14 columns without their own Pydantic rule are text columns, some holiday flags and date parts worked out from the date. They are still covered by the automatic checks.",
             "green means that check covers the column.")

# ------------------------------------------------------------------ live run
theme.chapter("4.4", "Run the validation yourself",
              "This runs the rules again right now on the data behind this site.")


class StoreDayTransactions(BaseModel):
    store_nbr: int = Field(ge=1, le=54)
    transactions: int = Field(ge=0)


class OilDay(BaseModel):
    date: date_type
    oil_price: float = Field(gt=0, allow_inf_nan=False)


if st.button("Run Pydantic validation now", type="primary"):
    sd = data.load("store_day")[["store_nbr", "transactions"]]
    od = data.load("daily")[["date", "oil_price"]].copy()
    od["date"] = od["date"].dt.date
    bar = st.progress(0.0, text="Validating store-days")
    errs, rows = 0, sd.to_dict("records")
    start = time.perf_counter()
    for i, row in enumerate(rows):
        try:
            StoreDayTransactions(**row)
        except ValidationError:
            errs += 1
        if i % 9000 == 0:
            bar.progress(i / (len(rows) + len(od)), text=f"Validating store-days · {i:,} / {len(rows):,}")
    oerrs = 0
    for row in od.to_dict("records"):
        try:
            OilDay(**row)
        except ValidationError:
            oerrs += 1
    bar.progress(1.0, text="Done")
    theme.stats([(f"{len(rows):,}", "store-days validated", f"{errs} errors", errs == 0),
                 (f"{len(od):,}", "dates validated", f"{oerrs} errors", oerrs == 0),
                 (f"{time.perf_counter() - start:.2f} s", "elapsed", "")])

theme.chapter("4.5", "Try to break it",
              "Type values for one store and day, and see whether the rule accepts them. This is the same rule used in the project's cleaning notebook.")
c1, c2, c3 = st.columns([1, 1, 2])
store = c1.text_input("store_nbr", "12")
tx = c2.text_input("transactions", "1530")
with c3:
    try:
        obj = StoreDayTransactions(store_nbr=store, transactions=tx)
        st.markdown(f'<div class="insight"><div class="t">Accepted</div><p>store_nbr = {obj.store_nbr}, transactions = {obj.transactions}. '
                    f'Try 0 or 55 for the store, or -4, 12.5 or "abc" for transactions.</p></div>', unsafe_allow_html=True)
    except ValidationError as e:
        msgs = "<br>".join(f"<code>{'.'.join(map(str, err['loc']))}</code>: {theme.esc(err['msg'])} (input: {theme.esc(err['input'])})" for err in e.errors())
        st.markdown(f'<div class="insight" style="border-color:{theme.PERSIMMON}"><div class="t">Rejected</div><p>{msgs}</p></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ download
theme.chapter("3.7", "Download the final clean data",
              "The complete cleaned table as a CSV inside a zip file: 3,000,888 rows, 38 columns, no missing values.")
theme.stats([("3,000,888", "rows"), ("38", "columns", "17 merged and 21 added by cleaning"), ("0", "missing values", "", "good")])
c1, c2 = st.columns([1, 2])
with c1:
    theme.html(theme.card("Everything", "Full table", "One CSV with all five years. Too large for Excel, which stops at about 1 million rows; use Python, Power BI or a database."))
    st.link_button("Download full CSV (36 MB zip)", DOWNLOADS + "cleaned_data.zip", type="primary", width="stretch")
with c2:
    theme.html(theme.card("One year at a time", "Opens in Excel", "Each year is its own CSV of about 650,000 rows (2017 runs to 15 August), so it fits in Excel."))
    for col, year in zip(st.columns(5), range(2013, 2018)):
        col.link_button(str(year), DOWNLOADS + f"cleaned_data_{year}.zip", width="stretch")
theme.ledger(["Columns", "Meaning"], [
    ["id, date, store_nbr, family, sales, onpromotion", "Original sales row"],
    ["city, state, type, cluster", "Store details"],
    ["transactions, transactions_missing, transactions_fill_method", "Receipts, and whether each value was observed, set to 0 or estimated"],
    ["oil_price, oil_price_missing", "Oil price, and whether it was filled"],
    ["holiday_type, holiday_locale, holiday_locale_name, holiday_description, holiday_transferred", "Merged holiday text"],
    ["is_holiday, is_national_holiday, is_regional_holiday, is_local_holiday, is_event, is_work_day", "Active holiday and event flags"],
    ["sales_log1p, sales_extreme_flag, is_earthquake_period", "Log of sales, flagged extreme values, earthquake month"],
    ["year, month, day, day_of_week, day_name, week_of_year, quarter, is_weekend, is_payday", "Date features"],
])

theme.flow_next("views/cleaning.py")
