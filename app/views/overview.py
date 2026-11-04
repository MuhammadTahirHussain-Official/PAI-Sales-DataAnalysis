import numpy as np
import streamlit as st

from lib import data, theme

S = data.summary()
daily = data.load("daily")
raw = S["raw"]

# ------------------------------------------------------------------ hero (animated)
weekly = daily.set_index("date")["sales"].resample("W").mean()
ys = weekly.values
xs = np.linspace(0, 1000, len(ys))
ys_n = 300 - (ys - ys.min()) / (ys.max() - ys.min()) * 250
path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys_n))
area = path + f" L1000,320 L0,320 Z"
years = [(1000 * i / 4.62, str(2013 + i)) for i in range(5)]
counters = [
    (raw["train"]["rows"], "rows in the training table", ""),
    (54, "stores across Ecuador", ""),
    (33, "product families", ""),
    (raw["train"]["dates"], "days, 2013 to 2017", ""),
    (round(raw["train"]["sales"]["total"] / 1e9, 2), "billion units sold", "bn"),
]

hero = f"""
<!doctype html><html><head>
<link rel="stylesheet" href="{theme.FONT_LINK}">
<style>
  * {{ box-sizing: border-box; margin: 0; }}
  body {{ background: {theme.PAPER}; color: {theme.INK}; font-family: {theme.FONT_BODY}; overflow: hidden; }}
  .wrap {{ position: relative; padding: 8px 4px 0; }}
  .eyebrow {{ font-family: {theme.FONT_MONO}; font-size: 12px; letter-spacing: .18em; text-transform: uppercase; color: {theme.PERSIMMON};
             opacity: 0; animation: up .8s .1s cubic-bezier(.2,.7,.1,1) forwards; }}
  h1 {{ font-family: {theme.FONT_DISPLAY}; font-weight: 400; font-size: clamp(44px, 6.6vw, 92px); line-height: .95; letter-spacing: -.015em; margin: 14px 0 18px; max-width: 980px; }}
  h1 span {{ display: inline-block; opacity: 0; transform: translateY(40px); animation: up 1s cubic-bezier(.2,.7,.1,1) forwards; }}
  h1 em {{ color: {theme.PERSIMMON}; }}
  p.lede {{ font-size: 18px; line-height: 1.6; color: {theme.INK_2}; max-width: 640px; opacity: 0; animation: up 1s .9s cubic-bezier(.2,.7,.1,1) forwards; }}
  svg {{ width: 100%; height: 230px; margin-top: 18px; overflow: visible; }}
  .line {{ fill: none; stroke: {theme.TEAL}; stroke-width: 1.6; stroke-dasharray: 4000; stroke-dashoffset: 4000; animation: draw 3.2s .6s cubic-bezier(.6,.1,.2,1) forwards; }}
  .area {{ fill: url(#g); opacity: 0; animation: fade 1.6s 2.4s forwards; }}
  .yr {{ font-family: {theme.FONT_MONO}; font-size: 11px; fill: {theme.MUTED}; }}
  .tick {{ stroke: {theme.RULE}; }}
  .dot {{ fill: {theme.PERSIMMON}; opacity: 0; animation: fade .4s 3.6s forwards, pulse 2.4s 4s infinite; transform-origin: center; transform-box: fill-box; }}
  .row {{ display: grid; grid-template-columns: repeat(5, 1fr); border-top: 1px solid {theme.INK}; margin-top: 10px; }}
  .c {{ padding: 16px 16px 6px 0; border-right: 1px solid {theme.RULE}; opacity: 0; animation: up .9s cubic-bezier(.2,.7,.1,1) forwards; }}
  .c:last-child {{ border-right: none; }}
  .c .v {{ font-family: {theme.FONT_DISPLAY}; font-size: 40px; line-height: 1; }}
  .c .k {{ font-family: {theme.FONT_MONO}; font-size: 10.5px; letter-spacing: .14em; text-transform: uppercase; color: {theme.MUTED}; margin-top: 8px; }}
  @keyframes up {{ to {{ opacity: 1; transform: none; }} }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  @keyframes fade {{ to {{ opacity: 1; }} }}
  @keyframes pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.8); }} }}
  @media (max-width: 760px) {{ .row {{ grid-template-columns: repeat(2, 1fr); }} .c .v {{ font-size: 28px; }} .c {{ padding-top: 10px; }}
                              svg {{ height: 120px; }} p.lede {{ font-size: 15px; }} h1 {{ font-size: 38px; }} }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation-duration: .01s !important; animation-delay: 0s !important; }} }}
</style></head><body><div class="wrap">
  <div class="eyebrow">Store Sales · Ecuador · Kaggle dataset · EDA &amp; ETL report</div>
  <h1><span style="animation-delay:.15s">Fifty-four&nbsp;</span><span style="animation-delay:.25s">stores,&nbsp;</span><span style="animation-delay:.35s">five&nbsp;</span><span style="animation-delay:.45s">years,&nbsp;</span><span style="animation-delay:.6s"><em>one&nbsp;story</em>&nbsp;</span><span style="animation-delay:.7s">of&nbsp;how&nbsp;</span><span style="animation-delay:.8s">people&nbsp;shop.</span></h1>
  <p class="lede">An interactive walk through three million rows of grocery sales: what the raw files contain, how they were joined and cleaned, how every rule was validated, and what the cleaned data finally tells us.</p>
  <svg viewBox="0 0 1000 330" preserveAspectRatio="none">
    <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="{theme.TEAL}" stop-opacity=".18"/><stop offset="1" stop-color="{theme.TEAL}" stop-opacity="0"/></linearGradient></defs>
    {''.join(f'<line class="tick" x1="{x:.0f}" x2="{x:.0f}" y1="0" y2="320"/><text class="yr" x="{x + 6:.0f}" y="326">{t}</text>' for x, t in years)}
    <path class="area" d="{area}"/><path class="line" d="{path}"/>
    <circle class="dot" cx="{xs[-1]:.1f}" cy="{ys_n[-1]:.1f}" r="4"/>
  </svg>
  <div class="row">{''.join(f'<div class="c" style="animation-delay:{1.2 + i * .12:.2f}s"><div class="v" data-n="{n}" data-u="{u}">0</div><div class="k">{k}</div></div>' for i, (n, k, u) in enumerate(counters))}</div>
</div>
<script>
  document.querySelectorAll('[data-n]').forEach(function(el, i) {{
    const n = parseFloat(el.dataset.n), u = el.dataset.u, dec = (n % 1) ? 2 : 0;
    const start = performance.now() + 1200 + i * 120, dur = 1600;
    function tick(t) {{
      const p = Math.min(Math.max((t - start) / dur, 0), 1), e = 1 - Math.pow(1 - p, 4);
      el.textContent = (n * e).toLocaleString('en-US', {{minimumFractionDigits: dec, maximumFractionDigits: dec}}) + (u ? ' ' + u : '');
      if (p < 1) requestAnimationFrame(tick);
    }}
    requestAnimationFrame(tick);
  }});
</script></body></html>
"""
st.iframe(hero, height=720)
theme.figcap("00", "Weekly average of daily sales",
             "The line is the real weekly average of total daily sales, 2013 – 2017.",
             "Sales roughly doubled over five years, with a sharp climb every December and a collapse to near zero every 1 January.",
             "left to right is time; higher means more units sold that week.")

