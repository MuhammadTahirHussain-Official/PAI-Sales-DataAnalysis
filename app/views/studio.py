import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from lib import data, explain, theme

theme.flow_top("views/studio.py")
theme.page_title(
    "Technical overview",
    "Chart <em>studio</em>",
    "Pick a table, any column for x and y, a chart type and filters. Hover any mark for its values; click a point to compare it with its neighbours.")

DATASETS = {
    "Store-day (90,936 rows)": ("store_day", "One row per store and day: total sales, transactions, promotions, oil and all flags."),
    "Daily total (1,684 rows)": ("daily", "One row per day for the whole chain."),
    "Family-day (55,572 rows)": ("family_day", "One row per product family and day, summed over all stores."),
    "Store-family (1,782 rows)": ("store_family", "One row per store and family: totals and averages over five years."),
    "Family summary (33 rows)": ("family_summary", "One row per family from the raw training table."),
}
c1, c2 = st.columns([1, 2])
ds_name = c1.selectbox("Table", list(DATASETS))
key, desc = DATASETS[ds_name]
c2.markdown(f'<div class="hint" style="margin-top:1.7rem">{desc}</div>', unsafe_allow_html=True)
df = data.load(key).copy()
if "store_nbr" in df.columns and "city" not in df.columns:
    df = df.merge(data.stores().rename(columns={"type": "store_type"}), on="store_nbr", how="left")

numeric = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in ("store_nbr", "cluster")]
categorical = [c for c in df.columns if c not in numeric and c != "date"] + [c for c in ("store_nbr", "cluster") if c in df.columns]
all_cols = (["date"] if "date" in df.columns else []) + categorical + numeric

c1, c2, c3, c4 = st.columns(4)
kind = c1.selectbox("Chart type", ["Line", "Scatter", "Bar", "Box", "Histogram", "Heatmap"])
x = c2.selectbox("X axis", all_cols, format_func=data.label, index=0)
y_opts = numeric if kind != "Heatmap" else categorical + (["date"] if "date" in df.columns else [])
y_default = y_opts.index("sales") if "sales" in y_opts else (y_opts.index("total_sales") if "total_sales" in y_opts else 0)
y = c3.selectbox("Y axis" if kind != "Histogram" else "Value (histogram uses x only)", y_opts, format_func=data.label, index=min(y_default, len(y_opts) - 1))
color = c4.selectbox("Colour / group", ["None"] + categorical, format_func=lambda c: "None" if c == "None" else data.label(c))

c1, c2, c3, c4 = st.columns(4)
agg = c1.selectbox("Aggregate y by x", ["sum", "mean", "median", "max", "min", "count", "none (raw rows)"], index=1 if key != "daily" else 6)
logx = c2.toggle("Log x", False)
logy = c3.toggle("Log y", False)
trend = c4.toggle("Linear trend", False)

with st.expander("Filters", expanded=False):
    f1, f2, f3 = st.columns(3)
    if "date" in df.columns:
        lo, hi = df["date"].min().date(), df["date"].max().date()
        dr = f1.slider("Date range", lo, hi, (lo, hi), format="MMM YYYY")
        df = df[(df["date"] >= pd.Timestamp(dr[0])) & (df["date"] <= pd.Timestamp(dr[1]))]
    filt_col = f2.selectbox("Filter column", ["None"] + categorical, format_func=lambda c: "None" if c == "None" else data.label(c))
    if filt_col != "None":
        vals = sorted(df[filt_col].dropna().unique().tolist())
        keep = f3.multiselect("Keep values", vals, default=vals[:5])
        if keep:
            df = df[df[filt_col].isin(keep)]
    if "sales" in df.columns and st.toggle("Exclude rows with zero sales", False):
        df = df[df["sales"] > 0]

