import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data, theme
from lib.data import WEEKDAYS

S = data.summary()
R = S["raw"]

theme.flow_top("views/eda_before.py")
theme.page_title("Technical overview", "EDA <em>before cleaning</em>",
                 "Now that the files are joined, what do they show, and what is wrong with them? Every chart here uses the data before any value was filled.")

if True:  # train.csv
    sales = R["train"]["sales"]
    theme.chapter("1.1", "How much does each row sell?",
                  "Each row is one product in one store on one day. Most rows sell very little, while a few sell thousands of units. "
                  "That is why ordinary averages can mislead here.")
    c1, c2, c3 = st.columns([1, 1, 1])
    scale = c1.segmented_control("Scale", ["Log bins (all rows)", "Linear (sample)"], default="Log bins (all rows)")
    clip = c2.slider("Linear view: cut the tail at percentile", 90.0, 100.0, 99.0, 0.5)
    fam = c3.selectbox("Family (linear view)", ["All families"] + sorted(data.load("family_summary")["family"]))
    if scale == "Linear (sample)":
        smp = data.load("raw_train_sample").sample(40_000, random_state=1)
        if fam != "All families":
            smp = smp[smp["family"] == fam]
        cut = smp["sales"].quantile(clip / 100)
        view = smp[smp["sales"] <= cut]
        fig = px.histogram(view, x="sales", nbins=80, color_discrete_sequence=[theme.TEAL])
        fig.update_traces(hovertemplate="sales %{x}<br>%{y:,} rows<extra></extra>", marker_line_width=0)
        fig.update_layout(xaxis_title="Units sold per row", yaxis_title="Rows (40,000-row sample)", bargap=0.04)
        theme.chart(fig, height=380)
        theme.figcap("1.1", "Histogram, linear scale",
                     f"{fam}: sales of a random sample of 40,000 rows, cut at the {clip:g}th percentile ({cut:,.0f} units).",
                     "Almost everything sits in the first bars, because most rows sell only a handful of units. Move the slider to 100 to see how far the biggest sales reach.",
                     "each bar is a range of sales; its height is how many rows fall into it.")
    else:
        h = data.load("sales_histogram")
        h["label"] = np.where(h["right"] <= 1e-6, "0", h["left"].round(1).astype(str) + " – " + h["right"].round(1).astype(str))
        colors = [theme.PERSIMMON if r <= 1e-6 else theme.TEAL for r in h["right"]]
        fig = go.Figure(go.Bar(x=h.index, y=h["rows"], marker_color=colors, customdata=h["label"],
                               hovertemplate="sales %{customdata}<br>%{y:,} rows<extra></extra>"))
        ticks = [i for i in range(1, len(h), 8)]
        fig.update_layout(xaxis=dict(tickvals=ticks, ticktext=[f"{h.loc[i, 'left']:,.0f}" for i in ticks], title="Units sold per row (logarithmic bins)"),
                          yaxis_title="Rows (all 3,000,888)", bargap=0.08)
        theme.chart(fig, height=380)
        theme.figcap("1.1", "Histogram, logarithmic bins",
                     "All 3,000,888 rows. The first, orange bar is rows that sold exactly zero: 939,130 of them. Each later bar covers a wider range, so small and large sales both fit.",
                     "There are really two groups: rows that sold nothing at all, and rows that sold normally, mostly between 10 and 1,000 units.",
                     "left to right goes from small sales to large; point at a bar for its exact range and count.")
    theme.stats([(f"{v:,.0f}", f"{float(k) * 100:g}th percentile", "") for k, v in sales["p"].items()])

    theme.chapter("1.2", "Which products sell, and which mostly do not",
                  "Zero sales are not errors. A store that does not stock baby care will record a zero every day.")
    fs = data.load("family_summary").copy()
    metric = st.segmented_control("Rank families by", ["zero_share", "total_sales", "mean_sales", "promo_share"],
                                  default="zero_share", format_func=data.label)
    metric = metric or "zero_share"
    fs = fs.sort_values(metric)
    fig = px.bar(fs, x=metric, y="family", orientation="h", color=metric, color_continuous_scale=theme.SEQUENTIAL,
                 hover_data={"total_sales": ":,.0f", "mean_sales": ":,.1f", "zero_share": ":.1%", "promo_share": ":.1%"})
    fig.update_layout(coloraxis_showscale=False, yaxis_title="", xaxis_title=data.label(metric),
                      xaxis_tickformat=".0%" if "share" in metric else ",")
    theme.chart(fig, height=760)
    theme.figcap("1.2", "Ranked bar chart",
                 f"The 33 product families ranked by {data.label(metric).lower()}.",
                 "Books, Baby care and similar products sell nothing on most days, because many stores barely stock them. Grocery I, Beverages and Produce make up most of the sales. "
                 "So what counts as unusually high must be judged separately for each store and product.",
                 "change the ranking above; point at a bar to see all four numbers for that product.")

    theme.chapter("1.3", "Promotions and sales in the raw file")
    smp = data.load("raw_train_sample").sample(20_000, random_state=1).copy()
    smp["promo_bucket"] = pd.cut(smp["onpromotion"], [-1, 0, 5, 20, 50, 1000], labels=["0", "1–5", "6–20", "21–50", "50+"])
    smp["log_sales"] = np.log1p(smp["sales"])
    fig = px.box(smp, x="promo_bucket", y="log_sales", color_discrete_sequence=[theme.OCHRE], points=False)
    fig.update_layout(xaxis_title="Items on promotion in that row", yaxis_title="log(1 + sales)")
    theme.chart(fig, height=380)
    theme.figcap("1.3", "Box plot",
                 "Sales of 20,000 randomly chosen rows, grouped by how many items were on promotion. Shown on a log scale so small and large sales both fit.",
                 "The more items on promotion, the more a row usually sells. No promotions were recorded in 2013. Part of this is simply that big products like Grocery I are promoted the most, so promotion is not the only reason.",
                 "the line in each box is the typical row; the box holds the middle half of rows.")

