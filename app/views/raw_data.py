import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from lib import data, theme
from lib.data import MONTHS, WEEKDAYS

S = data.summary()
R = S["raw"]

theme.flow_top("views/raw_data.py")
theme.page_title(
    "Technical dashboard",
    "Raw data and <em>EDA before cleaning</em>",
    "Before anything is joined or cleaned, each file already tells a story: what is counted, what is missing and why. "
    "Each file below shows its columns, what every column means, and the charts that matter for it.")



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

    theme.chapter("1.1", "How sales are distributed",
                  "Every row is a store-family-day. Most of them sell very little; a small number sell thousands of units. "
                  "That shape decides how we must plot, summarise and later model sales.")
    c1, c2, c3 = st.columns([1, 1, 1])
    scale = c1.segmented_control("Scale", ["Log bins (all rows)", "Linear (sample)"], default="Log bins (all rows)")
    clip = c2.slider("Linear view: cut the tail at percentile", 90.0, 100.0, 99.0, 0.5)
    fam = c3.selectbox("Family (linear view)", ["All families"] + sorted(data.load("family_summary")["family"]))
    if scale == "Linear (sample)":
        smp = data.load("raw_train_sample")
        if fam != "All families":
            smp = smp[smp["family"] == fam]
        cut = smp["sales"].quantile(clip / 100)
        view = smp[smp["sales"] <= cut]
        fig = px.histogram(view, x="sales", nbins=80, color_discrete_sequence=[theme.TEAL])
        fig.update_traces(hovertemplate="sales %{x}<br>%{y:,} rows<extra></extra>", marker_line_width=0)
        fig.update_layout(xaxis_title="Units sold per row", yaxis_title="Rows (150,000-row sample)", bargap=0.04)
        theme.chart(fig, height=380)
        theme.figcap("1.1", "Histogram, linear scale",
                     f"{fam}: sales of a random sample of 150,000 rows, cut at the {clip:g}th percentile ({cut:,.0f} units).",
                     "Almost everything is squeezed into the first bars: most rows sell a handful of units. Moving the slider to 100 shows how far the tail reaches.",
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
                     "All 3,000,888 rows. The first, orange bar is the exact zero: 939,130 rows. The other bars grow by a constant factor, so small and large sales are both visible.",
                     "With log bins the selling rows form a broad hill around 10 – 1,000 units. Two populations appear: rows that sell nothing at all, and rows that sell normally.",
                     "move left to right through ever wider sales ranges; hover a bar for its exact range and count.")
    theme.stats([(f"{v:,.0f}", f"{float(k) * 100:g}th percentile", "") for k, v in sales["p"].items()])

    theme.chapter("1.2", "Which families sell, and which mostly do not",
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
                 "BOOKS, BABY CARE and similar families are zero on most rows, because many stores barely sell them. GROCERY I, BEVERAGES and PRODUCE carry most of the volume. "
                 "This is why outliers must be judged inside each store and family, not across the whole table.",
                 "switch the ranking above; hover a bar for all four measures of that family.")

    theme.chapter("1.3", "Promotions and sales in the raw file")
    smp = data.load("raw_train_sample").copy()
    smp["promo_bucket"] = pd.cut(smp["onpromotion"], [-1, 0, 5, 20, 50, 1000], labels=["0", "1–5", "6–20", "21–50", "50+"])
    smp["log_sales"] = np.log1p(smp["sales"])
    fig = px.box(smp, x="promo_bucket", y="log_sales", color_discrete_sequence=[theme.OCHRE], points=False)
    fig.update_layout(xaxis_title="Items on promotion in that row", yaxis_title="log(1 + sales)")
    theme.chart(fig, height=380)
    theme.figcap("1.3", "Box plot",
                 "Sales (log scale) of 150,000 sample rows, grouped by how many items were on promotion.",
                 "The more items are promoted, the higher the typical sales. Note that 2013 has no promotions recorded at all. Part of the lift is because big families (GROCERY I) are promoted the most, so promotions and family size are tangled; the Explore page separates them.",
                 "the line in each box is the median; the box holds the middle 50% of rows.")

