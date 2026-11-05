import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from lib import data, explain, theme
from lib.data import MONTHS, WEEKDAYS

theme.flow_top("views/explore.py")
theme.page_title(
    "Technical overview",
    "EDA <em>after cleaning</em>",
    "Ten questions, each with its own charts and controls, all on this page. Point at any chart for exact values. On the time series, "
    "click a point to get a summary of that day: how it compares with the days around it, and the most likely reasons.")

store_day = data.load("store_day")
family_day = data.load("family_day")
daily = data.load("daily")
hol = data.holidays_active()

# national / any holiday names per date for hover text
names = (hol[hol["active"]].groupby("date")
         .apply(lambda g: " · ".join(f"{d} ({l})" if l != "Ecuador" else d for d, l in zip(g["description"], g["locale_name"])),
                include_groups=False))


def scope_picker(prefix, allow_family=True):
    c1, c2 = st.columns([1, 2])
    opts = ["All stores", "Store", "City", "Store type", "Cluster"] + (["Product family"] if allow_family else [])
    scope = c1.selectbox("Scope", opts, key=f"{prefix}_scope")
    value = None
    if scope == "Store":
        value = c2.selectbox("Store", sorted(store_day["store_nbr"].unique()), key=f"{prefix}_v",
                             format_func=lambda s: f"Store {s} · {data.stores().set_index('store_nbr').loc[s, 'city']}")
    elif scope == "City":
        value = c2.selectbox("City", sorted(store_day["city"].unique()), key=f"{prefix}_v")
    elif scope == "Store type":
        value = c2.selectbox("Store type", list("ABCDE"), key=f"{prefix}_v")
    elif scope == "Cluster":
        value = c2.selectbox("Cluster", sorted(store_day["cluster"].unique()), key=f"{prefix}_v")
    elif scope == "Product family":
        value = c2.selectbox("Family", sorted(family_day["family"].unique()), key=f"{prefix}_v",
                             index=sorted(family_day["family"].unique()).index("GROCERY I"))
    return scope, value


