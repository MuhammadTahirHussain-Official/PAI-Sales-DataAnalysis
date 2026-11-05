"""Store Sales: first page, a technical overview and a business overview.

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

pages = {
    "Start": [st.Page("views/welcome.py", title="Welcome", default=True)],
    "Technical overview": [
        st.Page("views/home.py", title="1. Project summary", url_path="summary"),
        st.Page("views/raw_data.py", title="2. Raw data and EDA before cleaning", url_path="raw-data"),
        st.Page("views/pipeline.py", title="3. Merging and cleaning", url_path="pipeline"),
        st.Page("views/validation.py", title="4. Validation", url_path="validation"),
        st.Page("views/explore.py", title="5. EDA after cleaning", url_path="explore"),
        st.Page("views/studio.py", title="6. Chart studio", url_path="studio"),
        st.Page("views/features.py", title="7. Features", url_path="features"),
    ],
    "Business overview": [
        st.Page("views/mgr_dashboard.py", title="Overview", url_path="manager"),
        st.Page("views/mgr_products.py", title="Product calendar", url_path="manager-products"),
        st.Page("views/mgr_insights.py", title="Insights and actions", url_path="manager-insights"),
    ],
}
st.navigation(pages, position="top").run()
