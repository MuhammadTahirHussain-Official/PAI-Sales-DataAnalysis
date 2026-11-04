"""Explain one clicked point of a time series: how it compares with its neighbours and why."""
import numpy as np
import pandas as pd
import streamlit as st

from lib import data
from lib.theme import esc, fmt

WINDOW = 7


def _pct(a, b):
    if b is None or b == 0 or pd.isna(b) or pd.isna(a):
        return None
    return (a - b) / abs(b) * 100


def _arrow(p):
    if p is None:
        return "–"
    cls = "up" if p >= 0 else "down"
    return f'<span class="{cls}">{p:+.1f}%</span>'


def store_scope(store_day, scope, value):
    """Filter the store-day table to a scope (all / store / city / type / cluster)."""
    if scope == "All stores" or value is None:
        return store_day
    col = {"Store": "store_nbr", "City": "city", "Store type": "store_type", "Cluster": "cluster"}[scope]
    return store_day[store_day[col] == value]


def context_table(sd):
    """Aggregate a store-day subset to one row per date with all context columns."""
    return (
        sd.groupby("date")
        .agg(sales=("sales", "sum"), transactions=("transactions", "sum"),
             transactions_original=("transactions_original", "sum"),
             promotions=("promotions", "sum"), stores_selling=("sales", lambda x: int((x > 0).sum())),
             stores=("store_nbr", "nunique"), filled=("fill_method", lambda x: int((x != "observed").sum())),
             zero_families=("zero_families", "sum"), oil_price=("oil_price", "first"),
             holiday_stores=("is_holiday", "sum"), event=("is_event", "max"),
             work_day=("is_work_day", "max"), earthquake=("is_earthquake_period", "max"),
             payday=("is_payday", "first"), weekend=("is_weekend", "first"),
             open_stores=("store_open", "sum"))
    )