# =================================================================== stores

if True:  # stores.csv
    s = data.stores()
    theme.chapter("1.4", "Where the stores are")
    sd = data.load("store_day")
    totals = sd.groupby("store_nbr")["sales"].sum().rename("total_sales").reset_index()
    s2 = s.merge(totals, on="store_nbr")
    s2["store"] = "Store " + s2["store_nbr"].astype(str)
    size = st.segmented_control("Box size", ["Number of stores", "Total sales"], default="Number of stores")
    fig = px.treemap(s2, path=[px.Constant("Ecuador"), "state", "city", "store"],
                     values=None if size == "Number of stores" else "total_sales", color="type",
                     color_discrete_map={"A": theme.TEAL, "B": theme.OCHRE, "C": theme.MOSS, "D": theme.PERSIMMON, "E": theme.PLUM, "(?)": theme.SAND},
                     hover_data={"total_sales": ":,.0f", "cluster": True})
    fig.update_traces(marker=dict(cornerradius=4, line=dict(color=theme.PAPER, width=1.5)), root_color=theme.PAPER_2,
                      textfont=dict(family=theme.FONT_BODY))
    theme.chart(fig, height=560)
    theme.figcap("1.4", "Treemap",
                 f"Province → city → store, sized by {size.lower()} and coloured by store type.",
                 "Pichincha (Quito) and Guayas (Guayaquil) have the most stores and the most sales. When sized by sales, type A stores get bigger and types C and E get smaller: the kind of store matters more than the number of stores.",
                 "click a province to zoom in, and the top bar to zoom out; point at a box for details.")
    theme.chapter("1.5", "Store type against cluster")
    ct = pd.crosstab(s["cluster"], s["type"])
    fig = px.imshow(ct, text_auto=True, color_continuous_scale=theme.SEQUENTIAL_COOL, aspect="auto")
    fig.update_layout(xaxis_title="Store type", yaxis_title="Cluster", coloraxis_showscale=False)
    fig.update_traces(hovertemplate="cluster %{y}, type %{x}: %{z} stores<extra></extra>")
    theme.chart(fig, height=520)
    theme.figcap("1.5", "Count heatmap", "Number of stores for every cluster and store type.",
                 "Almost every cluster contains just one store type, so a cluster is really a smaller group within a type.",
                 "darker cells mean more stores.")

