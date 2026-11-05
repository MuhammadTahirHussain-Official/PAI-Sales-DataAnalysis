"""Landing page: one full-screen animated page with two ways in."""
import json
from pathlib import Path

import numpy as np
import streamlit as st

from lib import data, theme
from lib.data import WEEKDAYS

# Full-screen on this page only: no menu bar, no margins. The two hidden links let the
# animated page move to the next page without reloading the app.
theme.html("""<style>
.st-key-topnav { display:none !important; }
[data-testid="stMainBlockContainer"] { padding:0 !important; max-width:none !important; }
[data-testid="stMain"] { overflow:hidden; }
[data-testid="stVerticalBlock"] { gap:0 !important; }
.st-key-doorlinks { position:absolute; width:1px; height:1px; overflow:hidden; opacity:0; pointer-events:none; }
</style>""")
with st.container(key="doorlinks"):
    st.page_link("views/home.py", label="Technical overview")
    st.page_link("views/mgr_dashboard.py", label="Business overview")

daily = data.load("daily")
store_day = data.load("store_day")
selling = store_day[store_day["sales"] > 0]
payload = {
    "weekly": np.round(daily.set_index("date")["sales"].resample("W").mean().values).astype(int).tolist(),
    "hist": data.load("sales_histogram")["rows"].astype(int).tolist(),
    "weekday": np.round(selling.groupby("weekday")["sales"].mean().reindex(WEEKDAYS).values).astype(int).tolist(),
    "days": [d[:3] for d in WEEKDAYS],
    "years": ["2013", "2014", "2015", "2016", "2017"],
}
ARROW = '<span class="arrow"><svg viewBox="0 0 24 24"><path d="M4 12h15M13 6l6 6-6 6"/></svg></span>'
doors = f"""
<button class="door" data-go="summary"><span class="row"><span><span class="mono">For analysts</span><h2>Technical overview</h2></span>{ARROW}</span>
<p>Starts with the project summary, then follows every step in order: raw data, merging, cleaning, validation, EDA and features.</p></button>
<button class="door" data-go="manager"><span class="row"><span><span class="mono">For store managers</span><h2>Business overview</h2></span>{ARROW}</span>
<p>Your store in plain words: what sold, which days to staff up, what to reorder and what to do next.</p></button>"""

page = (Path(__file__).resolve().parents[1] / "static" / "welcome.html").read_text(encoding="utf-8")
page = (page.replace("__FONTS__", theme.FONT_LINK).replace("__GSAP__", theme.gsap_scripts(scroll_trigger=True))
        .replace("__DOORS__", doors).replace("__DATA__", json.dumps(payload)))
st.iframe(page, height=800)
