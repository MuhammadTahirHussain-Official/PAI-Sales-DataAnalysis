import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data, theme

S = data.summary()
M = S["merged"]["missing"]
C = S["clean"]

theme.page_title(
    "Parts 1 & 3 · Extract, transform, load",
    "From five files to <em>one clean table</em>",
    "How the files were joined without losing or duplicating a single sales row, which values were missing after the join, "
    "and exactly which rule filled each of them.")

# ------------------------------------------------------------------ animated pipeline
steps = S["etl_steps"]
nodes = "".join(
    f'<div class="node" style="animation-delay:{0.15 + i * 0.35:.2f}s"><div class="k">{"Extract" if i == 0 else "Join " + str(i)}</div>'
    f'<div class="t">{s["step"]}</div><div class="m">{s["rows"]:,} rows · {s["columns"]} cols</div>'
    f'<div class="j">{s["join"]}<br>key: {s["key"]}</div></div>'
    + (f'<div class="link" style="animation-delay:{0.3 + i * 0.35:.2f}s"><span></span></div>' if i < len(steps) - 1 else "")
    for i, s in enumerate(steps))
flow = f"""<!doctype html><html><head><link rel="stylesheet" href="{theme.FONT_LINK}"><style>
* {{ box-sizing: border-box; margin: 0; }}
body {{ background: {theme.PAPER}; font-family: {theme.FONT_BODY}; color: {theme.INK}; }}
.flow {{ display: flex; align-items: stretch; gap: 0; padding: 6px 2px; }}
.node {{ flex: 1 1 0; background: {theme.CARD}; border: 1px solid {theme.RULE}; border-radius: 14px; padding: 14px 14px 12px;
        opacity: 0; transform: translateY(14px); animation: in .8s cubic-bezier(.2,.7,.1,1) forwards; }}
.node:last-child {{ background: {theme.INK}; color: {theme.PAPER}; border-color: {theme.INK}; }}
.node:last-child .m, .node:last-child .j {{ color: #CFC6B6; }}
.k {{ font-family: {theme.FONT_MONO}; font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: {theme.PERSIMMON}; }}
.t {{ font-family: {theme.FONT_DISPLAY}; font-size: 25px; line-height: 1.05; margin: 6px 0 8px; }}
.m {{ font-family: {theme.FONT_MONO}; font-size: 12px; color: {theme.INK_2}; }}
.j {{ font-size: 12px; color: {theme.MUTED}; margin-top: 8px; line-height: 1.45; }}
.link {{ flex: 0 0 34px; position: relative; opacity: 0; animation: fade .4s forwards; }}
.link span {{ position: absolute; top: 50%; left: 4px; right: 4px; height: 2px; background: {theme.RULE}; overflow: hidden; }}
.link span::after {{ content: ""; position: absolute; inset: 0; width: 40%; background: {theme.PERSIMMON}; animation: travel 1.6s linear infinite; }}
@keyframes in {{ to {{ opacity: 1; transform: none; }} }}
@keyframes fade {{ to {{ opacity: 1; }} }}
@keyframes travel {{ from {{ transform: translateX(-100%); }} to {{ transform: translateX(260%); }} }}
@media (max-width: 760px) {{ .flow {{ flex-direction: column; }} .link {{ flex-basis: 18px; }} }}
</style></head><body><div class="flow">{nodes}</div></body></html>"""
st.iframe(flow, height=210)
theme.figcap("3.0", "Pipeline diagram",
             "The four left joins of Part 1. The sales table stays the left side of every join.",
             "The row count stays 3,000,888 after every join: no sales row was lost and none was duplicated. Joins with many_to_one validation would fail if a store, a store-day or a holiday store-day appeared twice on the right side.",
             "read left to right; the dark box is the final merged table.")

theme.chapter("3.1", "Checks made at every join")
theme.ledger(
    ["Join", "Rule", "Why it matters", "Result"],
    [["stores", "validate='many_to_one', indicator=True", "every store must exist exactly once in stores.csv", '<span class="ok">54 / 54 matched</span>'],
     ["transactions", "validate='many_to_one'", "one record per store-day at most", '<span class="ok">0 duplicate keys</span>'],
     ["oil", "duplicate-date check", "one price per date", '<span class="ok">0 duplicate dates</span>'],
     ["holidays", "aggregate to one row per store-day, then many_to_one", "two events on one day must not double the sales rows", '<span class="ok">9,601 unique store-days</span>'],
     ["every join", "assert rows before == rows after", "nothing lost, nothing multiplied", '<span class="ok">3,000,888 rows</span>']])

# ------------------------------------------------------------------ missing after merge
theme.chapter("3.2", "What was missing after the join",
              "Joining never invents values: where the right-hand file had no match, the new columns are empty. These gaps are what Part 3 cleans.")
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
theme.figcap("3.2", "Grouped bar chart", "Empty values per column in the merged table, before and after cleaning.",
             "The five holiday columns are empty on 91% of rows simply because most days are not holidays. Oil is empty on weekends (928,422 rows), and transactions on 7,448 store-days (245,784 rows). After cleaning every column is complete.",
             "switch off 'after' to see the original gaps alone.")

# ------------------------------------------------------------------ cleaning ledger
theme.chapter("3.3", "The cleaning ledger", "Every rule applied in notebook 03, in order, with how many rows it touched.")
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
theme.figcap("3.4", "Donut and log-log scatter",
             "Left: where each store-day's transaction value comes from. Right: estimated store-days (orange) on top of 8,000 observed ones (sand).",
             "92% of store-days are real observations. The 118 estimates sit inside the cloud of real store-days, so the ratio rule produced plausible values; they cluster on 2 – 4 January 2016 when records were missing for 53 stores.",
             "on the right both axes are logarithmic; hover an orange point to see which store and day it is.")

# ------------------------------------------------------------------ oil before / after
theme.chapter("3.5", "Oil: forward fill, never interpolation",
              "On a Saturday the price in force is still Friday's close. Copying it forward uses only the past, which keeps the data safe for forecasting.")
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
             f"Oil price in {yr}: teal dots are original prices, orange diamonds were filled, the wide grey band is the cleaned series.",
             "Filled points always repeat the previous trading day, so every weekend appears as a short flat step. No price was invented between two known prices.",
             "change the year with the slider; hover a diamond to see that it copies the day before.")

# ------------------------------------------------------------------ flags
theme.chapter("3.6", "Holiday flags replace mixed text")
fl = pd.Series(C["flags"]).rename(data.label).rename_axis("flag").reset_index(name="rows").sort_values("rows")
fig = px.bar(fl, x="rows", y="flag", orientation="h", color_discrete_sequence=[theme.OCHRE], text="rows")
fig.update_traces(texttemplate="%{text:,}", textposition="outside", hovertemplate="%{y}: %{x:,} rows<extra></extra>", cliponaxis=False)
fig.update_layout(xaxis_title="Rows with the flag = 1", yaxis_title="")
theme.chart(fig, height=380)
theme.figcap("3.6", "Bar chart", "How many of the 3,000,888 rows carry each new 0/1 flag.",
             "Only 5% of rows are on an active holiday for their store. 12,837 rows whose only record was transferred away now correctly count as normal days, and Work Days are kept apart from holidays.", "")
