"""Store manager: what happened in my store this month, in plain words."""
import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import manager as m
from lib import theme
from lib.data import WEEKDAYS
from lib.theme import fmt

theme.page_title("For store managers", "Business <em>overview</em>",
                 "Choose your store and month. Real sales from the cleaned data, explained without any technical words.")
store, per, name = m.picker()
rows, days = m.store_rows(store), m.store_days(store)
now, last = rows[rows["month"] == per], rows[rows["month"] == per - 1]
n_days, n_prev = now["date"].nunique(), last["date"].nunique()
store_total = now["sales"].sum()
month_name = f"{m.MONTHS[per.month - 1]} {per.year}"
if store_total == 0:
    theme.insight(f"{name} had no sales in {month_name}", "This store had not opened yet. Choose a later month.")
    st.stop()

# per-product table for this month
tab = now.groupby("product")["sales"].sum().rename("units").to_frame()
tab["prev"] = last.groupby("product")["sales"].sum()
tab["per_day"] = tab["units"] / n_days
tab["change"] = (tab["per_day"] / (tab["prev"] / n_prev).where(tab["prev"] > 0)) - 1 if n_prev else float("nan")
tab = tab.sort_values("units", ascending=False)

st.session_state.setdefault("mgr_product", "All products")
product = st.session_state["mgr_product"]
sel = rows if product == "All products" else rows[rows["product"] == product]
daily = sel[sel["month"] == per].groupby("date")["sales"].sum()
total, prev_total = daily.sum(), sel[sel["month"] == per - 1]["sales"].sum()
delta = (total / n_days) / (prev_total / n_prev) - 1 if n_prev and prev_total > 0 else None
best_day, worst_day = daily.idxmax(), daily.idxmin()
who = "your store" if product == "All products" else f'<span class="hi">{product}</span>'

theme.html(f'<div class="story"><b>{month_name}:</b> {who} sold <span class="hi">{fmt(total)} units</span>'
           + (f', <b class="{"up" if delta >= 0 else "down"}">{abs(delta) * 100:.0f}% {"more" if delta >= 0 else "less"}</b> per day than the month before.' if delta is not None else ". This is the first month with sales.")
           + (f' Your best seller was <span class="hi">{tab.index[0]}</span>.' if product == "All products" else f" That is {total / store_total * 100:.1f}% of your store's sales.")
           + "</div>")
theme.stats([
    (fmt(total), "units sold this month"),
    (m.sg(delta) if delta is not None else "–", "per day vs last month", "", ("good" if delta >= 0 else "bad") if delta is not None else False),
    (f"{best_day:%a} {best_day.day}", "busiest day", f"{fmt(daily.max())} units"),
    (tab.index[0] if product == "All products" else f"{total / store_total * 100:.1f}%", "best-selling product" if product == "All products" else "share of store sales",
     f"{tab['units'].iloc[0] / store_total * 100:.0f}% of the store" if product == "All products" else ""),
])

# ------------------------------------------------------------------ products
theme.chapter("What sold", "What each product sold")
view = tab.iloc[::-1]
colors = [theme.CORAL if pd.notna(c) and c < 0 else theme.PERSIMMON if p in tab.index[:3] else theme.TEAL for p, c in zip(view.index, view["change"])]
labels = [f"{fmt(u)}  {m.sg(c) if pd.notna(c) else ''}" for u, c in zip(view["units"], view["change"])]
fig = go.Figure(go.Bar(x=view["units"], y=view.index, orientation="h", marker_color=colors, text=labels, textposition="outside", cliponaxis=False,
                       hovertemplate="%{y}<br>%{x:,.0f} units<extra></extra>"))
fig.update_xaxes(type="log", title="Units sold this month (log scale, so small products stay visible)")
fig.update_layout(yaxis=dict(dtick=1), margin=dict(r=110))
event = theme.chart(fig, key=f"bars_{store}_{per}", select=True, height=860)
theme.figcap("M.1", "Ranked bars", "All 33 products, best seller at the top.",
             "Orange = top 3. Red = sold less per day than last month. Blue = everything else. The percentage compares units per day with last month.",
             "click a product to see it day by day below.")
