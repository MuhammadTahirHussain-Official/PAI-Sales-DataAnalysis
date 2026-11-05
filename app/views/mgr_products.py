"""Store manager: a colour calendar for one product. Click a day to see why it was high or low."""
import calendar

import pandas as pd
import streamlit as st

from lib import manager as m
from lib import theme
from lib.theme import fmt

theme.page_title("Product page", "Product <em>calendar</em>", "Each box is one day and the number is the units sold. Click a day to see why it was high or low.")
store, per, name = m.picker()
rows = m.store_rows(store)
products = sorted(rows["product"].unique())
ss = st.session_state
default = ss.get("mgr_product", "Grocery I")
default = default if default in products else "Grocery I"
product = st.selectbox("Product", products, index=products.index(default))
ss["mgr_product"] = product

one = rows[rows["product"] == product]
now = one[one["month"] == per].set_index("date").sort_index()
month_name = f"{calendar.month_name[per.month]} {per.year}"
if now["sales"].sum() == 0:
    theme.insight(f"{product} had no sales in {month_name}", "Nothing was sold at this store this month. Choose another product or month.")
    st.stop()

sales = now["sales"]
avg = sales.mean()
best, worst = sales.idxmax(), sales.idxmin()
theme.html(f'<div class="story"><span class="hi">{product}</span> sold <span class="hi">{fmt(sales.sum())} units</span> in {month_name}, about {fmt(avg)} per day. '
           f'Its busiest day was <b class="up">{best:%a} {best.day}</b> with {fmt(sales.max())} units.</div>')
theme.stats([(fmt(sales.sum()), "total this month"), (fmt(avg), "average day"),
             (f"{best:%a} {best.day}", "busiest day", f"{fmt(sales.max())} units", "good"), (f"{worst:%a} {worst.day}", "slowest day", f"{fmt(sales.min())} units", "bad")])


def level(q):
    return "vh" if q >= 1.3 else "hi" if q >= 1.1 else "no" if q >= .9 else "lo" if q >= .7 else "vl"


theme.chapter("Calendar", "Daily sales calendar")
theme.html('<div class="legend"><span><i style="background:#9A3B32"></i>Very low</span><span><i style="background:#5A2A26"></i>Low</span>'
           '<span><i style="background:rgba(255,255,255,.12)"></i>Normal</span><span><i style="background:#1F4D3E"></i>High</span>'
           "<span><i style=\"background:#2E7D5B\"></i>Very high</span><span>compared with this product's average day</span></div>")
day_key = f"day_{store}_{per}_{product}"
chosen = ss.get(day_key, best.day)
with st.container(key="calgrid"):
    head = st.columns(7)
    for col, label in zip(head, ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
        col.markdown(f'<div class="calhead">{label}</div>', unsafe_allow_html=True)
    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(per.year, per.month):
        cols = st.columns(7)
        for col, d in zip(cols, week):
            if d == 0:
                continue
            date = pd.Timestamp(per.year, per.month, d)
            if date not in sales.index:
                col.button(f"{d}  \nno data", key=f"cal_no_off_{d}", disabled=True, width="stretch")
                continue
            prefix = "calsel_" if d == chosen else ""
            key = f"{prefix}cal_{level(sales[date] / avg)}_{d}"
            if col.button(f"{d}  \n{fmt(sales[date])}", key=key, width="stretch"):
                ss[day_key] = d
                st.rerun()

# ------------------------------------------------------------------ why this day
day = pd.Timestamp(per.year, per.month, chosen)
if day not in sales.index:
    day = best
value, q = sales[day], sales[day] / avg
same_wd = sales[sales.index.dayofweek == day.dayofweek].mean()
verdict = ("Very high demand", "up") if q >= 1.3 else ("High demand", "up") if q >= 1.1 else ("Normal day", "") if q >= .9 else ("Low demand", "down") if q >= .7 else ("Very low demand", "down")

reasons = []
wd_effect = same_wd / avg
if wd_effect >= 1.08:
    reasons.append(f"<b>{day:%A}</b> is a busy day for this product: {m.sg(wd_effect - 1)} compared with the average day this month.")
elif wd_effect <= .92:
    reasons.append(f"<b>{day:%A}</b> is usually a quiet day for this product: {m.sg(wd_effect - 1)} compared with the average day this month.")
if day.day == 15 or day == day + pd.offsets.MonthEnd(0):
    reasons.append(f"<b>Payday.</b> Public salaries arrive on the {'15th' if day.day == 15 else 'last day of the month'}.")
for _, h in m.holidays_on(store, day).iterrows():
    reasons.append(f"<b>{h['type']}: {theme.esc(h['description'])}</b>" + ("." if h["locale"] == "National" else f" in {h['locale_name']}."))
promo = int(now.loc[day, "onpromotion"])
if promo > 0:
    with_promo = one[(one["onpromotion"] > 0) & (one["month"] > per - 12) & (one["month"] <= per)]["sales"].mean()
    without = one[(one["onpromotion"] == 0) & (one["month"] > per - 12) & (one["month"] <= per)]["sales"].mean()
    lift = f" Over the past year promotion days sold {m.sg(with_promo / without - 1)} compared with other days." if without and without > 0 else ""
    reasons.append(f"<b>Promotion:</b> {promo} items of this product were on promotion.{lift}")
if value == 0 and m.store_days(store).set_index("date").loc[day, "sales"] == 0:
    reasons.append("<b>The whole store recorded no sales</b> on this day, so it was most likely closed.")
if pd.Timestamp("2016-04-16") <= day <= pd.Timestamp("2016-05-16"):
    reasons.append("<b>Earthquake month.</b> Shoppers bought and donated food and water across the country.")
if not reasons:
    reasons.append("No holiday, payday or promotion on this day. This is ordinary day-to-day variation.")

action = ("Stock up the day before and put extra staff on the floor." if q >= 1.1 else
          "Do not over-order for a day like this. A small offer could lift sales." if q < .9 else "No action needed. Keep normal stock and staffing.")
theme.html(f'<div class="explain"><div class="eyebrow">{day:%A} {day.day} {month_name} · {product}</div><h3>{fmt(value)} units</h3>'
           f'<div class="verdict"><span class="{verdict[1]}">{verdict[0]}</span> · {m.sg(q - 1)} vs the average day</div>'
           f'<p>Average day: {fmt(avg)} units. Average {day:%A} this month: {fmt(same_wd)} units.</p>'
           f'<div class="eyebrow" style="margin-top:14px">Why this happened</div><ol>{"".join(f"<li>{r}</li>" for r in reasons)}</ol>'
           f'<div class="eyebrow" style="margin-top:14px">What to do</div><p>{action}</p></div>')
st.page_link("views/mgr_dashboard.py", label="Back to business overview", icon=":material/arrow_back:")