# =================================================================== over time
@st.fragment
def ch_time():
    theme.chapter("5.1", "Sales and traffic over time",
                  "Choose what to plot and for which stores. Then click any point: the panel below explains that day.")
    scope, value = scope_picker("ts")
    family_scope = scope == "Product family"
    c1, c2, c3 = st.columns([1.3, 1, 1.4])
    metric_opts = (["sales", "promotions", "zero_stores"] if family_scope else
                   ["sales", "transactions_original", "transactions", "promotions", "sales_per_transaction", "stores_selling", "zero_families"])
    metric = c1.selectbox("Metric", metric_opts, format_func=data.label)
    smooth = c2.segmented_control("Smoothing", ["None", "7-day", "30-day"], default="None") or "None"
    dmin, dmax = daily["date"].min().date(), daily["date"].max().date()
    rng = c3.slider("Dates", dmin, dmax, (pd.Timestamp("2016-01-01").date(), pd.Timestamp("2016-12-31").date()), format="MMM YYYY")

    if family_scope:
        fd = family_day[family_day["family"] == value].set_index("date")
        series = fd[metric]
        ctx = explain.context_table(store_day)
        scope_text = f"family {value}, all stores"
        store_list = None
    else:
        sub = explain.store_scope(store_day, scope, value)
        ctx = explain.context_table(sub)
        if metric == "sales_per_transaction":
            series = ctx["sales"] / ctx["transactions_original"].replace(0, np.nan)
        elif metric == "transactions_original":
            series = ctx["transactions_original"].where(ctx["transactions_original"] > 0)
        else:
            series = ctx[metric]
        scope_text = "all 54 stores" if scope == "All stores" else f"{scope.lower()} {value}"
        store_list = sub["store_nbr"].unique()

    series = series.sort_index()
    shown = series.rolling({"7-day": 7, "30-day": 30}.get(smooth, 1), min_periods=1).mean() if smooth != "None" else series
    mask = (series.index >= pd.Timestamp(rng[0])) & (series.index <= pd.Timestamp(rng[1]))
    s_view, y_view = series[mask], shown[mask]
    hover_names = [names.get(d, "") for d in s_view.index]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=s_view.index, y=y_view.values, mode="lines+markers", name=data.label(metric),
        line=dict(color=theme.TEAL, width=1.6), marker=dict(size=4, color=theme.TEAL, opacity=.55),
        customdata=np.column_stack([s_view.values, [d.day_name() for d in s_view.index], hover_names]),
        hovertemplate="<b>%{x|%a %d %b %Y}</b><br>" + data.label(metric) + ": %{customdata[0]:,.1f}"
                      + ("<br>smoothed: %{y:,.1f}" if smooth != "None" else "") + "<br>%{customdata[2]}<extra></extra>"))
    hd = s_view[[d in names.index for d in s_view.index]]
    if len(hd):
        fig.add_trace(go.Scatter(x=hd.index, y=shown.loc[hd.index], mode="markers", name="holiday / event",
                                 marker=dict(size=8, color=theme.PERSIMMON, symbol="circle-open", line=dict(width=1.5)),
                                 hoverinfo="skip"))
    sel = st.session_state.get("ts_selected")
    if sel is not None and pd.Timestamp(sel) in s_view.index:
        fig.add_vline(x=pd.Timestamp(sel), line=dict(color=theme.PERSIMMON, width=1, dash="dot"))
    fig.update_layout(yaxis_title=data.label(metric), xaxis_title="", hovermode="closest",
                      legend=dict(orientation="h", y=1.1))
    event = theme.chart(fig, key=f"ts_{scope}_{value}_{metric}_{smooth}_{rng}", select=True, height=440)
    theme.figcap("5.1", "Interactive time series",
                 f"{data.label(metric)} per day for {scope_text}{', ' + smooth + ' average' if smooth != 'None' else ''}. Open orange circles mark holidays and events.",
                 "Sales go up and down every week, rise every December, fall to almost nothing every 1 January, and grow year after year. "
                 "Choose a store, city or product to see its own pattern, and click any point for an explanation.",
                 "point at a dot for its exact value and any holiday that day; click it for the summary below.")

    if event and event.selection and event.selection.points:
        st.session_state["ts_selected"] = event.selection.points[0]["x"]
    if st.session_state.get("ts_selected"):
        window, when = explain.explain(series.dropna(), ctx, st.session_state["ts_selected"], data.label(metric), scope_text, store_list)
        w = series[(series.index >= when - pd.Timedelta(days=21)) & (series.index <= when + pd.Timedelta(days=21))]
        f2 = go.Figure()
        f2.add_trace(go.Bar(x=w.index, y=w.values, marker_color=[theme.PERSIMMON if d == when else (theme.OCHRE if d.dayofweek >= 5 else theme.SAND) for d in w.index],
                            hovertemplate="%{x|%a %d %b}<br>%{y:,.1f}<extra></extra>"))
        f2.update_layout(yaxis_title=data.label(metric), bargap=.15)
        theme.chart(f2, height=260, key="ts_zoom")
        theme.figcap("5.2", "Zoom around the clicked day",
                     f"Three weeks either side of {when:%d %b %Y}. The clicked day is orange and weekends are yellow.",
                     "This shows whether the day is part of the normal weekly pattern, or really stands out.", "")
        if st.button("Clear selection"):
            st.session_state.pop("ts_selected", None)
            st.rerun(scope="fragment")
    else:
        st.markdown('<div class="hint">Click a point on the chart to see a summary of that day and why it is higher or lower than the days around it.</div>',
                    unsafe_allow_html=True)

# =================================================================== rhythm
@st.fragment
def ch_rhythm():
    theme.chapter("5.3", "When in the week and the year do people shop?")
    scope, value = scope_picker("rh", allow_family=False)
    c1, c2 = st.columns([1, 2])
    metric = c1.selectbox("Metric", ["sales", "transactions_original", "promotions"], format_func=data.label, key="rh_m")
    years = c2.multiselect("Years", sorted(store_day["year"].unique()), default=[2014, 2015, 2016], key="rh_y")
    sub = explain.store_scope(store_day, scope, value)
    sub = sub[(sub["sales"] > 0) & sub["year"].isin(years or sorted(store_day["year"].unique()))]
    pv = sub.pivot_table(index="weekday", columns="month", values=metric, aggfunc="mean").reindex(WEEKDAYS)
    pv.columns = [MONTHS[m - 1] for m in pv.columns]
    fig = px.imshow(pv, color_continuous_scale=theme.SEQUENTIAL, aspect="auto", text_auto=".3s")
    fig.update_traces(hovertemplate="%{y}, %{x}<br>average %{z:,.0f} per store-day<extra></extra>")
    fig.update_layout(coloraxis_colorbar_title="", xaxis_title="", yaxis_title="")
    theme.chart(fig, height=420)
    theme.figcap("5.3", "Heatmap, weekday × month",
                 f"Average {data.label(metric).lower()} per selling store-day for {('all stores' if scope == 'All stores' else scope.lower() + ' ' + str(value))}, in the selected years.",
                 "Saturdays and Sundays are the strongest in every month, and December is the strongest month. Thursday is the weakest day. "
                 "The day of the week matters far more than the month, except in December.",
                 "brighter squares mean more; point at one for its exact average.")
    prof = sub.groupby(["year", "weekday"])[metric].mean().reset_index()
    fig = px.line(prof, x="weekday", y=metric, color=prof["year"].astype(str), markers=True,
                  category_orders={"weekday": WEEKDAYS}, color_discrete_sequence=theme.COLORWAY)
    fig.update_layout(yaxis_title=data.label(metric), xaxis_title="", legend_title_text="")
    theme.chart(fig, height=360)
    theme.figcap("5.4", "Weekday profile per year", "Average for each weekday, one line per year.",
                 "Every year has the same shape: a dip mid-week and a peak at the weekend. The lines move up over time because the business grew.", "")

