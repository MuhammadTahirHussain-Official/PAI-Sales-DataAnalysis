import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from lib import data, explain, theme

theme.flow_top("views/studio.py")
theme.page_title("Technical overview", "Chart <em>studio</em>",
                 "Build your own chart: pick the data, what to plot, and which rows to include. Click any dotted word to see what it means.")

DATASETS = {
    "Each store on each day (90,936 rows)": ("store_day", "One row for each store on each day: sales, customers, promotions, oil price and holiday flags."),
    "Whole chain per day (1,684 rows)": ("daily", "One row per day, with all stores added together."),
    "Each product on each day (55,572 rows)": ("family_day", "One row for each product family on each day, with all stores added together."),
    "Each store and product (1,782 rows)": ("store_family", "One row for each store and product, summarised over all five years."),
    "Each product overall (33 rows)": ("family_summary", "One row for each product family, summarised over all stores and years."),
}
CHARTS = ["Line", "Scatter", "Bar", "Box", "Histogram", "Heatmap"]
CHART_TERMS = {"Scatter": "scatter", "Box": "boxplot", "Histogram": "histogram", "Heatmap": "heatmap"}
AGGREGATES = {"sum": "Add up (sum)", "mean": "Average (mean)", "median": "Middle value (median)", "max": "Highest",
              "min": "Lowest", "count": "Count the rows", "none": "No grouping, show every row"}

# ------------------------------------------------------------------ 1 what to plot
theme.chapter("Step 1", "Choose what to plot")
c1, c2 = st.columns([1, 2])
with c1:
    theme.label("Data table", "dataset_row")
    ds_name = st.selectbox("Table", list(DATASETS), label_visibility="collapsed")
key, desc = DATASETS[ds_name]
c2.markdown(f'<div class="hint" style="margin-top:1.7rem">{desc}</div>', unsafe_allow_html=True)

source = data.load(key).copy()
if "store_nbr" in source.columns and "city" not in source.columns:
    source = source.merge(data.stores().rename(columns={"type": "store_type"}), on="store_nbr", how="left")
numeric = [c for c in source.columns if pd.api.types.is_numeric_dtype(source[c]) and c not in ("store_nbr", "cluster")]
categorical = [c for c in source.columns if c not in numeric and c != "date"] + [c for c in ("store_nbr", "cluster") if c in source.columns]
all_cols = (["date"] if "date" in source.columns else []) + categorical + numeric

c1, c2, c3, c4 = st.columns(4)
with c1:
    theme.label("Chart type", "histogram")
    kind = st.selectbox("Chart type", CHARTS, label_visibility="collapsed")
with c2:
    theme.label("X axis", "xaxis")
    x = st.selectbox("X axis", all_cols, format_func=data.label, label_visibility="collapsed")
y_opts = numeric if kind != "Heatmap" else categorical + (["date"] if "date" in source.columns else [])
y_default = y_opts.index("sales") if "sales" in y_opts else (y_opts.index("total_sales") if "total_sales" in y_opts else 0)
with c3:
    theme.label("Y axis" if kind != "Histogram" else "Y axis (not used)", "yaxis")
    y = st.selectbox("Y axis", y_opts, format_func=data.label, index=min(y_default, len(y_opts) - 1), label_visibility="collapsed")
with c4:
    theme.label("Colour / group", "colour")
    color = st.selectbox("Colour", ["None"] + categorical, format_func=lambda c: "None" if c == "None" else data.label(c), label_visibility="collapsed")

c1, c2, c3, c4 = st.columns(4)
with c1:
    theme.label("Aggregate", "aggregate")
    agg = st.selectbox("Aggregate", list(AGGREGATES), format_func=AGGREGATES.get, index=6 if key == "daily" else 1, label_visibility="collapsed")
with c2:
    theme.label("Log scale, X axis", "log")
    logx = st.toggle("Use on X", False, label_visibility="collapsed")
with c3:
    theme.label("Log scale, Y axis", "log")
    logy = st.toggle("Use on Y", False, label_visibility="collapsed")
with c4:
    theme.label("Trend line", "trend")
    trend = st.toggle("Show trend", False, label_visibility="collapsed")

# ------------------------------------------------------------------ 2 filters
theme.chapter("Step 2", "Choose which data to include", "Leave a filter empty to include everything. Filters work together.")
ss = st.session_state
fk = f"f_{key}_"          # filter settings are remembered separately for each table
if st.button("Clear all filters", icon=":material/restart_alt:"):
    for name in [k for k in ss if str(k).startswith(fk)]:
        del ss[name]
    st.rerun()

