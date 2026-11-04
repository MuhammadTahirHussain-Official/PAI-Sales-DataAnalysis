"""Cached loaders for the prepared datasets in app/data."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parents[1] / "data"


@st.cache_data(show_spinner=False)
def load(name):
    return pd.read_parquet(DATA / f"{name}.parquet")


@st.cache_data(show_spinner=False)
def summary():
    return json.loads((DATA / "summary.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def holidays_active():
    """Holiday rows with an active flag (transferred-away rows are not active)."""
    h = load("raw_holidays").copy()
    h["active"] = ~h["transferred"]
    return h


@st.cache_data(show_spinner=False)
def stores():
    return load("raw_stores")


# Columns that can be chosen in the chart studio, with plain-English labels
LABELS = {
    "date": "Date", "sales": "Sales (units)", "transactions": "Transactions (cleaned)",
    "transactions_original": "Transactions (original, with gaps)", "transactions_observed": "Transactions (observed only)",
    "promotions": "Items on promotion", "zero_families": "Families with zero sales", "stores_selling": "Stores selling",
    "oil_price": "Oil price (USD, cleaned)", "oil_original": "Oil price (USD, original)",
    "sales_per_transaction": "Sales per transaction", "store_nbr": "Store", "city": "City", "state": "State",
    "store_type": "Store type", "cluster": "Cluster", "family": "Product family", "year": "Year", "month": "Month",
    "weekday": "Weekday", "fill_method": "Transaction source", "is_holiday": "Holiday flag",
    "is_national_holiday": "National holiday", "is_event": "Event", "is_work_day": "Work day",
    "is_earthquake_period": "Earthquake period", "is_weekend": "Weekend", "is_payday": "Payday",
    "store_open": "Store open", "zero_stores": "Stores with zero sales", "extreme_rows": "Extreme-sales rows",
    "total_sales": "Total sales", "mean_sales": "Mean sales per row", "zero_share": "Share of zero-sales rows",
    "mean_promotions": "Mean items on promotion", "filled_store_days": "Filled store-days",
    "stores_with_holiday": "Stores with a holiday", "is_regional_holiday": "Regional holiday",
    "is_local_holiday": "Local holiday", "median_sales": "Median sales per row", "promo_share": "Share of rows on promotion",
}


def label(col):
    return LABELS.get(col, col.replace("_", " ").capitalize())


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