# =================================================================== holidays
@st.fragment
def ch_holidays():
    theme.chapter("5.5", "Do holidays change sales?",
                  "Each day at each store is labelled as a holiday, an event, a Work Day or a normal day. Days when a store sold nothing are left out.")
    c1, c2, c3 = st.columns(3)
    metric = c1.selectbox("Metric", ["sales", "transactions_original", "promotions"], format_func=data.label, key="h_m")
    stat = c2.segmented_control("Statistic", ["mean", "median"], default="mean", key="h_s") or "mean"
    stype = c3.selectbox("Store type", ["All"] + list("ABCDE"), key="h_t")
    sd = store_day[store_day["sales"] > 0].copy()
    if stype != "All":
        sd = sd[sd["store_type"] == stype]
    sd["kind"] = "Normal day"
    for col, name in [("is_work_day", "Work Day"), ("is_event", "Event"), ("is_local_holiday", "Local holiday"),
                      ("is_regional_holiday", "Regional holiday"), ("is_national_holiday", "National holiday")]:
        sd.loc[sd[col] == 1, "kind"] = name
    g = sd.groupby("kind")[metric].agg([stat, "size"]).sort_values(stat, ascending=False).reset_index()
    base = g.loc[g["kind"] == "Normal day", stat].iloc[0]
    g["lift"] = g[stat] / base - 1
    fig = px.bar(g, x="kind", y=stat, color="kind", text=g["lift"].map(lambda v: f"{v:+.0%}"),
                 color_discrete_map={"National holiday": theme.PERSIMMON, "Local holiday": theme.OCHRE, "Regional holiday": theme.SAND,
                                     "Event": theme.PLUM, "Work Day": theme.DUSK, "Normal day": theme.TEAL},
                 custom_data=["size"])
    fig.update_traces(textposition="outside", cliponaxis=False,
                      hovertemplate="%{x}<br>" + stat + " %{y:,.0f}<br>%{customdata[0]:,} store-days<extra></extra>")
    fig.add_hline(y=base, line=dict(color=theme.INK, dash="dot", width=1))
    fig.update_layout(showlegend=False, xaxis_title="", yaxis_title=f"{stat.capitalize()} {data.label(metric).lower()} per store-day")
    theme.chart(fig, height=400)
    theme.figcap("5.5", "Bar chart with baseline",
                 f"{stat.capitalize()} {data.label(metric).lower()} per selling store-day by kind of day; labels show the change against a normal day (dotted line).",
                 "National holidays sell about a quarter more than normal days, and events about a sixth more. Work Days are close to normal, as expected. Regional holidays happen too rarely to judge.",
                 "point at a bar to see how many days it is based on.")

    theme.chapter("5.6", "Which holidays matter most",
                  "Each holiday is compared with the same weekday in the four weeks around it, so a Sunday holiday is compared with other Sundays.")
    ds = daily.set_index("date")["sales"]
    nat = hol[(hol["active"]) & (hol["locale"] == "National") & (hol["date"].isin(ds.index))].copy()
    lifts = []
    for _, r in nat.iterrows():
        d = r["date"]
        same = ds[(ds.index.dayofweek == d.dayofweek) & (abs((ds.index - d).days) <= 28) & (ds.index != d)]
        lifts.append(ds[d] / same.mean() - 1 if len(same) else np.nan)
    nat["lift"] = lifts
    nat["name"] = nat["description"].str.replace(r"[+-]\d+$", "", regex=True).str.strip()
    agg = nat.groupby(["name", "type"])["lift"].agg(["mean", "size"]).reset_index().sort_values("mean")
    agg = agg[agg["size"] >= 2] if st.toggle("Only days that occur at least twice", True) else agg
    fig = px.bar(agg, x="mean", y="name", color="type", orientation="h", custom_data=["size"],
                 color_discrete_map={"Holiday": theme.PERSIMMON, "Additional": theme.OCHRE, "Bridge": theme.MOSS,
                                     "Transfer": theme.DUSK, "Event": theme.PLUM, "Work Day": theme.SAND})
    fig.update_traces(hovertemplate="%{y}<br>%{x:+.1%} vs same weekday<br>%{customdata[0]} days<extra></extra>")
    fig.add_vline(x=0, line=dict(color=theme.INK, width=1))
    fig.update_layout(xaxis_tickformat="+.0%", xaxis_title="Change in total daily sales vs the same weekday nearby", yaxis_title="",
                      legend_title_text="")
    theme.chart(fig, height=max(420, 22 * len(agg)))
    theme.figcap("5.6", "Bars left and right of zero",
                 "Average change in total daily sales on each national holiday or event, compared with the same weekday in the surrounding four weeks.",
                 "The Christmas days (Navidad, about +36% over 20 days) and Labour Day (+48%) lift sales most. 1 January is the deepest drop (−39%): stores close. "
                 "Ecuador's 2014 World Cup matches cut sales by 17 – 35% while people watched, and Black Friday and Mother's Day are slightly below a normal day of the same weekday.",
                 "bars to the right sold more than a normal day, and bars to the left sold less.")

    theme.chapter("5.7", "The countdown to Christmas")
    dd = daily[daily["date"].dt.month.isin([11, 12])].copy()
    dd["to_xmas"] = (pd.to_datetime(dd["year"].astype(str) + "-12-25") - dd["date"]).dt.days
    dd = dd[dd["to_xmas"].between(0, 45)]
    fig = px.line(dd, x="to_xmas", y="sales", color=dd["year"].astype(str), markers=True, color_discrete_sequence=theme.COLORWAY,
                  hover_data={"date": "|%a %d %b %Y"})
    fig.update_layout(xaxis=dict(autorange="reversed", title="Days until 25 December"), yaxis_title="Total sales per day", legend_title_text="")
    theme.chart(fig, height=380)
    theme.figcap("5.7", "Line chart, days to Christmas", "Total daily sales in the 45 days before Christmas, one line per year.",
                 "Sales climb through December and peak on 23 December, two days before Christmas. The weekly up and down continues during the climb.",
                 "reading left to right counts down to Christmas.")