# ------------------------------------------------------------------ the grain
theme.chapter("01", "What one row means",
              "Before any chart makes sense we need to know what is being counted. Every row of the training table "
              "is <b>one product family, in one store, on one day</b>. Everything else is added around that grain.")
c1, c2, c3 = st.columns([1, 1, 1])
c1.markdown(theme.card("Grain", "date × store × family",
                       "1,684 days × 54 stores × 33 families = 3,000,888 rows. Each row says how many units of that family the store sold that day, and how many items were on promotion."),
            unsafe_allow_html=True)
c2.markdown(theme.card("Store-day measures", "repeated on 33 rows",
                       "Transactions (receipts) and holidays belong to a whole store on one day. After the merge, the same value sits on all 33 family rows of that store-day: never add them up across families."),
            unsafe_allow_html=True)
c3.markdown(theme.card("Day measures", "repeated on 1,782 rows",
                       "The oil price belongs to a date only. It is the same for every store and family on that day, and it is missing on weekends because the oil market is closed."),
            unsafe_allow_html=True)

# ------------------------------------------------------------------ sources
theme.chapter("02", "Five files, one table",
              "The Kaggle competition ships five CSV files. Part 1 of the project joins them into one table without changing the number of sales rows.")
src = [
    ("train.csv", f"{raw['train']['rows']:,} rows", "Sales and promotions per date, store and family. The thing we want to understand and later forecast."),
    ("stores.csv", "54 rows", "City, state, store type (A–E) and cluster of every store."),
    ("transactions.csv", f"{raw['transactions']['rows']:,} rows", "Number of receipts per store and day. Some store-days have no record."),
    ("oil.csv", f"{raw['oil']['rows']:,} rows", "Daily WTI oil price. Ecuador's economy depends on oil; weekends and market holidays have no price."),
    ("holidays_events.csv", f"{raw['holidays_events']['rows']} rows", "National, regional and local holidays and events, including transferred holidays, bridges and work days."),
]
cols = st.columns(5)
for col, (name, meta, text) in zip(cols, src):
    col.markdown(theme.card(meta, name, text), unsafe_allow_html=True)

