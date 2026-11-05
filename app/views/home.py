"""First page: the whole project in one view, for someone who has only a minute."""
import json
from pathlib import Path

import numpy as np
import streamlit as st

from lib import data, theme

S = data.summary()
raw = S["raw"]
daily = data.load("daily")
hist = data.load("sales_histogram")

weekly = daily.set_index("date")["sales"].resample("W").mean()
journey_data = {
    "nums": [[raw["train"]["rows"], "sales rows"], [54, "stores"], [33, "product families"], [raw["train"]["dates"], "days"],
             [S["model_ready"]["features"], "model features"], [sum(p["errors"] for p in S["pydantic"]), "validation errors"]],
    "steps": [
        {"t": "Raw data", "p": "Five CSV files from Kaggle: sales, stores, transactions, oil prices and holidays. Sales rows have no gaps; transactions and oil do not cover every day.",
         "m": f"{raw['train']['rows']:,} sales rows · 43 empty oil prices · 12 moved holidays"},
        {"t": "Merging", "p": "Store, customer, oil and holiday details are added to every sales row. Each merge is checked so no row is lost or doubled.",
         "m": "row count checked after every merge"},
        {"t": "EDA before cleaning", "p": "Most rows sell very little and a few sell a lot. A third of rows are real zeros, because stores do not stock every product or were closed.",
         "m": "half of rows sell 11 units or fewer · the average is 358"},
        {"t": "Cleaning", "p": "Each gap gets a documented rule: zero transactions when nothing sold, a ratio estimate when sales happened, and the last trading day's oil price on closed days.",
         "m": "11 of 11 integrity checks pass · sales values unchanged"},
        {"t": "EDA after cleaning", "p": "With clean data the patterns are clear: strong weekends, a December peak every year, steady growth and a jump after the 2016 earthquake.",
         "m": "more customers means more sales: a strong link of 0.84"},
        {"t": "Conclusion", "p": "The table is complete, validated and ready for forecasting. Managers get the same findings as plain actions for their own store.",
         "m": f"{S['model_ready']['rows']:,} model-ready rows · no train/test split yet"},
    ],
    "files": [["train.csv", f"{raw['train']['rows']:,} rows"], ["stores.csv", "54 rows"], ["transactions.csv", f"{raw['transactions']['rows']:,} rows"],
              ["oil.csv", f"{raw['oil']['rows']:,} rows"], ["holidays_events.csv", f"{raw['holidays_events']['rows']} rows"]],
    "hist": hist["rows"].astype(int).tolist(),
    "gaps": [["Transactions", S["merged"]["missing"]["transactions"], "0 on zero-sales days, ratio estimate on the rest"],
             ["Oil price", S["merged"]["missing"]["oil_price"], "last trading day's price, at most 7 days"],
             ["Holiday text", S["merged"]["missing"]["holiday_type"], "\"No Event\", plus clear 0/1 flags"]],
    "weekly": np.round(weekly.values).astype(int).tolist(),
    "years": ["2013", "2014", "2015", "2016", "2017"],
    "tags": ["weekends +39%", "national holidays +26%", "earthquake month +17%"],
    "ends": ["Every missing value filled by a written rule", "No original sales value changed",
             "4 Pydantic models, 0 errors", "85 numeric features with no future data",
             "Technical overview for analysts", "Business overview with actions for store managers"],
}
theme.flow_top("views/home.py")
page = (Path(__file__).resolve().parents[1] / "static" / "journey.html").read_text(encoding="utf-8")
page = (page.replace("__FONTS__", theme.FONT_LINK).replace("__GSAP__", theme.gsap_scripts()).replace("__FIT__", theme.FIT)
        .replace("__DATA__", json.dumps(journey_data)))
st.iframe(page, height=890)

st.link_button("Download the final clean data (CSV, 36 MB zip)", "https://github.com/MuhammadTahirHussain-Official/PAI-Sales-DataAnalysis/raw/main/downloads/cleaned_data.zip", type="primary")

theme.chapter("In short", "What the data tells us")
theme.stats([
    ("31.3<small>%</small>", "rows with zero sales", "Kept: they are real, not errors.", True),
    ("+39<small>%</small>", "weekend lift", "Sunday is strongest, Thursday weakest."),
    ("+26<small>%</small>", "national holidays", "Christmas days lift most; 1 January stores close."),
    ("23 Dec", "busiest day of December", "In every December of the data."),
    ("+1<small>%</small>", "payday effect", "Much smaller than expected at store level."),
    ("0.84", "sales and transactions", "The strongest link, on observed days only."),
])
c1, c2, c3 = st.columns(3)
c1.markdown(theme.card("Data quality", "Trustworthy", f"{sum(ok for _, ok in S['integrity'])} of {len(S['integrity'])} integrity checks pass and {sum(p['checked'] for p in S['pydantic']):,} records were validated by Pydantic with 0 errors."), unsafe_allow_html=True)
c2.markdown(theme.card("Next step", "Ready to forecast", f"{S['model_ready']['rows']:,} rows and {S['model_ready']['features']} features use only information known 16 days ahead. Split by date, then train."), unsafe_allow_html=True)
c3.markdown(theme.card("Team", "Project contributors", "Usman Ahmad, Muhammad Anas Alam, Muhammad Tahir Hussain and Hamza Noor. Data: Kaggle Store Sales, Ecuador."), unsafe_allow_html=True)

theme.flow_next("views/home.py")