# =================================================================== families
@st.fragment
def ch_families():
    theme.chapter("5.8", "What sells, and how each product changes")
    fams = sorted(family_day["family"].unique())
    c1, c2, c3 = st.columns([2, 1, 1])
    pick = c1.multiselect("Families", fams, default=["GROCERY I", "BEVERAGES", "PRODUCE", "CLEANING", "DAIRY"])
    norm = c2.segmented_control("View", ["Units", "Share of total", "Index (mean = 100)"], default="Units") or "Units"
    freq = c3.segmented_control("Resolution", ["Week", "Month"], default="Month") or "Month"
    fd = family_day[family_day["family"].isin(pick or fams[:3])]
    fd = fd.set_index("date").groupby("family")["sales"].resample("W" if freq == "Week" else "MS").sum().reset_index()
    if norm == "Share of total":
        tot = family_day.set_index("date")["sales"].resample("W" if freq == "Week" else "MS").sum()
        fd["sales"] = fd["sales"] / fd["date"].map(tot)
    elif norm == "Index (mean = 100)":
        fd["sales"] = fd["sales"] / fd.groupby("family")["sales"].transform("mean") * 100
    fd = fd[fd["date"] < "2017-08-01"] if freq == "Month" else fd
    fig = px.line(fd, x="date", y="sales", color="family", color_discrete_sequence=theme.COLORWAY)
    fig.update_traces(hovertemplate="%{x|%b %Y}<br>%{y:,.3s}<extra>%{fullData.name}</extra>")
    fig.update_layout(yaxis_title={"Units": "Units sold", "Share of total": "Share of all sales", "Index (mean = 100)": "Index"}[norm],
                      yaxis_tickformat=".0%" if norm == "Share of total" else None, xaxis_title="", legend_title_text="")
    theme.chart(fig, height=440)
    theme.figcap("5.8", "Multi-line chart", f"{freq}ly sales of the selected families, shown as {norm.lower()}.",
                 "'Index' puts small and large products on one scale, so you can see which ones change with the seasons (School supplies peak when school starts, Liquor in December) and which grow over time.",
                 "add or remove products above; double-click a name in the legend to show only that one.")

    theme.chapter("5.9", "When in the year each product sells",
                  "Each row is a product and each column a month. 100 means a normal month for that product.")
    fm = family_day.copy()
    fm["month"] = fm["date"].dt.month
    fm = fm[fm["date"].dt.year.between(2014, 2016)]
    pv = fm.groupby(["family", "month"])["sales"].mean().unstack()
    pv = pv.div(pv.mean(axis=1), axis=0) * 100
    pv.columns = MONTHS
    pv = pv.loc[pv.max(axis=1).sort_values().index]
    fig = px.imshow(pv, color_continuous_scale=theme.DIVERGING, color_continuous_midpoint=100, aspect="auto", zmin=40, zmax=160)
    fig.update_traces(hovertemplate="%{y}, %{x}: index %{z:.0f}<extra></extra>")
    fig.update_layout(xaxis_title="", yaxis_title="", coloraxis_colorbar_title="index")
    theme.chart(fig, height=780)
    theme.figcap("5.9", "Seasonal index heatmap", "Each product's sales per month compared with its own normal level (2014 to 2016).",
                 "Most products stay level, with a jump in December. School supplies jump in August and September, when school starts in the highlands. Books and Frozen foods have the biggest single peaks, and Liquor doubles in December. "
                 "Products at the bottom of the chart change the most through the year.",
                 "orange is above the product's normal level and blue is below.")

