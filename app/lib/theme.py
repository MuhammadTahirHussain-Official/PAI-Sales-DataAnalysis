"""Visual system: fonts, colours, motion and Plotly template for the app."""
import html as _html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

PAPER = "#F4EFE6"
PAPER_2 = "#EBE4D8"
CARD = "#FBF8F2"
INK = "#1A1814"
INK_2 = "#4A453D"
MUTED = "#857D70"
RULE = "#D8CFBF"

PERSIMMON = "#C4472B"
TEAL = "#1E4D4F"
MOSS = "#556B2F"
OCHRE = "#C38E2E"
PLUM = "#6D3B47"
DUSK = "#6F8FA6"
SAND = "#B9A88C"

COLORWAY = [TEAL, PERSIMMON, OCHRE, MOSS, PLUM, DUSK, SAND, "#3E3A33", "#9C5A3C", "#7E8C69"]
SEQUENTIAL = [[0, "#F4EFE6"], [0.25, "#E3CFA8"], [0.5, "#C38E2E"], [0.75, "#9C5A3C"], [1, "#3A1F16"]]
SEQUENTIAL_COOL = [[0, "#F4EFE6"], [0.35, "#A9BDB3"], [0.7, "#4F7A72"], [1, "#12312F"]]
DIVERGING = [[0, TEAL], [0.5, "#F4EFE6"], [1, PERSIMMON]]

FONT_BODY = "Geist, 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "'Geist Mono', ui-monospace, Menlo, monospace"
FONT_DISPLAY = "'Instrument Serif', Georgia, serif"

FONT_LINK = (
    "https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700"
    "&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap"
)