points = event.selection.points if event and event.selection else []
if points and points[0]["y"] != st.session_state.get("mgr_click"):
    st.session_state["mgr_click"] = points[0]["y"]
    st.session_state["mgr_product"] = points[0]["y"]
    st.rerun()

# ------------------------------------------------------------------ day by day
theme.chapter("Day by day", "Sales day by day")
options = ["All products"] + list(tab.index)
choice = st.selectbox("Product", options, index=options.index(product), key=f"prod_{product}")
if choice != product:
    st.session_state["mgr_product"] = choice
    st.rerun()
fig = go.Figure()
for d in daily.index:
    if d.dayofweek >= 5:
        fig.add_vrect(x0=d - pd.Timedelta(hours=12), x1=d + pd.Timedelta(hours=12), fillcolor="rgba(255,255,255,.07)", line_width=0)
fig.add_trace(go.Scatter(x=daily.index, y=daily.values, mode="lines+markers", line=dict(color=theme.PERSIMMON, width=2.5), marker=dict(size=6),
                         fill="tozeroy", fillcolor="rgba(255,138,76,.1)", hovertemplate="%{x|%a %d %b}<br>%{y:,.0f} units<extra></extra>", showlegend=False))
fig.add_trace(go.Scatter(x=[best_day], y=[daily.max()], mode="markers+text", text=["Best day"], textposition="top center", marker=dict(size=12, color=theme.MOSS),
                         textfont=dict(color=theme.MOSS), hoverinfo="skip", showlegend=False))
fig.add_trace(go.Scatter(x=[worst_day], y=[daily.min()], mode="markers+text", text=["Slowest"], textposition="bottom center", marker=dict(size=12, color=theme.OCHRE),
                         textfont=dict(color=theme.OCHRE), hoverinfo="skip", showlegend=False))
fig.update_layout(yaxis_title="Units sold", xaxis_title="", yaxis_rangemode="tozero")
theme.chart(fig, height=380)
theme.figcap("M.2", "Line chart", f"Units sold each day in {month_name}: {product.lower() if product != 'All products' else 'all products'}.",
             f"Lighter stripes are weekends. Best day: {best_day:%A} {best_day.day}. Slowest: {worst_day:%A} {worst_day.day}.", "higher means more units sold that day; hover for any day.")

# ------------------------------------------------------------------ year trend
start = per - 11
months = sel[(sel["month"] >= start) & (sel["month"] <= per)].groupby("month").agg(units=("sales", "sum"), dates=("date", "nunique"))
months["per_day"] = months["units"] / months["dates"]
ly = sel[sel["month"] == per - 12]
yoy = (total / n_days) / (ly["sales"].sum() / ly["date"].nunique()) - 1 if len(ly) and ly["sales"].sum() > 0 else None
fig = go.Figure(go.Scatter(x=[f"{m.MONTHS[p.month - 1]} {str(p.year)[2:]}" for p in months.index], y=months["per_day"], mode="lines+markers",
                           line=dict(color=theme.TEAL, width=2.5), marker=dict(size=7), hovertemplate="%{x}<br>%{y:,.0f} units per day<extra></extra>"))
fig.update_layout(yaxis_title="Units per day", yaxis_rangemode="tozero")
theme.chart(fig, height=300)
theme.figcap("M.3", "Line chart", "Average units per day, last 12 months.",
             "A rising line means growing." + (f" Versus {m.MONTHS[per.month - 1]} {per.year - 1}: {m.sg(yoy)}." if yoy is not None else ""), "")

# ------------------------------------------------------------------ quick insights and goal
whole = now.groupby("date")["sales"].sum()
we, wd = whole[whole.index.dayofweek >= 5].mean(), whole[whole.index.dayofweek < 5].mean()
rising = int((tab["change"] > 0).sum())
c1, c2, c3 = st.columns(3)
c1.markdown(theme.card("Weekends", f"{abs(we / wd - 1) * 100:.0f}% {'more' if we >= wd else 'less'}", "Units per day on weekends compared with weekdays."), unsafe_allow_html=True)
peak = whole.idxmax()
c2.markdown(theme.card("Peak day", f"{whole.max() / whole.mean():.1f} times", f"{peak:%A} {peak.day} sold this much more than an average day."), unsafe_allow_html=True)
c3.markdown(theme.card("Products", f"{rising} of 33 rising", "Products selling more per day than last month.") if n_prev else theme.card("Products", "First month", "No comparison yet."), unsafe_allow_html=True)