# =================================================================== stores
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
                 "Pichincha (Quito) and Guayas (Guayaquil) dominate both the number of stores and the sales. Sized by sales, type A stores grow and type C/E stores shrink: format matters more than count.",
                 "click a province to zoom in, click the top bar to zoom out; hover for type, cluster and sales.")
    theme.chapter("1.5", "Store type against cluster")
    ct = pd.crosstab(s["cluster"], s["type"])
    fig = px.imshow(ct, text_auto=True, color_continuous_scale=theme.SEQUENTIAL_COOL, aspect="auto")
    fig.update_layout(xaxis_title="Store type", yaxis_title="Cluster", coloraxis_showscale=False)
    fig.update_traces(hovertemplate="cluster %{y}, type %{x}: %{z} stores<extra></extra>")
    theme.chart(fig, height=520)
    theme.figcap("1.5", "Count heatmap", "Number of stores for every cluster and store type.",
                 "Nearly every cluster contains a single store type, so cluster is a finer split of type, not an independent property.",
                 "darker cells mean more stores.")

# =================================================================== transactions
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
    theme.chapter("1.6", "Where transaction records are missing",
                  "A missing transaction record is <b>unknown</b>, not zero. The map shows where the gaps are: they are not random.")
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
                 "Number of days per month on which a store has sales rows but no transaction record.",
                 "Long dark bands belong to stores that had not opened yet (store 52 until April 2017, stores 20, 21, 22, 29, 42 until 2015). Short marks across all stores are 1 January and a few early-January days. "
                 "Switch to 'positive sales' to see the 118 store-days where sales happened anyway: these need an estimate, not a zero.",
                 "darker means more missing days in that month; hover for exact numbers.")
    theme.chapter("1.7", "Traffic by store type")
    obs = sd[sd["transactions_original"].notna()]
    fig = px.violin(obs, x="store_type", y="transactions_original", color="store_type", box=True, points=False,
                    color_discrete_sequence=theme.COLORWAY, category_orders={"store_type": list("ABCDE")})
    fig.update_layout(showlegend=False, xaxis_title="Store type", yaxis_title="Transactions per store-day")
    theme.chart(fig, height=420)
    theme.figcap("1.7", "Violin plot", "Distribution of observed transactions per store-day for each store type.",
                 "Type A stores serve about three times as many customers per day as type C (median 3,138 against 1,017). The wide shapes show that stores of one type still differ a lot.",
                 "the width shows how common a value is; the inner box marks the median and middle half.")

# =================================================================== oil
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
                 "Daily WTI price. Gaps in the line are weekends; orange marks are weekdays with an empty price (US market holidays).",
                 "From about 100 USD in mid-2014 the price fell to under 50 in early 2015 and to about 26 in early 2016. Every empty value sits on a closed-market day, so copying the last price forward is the correct fill.",
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
                 "Each mark is one record of holidays_events.csv, coloured by who it applies to; crosses are holidays that were moved to another date.",
                 "The dense band of Events in April – May 2016 is the earthquake (Terremoto Manabi +1 … +30). Local holidays (orange) are city foundation days. "
                 "A transferred holiday always has a matching 'Transfer' record on its new date.",
                 "hover a mark for its name and place; use the selector to hide types.")
    theme.chapter("2.1", "Transferred holidays: the pairs")
    moved = h[h["transferred"]][["date", "description", "locale_name"]].rename(columns={"date": "official date"})
    new = h[h["type"] == "Transfer"][["date", "description"]].rename(columns={"date": "celebrated on", "description": "transfer record"})
    moved = moved.sort_values("official date").reset_index(drop=True)
    new = new.sort_values("celebrated on").reset_index(drop=True)
    pairs = pd.concat([moved, new], axis=1)
    pairs["official date"] = pairs["official date"].dt.strftime("%a %d %b %Y")
    pairs["celebrated on"] = pairs["celebrated on"].dt.strftime("%a %d %b %Y")
    st.dataframe(pairs, width="stretch", hide_index=True)
    theme.figcap("2.2", "Table", "The 12 transferred holidays next to the 12 Transfer records, both sorted by date.",
                 "Holidays falling mid-week are often moved next to a weekend. In the cleaned data the official date counts as a normal day and the new date as the holiday.", "")

theme.flow_next("views/raw_data.py")