# ------------------------------------------------------------------ key findings
theme.chapter("03", "What the data says, in one minute",
              "The short version. Every number below is measured on the full data and explored in detail on the other pages.")
theme.stats([
    ("31.3<small>%</small>", "rows with zero sales", "Real zeros: families a store does not stock, closed days, stores not yet open.", True),
    ("7.36", "sales skewness", "Most rows sell a little, a few sell a lot. log(1 + sales) brings it to 0.41."),
    ("+39<small>%</small>", "weekend lift", "Saturday and Sunday are the busiest days; Thursday is the quietest."),
    ("+26<small>%</small>", "national holidays", "A national holiday sells about a quarter more than a normal day."),
    ("+17<small>%</small>", "earthquake month", "16 April – 16 May 2016, during donations of food and water."),
    ("0.84", "sales ~ transactions", "More receipts, more units: the strongest relationship in the data."),
])
theme.insight("Cleaning added information; it did not change a single observation.",
              "All 3,000,888 rows, their sales and promotions are identical after cleaning. 245,784 missing transactions and "
              "928,422 missing oil prices were filled by documented rules, 21 explanatory columns were added, and every rule is "
              "checked by Pydantic models and pandas assertions — see the Validation page.")

theme.chapter("04", "How to use this site")
g1, g2, g3 = st.columns(3)
with g1:
    st.markdown(theme.card("Start here", "The raw data", "What each file contains before any cleaning, and what every column is telling us."), unsafe_allow_html=True)
    st.page_link("views/raw_data.py", label="Open the raw data", icon=":material/arrow_forward:")
with g2:
    st.markdown(theme.card("Then", "Explore sales", "Click any point of a chart to get a summary of that day and why it is high or low."), unsafe_allow_html=True)
    st.page_link("views/explore.py", label="Explore sales", icon=":material/arrow_forward:")
with g3:
    st.markdown(theme.card("Your own questions", "Chart studio", "Pick any column for x and y, change the chart type, filters and aggregation."), unsafe_allow_html=True)
    st.page_link("views/studio.py", label="Open the studio", icon=":material/arrow_forward:")
