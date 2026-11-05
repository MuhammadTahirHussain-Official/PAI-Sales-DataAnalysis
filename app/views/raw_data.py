import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data, theme
from lib.data import WEEKDAYS

S = data.summary()
R = S["raw"]

theme.flow_top("views/raw_data.py")
theme.page_title("Technical overview", "The <em>raw data</em>",
                 "Five files from Kaggle, before anything is joined or cleaned: what each one contains, what every column means and what it tells us.")


def dictionary(rows):
    theme.ledger(["Column", "Type", "What it is", "What it tells us"], rows)


# =================================================================== train
if True:  # train.csv
    theme.chapter("File", "train.csv", "Sales per date, store and product family")
    t = R["train"]
    sales = t["sales"]
    theme.stats([
        (f"{t['rows']:,}", "rows", "one per date × store × family"),
        (str(t["dates"]), "dates", f"{t['date_min']} → {t['date_max']}"),
        ("0", "missing values", "no empty cells in any column"),
        (f"{sales['zero_share'] * 100:.1f}<small>%</small>", "zero-sales rows", f"{sales['zero_rows']:,} rows", True),
        (f"{sales['median']:.0f} / {sales['mean']:.0f}", "median / mean", "a long right tail pulls the mean up"),
    ])
    dictionary([
        ["id", "int", "Row number", "Unique for every row; no duplicates"],
        ["date", "date", "The day", "1,684 days; only 25 December is missing (stores closed)"],
        ["store_nbr", "int", "Store 1 – 54", "An identifier, not a quantity"],
        ["family", "text", "One of 33 product groups", "GROCERY I and BEVERAGES dominate; BOOKS and BABY CARE barely sell"],
        ["sales", "float", "Units sold (fractions for goods sold by weight)", "The target. 31% zeros, skewness 7.36"],
        ["onpromotion", "int", "Items of that family on promotion", "0 on 80% of rows; nothing recorded in 2013, then strong growth until 2016"],
    ])

if True:  # stores.csv
    theme.chapter("File", "stores.csv", "Where each store is and what kind it is")
    s = data.stores()
    theme.stats([("54", "stores", "no duplicates, no missing values"), (str(s["city"].nunique()), "cities", ""),
                 (str(s["state"].nunique()), "states", ""), ("5", "store types", "A – E"), (str(s["cluster"].nunique()), "clusters", "groups of similar stores")])
    dictionary([
        ["store_nbr", "int", "Store id", "Key for the join with train and transactions"],
        ["city", "text", "City", "Quito (18 stores) and Guayaquil (8) hold almost half of all stores"],
        ["state", "text", "Province", "Used to match regional holidays"],
        ["type", "text", "Store format A – E", "A and D are the large formats; C is the most common"],
        ["cluster", "int", "Group of similar stores (1 – 17)", "A label, not a ranking"],
    ])

if True:  # transactions.csv
    theme.chapter("File", "transactions.csv", "Customer receipts per store and day")
    t = R["transactions"]
    sd = data.load("store_day")
    theme.stats([(f"{t['rows']:,}", "store-days with a record", f"{t['date_min']} → {t['date_max']}"),
                 ("90,936", "store-days in train", "54 stores × 1,684 days"),
                 ("7,448", "store-days without a record", "245,784 family rows after the merge", True),
                 ("0", "records equal to zero", "a missing record is not a recorded zero")])
    dictionary([
        ["date", "date", "The day", "Join key with train"],
        ["store_nbr", "int", "Store", "Join key with train"],
        ["transactions", "int", "Receipts in that store that day", "Customer traffic; never 0 in the file"],
    ])

if True:  # oil.csv
    theme.chapter("File", "oil.csv", "Daily oil price")
    t = R["oil"]
    oil = data.load("raw_oil").rename(columns={"dcoilwtico": "price"})
    theme.stats([(f"{t['rows']:,}", "rows", f"{t['date_min']} → {t['date_max']}"),
                 ("43", "rows with an empty price", "market holidays", True),
                 (f"{t['calendar_days_without_row']}", "calendar days with no row", "weekends: no trading"),
                 ("0", "duplicate dates", "")])
    dictionary([
        ["date", "date", "Trading day", "Only working days of the oil market"],
        ["dcoilwtico", "float", "WTI crude price in USD (FRED series DCOILWTICO)", "Ecuador's economy depends on oil exports; matched to FRED exactly"],
    ])

if True:  # holidays_events.csv
    theme.chapter("File", "holidays_events.csv", "National, regional and local days")
    t = R["holidays_events"]
    h = data.load("raw_holidays")
    theme.stats([(str(t["rows"]), "records", "2012-03-02 → 2017-12-26"),
                 (str(t["locales"].get("National", 0)), "national", "apply to every store"),
                 (str(t["locales"].get("Regional", 0)), "regional", "apply to one province"),
                 (str(t["locales"].get("Local", 0)), "local", "apply to one city"),
                 (str(t["transferred"]), "transferred", "moved to another date", True)])
    dictionary([
        ["date", "date", "Day of the record", "Some dates have several records"],
        ["type", "text", "Holiday, Transfer, Additional, Bridge, Work Day, Event", "Only the first four are days off"],
        ["locale", "text", "National / Regional / Local", "Who the day applies to"],
        ["locale_name", "text", "Ecuador, a province or a city", "Matched to store state or city"],
        ["description", "text", "Name of the day", "e.g. Navidad, Carnaval, Terremoto Manabi"],
        ["transferred", "bool", "Moved to another date", "If True, the original date was a normal working day"],
    ])

theme.flow_next("views/raw_data.py")