# =================================================================== stores
@st.fragment
def ch_stores_():
    theme.chapter("5.10", "How different are the stores?")
    c1, c2 = st.columns(2)
    color_by = c1.selectbox("Colour by", ["store_type", "cluster", "city", "state"], format_func=data.label)
    yrs = c2.slider("Years", 2013, 2017, (2015, 2016))
    sd = store_day[store_day["year"].between(*yrs) & (store_day["sales"] > 0)]
    st_ = sd.groupby("store_nbr").agg(sales=("sales", "mean"), transactions=("transactions_original", "mean"),
                                      store_type=("store_type", "first"), cluster=("cluster", "first"),
                                      city=("city", "first"), state=("state", "first"), days=("date", "size")).reset_index()
    st_["sales_per_tx"] = st_["sales"] / st_["transactions"]
    st_[color_by] = st_[color_by].astype(str)
    fig = px.scatter(st_, x="transactions", y="sales", color=color_by, size="days", size_max=16, text="store_nbr",
                     hover_data={"city": True, "store_type": True, "cluster": True, "sales_per_tx": ":.2f", "days": True},
                     color_discrete_sequence=theme.COLORWAY)
    fig.update_traces(textposition="top center", textfont=dict(family=theme.FONT_MONO, size=9, color=theme.MUTED),
                      marker=dict(line=dict(width=1, color=theme.PAPER)))
    fig.update_layout(xaxis_title="Average transactions per selling day", yaxis_title="Average sales per selling day", legend_title_text="")
    theme.chart(fig, height=520)
    theme.figcap("5.10", "Bubble scatter", "One bubble per store: customers per day going right, units sold per day going up. Bigger bubbles have more days of data.",
                 "The more customers a store has, the more it sells. Stores above the general line sell more per customer (bigger baskets), and stores below it serve many small baskets. "
                 "Type A stores occupy the top right.",
                 "point at a bubble for the store's details; change the colour to compare clusters or cities.")
    rank = st_.sort_values("sales")
    fig = px.bar(rank, x="sales", y=rank["store_nbr"].astype(str), color=color_by, orientation="h", color_discrete_sequence=theme.COLORWAY,
                 hover_data={"city": True})
    fig.update_layout(yaxis_title="Store", xaxis_title="Average sales per selling day", legend_title_text="", yaxis=dict(type="category"))
    theme.chart(fig, height=900)
    theme.figcap("5.11", "Ranked bars", "All stores ranked by average daily sales in the selected years.",
                 "The best store sells more than ten times as much per day as the weakest.", "")