CSS = f"""
<style>
@import url('{FONT_LINK}');
:root {{
  --paper:{PAPER}; --paper-2:{PAPER_2}; --card:{CARD}; --ink:{INK}; --ink-2:{INK_2};
  --muted:{MUTED}; --rule:{RULE}; --persimmon:{PERSIMMON}; --teal:{TEAL}; --moss:{MOSS};
  --ochre:{OCHRE}; --plum:{PLUM};
  --ease: cubic-bezier(.2,.7,.1,1);
}}
html, body, .stApp, [data-testid="stAppViewContainer"] {{ background: var(--paper); }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button, .stApp textarea,
.stApp [data-baseweb] {{ font-family: {FONT_BODY}; color: var(--ink); }}
.stApp h1, .stApp h2, .stApp h3 {{ font-family: {FONT_DISPLAY}; font-weight: 400; letter-spacing: -0.01em; color: var(--ink); }}
.stApp code {{ font-family: {FONT_MONO}; background: var(--paper-2); color: var(--plum); border-radius: 4px; }}
[data-testid="stMainBlockContainer"] {{ max-width: 1240px; padding-top: 4.2rem; padding-bottom: 6rem; }}
[data-testid="stHeader"] {{ background: rgba(244,239,230,.86); backdrop-filter: blur(10px); border-bottom: 1px solid var(--rule); }}
[data-testid="stHeader"] a {{ font-family: {FONT_BODY} !important; letter-spacing: .01em; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: 'Material Symbols Rounded' !important; }}
[data-testid="stToolbar"] {{ right: 1rem; }}
[data-testid="stSidebar"] {{ background: var(--paper-2); border-right: 1px solid var(--rule); }}

/* motion */
@keyframes rise {{ from {{ opacity:0; transform: translateY(16px); }} to {{ opacity:1; transform:none; }} }}
@keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
@keyframes shimmer {{ from {{ background-position: -200% 0; }} to {{ background-position: 200% 0; }} }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div {{ animation: rise .7s var(--ease) both; }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(2) {{ animation-delay: .05s; }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(3) {{ animation-delay: .10s; }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(4) {{ animation-delay: .15s; }}
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] > div:nth-child(n+5) {{ animation-delay: .2s; }}
body.js-reveal .rv {{ opacity: 0; transform: translateY(22px); transition: opacity .9s var(--ease), transform .9s var(--ease); }}
body.js-reveal .rv.in {{ opacity: 1; transform: none; }}
@media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; transition: none !important; }} }}

/* editorial blocks */
.eyebrow {{ font-family: {FONT_MONO}; font-size: .74rem; letter-spacing: .16em; text-transform: uppercase; color: var(--persimmon); margin-bottom: .55rem; }}
.chapter {{ border-top: 1px solid var(--ink); padding-top: 1.1rem; margin: 3.2rem 0 1.2rem; }}
.chapter h2 {{ font-size: 2.6rem; line-height: 1.04; margin: 0 0 .6rem; }}
.chapter .lede {{ font-size: 1.08rem; line-height: 1.65; color: var(--ink-2); max-width: 760px; }}
.chapter .num {{ font-family: {FONT_MONO}; color: var(--muted); font-size: .8rem; float: right; }}
.page-title {{ margin: .4rem 0 2rem; }}
.page-title h1 {{ font-size: clamp(2.8rem, 6vw, 4.6rem); line-height: .98; margin: 0 0 1rem; }}
.page-title h1 em {{ color: var(--persimmon); font-style: italic; }}
.page-title p {{ font-size: 1.15rem; line-height: 1.6; color: var(--ink-2); max-width: 780px; }}
.prose {{ font-size: 1.02rem; line-height: 1.72; color: var(--ink-2); max-width: 780px; }}
.prose strong {{ color: var(--ink); font-weight: 600; }}

.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); margin: 1rem 0 1.6rem; }}
.stat {{ padding: 1.1rem 1.2rem 1.15rem 0; border-right: 1px solid var(--rule); margin-right: 1.2rem; }}
.stat:last-child {{ border-right: none; }}
.stat .v {{ font-family: {FONT_DISPLAY}; font-size: 2.3rem; line-height: 1; color: var(--ink); }}
.stat .v small {{ font-size: 1rem; color: var(--muted); margin-left: .2rem; }}
.stat .k {{ font-family: {FONT_MONO}; font-size: .7rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); margin-top: .45rem; }}
.stat .d {{ font-size: .86rem; color: var(--ink-2); margin-top: .35rem; line-height: 1.45; }}
.stat.hot .v {{ color: var(--persimmon); }}

.figcap {{ display: grid; grid-template-columns: 150px 1fr; gap: 1.2rem; border-top: 1px solid var(--rule); padding: .9rem 0 .2rem; margin: -.4rem 0 1.8rem; }}
.figcap .tag {{ font-family: {FONT_MONO}; font-size: .7rem; letter-spacing: .12em; text-transform: uppercase; color: var(--persimmon); line-height: 1.6; }}
.figcap .tag span {{ display: block; color: var(--muted); }}
.figcap .body b {{ font-weight: 600; color: var(--ink); }}
.figcap .body p {{ margin: .2rem 0 .45rem; font-size: .93rem; line-height: 1.6; color: var(--ink-2); }}
.figcap .read {{ font-size: .85rem; color: var(--muted); }}
@media (max-width: 700px) {{ .figcap {{ grid-template-columns: 1fr; gap: .3rem; }} }}

.card {{ background: var(--card); border: 1px solid var(--rule); border-radius: 14px; padding: 1.25rem 1.35rem; height: 100%; }}
.card h4 {{ font-family: {FONT_DISPLAY}; font-weight: 400; font-size: 1.5rem; margin: 0 0 .4rem; }}
.card p {{ font-size: .92rem; line-height: 1.6; color: var(--ink-2); margin: 0; }}
.card .meta {{ font-family: {FONT_MONO}; font-size: .72rem; color: var(--muted); letter-spacing: .08em; text-transform: uppercase; margin-bottom: .6rem; }}

.ledger {{ width: 100%; border-collapse: collapse; font-size: .92rem; margin: .4rem 0 1.4rem; }}
.ledger th {{ font-family: {FONT_MONO}; font-weight: 500; font-size: .7rem; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); text-align: left; padding: .55rem .7rem .55rem 0; border-bottom: 1px solid var(--ink); }}
.ledger td {{ padding: .7rem .7rem .7rem 0; border-bottom: 1px solid var(--rule); vertical-align: top; color: var(--ink-2); line-height: 1.5; }}
.ledger td:first-child {{ color: var(--ink); font-weight: 500; }}
.ledger td.n {{ font-family: {FONT_MONO}; color: var(--ink); white-space: nowrap; }}
.ok {{ display: inline-block; font-family: {FONT_MONO}; font-size: .7rem; letter-spacing: .1em; padding: .15rem .5rem; border-radius: 99px; background: #E3E8D6; color: var(--moss); }}
.bad {{ display: inline-block; font-family: {FONT_MONO}; font-size: .7rem; letter-spacing: .1em; padding: .15rem .5rem; border-radius: 99px; background: #F3D9CF; color: var(--persimmon); }}
.pill {{ display: inline-block; font-family: {FONT_MONO}; font-size: .7rem; padding: .12rem .5rem; border: 1px solid var(--rule); border-radius: 99px; margin: 0 .25rem .25rem 0; color: var(--ink-2); background: var(--card); }}

.insight {{ border-left: 3px solid var(--persimmon); padding: .3rem 0 .3rem 1rem; margin: 1rem 0; }}
.insight .t {{ font-family: {FONT_DISPLAY}; font-size: 1.45rem; line-height: 1.2; color: var(--ink); }}
.insight p {{ margin: .35rem 0 0; color: var(--ink-2); font-size: .95rem; line-height: 1.6; }}

.explain {{ background: var(--ink); color: var(--paper); border-radius: 16px; padding: 1.5rem 1.6rem; animation: rise .6s var(--ease) both; }}
.explain .eyebrow {{ color: {OCHRE}; }}
.explain h3 {{ color: var(--paper) !important; font-size: 2rem; margin: 0 0 .2rem; }}
.explain .verdict {{ font-family: {FONT_DISPLAY}; font-size: 1.3rem; color: #EADFCB; margin-bottom: 1rem; }}
.explain .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .8rem; margin: .4rem 0 1.1rem; }}
.explain .cell {{ border-top: 1px solid #4A453D; padding-top: .5rem; }}
.explain .cell .v {{ font-family: {FONT_MONO}; font-size: 1.15rem; color: var(--paper); }}
.explain .cell .k {{ font-family: {FONT_MONO}; font-size: .66rem; letter-spacing: .12em; text-transform: uppercase; color: #A89F90; }}
.explain ol {{ margin: .2rem 0 0 1.1rem; padding: 0; }}
.explain li {{ color: #E9E1D3 !important; margin-bottom: .45rem; line-height: 1.55; font-size: .95rem; }}
.explain li b {{ color: #fff; font-weight: 600; }}
.explain .up {{ color: #9CC5A1; }} .explain .down {{ color: #F0A08A; }}
.hint {{ font-family: {FONT_MONO}; font-size: .74rem; letter-spacing: .06em; color: var(--muted); border: 1px dashed var(--rule); border-radius: 10px; padding: .7rem .9rem; }}

/* widgets */
.stButton > button, .stDownloadButton > button {{ border-radius: 99px; border: 1px solid var(--ink); background: transparent; color: var(--ink); font-weight: 500; padding: .45rem 1.1rem; transition: all .25s var(--ease); }}
.stButton > button:hover {{ background: var(--ink); color: var(--paper); border-color: var(--ink); }}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {{ background: var(--persimmon); border-color: var(--persimmon); color: #fff !important; }}
[data-testid="stBaseButton-primary"] p {{ color: #fff !important; }}
[data-testid="stBaseButton-primary"]:hover {{ background: var(--ink) !important; border-color: var(--ink) !important; }}
[data-baseweb="select"] > div, [data-baseweb="input"] > div {{ background: var(--card) !important; border-color: var(--rule) !important; border-radius: 10px !important; }}
[data-testid="stWidgetLabel"] p {{ font-family: {FONT_MONO}; font-size: .7rem !important; letter-spacing: .1em; text-transform: uppercase; color: var(--muted) !important; }}
[data-testid="stTabs"] button p {{ font-family: {FONT_BODY}; font-size: .95rem; }}
[data-testid="stTabs"] [aria-selected="true"] p {{ color: var(--persimmon); }}
[data-testid="stExpander"] {{ border: 1px solid var(--rule); border-radius: 12px; background: var(--card); }}
[data-testid="stPlotlyChart"] {{ animation: rise .8s var(--ease) both; }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--rule); border-radius: 10px; }}
div[data-testid="stSegmentedControl"] button, [data-testid="stButtonGroup"] button {{ border-radius: 99px !important; }}
a {{ color: var(--teal); }}
footer {{ visibility: hidden; }}
</style>
"""

