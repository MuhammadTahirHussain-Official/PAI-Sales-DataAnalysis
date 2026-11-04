"""Stores Sales: an interactive EDA and ETL report.

Run from the repository root:
    streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from lib import theme  # noqa: E402

st.set_page_config(page_title="Ledger of a Grocery Chain", page_icon=":material/insights:",
                   layout="wide", initial_sidebar_state="collapsed")
theme.apply()

pages = [
    st.Page("views/overview.py", title="Overview", url_path="overview", default=True),
    st.Page("views/raw_data.py", title="The raw data", url_path="raw-data"),
    st.Page("views/pipeline.py", title="ETL & cleaning", url_path="pipeline"),
    st.Page("views/validation.py", title="Validation", url_path="validation"),
    st.Page("views/explore.py", title="Explore sales", url_path="explore"),
    st.Page("views/studio.py", title="Chart studio", url_path="studio"),
    st.Page("views/features.py", title="Features", url_path="features"),
]
st.navigation(pages, position="top").run()
