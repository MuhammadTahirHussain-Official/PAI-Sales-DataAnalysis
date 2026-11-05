import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import data, theme

S = data.summary()
M = S["merged"]["missing"]
C = S["clean"]

theme.flow_top("views/merging.py")
theme.page_title("Technical overview", "<em>Merging</em> five files into one",
                 "How the files were joined without losing or duplicating a single sales row, and what was empty after the join.")

# ------------------------------------------------------------------ animated pipeline
steps = S["etl_steps"]
nodes = "".join(
    f'<div class="node"><div class="k">{"Extract" if i == 0 else "Join " + str(i)}</div>'
    f'<div class="t">{s["step"]}</div><div class="m">{s["rows"]:,} rows · {s["columns"]} cols</div>'
    f'<div class="j">{s["join"]}</div><div class="on">{"starting table" if i == 0 else "joined on"}<b>{s["key"] if i else "one row per date, store, product"}</b></div></div>'
    + ('<div class="link"><span></span></div>' if i < len(steps) - 1 else "")
    for i, s in enumerate(steps))
flow = f"""<!doctype html><html><head><link rel="stylesheet" href="{theme.FONT_LINK}"><style>
* {{ box-sizing: border-box; margin: 0; }}
html, body {{ background: transparent; font-family: {theme.FONT_BODY}; color: {theme.INK}; overflow: hidden; }}
.flow {{ display: flex; align-items: stretch; padding: 4px; }}
.node {{ flex: 1 1 0; background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.12); border-radius: 16px; padding: 14px; }}
.node:last-child {{ background: {theme.PERSIMMON}; color: #14110E; border-color: {theme.PERSIMMON}; }}
.node:last-child .k, .node:last-child .m, .node:last-child .j {{ color: #14110E; }}
.k {{ font-family: {theme.FONT_MONO}; font-size: 10px; letter-spacing: .14em; text-transform: uppercase; color: {theme.PERSIMMON}; }}
.t {{ font-family: {theme.FONT_DISPLAY}; font-size: 22px; line-height: 1.1; margin: 6px 0 8px; }}
.m {{ font-family: {theme.FONT_MONO}; font-size: 12px; color: {theme.INK_2}; }}
.j {{ font-size: 12px; color: {theme.MUTED}; margin-top: 8px; line-height: 1.45; }}
.on {{ margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,.14); font-family: {theme.FONT_MONO}; font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: {theme.MUTED}; }}
.on b {{ display: block; margin-top: 3px; font-size: 13px; font-weight: 500; letter-spacing: 0; text-transform: none; color: {theme.OCHRE}; }}
.node:last-child .on, .node:last-child .on b {{ color: #14110E; border-color: rgba(20,17,14,.3); }}
.link {{ flex: 0 0 28px; position: relative; }}
.link span {{ position: absolute; top: 50%; left: 4px; right: 4px; height: 2px; background: {theme.PERSIMMON}; transform-origin: left; }}
@media (max-width: 760px) {{ .flow {{ flex-direction: column; }} .link {{ flex-basis: 16px; }} }}
</style></head><body><div class="flow">{nodes}</div>{theme.gsap_scripts()}{theme.FIT}<script>
gsap.timeline()
  .from('.node', {{autoAlpha: 0, y: 18, stagger: .22, duration: .6, ease: 'power3.out'}})
  .from('.link span', {{scaleX: 0, stagger: .22, duration: .4, ease: 'power2.inOut'}}, .3);
</script></body></html>"""
st.iframe(flow, height=280)
theme.figcap("3.0", "Pipeline diagram",
             "The four merges, one after another. The sales table is the main table every time, so no sales row can be lost.",
             "The table stays at 3,000,888 rows after every merge: nothing lost and nothing doubled. If a store or a store-day appeared twice in a file, the many-to-one check would stop the merge with an error.",
             "read left to right; the orange box is the final table.")

theme.chapter("3.0", "Which file is merged on what",
              "Each join needs a column both tables share. The right column depends on what the file describes: one store, one store on one day, or one day.")
