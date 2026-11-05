"""Store Sales: first page, a technical dashboard and a store manager dashboard.

Run from the repository root:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from lib import theme  # noqa: E402

st.set_page_config(page_title="Store Sales Ecuador", page_icon=":material/insights:",
                   layout="wide", initial_sidebar_state="collapsed")
theme.apply()

pages = {
    "Summary": [st.Page("views/home.py", title="Project summary", default=True)],
    "Technical dashboard": [
        st.Page("views/raw_data.py", title="1. Raw data and EDA before cleaning", url_path="raw-data"),
        st.Page("views/pipeline.py", title="2. Merging and cleaning", url_path="pipeline"),
        st.Page("views/validation.py", title="3. Validation", url_path="validation"),
        st.Page("views/explore.py", title="4. EDA after cleaning", url_path="explore"),
        st.Page("views/studio.py", title="5. Chart studio", url_path="studio"),
        st.Page("views/features.py", title="6. Features", url_path="features"),
    ],
    "Store manager dashboard": [
        st.Page("views/mgr_dashboard.py", title="My store", url_path="manager"),
        st.Page("views/mgr_products.py", title="Product calendar", url_path="manager-products"),
        st.Page("views/mgr_insights.py", title="Insights and actions", url_path="manager-insights"),
    ],
}
st.navigation(pages, position="top").run()