def explain(series, ctx, when, metric_label, scope_text, store_list=None):
    """series: pd.Series indexed by date (the plotted metric). ctx: context_table() output."""
    when = pd.Timestamp(when).normalize()
    if when not in series.index:
        nearest = series.index[np.argmin(np.abs((series.index - when).days))]
        when = nearest
    value = series.loc[when]
    before = series[(series.index < when) & (series.index >= when - pd.Timedelta(days=WINDOW))]
    after = series[(series.index > when) & (series.index <= when + pd.Timedelta(days=WINDOW))]
    neighbours = pd.concat([before, after])
    same_weekday = series[(series.index.dayofweek == when.dayofweek) & (series.index != when)
                          & (abs((series.index - when).days) <= 35)]
    p_before, p_after = _pct(value, before.mean()), _pct(value, after.mean())
    p_nb, p_wd = _pct(value, neighbours.mean()), _pct(value, same_weekday.mean())
    rank = (series.rank(pct=True).loc[when]) * 100

    if p_nb is None:
        verdict, tone = "Not enough neighbouring days to compare.", "flat"
    elif p_nb <= -15:
        verdict, tone = f"A dip: {abs(p_nb):.0f}% below the surrounding two weeks.", "down"
    elif p_nb >= 15:
        verdict, tone = f"A peak: {p_nb:.0f}% above the surrounding two weeks.", "up"
    else:
        verdict, tone = f"In line with its neighbours ({p_nb:+.0f}%).", "flat"

    reasons = []  # (weight, html)
    c = ctx.loc[when] if when in ctx.index else None
    near = ctx[(ctx.index != when) & (abs((ctx.index - when).days) <= WINDOW)] if c is not None else None

    # calendar
    h = data.holidays_active()
    todays = h[h["date"] == when]
    if store_list is not None and len(todays):
        st_meta = data.stores()
        st_meta = st_meta[st_meta["store_nbr"].isin(store_list)]
        todays = todays[(todays["locale"] == "National")
                        | ((todays["locale"] == "Regional") & todays["locale_name"].isin(st_meta["state"]))
                        | ((todays["locale"] == "Local") & todays["locale_name"].isin(st_meta["city"]))]
    if when.month == 1 and when.day == 1:
        reasons.append((100, "<b>1 January.</b> Almost every store is closed on New Year's Day, so sales fall to nearly zero every year."))
    if when.month == 12 and 15 <= when.day <= 24:
        reasons.append((60, f"<b>Christmas run-up.</b> {25 - when.day} days before Christmas: December is the strongest month every year."))
    if when.month == 12 and when.day in (26, 31) or (when.month == 1 and when.day in (2, 3)):
        reasons.append((45, "<b>Holiday-season shopping.</b> The days around Christmas and New Year are among the busiest of the year."))
    for _, ev in todays.iterrows():
        kind = ev["type"]
        where = "nationwide" if ev["locale"] == "National" else f'in {ev["locale_name"]}'
        if not ev["active"]:
            reasons.append((20, f'<b>{esc(ev["description"])}</b> was officially on this date but was <b>transferred</b> to another day, so it was a normal working day {where}.'))
        elif kind == "Work Day":
            reasons.append((35, f'<b>Work Day ({esc(ev["description"])}).</b> A weekend day turned into a working day {where} to make up for a bridge holiday.'))
        elif kind == "Event":
            reasons.append((55, f'<b>Event: {esc(ev["description"])}</b> {where}. Events such as Black Friday, Mother\'s Day, the World Cup or the earthquake change shopping behaviour.'))
        elif when.month == 1 and when.day == 1:
            continue
        elif tone == "down":
            reasons.append((60, f'<b>{kind}: {esc(ev["description"])}</b> {where}. On this holiday sales went down: many shops close early or people stay at home.'))
        elif tone == "up":
            reasons.append((60, f'<b>{kind}: {esc(ev["description"])}</b> {where}. Holidays usually raise grocery sales (about +26% on national holidays in this data).'))
        else:
            reasons.append((30, f'<b>{kind}: {esc(ev["description"])}</b> {where}. It had little effect on this day.'))

    wd = when.day_name()
    if p_wd is not None and p_nb is not None:
        if when.dayofweek >= 5:
            reasons.append((30 + abs(p_nb) / 4, f"<b>{wd}.</b> Weekends sell about 39% more than weekdays. Compared with nearby {wd}s this day is {_arrow(p_wd)}, so the weekday explains {'most' if abs(p_wd) < abs(p_nb) / 2 else 'only part'} of the difference."))
        else:
            reasons.append((10 + abs(p_wd) / 4, f"<b>{wd}.</b> Compared with other {wd}s in the five weeks around it, this day is {_arrow(p_wd)}."))

    if c is not None and near is not None and len(near):
        p_promo = _pct(c["promotions"], near["promotions"].mean())
        if p_promo is not None and abs(p_promo) >= 20 and near["promotions"].mean() > 0:
            reasons.append((abs(p_promo) / 3, f"<b>Promotions {_arrow(p_promo)}</b> versus the neighbouring days ({fmt(c['promotions'])} items on promotion). More promoted items usually lift sales (correlation 0.31)."))
        sel_near = near["stores_selling"].mean()
        if c["stores_selling"] < sel_near - 0.5:
            reasons.append((70 * (1 - c["stores_selling"] / max(sel_near, 1)) + 10,
                            f"<b>Fewer stores selling:</b> {int(c['stores_selling'])} of {int(c['stores'])} stores had sales, against {sel_near:.1f} on neighbouring days. Closed stores pull the total down."))
        p_tx = _pct(c["transactions_original"], near["transactions_original"].mean())
        if p_tx is not None and abs(p_tx) >= 10 and c["transactions_original"] > 0:
            reasons.append((abs(p_tx) / 3, f"<b>Customer traffic {_arrow(p_tx)}:</b> {fmt(c['transactions_original'])} observed transactions. Sales follow transactions closely (correlation 0.84)."))
        if c["filled"] > 0:
            reasons.append((15, f"<b>{int(c['filled'])} store-day(s) had no transaction record</b> and were filled during cleaning (0 if the store sold nothing, otherwise a ratio estimate)."))
        if c["earthquake"]:
            reasons.append((40, "<b>Earthquake period</b> (16 April – 16 May 2016). People bought and donated food and water; daily sales averaged 17% more than the month before."))
        if c["payday"]:
            reasons.append((8, "<b>Payday</b> (15th or month end). In this data the payday effect is small, about +1%."))
        if c["open_stores"] < c["stores"]:
            reasons.append((25, f"<b>{int(c['stores'] - c['open_stores'])} store(s) not open yet</b> on this date (they sold nothing before their first sales day)."))
        oil_week = ctx["oil_price"][(ctx.index <= when) & (ctx.index >= when - pd.Timedelta(days=7))]
        if len(oil_week) > 1:
            p_oil = _pct(oil_week.iloc[-1], oil_week.iloc[0])
            if p_oil is not None and abs(p_oil) >= 5:
                reasons.append((6, f"<b>Oil price moved {_arrow(p_oil)}</b> during the week (now {c['oil_price']:.2f} USD). Oil affects Ecuador's economy over months, not single days, so this is a background factor."))

    if tone == "flat" and not reasons:
        reasons.append((1, "No special calendar, promotion or store effect: this looks like an ordinary day for this scope."))
    reasons.sort(key=lambda r: -r[0])

    cells = [
        (fmt(value, 0 if abs(value) >= 100 else 2), metric_label),
        (_arrow(p_before), f"vs {WINDOW} days before"),
        (_arrow(p_after), f"vs {WINDOW} days after"),
        (_arrow(p_wd), f"vs nearby {wd}s"),
        (f"{rank:.0f}th", "percentile of all days"),
    ]
    grid = "".join(f'<div class="cell"><div class="v">{v}</div><div class="k">{k}</div></div>' for v, k in cells)
    items = "".join(f"<li>{r[1]}</li>" for r in reasons[:6])
    st.markdown(
        f'<div class="explain"><div class="eyebrow">Clicked point · {esc(scope_text)}</div>'
        f'<h3>{when:%A, %d %B %Y}</h3><div class="verdict">{verdict}</div>'
        f'<div class="grid">{grid}</div>'
        f'<div class="eyebrow">Why it looks like this — strongest reasons first</div><ol>{items}</ol></div>',
        unsafe_allow_html=True)

    window = series[(series.index >= when - pd.Timedelta(days=WINDOW)) & (series.index <= when + pd.Timedelta(days=WINDOW))]
    return window, when