theme.ledger(
    ["File", "Merged on", "Why this column", "Adds", "How it matches"],
    [["stores.csv", "<code>store_nbr</code>", "Each store has one row, and its details never change over time", "<code>city</code>, <code>state</code>, <code>type</code>, <code>cluster</code>", "All 54 stores matched"],
     ["transactions.csv", "<code>date</code> + <code>store_nbr</code>", "Receipts are counted per store per day, so both columns are needed", "<code>transactions</code>", "7,448 store-days have no record and stay empty"],
     ["oil.csv", "<code>date</code>", "The oil price is the same for every store on a given day", "<code>oil_price</code> (renamed from <code>dcoilwtico</code>)", "521 sales dates have no price and stay empty"],
     ["holidays_events.csv", "<code>date</code> + <code>store_nbr</code>", "A holiday only counts for the stores it applies to, so records are first matched to stores (below)", "5 columns: <code>holiday_type</code>, <code>holiday_locale</code>, <code>holiday_locale_name</code>, <code>holiday_description</code>, <code>holiday_transferred</code>", "8,109 sales store-days have an event"]])
theme.chapter("3.0.1", "How a holiday finds its stores",
              "The holiday file has no store number, only a place name. So it takes two steps: match each record to stores, then combine the records so each store-day has one row.")
theme.ledger(
    ["Holiday level", "Matched using", "Which stores", "Store matches"],
    [["National", "every store (cross join)", "All 54 stores", "9,396"],
     ["Regional", "<code>locale_name</code> = store <code>state</code>", "Stores in that province", "42"],
     ["Local", "<code>locale_name</code> = store <code>city</code>", "Stores in that city", "512"]])
theme.prose("Two events can fall on the same store-day. They are combined into one row (for example <code>Holiday | Event</code>) before the merge, so the sales rows are never duplicated.")

theme.chapter("3.1", "Checks made at every merge")
theme.ledger(
    ["Join", "Rule", "Why it matters", "Result"],
    [["stores", "validate='many_to_one', indicator=True", "every store must exist exactly once in stores.csv", '<span class="ok">54 / 54 matched</span>'],
     ["transactions", "validate='many_to_one'", "one record per store-day at most", '<span class="ok">0 duplicate keys</span>'],
     ["oil", "duplicate-date check", "one price per date", '<span class="ok">0 duplicate dates</span>'],
     ["holidays", "aggregate to one row per store-day, then many_to_one", "two events on one day must not double the sales rows", '<span class="ok">9,601 unique store-days</span>'],
     ["every join", "assert rows before == rows after", "nothing lost, nothing multiplied", '<span class="ok">3,000,888 rows</span>']])

# ------------------------------------------------------------------ missing after merge
theme.chapter("3.2", "What was missing after the join",
              "A merge never invents values. Where a file had no matching row, the new columns stay empty. The cleaning step fixes these gaps.")
miss = pd.DataFrame([
    {"column": k, "before": v, "after": C["missing"].get(k, 0)} for k, v in M.items() if v > 0
]).sort_values("before")
view = "Before cleaning"
fig = go.Figure()
fig.add_trace(go.Bar(y=miss["column"], x=miss["before"], orientation="h", name="before cleaning", marker_color=theme.PERSIMMON,
                     hovertemplate="%{y}: %{x:,} empty rows before<extra></extra>"))
if view == "Before and after":
    fig.add_trace(go.Bar(y=miss["column"], x=miss["after"], orientation="h", name="after cleaning", marker_color=theme.MOSS,
                         hovertemplate="%{y}: %{x:,} empty rows after<extra></extra>"))
fig.update_layout(barmode="group", xaxis_title="Empty rows (of 3,000,888)", yaxis_title="")
theme.chart(fig, height=360)
theme.figcap("3.2", "Bar chart", "Empty values per column in the merged table.",
             "The five holiday columns are empty on 91% of rows simply because most days are not holidays. Oil is empty on weekends (928,422 rows), and transactions on 7,448 store-days (245,784 rows). These gaps are fixed in the cleaning step.",
             "a longer bar means more empty rows.")


theme.flow_next("views/merging.py")
