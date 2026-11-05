"""Last technical step: what was done, what was found, what comes next."""
import streamlit as st

from lib import data, theme

S = data.summary()
MR = S["model_ready"]
checks = sum(ok for _, ok in S["integrity"])
records = sum(p["checked"] for p in S["pydantic"])

theme.flow_top("views/conclusion.py")
theme.page_title("Technical overview", "The <em>conclusion</em>",
                 "Five raw files became one complete, validated table. This is what we did, what it showed, and what should happen next.")

theme.chapter("Findings", "What the data tells us")
theme.stats([
    ("31.3<small>%</small>", "rows with zero sales", "Kept: they are real, not errors.", True),
    ("+39<small>%</small>", "weekend lift", "Sunday is strongest, Thursday weakest."),
    ("+26<small>%</small>", "national holidays", "Christmas days lift most; on 1 January stores close."),
    ("23 Dec", "busiest day of December", "In every December of the data."),
    ("+1<small>%</small>", "payday effect", "Much smaller than expected at store level."),
    ("+17<small>%</small>", "earthquake month", "16 April to 16 May 2016 against the month before."),
    ("0.84", "sales and transactions", "The strongest link, on observed days only."),
    ("11 times", "best store vs weakest", "Average daily sales in 2015 and 2016."),
])

theme.chapter("What we did", "From raw files to model-ready")
theme.ledger(["Step", "What happened", "Result"], [
    ["Raw data", "Five Kaggle files read and described", f"{S['raw']['train']['rows']:,} sales rows"],
    ["Merging", "Four left joins, each checked", "Row count unchanged, 6 to 17 columns"],
    ["EDA before cleaning", "Distributions, gaps and outliers explored", "Skewness 7.36, gaps explained"],
    ["Cleaning", "Every gap filled by a written rule", f"0 missing values, {checks} of {len(S['integrity'])} integrity checks pass"],
    ["Validation", "4 Pydantic models and pandas assertions", f"{records:,} records, 0 errors"],
    ["EDA after cleaning", "Time, holidays, products, stores, promotions, oil", "Findings above"],
    ["Features", "Lags, calendar, promotions, encoding", f"{MR['rows']:,} rows, {MR['features']} features, no future data"],
])

theme.chapter("Limits", "What to keep in mind")
c1, c2, c3 = st.columns(3)
c1.markdown(theme.card("Estimates", "118 store-days", "Transactions on these days were estimated from sales, so they cannot prove the link between sales and transactions."), unsafe_allow_html=True)
c2.markdown(theme.card("Assumption", "Zero means no sales", "A store-day with no sales and no record is set to 0 transactions. It is not proof that the store was closed."), unsafe_allow_html=True)
c3.markdown(theme.card("Next step", "Split by date, then train", "No train and test split or scaling has been done. Both must use the training period only, to avoid using future data."), unsafe_allow_html=True)

st.link_button("Download the final clean data (CSV, 36 MB zip)", "https://github.com/MuhammadTahirHussain-Official/PAI-Sales-DataAnalysis/raw/main/downloads/cleaned_data.zip", type="primary")
theme.flow_next("views/conclusion.py")