def generic_point(df, x, y, xval, agg_label):
    """For non-date x axes: compare the clicked category/value with its neighbours on x."""
    ordered = df.sort_values(x).reset_index(drop=True)
    idx = ordered.index[ordered[x] == xval]
    if len(idx) == 0:
        return
    i = idx[0]
    v = ordered.loc[i, y]
    prev_v = ordered.loc[i - 1, y] if i > 0 else None
    next_v = ordered.loc[i + 1, y] if i < len(ordered) - 1 else None
    mean_v = ordered[y].mean()
    rank = ordered[y].rank(pct=True).loc[i] * 100
    p_prev, p_next, p_mean = _pct(v, prev_v), _pct(v, next_v), _pct(v, mean_v)
    if p_mean is None:
        verdict = "Comparison not available."
    elif p_mean >= 25:
        verdict = f"Well above average: {p_mean:.0f}% higher than the mean of all {len(ordered)} points."
    elif p_mean <= -25:
        verdict = f"Well below average: {abs(p_mean):.0f}% lower than the mean of all {len(ordered)} points."
    else:
        verdict = f"Close to the average of all points ({p_mean:+.0f}%)."
    cells = [(fmt(v, 2 if abs(v) < 100 else 0), agg_label), (_arrow(p_prev), "vs previous on x"),
             (_arrow(p_next), "vs next on x"), (_arrow(p_mean), "vs mean of all"), (f"{rank:.0f}th", "percentile")]
    grid = "".join(f'<div class="cell"><div class="v">{a}</div><div class="k">{b}</div></div>' for a, b in cells)
    st.markdown(f'<div class="explain"><div class="eyebrow">Clicked point</div><h3>{esc(data.label(x))}: {esc(xval)}</h3>'
                f'<div class="verdict">{verdict}</div><div class="grid">{grid}</div></div>', unsafe_allow_html=True)