df = source
if "date" in df.columns:
    lo, hi = df["date"].min().date(), df["date"].max().date()
    c1, c2 = st.columns(2)
    start = c1.date_input("From date", lo, min_value=lo, max_value=hi, key=fk + "from")
    end = c2.date_input("To date", hi, min_value=lo, max_value=hi, key=fk + "to")
    df = df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]

filter_cols = [c for c in ["store_nbr", "city", "state", "store_type", "cluster", "family", "year", "month", "weekday", "fill_method"] if c in df.columns]
for i in range(0, len(filter_cols), 3):
    for col_box, col in zip(st.columns(3), filter_cols[i:i + 3]):
        values = sorted(source[col].dropna().unique().tolist())
        if col == "weekday":
            values = [d for d in data.WEEKDAYS if d in values]
        names = {"month": lambda m: data.MONTHS[int(m) - 1], "store_nbr": lambda s: f"Store {s}"}.get(col, str)
        keep = col_box.multiselect(data.label(col), values, format_func=names, key=fk + col, placeholder="All")
        if keep:
            df = df[df[col].isin(keep)]

kinds = {"is_holiday": "Holiday", "is_national_holiday": "National holiday", "is_event": "Event", "is_work_day": "Work Day", "is_weekend": "Weekend",
         "is_payday": "Payday", "is_earthquake_period": "Earthquake month"}
kinds = {c: n for c, n in kinds.items() if c in df.columns}
if kinds:
    chosen = st.pills("Only these kinds of day", list(kinds), format_func=kinds.get, selection_mode="multi", key=fk + "days")
    for c in chosen or []:
        df = df[df[c] == 1]

c1, c2, c3 = st.columns([1.2, 2, 1])
limit_col = c1.selectbox("Limit a number", ["None"] + [c for c in numeric if not c.startswith("is_") and c not in ("year", "month")],
                         format_func=lambda c: "No limit" if c == "None" else data.label(c), key=fk + "limit")
if limit_col != "None":
    low, high = float(source[limit_col].min()), float(source[limit_col].max())
    if low < high:
        rng = c2.slider(f"Keep {data.label(limit_col).lower()} between", low, high, (low, high), key=fk + "range_" + limit_col)
        df = df[df[limit_col].between(*rng)]
if "sales" in df.columns and c3.toggle("Hide zero sales", False, key=fk + "zero"):
    df = df[df["sales"] > 0]

# ------------------------------------------------------------------ 3 pick rows by hand
with st.expander("Pick rows by hand (optional)"):
    theme.html('<div class="hint">Tick the boxes at the left of the table, and the chart will use only those rows. '
               f"Showing the first 2,000 of {len(df):,} rows; use the filters above to narrow them down.</div>")
    table = df.head(2000).reset_index(drop=True)
    shown = table.rename(columns=data.label)
    if "Date" in shown.columns:
        shown["Date"] = shown["Date"].dt.strftime("%d %b %Y")
    picked = st.dataframe(shown, hide_index=True, width="stretch", height=320, on_select="rerun", selection_mode="multi-row",
                          key=f"pick_{key}_{len(df)}")
    rows = picked.selection.rows if picked and picked.selection else []
    if rows:
        df = table.iloc[rows]

theme.stats([(f"{len(df):,}", "rows included", f"of {len(source):,} in this table", "hot" if len(df) < len(source) else False),
             (data.label(x), "x axis"), (AGGREGATES[agg] if kind in ("Line", "Scatter", "Bar") else "Not used", "aggregate")])

# ------------------------------------------------------------------ 4 chart
theme.chapter("Step 3", "Your chart")
if df.empty:
    theme.insight("No rows left", "These filters remove every row. Clear some filters to see a chart.")
elif kind == "Heatmap" and x == y:
    theme.insight("Choose two different columns", "A heatmap compares two things, so the X axis and Y axis need different columns.")
