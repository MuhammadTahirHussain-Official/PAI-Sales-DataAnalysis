"""Store manager: promotions, special days, customers, unusual days, store comparison, next actions."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import data
from lib import manager as m
from lib import theme
from lib.theme import fmt

theme.page_title("Business insights", "Insights and <em>actions</em>", "What worked, what looks unusual and what to do next at your store.")
store, per, name = m.picker()
rows, days = m.store_rows(store), m.store_days(store)
month_name = f"{m.MONTHS[per.month - 1]} {per.year}"
month = days[days["month"] == per].copy()
if month["sales"].sum() == 0:
    theme.insight(f"{name} had no sales in {month_name}", "This store had not opened yet. Choose a later month.")
    st.stop()
n = len(month)
all_stores = data.load("store_day")
meta = data.stores().set_index("store_nbr")

# ---- calculations used by the sections and by the action list
year = rows[(rows["month"] > per - 12) & (rows["month"] <= per)].copy()
year["ratio"] = year["sales"] / year.groupby("product")["sales"].transform("mean").replace(0, np.nan)
year["group"] = np.where(year["onpromotion"] > 0, "Promoted", "Not promoted")
has_promo = (year["onpromotion"] > 0).any()
top_products = rows.groupby("product")["sales"].sum().nlargest(8).index
lift = None
if has_promo:
    # a product needs at least 10 days of each kind, otherwise there is nothing fair to compare
    stats = year[year["product"].isin(top_products)].groupby(["product", "group"])["sales"].agg(["mean", "size"]).unstack()
    if ("mean", "Promoted") in stats.columns and ("mean", "Not promoted") in stats.columns:
        fair = (stats[("size", "Promoted")] >= 10) & (stats[("size", "Not promoted")] >= 10) & (stats[("mean", "Not promoted")] > 0)
        lift = (stats[("mean", "Promoted")] / stats[("mean", "Not promoted")] - 1)[fair].sort_values(ascending=False)
promo_lift = year[year["group"] == "Promoted"]["ratio"].mean() / year[year["group"] == "Not promoted"]["ratio"].mean() - 1 if has_promo else None

selling = days[days["sales"] > 0].copy()
selling["base"] = selling["sales"] / selling.groupby("month")["sales"].transform("mean") * 100
selling["kind"] = "Weekday Mon to Thu"
selling.loc[selling["date"].dt.dayofweek == 4, "kind"] = "Friday"
selling.loc[selling["date"].dt.dayofweek == 5, "kind"] = "Saturday"
selling.loc[selling["date"].dt.dayofweek == 6, "kind"] = "Sunday"
selling.loc[selling["is_payday"] == 1, "kind"] = "Payday (15th, month end)"
selling.loc[selling["is_event"] == 1, "kind"] = "Event day"
selling.loc[selling["is_holiday"] == 1, "kind"] = "Holiday"
kinds = selling.groupby("kind")["base"].mean().sort_values()

values = month["sales"]
q1, q3 = values.quantile(.25), values.quantile(.75)
low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
flags = month[(values > high) | (values < low)].copy()
flags["known"] = [" · ".join(m.holidays_on(store, d)["description"]) for d in flags["date"]]
unexplained = flags[flags["known"] == ""]

per_day = all_stores.assign(month=all_stores["date"].dt.to_period("M"))
per_day = per_day[per_day["month"] == per]
store_avgs = per_day.groupby("store_nbr")["sales"].mean()
store_avgs = store_avgs[store_avgs > 0]
rank = int(store_avgs.rank(ascending=False)[store]) if store in store_avgs.index else None
vs_chain = store_avgs[store] / store_avgs.mean() - 1
region_ids = meta.index[meta["state"] == meta.loc[store, "state"]]

# ------------------------------------------------------------------ actions
theme.chapter("Do this next", "What to do next", "Suggestions generated from the analysis on this page, most important first.")
actions = []
if len(unexplained):
    dates = ", ".join(f"{m.MONTHS[d.month - 1]} {d.day}" for d in unexplained["date"].head(3))
    actions.append((theme.CORAL, "Check unusual days", "High", f"{len(unexplained)} day(s) had unexplained sales ({dates}). Check stock records, staff notes and local events."))
if vs_chain < 0:
    actions.append((theme.CORAL, "Catch up with the chain", "High", f"Your store sells {abs(vs_chain) * 100:.0f}% less per day than the chain average. Compare your top products with stores in your region."))
weekend = kinds.get("Sunday", 100)
actions.append((theme.OCHRE, "Prepare for weekends", "Medium", f"Sundays sell {weekend - 100:+.0f}% and Saturdays {kinds.get('Saturday', 100) - 100:+.0f}% against an average day. Increase availability before Saturday."))
if "Payday (15th, month end)" in kinds:
    actions.append((theme.OCHRE, "Check payday staffing", "Medium", f"Paydays sell {kinds['Payday (15th, month end)'] - 100:+.0f}% against an average day at this store. Plan staff and stock from this number."))
if lift is not None and len(lift):
    actions.append((theme.OCHRE, "Use promotions where they work", "Medium", f"Promotions lift {lift.index[0]} most ({m.sg(lift.iloc[0])}). Try the next promotion there, on a quiet weekday."))
theme.html("".join(f'<div class="action"><div class="bar" style="background:{c}"></div><div><b>{t}</b><span class="tag" style="color:{c}">{lv}</span><p>{txt}</p></div></div>' for c, t, lv, txt in actions))

# ------------------------------------------------------------------ promotions
theme.chapter("Promotions", "Promotion effectiveness", "Last 12 months at your store.")
if has_promo and lift is not None and len(lift):
    view = lift.sort_values()
    fig = go.Figure(go.Bar(x=view.values, y=view.index, orientation="h", marker_color=[theme.PERSIMMON if v > 0 else theme.CORAL for v in view.values],
                           text=[m.sg(v) for v in view.values], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:+.0%}<extra></extra>"))
    fig.update_layout(xaxis_tickformat="+.0%", xaxis_title="How much more sold on promotion days", margin=dict(r=60))
    theme.chart(fig, height=max(260, 44 * len(view)))
    theme.figcap("I.1", "Bar chart", "How much more each big product sold on promotion days.",
                 f"Best result: {lift.index[0]} ({m.sg(lift.iloc[0])}). Overall, products sold about {m.sg(promo_lift)} on promotion days, partly because stores promote what already sells well. "
                 "Products on promotion almost every day are left out, because there is nothing to compare them with.", "")
else:
    theme.html(theme.card("Promotions", "No promotions recorded", "Promotions are recorded from 2014. Choose a later month."))

# ------------------------------------------------------------------ special days
theme.chapter("Special days", "Holidays, weekends and payday", "All months at your store. 100% = an average day of that month.")
c1, c2 = st.columns(2)
with c1:
    fig = go.Figure(go.Bar(x=kinds.values, y=kinds.index, orientation="h", marker_color=[theme.PERSIMMON if v >= 100 else theme.CORAL for v in kinds.values],
                           text=[f"{v:.0f}%" for v in kinds.values], textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x:.0f}%<extra></extra>"))
    fig.add_vline(x=100, line=dict(color=theme.INK, width=1, dash="dot"))
    fig.update_layout(xaxis_title="% of an average day", margin=dict(r=60))
    theme.chart(fig, height=340)
    theme.figcap("I.2", "Bar chart", "Sales on each type of day.", f"{kinds.index[-1]} is your strongest kind of day; {kinds.index[0]} the weakest.", "right of the dotted line means above an average day.")
with c2:
    dec_year = per.year if per.month == 12 else per.year - 1
    dec = days[(days["date"] >= f"{dec_year}-12-15") & (days["date"] <= f"{dec_year}-12-31")]
    normal = days[days["month"] == pd.Period(f"{dec_year}-11", "M")]["sales"].mean() if dec_year >= 2013 else None
    if len(dec) and normal:
        fig = go.Figure(go.Scatter(x=dec["date"], y=dec["sales"] / normal * 100, mode="lines+markers", line=dict(color=theme.OCHRE, width=2.5),
                                   hovertemplate="%{x|%a %d %b}<br>%{y:.0f}% of a normal November day<extra></extra>"))
        fig.update_layout(yaxis_title="% of a normal November day", yaxis_rangemode="tozero")
        theme.chart(fig, height=340)
        theme.figcap("I.3", "Line chart", f"Late December {dec_year} at your store.", f"The highest day was {dec.loc[dec['sales'].idxmax(), 'date']:%A %d December}. There is no 25 December because stores are closed. Stock up before the peak.", "")
    else:
        theme.html(theme.card("Christmas", "Available from December 2013", "This store has no earlier December in the data."))

# ------------------------------------------------------------------ unusual days
theme.chapter("Unusual days", "Unusual sales days")
fig = go.Figure(go.Scatter(x=month["date"], y=month["sales"], mode="lines+markers", line=dict(color=theme.PERSIMMON, width=2.2), showlegend=False,
                           hovertemplate="%{x|%a %d %b}<br>%{y:,.0f} units<extra></extra>"))
if len(flags):
    fig.add_trace(go.Scatter(x=flags["date"], y=flags["sales"], mode="markers", marker=dict(size=13, color=theme.CORAL, symbol="circle-open", line=dict(width=2.5)), showlegend=False, hoverinfo="skip"))
fig.update_layout(yaxis_title="Units sold", yaxis_rangemode="tozero")
theme.chart(fig, height=320)
theme.figcap("I.4", "Line chart", f"{len(flags)} unusual day(s) in {month_name}" + (f", {len(unexplained)} without a known reason." if len(flags) else "."),
             "A day is flagged when it is far outside the normal range of this month (circled in red).", "")
if len(flags):
    theme.html("".join(f'<div class="mv"><span><b>{r.date:%a %b %d}</b> · {fmt(r.sales)} units</span><span>{("Explained: " + theme.esc(r.known)) if r.known else "Investigate: no holiday or event on this day. Check stock, staff notes or a bulk order."}</span></div>' for r in flags.itertuples()))

# ------------------------------------------------------------------ comparison
theme.chapter("Compare", "How your store compares", f"Your store ranks #{rank} of {len(store_avgs)} by units per day. Region = stores in {meta.loc[store, 'state']}. You see only averages of other stores.")
region = per_day[per_day["store_nbr"].isin(region_ids)]
zero_share = lambda d: d["zero_families"].mean() / 33 * 100
per_tx = lambda d: d["sales"].sum() / d["transactions"].sum() if d["transactions"].sum() else 0
mine = per_day[per_day["store_nbr"] == store]
metrics = [
    ("Units sold per day", lambda d: d["sales"].mean(), fmt),
    ("Customers per day", lambda d: d["transactions"].mean(), fmt),
    ("Units per customer", per_tx, lambda v: f"{v:.1f}"),
    ("Products with zero sales (lower is better)", zero_share, lambda v: f"{v:.0f}%"),
    ("Items on promotion per day", lambda d: d["promotions"].mean(), fmt),
]
cols = st.columns(2)
for i, (title, calc, show) in enumerate(metrics):
    vals = [("Your store", calc(mine)), ("Region average", calc(region)), ("Chain average", calc(per_day))]
    cols[i % 2].markdown(f'<div class="card" style="margin-bottom:1.5rem"><div class="meta">{title}</div>' + m.bars_html([(a, b, show(b)) for a, b in vals]) + "</div>", unsafe_allow_html=True)
st.page_link("views/mgr_dashboard.py", label="Back to business overview", icon=":material/arrow_back:")
