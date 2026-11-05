"""Shared helpers for the three store manager pages: real data for one store at a time."""
from pathlib import Path

import pandas as pd
import streamlit as st

from lib import data, theme

STORE_DIR = Path(__file__).resolve().parents[1] / "data" / "stores"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
FIRST, LAST = pd.Period("2013-01", "M"), pd.Period("2017-08", "M")


def nice(family):
    """'LIQUOR,WINE,BEER' -> 'Liquor, wine, beer'; keeps the Roman numerals in 'Grocery I'."""
    words = family.replace(",", ", ").replace("/", " / ").split()
    words = [w if w in ("I", "II") else w.lower() for w in words]
    return " ".join(words).capitalize().replace(" i", " I") if words[-1] == "I" else " ".join(words).capitalize().replace(" ii", " II")


@st.cache_data(show_spinner=False)
def store_rows(store):
    df = pd.read_parquet(STORE_DIR / f"store_{store}.parquet")
    df["product"] = df["family"].map(nice)
    df["month"] = df["date"].dt.to_period("M")
    return df


@st.cache_data(show_spinner=False)
def store_days(store):
    sd = data.load("store_day")
    sd = sd[sd["store_nbr"] == store].sort_values("date").copy()
    sd["month"] = sd["date"].dt.to_period("M")
    return sd


def holidays_on(store, day):
    """Active holiday and event names that apply to this store on this date."""
    meta = data.stores().set_index("store_nbr").loc[store]
    h = data.holidays_active()
    h = h[(h["date"] == day) & h["active"]]
    return h[(h["locale"] == "National") | ((h["locale"] == "Regional") & (h["locale_name"] == meta["state"]))
             | ((h["locale"] == "Local") & (h["locale_name"] == meta["city"]))]


def sg(v):
    return f"{'+' if v >= 0 else '−'}{abs(v) * 100:.0f}%"


def picker(with_store=True):
    """Store and month controls, remembered across the three manager pages."""
    ss = st.session_state
    if "mgr_store" not in ss:
        st.switch_page("views/mgr_stores.py")
    ss.setdefault("mgr_month", str(LAST - 1))
    per = pd.Period(ss["mgr_month"], "M")
    meta = data.stores().set_index("store_nbr")

    bar = st.container(key="mgrbar")
    c1, c3, c2, c4 = bar.columns([3, 1.2, .55, .55], vertical_alignment="bottom")
    c1.page_link("views/mgr_stores.py", label=f"Store {ss['mgr_store']} · {meta.loc[ss['mgr_store'], 'city']} · change store", icon=":material/swap_horiz:")
    if c2.button("", icon=":material/chevron_left:", help="Previous month", disabled=per <= FIRST, width="stretch"):
        ss["mgr_month"] = str(per - 1)
        st.rerun()
    year = c3.selectbox("Year", list(range(2013, 2018)), index=per.year - 2013, key=f"yr_{per}")
    if c4.button("", icon=":material/chevron_right:", help="Next month", disabled=per >= LAST, width="stretch"):
        ss["mgr_month"] = str(per + 1)
        st.rerun()
    if year != per.year:
        ss["mgr_month"] = str(min(pd.Period(f"{year}-{per.month:02d}", "M"), LAST))
        st.rerun()

    options = [m for i, m in enumerate(MONTHS) if pd.Period(f"{per.year}-{i + 1:02d}", "M") <= LAST]
    picked = st.pills("Month", options, default=MONTHS[per.month - 1], key=f"mo_{per}", label_visibility="collapsed")
    if picked and picked != MONTHS[per.month - 1]:
        ss["mgr_month"] = f"{per.year}-{MONTHS.index(picked) + 1:02d}"
        st.rerun()
    return int(ss["mgr_store"]), per, f"Store {ss['mgr_store']} · {meta.loc[ss['mgr_store'], 'city']}"


def bars_html(rows):
    """rows: (label, value, text). Simple horizontal bars for small comparisons."""
    top = max(abs(r[1]) for r in rows) or 1
    out = ""
    for label, value, text in rows:
        out += (f'<div style="display:grid;grid-template-columns:130px 1fr 80px;gap:12px;align-items:center;margin-bottom:10px;font-size:.93rem">'
                f'<span>{label}</span><div style="height:12px;border-radius:7px;background:rgba(255,255,255,.08)">'
                f'<div style="height:100%;width:{abs(value) / top * 100:.0f}%;border-radius:7px;background:{theme.PERSIMMON if label == "Your store" else theme.SAND}"></div></div>'
                f'<span style="text-align:right;font-family:{theme.FONT_MONO};font-size:.82rem">{text}</span></div>')
    return out
