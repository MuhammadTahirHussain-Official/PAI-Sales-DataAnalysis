import time
from datetime import date as date_type

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from pydantic import BaseModel, Field, ValidationError

from lib import data, theme

S = data.summary()

theme.page_title(
    "Technical · Step 3",
    "Every rule, <em>checked</em>",
    "Cleaning is only trustworthy if it is tested. The project checks itself in two ways: pandas assertions over all three million rows, "
    "and Pydantic models that describe what a valid row looks like and reject anything else.")

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
              "Each line compares the cleaned table with the merged table it came from. Cleaning may add information; it must never change an observation.")
theme.ledger(["Check", "Result"],
             [[name, '<span class="ok">PASS</span>' if ok else '<span class="fail">FAIL</span>'] for name, ok in S["integrity"]])

# ------------------------------------------------------------------ models
theme.chapter("4.2", "The Pydantic models",
              "A Pydantic model is a small class: one line per column, with its type and allowed range. "
              "<code>ge</code> means greater or equal, <code>gt</code> greater than, <code>le</code> less or equal. "
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
theme.chapter("4.3", "Coverage: which column is protected by what",
              "Every column of the cleaned table is covered by the pandas checks. The heat map shows which ones are also validated field by field by a Pydantic model.")
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
             f"{covered} of {len(cov)} cleaned columns are validated by at least one Pydantic model; all {len(cov)} are covered by pandas assertions.",
             "The 14 columns without a Pydantic rule are the five holiday text columns, the national / regional / local holiday flags, "
             "transactions_fill_method and the calendar parts recalculated from the date (year, day, day_name, week_of_year, quarter). "
             "They are checked by pandas assertions instead (flags only 0/1, months 1 – 12, weekdays 0 – 6, text never empty). "
             "Adding them to CleanSalesRow is an easy next step.",
             "green means the column is validated by that check; hover for details.")

# ------------------------------------------------------------------ live run
theme.chapter("4.4", "Run the validation yourself",
              "This re-runs the store-day and oil models on the data bundled with this site, right now, in your browser session.")


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
              "Type values for one store-day and see how Pydantic answers. This is exactly the rule used in notebook 03, section 15.8.")
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
