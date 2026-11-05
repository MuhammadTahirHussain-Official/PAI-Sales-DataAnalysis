"""Business overview starts here: choose one store, then see only that store."""
import pandas as pd
import streamlit as st

from lib import data, theme

theme.page_title("For store managers", "Choose your <em>store</em>",
                 "Pick one store to open its business overview. You can change store at any time.")

stores = data.stores().sort_values("store_nbr")
sd = data.load("store_day")
recent = sd[sd["date"] >= "2017-01-01"].groupby("store_nbr")["sales"].mean()

c1, c2, c3 = st.columns([1.4, 1, 1])
city = c1.selectbox("City", ["All cities"] + sorted(stores["city"].unique()))
kind = c2.selectbox("Store type", ["All types"] + sorted(stores["type"].unique()))
order = c3.selectbox("Sort by", ["Store number", "City", "Sales, highest first"])

view = stores.copy()
if city != "All cities":
    view = view[view["city"] == city]
if kind != "All types":
    view = view[view["type"] == kind]
view["daily"] = view["store_nbr"].map(recent)
if order == "City":
    view = view.sort_values(["city", "store_nbr"])
elif order == "Sales, highest first":
    view = view.sort_values("daily", ascending=False)

theme.html(f'<div class="hint">{len(view)} of {len(stores)} stores shown. Daily sales are the 2017 average.</div>')
if view.empty:
    theme.html(theme.card("No match", "No store fits these choices", "Try another city or store type."))
    st.stop()

with st.container(key="storegrid"):
    for row in view.itertuples():
        label = f"**Store {row.store_nbr}**  \n{row.city}, {row.state}  \nType {row.type} · {theme.fmt(row.daily)} units a day"
        if st.button(label, key=f"open_{row.store_nbr}", width="stretch"):
            st.session_state["mgr_store"] = int(row.store_nbr)
            st.switch_page("views/mgr_dashboard.py")
