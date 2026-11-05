"""Store Sales: welcome page, a technical overview and a business overview.

Run from the repository root:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

# Streamlit Cloud pulls new code without restarting, so old helper modules can stay in
# memory. If any helper file changed, drop them so the new versions are imported.
stamp = max(p.stat().st_mtime for p in (Path(__file__).parent / "lib").glob("*.py"))
if getattr(sys, "_lib_stamp", stamp) != stamp:
    for name in [m for m in sys.modules if m == "lib" or m.startswith("lib.")]:
        del sys.modules[name]
sys._lib_stamp = stamp

from lib import theme  # noqa: E402

st.set_page_config(page_title="Store Sales Ecuador", page_icon=":material/insights:",
                   layout="wide", initial_sidebar_state="collapsed")
theme.apply()

start = st.Page("views/welcome.py", title="Start", default=True)
technical = [
    st.Page("views/home.py", title="Project summary", url_path="summary"),
    st.Page("views/raw_data.py", title="Raw data", url_path="raw-data"),
    st.Page("views/merging.py", title="Merging", url_path="merging"),
    st.Page("views/eda_before.py", title="EDA before cleaning", url_path="eda-before"),
    st.Page("views/cleaning.py", title="Cleaning", url_path="cleaning"),
    st.Page("views/explore.py", title="EDA after cleaning", url_path="eda-after"),
    st.Page("views/studio.py", title="Chart studio", url_path="studio"),
    st.Page("views/features.py", title="Features", url_path="features"),
    st.Page("views/conclusion.py", title="Conclusion", url_path="conclusion"),
]
business = [
    st.Page("views/mgr_stores.py", title="Choose a store", url_path="choose-store"),
    st.Page("views/mgr_dashboard.py", title="Store overview", url_path="manager"),
    st.Page("views/mgr_products.py", title="Product calendar", url_path="manager-products"),
    st.Page("views/mgr_insights.py", title="Insights and actions", url_path="manager-insights"),
]
page = st.navigation([start] + technical + business, position="hidden")
theme.top_menu(start, technical, business)
page.run()