theme.chapter("Goal", "Monthly goal", "Goal = 8% more than the same month last year.")
same = days[days["month"] == per - 12]["sales"].sum()
if same > 0:
    goal = same * 1.08
    partial = per == m.LAST
    pace = store_total / n_days * per.days_in_month if partial else store_total
    pct = pace / goal * 100
    color = theme.MOSS if pct >= 100 else theme.OCHRE if pct >= 95 else theme.CORAL
    verdict = ("On track" if partial else "Goal reached") if pct >= 100 else "Almost there" if pct >= 95 else "Behind the goal"
    theme.html(f'<div class="card"><h4 style="color:{color}">{pct:.0f}% of goal · {verdict}</h4>'
               f'<div class="goalbar"><i style="width:{min(pct, 120) / 120 * 100:.1f}%;background:{color}"></i><span></span></div>'
               f'<p>Goal: <b>{fmt(goal)}</b> units. ' + (f"So far {fmt(store_total)} (1 to 15 August); at this pace you finish near <b>{fmt(pace)}</b>." if partial else f"Final: <b>{fmt(store_total)}</b> units.")
               + f' {fmt(abs(pace - goal))} units {"above" if pace >= goal else "short of"} the goal. The white line marks the goal.</p></div>')
else:
    theme.html(theme.card("Goal", "Not available yet", "A goal needs the same month from last year for this store."))

# ------------------------------------------------------------------ weekdays and movers
c1, c2 = st.columns(2)
with c1:
    theme.chapter("Staffing", "Best days of the week")
    wk = whole.groupby(whole.index.day_name()).mean().reindex(WEEKDAYS)
    top_day = wk.idxmax()
    fig = go.Figure(go.Bar(x=[d[:3] for d in WEEKDAYS], y=wk.values, marker_color=[theme.PERSIMMON if d == top_day else theme.SAND for d in WEEKDAYS],
                           hovertemplate="%{x}<br>%{y:,.0f} units on average<extra></extra>"))
    fig.update_layout(yaxis_title="Average units")
    theme.chart(fig, height=320)
    theme.figcap("M.4", "Bar chart", "Average units per weekday this month.",
                 f"{top_day} is the busiest, {(wk.max() / whole.mean() - 1) * 100:.0f}% above an average day. Schedule more staff and restock the day before.", "")
with c2:
    theme.chapter("Reorder", "Products to watch")
    table = tab[(tab["units"] >= 30) & tab["change"].notna()].copy()
    table["next_month"] = (table["per_day"] * (1 + table["change"].clip(-.25, .25)) * 30).round()
    table["order"] = (table["next_month"] * 1.1).round()
    if len(table):
        table = table.sort_values("change", ascending=False)
        line = lambda row, cls: f'<div class="mv"><span>{row.Index}</span><span><b class="{cls}">{m.sg(row.change)}</b> · order about <b>{fmt(row.order)}</b> units</span></div>'
        theme.html('<div class="card"><div class="meta">Rising fastest</div>' + "".join(line(r, "up") for r in table.head(3).itertuples())
                   + '<div class="meta" style="margin-top:14px">Falling fastest</div>' + "".join(line(r, "down") for r in table.tail(3).iloc[::-1].itertuples())
                   + "<p>Suggested order = expected sales next month (change limited to 25%) plus 10% safety stock. We do not have stock counts, so subtract what you already hold.</p></div>")
        buffer = io.BytesIO()
        out = table.reset_index()[["product", "units", "change", "next_month", "order"]]
        out.columns = ["Product", "Units this month", "Change per day vs last month", "Expected next month", "Suggested order"]
        out.to_excel(buffer, index=False, sheet_name=month_name)
        st.download_button("Download order list (Excel)", buffer.getvalue(), file_name=f"store{store}-order-list-{per}.xlsx")
    else:
        theme.html(theme.card("Reorder", "Available from the second month", "A comparison with last month is needed."))

c1, c2 = st.columns(2)
c1.page_link("views/mgr_products.py", label="See one product day by day, and why", icon=":material/arrow_forward:")
c2.page_link("views/mgr_insights.py", label="Insights and what to do next", icon=":material/arrow_forward:")