# =================================================================== promotions
@st.fragment
def ch_promotions():
    theme.chapter("5.12", "Do promotions lift sales?",
                  "No promotions were recorded before 2014. For each product, days with a promotion are compared with days without one.")
    smp = data.load("clean_sample")
    smp = smp[smp["date"] >= "2014-04-01"]
    smp["promo"] = np.where(smp["onpromotion"] > 0, "with promotion", "no promotion")
    stat = st.segmented_control("Statistic", ["median", "mean"], default="median", key="p_s") or "median"
    g = smp.groupby(["family", "promo"])["sales"].agg(stat).unstack().dropna()
    g["lift"] = g["with promotion"] / g["no promotion"].replace(0, np.nan)
    g = g.sort_values("with promotion").reset_index()
    fig = go.Figure()
    for _, r in g.iterrows():
        fig.add_trace(go.Scatter(x=[r["no promotion"], r["with promotion"]], y=[r["family"]] * 2, mode="lines",
                                 line=dict(color=theme.RULE, width=3), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=g["no promotion"], y=g["family"], mode="markers", name="no promotion",
                             marker=dict(color=theme.SAND, size=10), hovertemplate="%{y}<br>no promotion: %{x:,.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=g["with promotion"], y=g["family"], mode="markers", name="with promotion",
                             marker=dict(color=theme.PERSIMMON, size=10), customdata=g["lift"],
                             hovertemplate="%{y}<br>with promotion: %{x:,.1f}<br>%{customdata:.1f}× the no-promotion value<extra></extra>"))
    fig.update_layout(xaxis_type="log", xaxis_title=f"{stat.capitalize()} units per row (log scale)", yaxis_title="")
    theme.chart(fig, height=820)
    theme.figcap("5.12", "Two dots per product", f"{stat.capitalize()} sales per row with and without promotion, per family (150,000-row sample, from April 2014).",
                 "Almost every product sells far more when on promotion. Part of that is the promotion itself, and part is that stores tend to promote what already sells well.",
                 "the further apart the two dots, the bigger the difference; point at the orange dot for how many times more.")
    d = daily.set_index("date")[["sales", "promotions"]].resample("MS").sum().iloc[:-1]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=d.index, y=d["sales"], name="sales", line=dict(color=theme.TEAL, width=2)), secondary_y=False)
    fig.add_trace(go.Bar(x=d.index, y=d["promotions"], name="items on promotion", marker_color=theme.OCHRE, opacity=.45), secondary_y=True)
    fig.update_yaxes(title_text="Monthly sales", secondary_y=False)
    fig.update_yaxes(title_text="Monthly promoted items", secondary_y=True, showgrid=False)
    theme.chart(fig, height=360)
    theme.figcap("5.13", "Line and bars together", "Monthly total sales (line) and monthly promoted items (bars).",
                 "Promotions start in 2014 and grow quickly until 2016, while sales also grow. Because both rise together over time, this chart alone can make promotions look more powerful than they are.", "")