REVEAL_JS = """
<script>
(function(){
  const doc = window.parent.document;
  doc.body.classList.add('js-reveal');
  const io = new (window.parent.IntersectionObserver)(function(entries){
    entries.forEach(function(e){ if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, {threshold: 0.12});
  function scan(){ doc.querySelectorAll('.rv:not(.in)').forEach(function(el){ io.observe(el); }); }
  scan();
  new (window.parent.MutationObserver)(scan).observe(doc.body, {childList: true, subtree: true});
  setTimeout(function(){ doc.querySelectorAll('.rv:not(.in)').forEach(function(el){
    const r = el.getBoundingClientRect(); if (r.top < window.parent.innerHeight) el.classList.add('in'); }); }, 400);
})();
</script>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    st.iframe(REVEAL_JS, height=1)
    pio.templates["ledger"] = _template()
    pio.templates.default = "ledger"


def _template():
    t = go.layout.Template()
    t.layout = go.Layout(
        font=dict(family=FONT_BODY, color=INK_2, size=13),
        title=dict(font=dict(family=FONT_DISPLAY, size=22, color=INK), x=0, xanchor="left"),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        colorway=COLORWAY,
        xaxis=dict(gridcolor=RULE, linecolor=INK, zeroline=False, ticks="outside", tickcolor=RULE,
                   tickfont=dict(family=FONT_MONO, size=11, color=MUTED), title=dict(font=dict(size=12, color=MUTED))),
        yaxis=dict(gridcolor=RULE, zeroline=False, linecolor="rgba(0,0,0,0)",
                   tickfont=dict(family=FONT_MONO, size=11, color=MUTED), title=dict(font=dict(size=12, color=MUTED))),
        hoverlabel=dict(bgcolor=INK, bordercolor=INK, font=dict(family=FONT_MONO, color=PAPER, size=12)),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(size=12), bgcolor="rgba(0,0,0,0)", title=dict(text="")),
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="closest",
        transition=dict(duration=500, easing="cubic-in-out"),
        coloraxis=dict(colorscale=SEQUENTIAL, colorbar=dict(outlinewidth=0, tickfont=dict(family=FONT_MONO, size=10))),
    )
    return t


PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}


def esc(text):
    return _html.escape(str(text))


def page_title(eyebrow, title_html, lede):
    st.markdown(f'<div class="page-title"><div class="eyebrow">{eyebrow}</div><h1>{title_html}</h1><p>{lede}</p></div>',
                unsafe_allow_html=True)


def chapter(number, title, lede=""):
    st.markdown(f'<div class="chapter rv"><span class="num">{number}</span><h2>{title}</h2>'
                f'{f"<div class=lede>{lede}</div>" if lede else ""}</div>', unsafe_allow_html=True)


def prose(html_text):
    st.markdown(f'<div class="prose rv">{html_text}</div>', unsafe_allow_html=True)


def stats(items):
    """items: list of (value, key, description, hot)"""
    cells = "".join(
        f'<div class="stat{" hot" if (len(i) > 3 and i[3]) else ""}"><div class="v">{i[0]}</div>'
        f'<div class="k">{i[1]}</div>{f"<div class=d>{i[2]}</div>" if len(i) > 2 and i[2] else ""}</div>'
        for i in items)
    st.markdown(f'<div class="stats rv">{cells}</div>', unsafe_allow_html=True)


def figcap(fig_id, kind, title, summary, how_to_read=""):
    st.markdown(
        f'<div class="figcap"><div class="tag">Fig. {fig_id}<span>{kind}</span></div>'
        f'<div class="body"><b>{title}</b><p>{summary}</p>'
        f'{f"<div class=read>How to read it: {how_to_read}</div>" if how_to_read else ""}</div></div>',
        unsafe_allow_html=True)


def insight(title, text):
    st.markdown(f'<div class="insight rv"><div class="t">{title}</div><p>{text}</p></div>', unsafe_allow_html=True)


def card(meta, title, text):
    return f'<div class="card rv"><div class="meta">{meta}</div><h4>{title}</h4><p>{text}</p></div>'


def ledger(headers, rows, numeric_cols=()):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f'<td class="{"n" if j in numeric_cols else ""}">{v}</td>' for j, v in enumerate(r)) + "</tr>"
        for r in rows)
    st.markdown(f'<table class="ledger rv"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>',
                unsafe_allow_html=True)


def chart(fig, key=None, select=False, height=None):
    if height:
        fig.update_layout(height=height)
    if select:
        return st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key,
                               on_select="rerun", selection_mode="points")
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key)
    return None


def fmt(n, digits=0):
    if n is None:
        return "–"
    try:
        if abs(n) >= 1e9:
            return f"{n / 1e9:.2f} bn"
        if abs(n) >= 1e6:
            return f"{n / 1e6:.2f} m"
        return f"{n:,.{digits}f}"
    except (TypeError, ValueError):
        return str(n)