else:
    group = [x] + ([color] if color != "None" and color != x else [])
    if kind in ("Line", "Scatter", "Bar") and agg != "none" and y != x:
        plot = df.groupby(group, observed=True)[y].agg("size" if agg == "count" else agg).reset_index()
    else:
        plot = df
    if len(plot) > 60000 and kind in ("Scatter", "Line"):
        plot = plot.sample(60000, random_state=0).sort_values(x)
        st.caption("Showing a random sample of 60,000 points so the chart stays fast.")

    clr = None if color == "None" else color
    if clr:
        plot = plot.copy()
        plot[clr] = plot[clr].astype(str)
    labels = {c: data.label(c) for c in plot.columns}
    common = dict(color=clr, labels=labels, color_discrete_sequence=theme.COLORWAY, log_x=logx)
    if kind == "Line":
        fig = px.line(plot.sort_values(x), x=x, y=y, markers=len(plot) < 400, log_y=logy, **common)
        if len(plot) >= 400:
            fig.update_traces(mode="lines+markers", marker=dict(size=3, opacity=.35), line=dict(width=1.3))
    elif kind == "Scatter":
        fig = px.scatter(plot, x=x, y=y, log_y=logy, opacity=.6, render_mode="webgl", **common)
    elif kind == "Bar":
        fig = px.bar(plot, x=x, y=y, log_y=logy, barmode="group", **common)
    elif kind == "Box":
        fig = px.box(plot.sample(min(20000, len(plot)), random_state=0), x=x, y=y, log_y=logy, points=False, **common)
    elif kind == "Histogram":
        fig = px.histogram(plot.sample(min(40000, len(plot)), random_state=0), x=x, nbins=60, log_y=logy, **common)
    else:
        z = df.pivot_table(index=y, columns=x, values="sales" if "sales" in df.columns else numeric[0], aggfunc="mean")
        fig = px.imshow(z, color_continuous_scale=theme.SEQUENTIAL, aspect="auto", labels=dict(color="average"))

    if trend and kind in ("Scatter", "Line") and pd.api.types.is_numeric_dtype(plot[x]) and len(plot) > 2:
        xs = plot[x].astype(float).values
        ys = plot[y].astype(float).values
        ok = np.isfinite(xs) & np.isfinite(ys)
        k, b0 = np.polyfit(xs[ok], ys[ok], 1)
        r = np.corrcoef(xs[ok], ys[ok])[0, 1]
        grid = np.linspace(xs[ok].min(), xs[ok].max(), 50)
        fig.add_scatter(x=grid, y=k * grid + b0, mode="lines", name=f"trend (r = {r:.2f})", line=dict(color=theme.INK, dash="dash", width=1.5))

    fig.update_layout(xaxis_title=data.label(x), yaxis_title=(data.label(y) if kind != "Histogram" else "Number of rows"), legend_title_text="")
    event = theme.chart(fig, key=f"studio_{ds_name}_{kind}_{x}_{y}_{color}_{agg}", select=kind in ("Line", "Scatter", "Bar"), height=520)

    what = "How many rows fall in each range" if kind == "Histogram" else data.label(y)
    agg_txt = "" if agg == "none" or kind not in ("Line", "Scatter", "Bar") else f", {AGGREGATES[agg].lower()} for each {data.label(x).lower()}"
    theme.figcap("S.1", f"Your {kind.lower()} chart",
                 f"{what}{agg_txt}, shown against {data.label(x).lower()}{', split by ' + data.label(color).lower() if clr else ''}. Uses {len(df):,} rows after your filters.",
                 "Change any choice above and the chart redraws straight away. Aggregate decides what one point means: added up, average, or every single row.",
                 "point at a mark to see its values. On line, scatter and bar charts, click a point to compare it with its neighbours.")

    if event and event.selection and event.selection.points:
        p = event.selection.points[0]
        xv = p.get("x")
        if x == "date" and y in df.columns:
            sd = data.load("store_day")
            series = plot.groupby("date")[y].sum() if plot["date"].duplicated().any() else plot.set_index("date")[y]
            explain.explain(series.sort_index(), explain.context_table(sd), xv, data.label(y), "your chart")
        elif kind != "Box" and clr is None and y in plot.columns:
            explain.generic_point(plot, x, y, type(plot[x].iloc[0])(xv) if not isinstance(plot[x].iloc[0], str) else xv, data.label(y))
        else:
            st.markdown(f'<div class="hint">You picked {data.label(x)} = {theme.esc(xv)}, {data.label(y)} = {theme.esc(p.get("y"))}. '
                        f'Set Colour / group to None to compare it with its neighbours.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="hint">Click a point to compare it with the previous and next value. With Date on the X axis you get a full explanation of that day.</div>',
                    unsafe_allow_html=True)

    with st.expander("See the numbers behind this chart"):
        st.dataframe(plot.head(500).rename(columns=data.label), width="stretch", hide_index=True)
        st.download_button("Download as CSV", plot.to_csv(index=False).encode(), file_name="chart_data.csv")

theme.flow_next("views/studio.py")