group = [x] + ([color] if color != "None" and color != x else [])
if kind in ("Line", "Scatter", "Bar") and not agg.startswith("none") and y != x:
    plot = df.groupby(group, observed=True)[y].agg("size" if agg == "count" else agg).reset_index()
else:
    plot = df
if len(plot) > 60000 and kind in ("Scatter", "Line"):
    plot = plot.sample(60000, random_state=0).sort_values(x)
    st.caption("Showing a random sample of 60,000 points for speed.")

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
    fig = px.box(plot, x=x, y=y, log_y=logy, points=False, **common)
elif kind == "Histogram":
    fig = px.histogram(plot, x=x, nbins=60, log_y=logy, **common)
else:
    z = df.pivot_table(index=y, columns=x, values="sales" if "sales" in df.columns else numeric[0], aggfunc="mean")
    fig = px.imshow(z, color_continuous_scale=theme.SEQUENTIAL, aspect="auto", labels=dict(color="mean"))

if trend and kind in ("Scatter", "Line") and pd.api.types.is_numeric_dtype(plot[x]) and len(plot) > 2:
    xs = plot[x].astype(float).values
    ys = plot[y].astype(float).values
    ok = np.isfinite(xs) & np.isfinite(ys)
    k, b0 = np.polyfit(xs[ok], ys[ok], 1)
    r = np.corrcoef(xs[ok], ys[ok])[0, 1]
    grid = np.linspace(xs[ok].min(), xs[ok].max(), 50)
    fig.add_scatter(x=grid, y=k * grid + b0, mode="lines", name=f"trend (r = {r:.2f})", line=dict(color=theme.INK, dash="dash", width=1.5))

fig.update_layout(xaxis_title=data.label(x), yaxis_title=(data.label(y) if kind != "Histogram" else "Rows"), legend_title_text="")
event = theme.chart(fig, key=f"studio_{ds_name}_{kind}_{x}_{y}_{color}_{agg}", select=kind in ("Line", "Scatter", "Bar"), height=520)

agg_txt = "" if agg.startswith("none") or kind not in ("Line", "Scatter", "Bar") else f" ({agg} per {data.label(x).lower()})"
theme.figcap("S.1", f"{kind} chart, custom",
             f"{data.label(y) if kind != 'Histogram' else 'Row count'}{agg_txt} against {data.label(x).lower()}"
             f"{', split by ' + data.label(color).lower() if clr else ''}, from the {ds_name.split(' (')[0].lower()} table ({len(df):,} rows after filters).",
             "Change any control above and the chart redraws. Aggregation decides what one point means: 'sum' gives totals, 'mean' typical values, 'none' every single row.",
             "hover for values; click a point (line, scatter or bar) for a comparison with its neighbours.")

if event and event.selection and event.selection.points:
    p = event.selection.points[0]
    xv = p.get("x")
    if x == "date" and y in df.columns:
        sd = data.load("store_day")
        series = plot.groupby("date")[y].sum() if plot["date"].duplicated().any() else plot.set_index("date")[y]
        explain.explain(series.sort_index(), explain.context_table(sd), xv, data.label(y), "chart studio selection")
    elif kind != "Box" and clr is None and y in plot.columns:
        explain.generic_point(plot, x, y, type(plot[x].iloc[0])(xv) if not isinstance(plot[x].iloc[0], str) else xv, data.label(y))
    else:
        st.markdown(f'<div class="hint">Selected {data.label(x)} = {theme.esc(xv)}, {data.label(y)} = {theme.esc(p.get("y"))}. '
                    f'Remove the colour grouping for a neighbour comparison.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="hint">Click a point to compare it with the previous and next value on the x axis. With date on the x axis you get the full day explanation.</div>',
                unsafe_allow_html=True)

with st.expander("Data behind the chart"):
    st.dataframe(plot.head(500), width="stretch", hide_index=True)
    st.download_button("Download as CSV", plot.to_csv(index=False).encode(), file_name="chart_data.csv")

theme.flow_next("views/studio.py")