# =================================================================== transactions

if True:  # transactions.csv
    sd = data.load("store_day")
    theme.chapter("1.6", "Where transaction records are missing",
                  "A missing customer count means <b>we do not know</b>, not zero. The map shows where the gaps are, and they follow a pattern.")
    sd = sd.copy()
    sd["ym"] = sd["date"].dt.to_period("M").dt.to_timestamp()
    sd["missing"] = sd["transactions_original"].isna().astype(int)
    view = st.segmented_control("Show", ["Missing store-days", "Missing with positive sales"], default="Missing store-days")
    if view == "Missing with positive sales":
        sd["missing"] = (sd["transactions_original"].isna() & (sd["sales"] > 0)).astype(int)
    pv = sd.pivot_table(index="store_nbr", columns="ym", values="missing", aggfunc="sum")
    fig = px.imshow(pv, color_continuous_scale=theme.SEQUENTIAL, aspect="auto")
    fig.update_traces(hovertemplate="store %{y}<br>%{x|%b %Y}<br>%{z} missing days<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="Store", coloraxis_colorbar_title="days")
    theme.chart(fig, height=620)
    theme.figcap("1.6", "Heatmap, store × month",
                 "How many days each month a store has sales but no customer count.",
                 "Long bands are stores that had not opened yet (store 52 until April 2017; stores 20, 21, 22, 29 and 42 until 2015). Short marks across all stores are 1 January and a few early-January days. "
                 "Switch to 'Missing with positive sales' to see the 118 cases where sales happened with no count: these need an estimate, not a zero.",
                 "darker means more missing days in that month; hover for exact numbers.")
    theme.chapter("1.7", "Traffic by store type")
    obs = sd[sd["transactions_original"].notna()]
    fig = px.violin(obs.sample(10_000, random_state=1), x="store_type", y="transactions_original", color="store_type", box=True, points=False,
                    color_discrete_sequence=theme.COLORWAY, category_orders={"store_type": list("ABCDE")})
    fig.update_layout(showlegend=False, xaxis_title="Store type", yaxis_title="Transactions per store-day")
    theme.chart(fig, height=420)
    theme.figcap("1.7", "Violin plot", "How many customers a store serves per day, for each store type (10,000 randomly chosen days).",
                 "Type A stores serve about three times as many customers per day as type C (median 3,138 against 1,017). The wide shapes show that stores of one type still differ a lot.",
                 "the shape is wide where a number is common; the small box inside marks the typical range.")

# =================================================================== oil

if True:  # oil.csv
    t = R["oil"]
    oil = data.load("raw_oil").rename(columns={"dcoilwtico": "price"})
    theme.chapter("1.8", "Five years of oil", "The price collapsed in late 2014. Empty days are not errors: the market was closed.")
    full = pd.DataFrame({"date": pd.date_range(oil["date"].min(), oil["date"].max())}).merge(oil, on="date", how="left")
    full["kind"] = np.where(full["price"].notna(), "price", np.where(full["date"].isin(oil["date"]), "empty row", "no row"))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=full["date"], y=full["price"], mode="lines", line=dict(color=theme.TEAL, width=1.4),
                             name="WTI price", connectgaps=False, hovertemplate="%{x|%a %d %b %Y}<br>%{y:.2f} USD<extra></extra>"))
    holes = full[full["kind"] == "empty row"]
    fig.add_trace(go.Scatter(x=holes["date"], y=np.full(len(holes), full["price"].min() - 4), mode="markers",
                             marker=dict(symbol="line-ns-open", size=10, color=theme.PERSIMMON), name="empty price (43)",
                             hovertemplate="%{x|%a %d %b %Y}: no price<extra></extra>"))
    fig.update_layout(yaxis_title="USD per barrel", xaxis=dict(rangeslider=dict(visible=True, thickness=.06)))
    theme.chart(fig, height=460)
    theme.figcap("1.8", "Line chart with gap markers",
                 "The oil price each day. Gaps in the line are weekends; orange marks are weekdays with no price because the US market was on holiday.",
                 "The price fell from about 100 dollars in mid-2014 to under 50 in early 2015 and about 26 in early 2016. Every empty day is a day the market was closed, so using the last known price is the right fix.",
                 "drag the slider under the chart to zoom into a period.")
    full["weekday"] = full["date"].dt.day_name()
    wd = full[full["price"].isna()].groupby("weekday").size().reindex(WEEKDAYS, fill_value=0).reset_index(name="days")
    fig = px.bar(wd, x="weekday", y="days", color_discrete_sequence=[theme.OCHRE], text="days")
    fig.update_traces(textposition="outside", hovertemplate="%{x}: %{y} days without a price<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="Days without a price")
    theme.chart(fig, height=340)
    theme.figcap("1.9", "Bar chart", "Calendar days without a price, by weekday (2013 – 2017).",
                 "Saturdays and Sundays have no price at all; the few weekday gaps are holidays such as Christmas, New Year and Thanksgiving.", "")

# =================================================================== holidays

if True:  # holidays_events.csv
    h = data.load("raw_holidays")
    theme.chapter("2.0", "The holiday calendar", "Every record, placed on a timeline. Hover for its name; filter by type.")
    types = st.multiselect("Types", sorted(h["type"].unique()), default=sorted(h["type"].unique()))
    hv = h[h["type"].isin(types)].copy()
    hv["status"] = np.where(hv["transferred"], "transferred away", "active")
    fig = px.scatter(hv, x="date", y="type", color="locale", symbol="status",
                     symbol_map={"active": "circle", "transferred away": "x-thin-open"},
                     hover_data={"description": True, "locale_name": True, "date": "|%d %b %Y", "status": True},
                     color_discrete_map={"National": theme.TEAL, "Regional": theme.OCHRE, "Local": theme.PERSIMMON})
    fig.update_traces(marker=dict(size=9, opacity=.8, line=dict(width=0)))
    fig.update_layout(yaxis_title="", xaxis_title="", legend_title_text="")
    theme.chart(fig, height=430)
    theme.figcap("2.0", "Timeline (strip plot)",
                 "Each mark is one holiday or event, coloured by who it applies to. Crosses are holidays that were moved to another date.",
                 "The dense band of events in April and May 2016 is the earthquake. Most local holidays are city foundation days. "
                 "A holiday that was moved always has a matching record on its new date.",
                 "point at a mark for its name and place; use the selector to hide types.")
    theme.chapter("2.1", "Transferred holidays: the pairs")
    moved = h[h["transferred"]][["date", "description", "locale_name"]].rename(columns={"date": "official date"})
    new = h[h["type"] == "Transfer"][["date", "description"]].rename(columns={"date": "celebrated on", "description": "transfer record"})
    moved = moved.sort_values("official date").reset_index(drop=True)
    new = new.sort_values("celebrated on").reset_index(drop=True)
    pairs = pd.concat([moved, new], axis=1)
    pairs["official date"] = pairs["official date"].dt.strftime("%a %d %b %Y")
    pairs["celebrated on"] = pairs["celebrated on"].dt.strftime("%a %d %b %Y")
    st.dataframe(pairs, width="stretch", hide_index=True)
    theme.figcap("2.2", "Table", "The 12 holidays that were moved, next to the dates they were moved to.",
                 "Holidays in the middle of the week are often moved next to a weekend. So the official date counts as a normal day, and the new date as the holiday.", "")

theme.flow_next("views/eda_before.py")