# =================================================================== oil
@st.fragment
def ch_oil():
    theme.chapter("5.14", "Does the oil price move grocery sales?",
                  "Ecuador exports oil, so a price crash can squeeze incomes. Can we see that in grocery sales?")
    win = st.slider("Rolling window (days)", 30, 365, 90, 15)
    d = daily.set_index("date")[["sales", "oil_price"]].copy()
    d = d[d["sales"] > 1000]
    d["sales_avg"] = d["sales"].rolling(30, min_periods=10).mean()
    d["corr"] = d["sales"].rolling(win, min_periods=win // 2).corr(d["oil_price"])
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[.65, .35], vertical_spacing=.06,
                        specs=[[{"secondary_y": True}], [{}]])
    fig.add_trace(go.Scatter(x=d.index, y=d["sales_avg"], name="sales, 30-day average", line=dict(color=theme.TEAL, width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=d.index, y=d["oil_price"], name="oil price", line=dict(color=theme.PERSIMMON, width=1.5)), row=1, col=1, secondary_y=True)
    fig.add_trace(go.Scatter(x=d.index, y=d["corr"], name=f"{win}-day correlation", fill="tozeroy",
                             line=dict(color=theme.PLUM, width=1), fillcolor="rgba(109,59,71,.15)"), row=2, col=1)
    fig.update_yaxes(title_text="Sales", row=1, col=1, secondary_y=False)
    fig.update_yaxes(title_text="USD", row=1, col=1, secondary_y=True, showgrid=False)
    fig.update_yaxes(title_text="corr.", range=[-1, 1], row=2, col=1)
    fig.update_layout(hovermode="x unified")
    theme.chart(fig, height=560)
    theme.figcap("5.14", "Lines, with their link below",
                 f"Top: sales (smoothed over 30 days) and the oil price. Bottom: how closely the two moved together over each {win}-day stretch.",
                 "Over the five years oil fell while sales rose, so overall they move in opposite directions (about −0.24). "
                 "But the link keeps swinging from negative to positive, so there is no steady day-to-day connection. Oil is at most a slow background factor.",
                 "change the number of days to compare short and long periods.")
    m = daily.set_index("date")[["sales", "oil_price"]].resample("MS").mean().reset_index()
    m["year"] = m["date"].dt.year.astype(str)
    fig = px.scatter(m, x="oil_price", y="sales", color="year", color_discrete_sequence=theme.COLORWAY,
                     hover_data={"date": "|%b %Y"})
    fig.update_traces(marker=dict(size=10, line=dict(width=1, color=theme.PAPER)))
    fig.update_layout(xaxis_title="Average oil price in the month (USD)", yaxis_title="Average daily sales in the month", legend_title_text="")
    theme.chart(fig, height=400)
    theme.figcap("5.15", "Scatter, one point per month", "Monthly average oil price against monthly average daily sales, coloured by year.",
                 "The dots group by year instead of forming one line, so the growth of the business explains sales much better than the oil price does.", "")

# =================================================================== earthquake
@st.fragment
def ch_earthquake():
    theme.chapter("5.16", "16 April 2016: the earthquake",
                  "A magnitude 7.8 earthquake hit the coast of Ecuador. The holiday file marks the month after it as special events.")
    ds = daily.set_index("date")["sales"]
    w = ds["2016-03-01":"2016-06-30"]
    prev = ds.shift(364)["2016-03-01":"2016-06-30"]
    fig = go.Figure()
    fig.add_vrect(x0="2016-04-16", x1="2016-05-16", fillcolor=theme.PERSIMMON, opacity=.08, line_width=0,
                  annotation_text="earthquake period", annotation_position="top left",
                  annotation_font=dict(family=theme.FONT_MONO, size=11, color=theme.PERSIMMON))
    fig.add_trace(go.Scatter(x=prev.index, y=prev.values, name="same weekday one year earlier", line=dict(color=theme.SAND, width=1.5)))
    fig.add_trace(go.Scatter(x=w.index, y=w.values, name="2016", line=dict(color=theme.TEAL, width=2)))
    fig.update_layout(yaxis_title="Total sales per day", hovermode="x unified")
    theme.chart(fig, height=420)
    before = ds["2016-03-16":"2016-04-15"].mean()
    during = ds["2016-04-16":"2016-05-16"].mean()
    theme.figcap("5.16", "Line chart with comparison year",
                 "Daily sales from March to June 2016 against the same weekdays one year earlier (shifted by 364 days).",
                 f"Right after the earthquake daily sales jumped far above the weekday pattern; the month averaged {during / before - 1:+.0%} against the 30 days before. "
                 "The gap to the year before widens during that month and then closes again.",
                 "point at the chart to read both years for the same day.")
    fdd = family_day.set_index("date")
    b = fdd.loc["2016-03-16":"2016-04-15"].groupby("family")["sales"].mean()
    a = fdd.loc["2016-04-16":"2016-05-16"].groupby("family")["sales"].mean()
    ch = ((a / b - 1).dropna().sort_values()).reset_index(name="change")
    ch = ch[b.reindex(ch["family"]).values > 50]
    fig = px.bar(ch, x="change", y="family", orientation="h", color="change", color_continuous_scale=theme.DIVERGING, color_continuous_midpoint=0)
    fig.update_traces(hovertemplate="%{y}: %{x:+.1%}<extra></extra>")
    fig.update_layout(xaxis_tickformat="+.0%", coloraxis_showscale=False, yaxis_title="", xaxis_title="Change in average daily sales vs the 30 days before")
    theme.chart(fig, height=760)
    theme.figcap("5.17", "Bars by product", "How each product's daily sales changed during the earthquake month (products selling at least 50 units a day).",
                 "Almost every product rose; Grocery I, the largest, grew about 31%. School supplies jumped about 270%, but that overlaps with school starting on the coast in April and May, so not all of it is the earthquake.", "")

# =================================================================== distribution
@st.fragment
def ch_distribution():
    theme.chapter("5.18", "How sales are spread, and the unusually high days")
    smp = data.load("clean_sample")
    c1, c2, c3 = st.columns(3)
    by = c1.selectbox("Split by", ["type", "family", "cluster", "is_holiday", "is_weekend"], format_func=lambda c: data.label({"type": "store_type"}.get(c, c)))
    col = c2.segmented_control("Values", ["sales_log1p", "sales"], default="sales_log1p", format_func=lambda c: "log(1 + sales)" if c == "sales_log1p" else "sales") or "sales_log1p"
    zeros = c3.toggle("Include zero-sales rows", False)
    v = smp if zeros else smp[smp["sales"] > 0]
    v = v.sample(min(20_000, len(v)), random_state=1).copy()
    v[by] = v[by].astype(str)
    order = v.groupby(by)[col].median().sort_values().index.tolist()
    fig = px.box(v, x=col, y=by, color_discrete_sequence=[theme.TEAL], points=False, category_orders={by: order})
    fig.update_layout(xaxis_title="log(1 + sales)" if col == "sales_log1p" else "sales", yaxis_title="")
    theme.chart(fig, height=max(360, 24 * len(order)))
    theme.figcap("5.18", "Box plots", f"Distribution of {('log ' if col == 'sales_log1p' else '')}sales per row, split by {data.label(by).lower()} (20,000 sampled rows{', zeros included' if zeros else ', selling rows only'}).",
                 "Products differ hugely in size, so one limit for everything would mark all of Grocery I as extreme and none of Books. That is why each product is judged on its own.",
                 "switch to 'sales' to see how uneven the original values are.")
    sf = data.load("store_family")
    ex = sf.groupby("family")["extreme_rows"].sum().sort_values(ascending=False).head(15).reset_index()
    fig = px.bar(ex, x="family", y="extreme_rows", color_discrete_sequence=[theme.PERSIMMON])
    fig.update_layout(xaxis_title="", yaxis_title="Flagged rows", xaxis_tickangle=-35)
    theme.chart(fig, height=380)
    theme.figcap("5.19", "Bar chart", "Rows unusually high for their own store and product, using the IQR rule (top 15 products). 3,373 rows in total, or 0.11%.",
                 "Frozen foods are mostly in the week before Christmas. Home appliances appear when a store that usually sells 0 to 2 items sells a few more. These are real sales, so they are kept and only marked.", "")
    zz = daily.copy()
    zz["share"] = zz["zero_families"] / 1782
    fig = px.area(zz, x="date", y="share", color_discrete_sequence=[theme.SAND])
    fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Rows with zero sales", xaxis_title="")
    theme.chart(fig, height=300)
    theme.figcap("5.20", "Area chart", "Each day, the share of the 1,782 store and product combinations with no sales.",
                 "Rows with no sales fall from about 50% in 2013 to about 15% in 2017, as stores open and stock more products. The spikes to 100% are 1 January.", "")

# =================================================================== correlations
@st.fragment
def ch_corr():
    theme.chapter("5.21", "Which measures move together?",
                  "Only days with a real customer count are used. The estimated counts were worked out from sales, so including them would make the link look stronger than it is.")
    sd = store_day[store_day["fill_method"] == "observed"].copy()
    sd["sales_log"] = np.log1p(sd["sales"])
    sd["transactions_log"] = np.log1p(sd["transactions_original"])
    sd["store_type_A"] = (sd["store_type"] == "A").astype(int)
    opts = ["sales", "sales_log", "transactions_original", "transactions_log", "promotions", "oil_price", "zero_families",
            "is_holiday", "is_event", "is_weekend", "is_payday", "is_earthquake_period", "year", "month", "store_type_A"]
    pick = st.multiselect("Variables", opts, default=["sales", "transactions_original", "promotions", "oil_price", "is_holiday", "is_weekend", "is_payday", "year"],
                          format_func=data.label)
    method = st.segmented_control("Method", ["pearson", "spearman"], default="pearson") or "pearson"
    if len(pick) >= 2:
        cm = sd[pick].corr(method=method)
        lab = [data.label(c) for c in pick]
        fig = px.imshow(cm.values, x=lab, y=lab, color_continuous_scale=theme.DIVERGING, zmin=-1, zmax=1, text_auto=".2f", aspect="auto")
        fig.update_traces(hovertemplate="%{y} × %{x}<br>%{z:.3f}<extra></extra>")
        fig.update_layout(coloraxis_colorbar_title="")
        theme.chart(fig, height=560)
        theme.figcap("5.21", "Correlation matrix", f"{method.capitalize()} correlation between the chosen store-day measures (83,488 observed store-days).",
                     "Sales and customers are strongly linked (0.84). Promotions and year are linked because promotions grew over time. Oil is negative because it fell while sales grew.",
                     "+1 means they rise together, −1 means one falls when the other rises, and 0 means no steady link.")


for chapter_view in [ch_time, ch_rhythm, ch_holidays, ch_families, ch_stores_, ch_promotions,
                     ch_oil, ch_earthquake, ch_distribution, ch_corr]:
    chapter_view()

theme.flow_next("views/explore.py")
