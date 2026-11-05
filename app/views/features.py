import pandas as pd
import plotly.express as px
import streamlit as st

from lib import data, theme

S = data.summary()
MR = S["model_ready"]
feat = data.load("features")

theme.page_title(
    "Technical · Step 6",
    "Ready for a model, <em>without peeking</em>",
    "Notebook 05 turns the cleaned table into numbers a model can learn from. The rule behind every feature: "
    "use only information that would really be known at forecast time.")

theme.stats([
    (f"{MR['rows']:,}", "model-ready rows", f"from {MR['first_date']}"),
    (str(MR["features"]), "numeric features", "plus id, date and 2 targets"),
    (f"{MR['removed_rows']:,}", "rows removed", "first 43 days: no history yet"),
    (str(MR["missing"]), "missing values", "", MR["missing"] == 0),
    ("16", "days minimum lag", "the forecast horizon"),
])

theme.chapter("6.1", "The no-leakage rule",
              "The Kaggle task forecasts the next 16 days. On the last of those days the newest known sales are 16 days old, "
              "so every feature built from sales or transactions looks at least 16 days back. Promotions and holidays are planned in advance, so they can be used for the same day.")
theme.ledger(["Group", "Features", "Known at forecast time because"],
             [["Sales history", "lags 16 / 21 / 28 / 364 days, rolling mean 7 / 14 / 28, rolling std 7", "they end 16 days before the target day"],
              ["Transactions", "transactions 16 days earlier (log)", "same-day receipts do not exist yet"],
              ["Promotions", "log promoted items, has promotion", "promotions are planned ahead"],
              ["Oil", "oil price, 7-day change", "published daily, before the target day"],
              ["Holidays", "flags, day before / after a holiday, earthquake period", "the calendar is published in advance"],
              ["Calendar", "cyclic month and weekday (sin / cos), days to Christmas, month start / end, payday", "pure functions of the date"],
              ["Store", "store open, codes for family / city / state / cluster, one-hot store type and family", "fixed properties"]])
theme.ledger(["Removed column", "Reason"],
             [["transactions", "same-day value: unknown when forecasting"], ["sales_extreme_flag", "computed from the same day's sales"],
              ["transactions_missing / fill_method", "describe same-day data"], ["holiday text, city, state, cluster, day_name", "replaced by flags and codes"]])

theme.chapter("6.2", "How strongly each feature relates to the target",
              "Correlation of each feature with log(1 + sales) on a 200,000-row sample. A quick first look, not a model's importance.")
c1, c2 = st.columns([2, 1])
groups = sorted(feat["group"].unique())
pick = c1.multiselect("Feature groups", groups, default=[g for g in groups if g not in ("one-hot family",)])
n = c2.slider("Show top", 5, 85, 30)
f = feat[feat["group"].isin(pick or groups)].copy()
f["abs"] = f["corr_with_target"].abs()
f = f.sort_values("abs", ascending=False).head(n).sort_values("corr_with_target")
fig = px.bar(f, x="corr_with_target", y="feature", color="group", orientation="h", color_discrete_sequence=theme.COLORWAY)
fig.update_traces(hovertemplate="%{y}<br>r = %{x:.3f}<extra></extra>")
fig.add_vline(x=0, line=dict(color=theme.INK, width=1))
fig.update_layout(xaxis_title="Correlation with log(1 + sales)", yaxis_title="", legend_title_text="",
                  yaxis=dict(tickfont=dict(family=theme.FONT_MONO, size=11)))
theme.chart(fig, height=max(380, 22 * len(f)))
theme.figcap("6.1", "Ranked correlation bars", "Pearson correlation between each feature and the target, coloured by feature group.",
             "The rolling means and lags of past sales correlate above 0.93 with today's sales: history is by far the strongest signal. "
             "Promotions come next (about 0.55). Calendar and oil features are weak on their own but help a model separate weekdays, seasons and the Christmas peak.",
             "bars to the right move with sales, to the left against it; hide groups above to compare the rest.")

theme.chapter("6.3", "Encoding the categories")
theme.ledger(["Column", "Values", "Encoding", "Why"],
             [["store type", "5", "one-hot (store_type_A … E)", "few values, no order"],
              ["family", "33", "one-hot and family_code", "one-hot for linear models, the code for tree models"],
              ["city", "22", "city_code", "many values; trees split on codes well"],
              ["state", "16", "state_code", ""], ["cluster", "17", "cluster_code", "a label, not a ranking"],
              ["store_nbr", "54", "kept as a number", "already a code"]])
theme.insight("Not done yet, on purpose: the split and the scaling.",
              "The next step splits by date (for example, train until 2017-07-30 and validate on the last 16 days) and fits any scaler on the training part only. "
              "Doing either on all data now would leak the future into the model.")
