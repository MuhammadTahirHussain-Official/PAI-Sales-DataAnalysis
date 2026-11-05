"""Visual system: charcoal glass panels, one ember accent, GSAP motion, Plotly template."""
import html as _html
import json
import re
from pathlib import Path

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from lib.glossary import GLOSSARY, WORD_TO_KEY

# Names kept simple: PAPER = page colour, INK = text colour
PAPER = "#0E0F11"
PAPER_2 = "#1A1B1F"
CARD = "#17181C"
INK = "#EDEAE3"
INK_2 = "#C9C7C1"
MUTED = "#9C9CA4"
RULE = "#2F3036"

PERSIMMON = "#FF8A4C"   # the accent (ember)
TEAL = "#7FB7C9"        # chalk blue
MOSS = "#A9D18E"        # sage, also "good"
OCHRE = "#F2D479"       # butter
PLUM = "#E58BA0"        # rose
DUSK = "#9D9BD6"        # lavender grey
SAND = "#6E6F78"        # neutral bars
CORAL = "#F0766A"       # "bad"

COLORWAY = [PERSIMMON, TEAL, OCHRE, MOSS, PLUM, DUSK, "#C9A27E", "#8FD3BE", "#D9D7D0", SAND]
SEQUENTIAL = [[0, "#1A1B1F"], [0.3, "#5A3524"], [0.6, "#C4632F"], [0.85, "#FF8A4C"], [1, "#F2D479"]]
SEQUENTIAL_COOL = [[0, "#1A1B1F"], [0.4, "#2F5560"], [0.75, "#5F99AB"], [1, "#BFE3EE"]]
DIVERGING = [[0, "#5F99AB"], [0.5, "#1F2024"], [1, "#FF8A4C"]]

FONT_BODY = "'Hanken Grotesk', 'Helvetica Neue', Arial, sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"
FONT_DISPLAY = "'Bricolage Grotesque', 'Hanken Grotesk', sans-serif"
FONT_LINK = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600"
             "&family=Hanken+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap")

GLASS = "background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.11);border-radius:18px;box-shadow:inset 0 1px 0 rgba(255,255,255,.07);"
BLUR = ""  # live blur over the moving glow made every frame slow

CSS = f"""
<style>
@import url('{FONT_LINK}');
html, body, .stApp, [data-testid="stAppViewContainer"] {{ background: {PAPER}; }}
.stApp::before, .stApp::after {{ content:""; position:fixed; z-index:0; border-radius:50%; pointer-events:none; will-change:transform; }}
.stApp::before {{ width:900px; height:900px; left:-300px; top:-320px; background:radial-gradient(circle, rgba(255,138,76,.22), transparent 65%); animation:drift 26s ease-in-out infinite alternate; }}
.stApp::after {{ width:820px; height:820px; right:-280px; bottom:-320px; background:radial-gradient(circle, rgba(127,183,201,.16), transparent 65%); animation:drift 32s ease-in-out infinite alternate-reverse; }}
@keyframes drift {{ to {{ transform:translate(120px,90px) scale(1.12); }} }}
[data-testid="stAppViewContainer"] {{ background:transparent; }}
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp button, .stApp textarea, .stApp [data-baseweb] {{ font-family:{FONT_BODY}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{ font-family:{FONT_DISPLAY}; font-weight:500; letter-spacing:-.02em; color:{INK}; }}
.stApp code {{ font-family:{FONT_MONO}; background:rgba(255,255,255,.08); color:{OCHRE}; border-radius:5px; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family:'Material Symbols Rounded' !important; }}
[data-testid="stMainBlockContainer"] {{ max-width:1260px; padding:5rem 2rem 6rem; position:relative; z-index:1; }}
[data-testid="stHeader"] {{ display:none; }}
[data-testid="stVerticalBlock"] {{ gap:1.5rem; }}
[data-testid="stHorizontalBlock"] {{ gap:1.5rem !important; }}
@media (min-width:641px) {{ [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap; }} [data-testid="stColumn"] {{ min-width:0 !important; }} }}
.st-key-fx {{ position:absolute; width:1px; height:1px; opacity:0; overflow:hidden; pointer-events:none; }}

/* every chart sits in its own glass panel with air around it */
[data-testid="stElementContainer"]:has([data-testid="stPlotlyChart"]) {{ {GLASS} padding:14px 16px 10px; box-sizing:border-box; }}
[data-testid="stPlotlyChart"] .main-svg {{ background:transparent !important; }}
[data-testid="stPlotlyChart"] .bglayer rect.bg {{ fill:transparent !important; }}
[data-testid="stDataFrame"] {{ border-radius:14px; overflow:hidden; }}
[data-testid="stExpander"] {{ {GLASS} }}

.eyebrow {{ font-family:{FONT_MONO}; font-size:.74rem; letter-spacing:.16em; text-transform:uppercase; color:{PERSIMMON}; margin-bottom:.6rem; }}
.page-title {{ margin:.4rem 0 1rem; }}
.page-title h1 {{ font-size:clamp(2.5rem,5.4vw,4.2rem); line-height:1.02; margin:0 0 1rem; padding:0; }}
.page-title h1 em {{ color:{PERSIMMON}; font-style:normal; }}
.page-title p {{ font-size:1.14rem; line-height:1.6; color:{INK_2}; max-width:780px; }}
.chapter {{ margin:2.6rem 0 .2rem; }}
.chapter .num {{ font-family:{FONT_MONO}; color:{PERSIMMON}; font-size:.78rem; letter-spacing:.14em; }}
.chapter h2 {{ font-size:clamp(1.8rem,3.4vw,2.6rem); line-height:1.08; margin:.3rem 0 .5rem; padding:0; }}
.chapter .lede {{ font-size:1.06rem; line-height:1.62; color:{INK_2}; max-width:800px; }}
.prose {{ font-size:1.02rem; line-height:1.7; color:{INK_2}; max-width:800px; }}
.prose strong {{ color:{INK}; }}

.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:18px; }}
.stat {{ {GLASS} {BLUR} padding:1.15rem 1.25rem; }}
.stat .v {{ font-family:{FONT_DISPLAY}; font-size:2.05rem; line-height:1.05; color:{INK}; }}
.stat .v small {{ font-size:1rem; color:{MUTED}; margin-left:.15rem; }}
.stat .k {{ font-family:{FONT_MONO}; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:{MUTED}; margin-top:.55rem; }}
.stat .d {{ font-size:.9rem; color:{INK_2}; margin-top:.35rem; line-height:1.45; }}
.stat.hot .v {{ color:{PERSIMMON}; }} .stat.good .v {{ color:{MOSS}; }} .stat.bad .v {{ color:{CORAL}; }}

.figcap {{ {GLASS} display:grid; grid-template-columns:150px 1fr; gap:1.2rem; padding:1rem 1.25rem; margin:0 0 1rem; }}
.figcap .tag {{ font-family:{FONT_MONO}; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:{PERSIMMON}; line-height:1.6; }}
.figcap .tag span {{ display:block; color:{MUTED}; }}
.figcap .body b {{ font-weight:600; color:{INK}; }}
.figcap .body p {{ margin:.2rem 0 .4rem; font-size:.95rem; line-height:1.58; color:{INK_2}; }}
.figcap .read {{ font-size:.86rem; color:{MUTED}; }}
@media (max-width:700px) {{ .figcap {{ grid-template-columns:1fr; gap:.3rem; }} }}

.card {{ {GLASS} {BLUR} padding:1.3rem 1.4rem; height:100%; }}
.card h4 {{ font-size:1.32rem; margin:0 0 .4rem; padding:0; }}
.card p {{ font-size:.95rem; line-height:1.58; color:{INK_2}; margin:0; }}
.card .meta {{ font-family:{FONT_MONO}; font-size:.68rem; color:{PERSIMMON}; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.6rem; }}

.ledger-wrap {{ {GLASS} padding:.5rem 1.2rem; overflow-x:auto; }}
.ledger {{ width:100%; border-collapse:collapse; font-size:.94rem; }}
.ledger th {{ font-family:{FONT_MONO}; font-weight:500; font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:{MUTED}; text-align:left; padding:.7rem .8rem .6rem 0; border-bottom:1px solid rgba(255,255,255,.18); }}
.ledger td {{ padding:.7rem .8rem .7rem 0; border-bottom:1px solid rgba(255,255,255,.07); vertical-align:top; color:{INK_2}; line-height:1.5; }}
.ledger tr:last-child td {{ border-bottom:none; }}
.ledger td:first-child {{ color:{INK}; font-weight:500; }}
.ledger td.n {{ font-family:{FONT_MONO}; color:{INK}; white-space:nowrap; }}
@media (max-width:700px) {{
  .ledger thead {{ display:none; }}
  .ledger, .ledger tbody, .ledger tr, .ledger td {{ display:block; width:100%; }}
  .ledger tr {{ padding:.75rem 0; border-bottom:1px solid rgba(255,255,255,.12); }}
  .ledger tr:last-child {{ border-bottom:none; }}
  .ledger td, .ledger td.n {{ border:0; padding:.22rem 0; white-space:normal; }}
  .ledger td:first-child {{ font-size:1.05rem; }}
  .ledger td:not(:first-child)::before {{ content:attr(data-label); display:block; font-family:{FONT_MONO}; font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED}; }}
}}
.ok, .fail {{ display:inline-block; font-family:{FONT_MONO}; font-size:.7rem; letter-spacing:.08em; padding:.15rem .55rem; border-radius:99px; white-space:nowrap; }}
.ok {{ background:rgba(169,209,142,.16); color:{MOSS}; }} .fail {{ background:rgba(240,118,106,.16); color:{CORAL}; }}

.insight {{ {GLASS} border-left:3px solid {PERSIMMON}; padding:1rem 1.3rem; }}
.insight .t {{ font-family:{FONT_DISPLAY}; font-size:1.34rem; line-height:1.25; color:{INK}; }}
.insight p {{ margin:.35rem 0 0; color:{INK_2}; font-size:.97rem; line-height:1.6; }}
.up {{ color:{MOSS} !important; }} .down {{ color:{CORAL} !important; }} .hi {{ color:{PERSIMMON}; font-weight:600; }}

.explain {{ {GLASS} border-color:rgba(255,138,76,.45); padding:1.5rem 1.6rem; }}
.explain h3 {{ font-size:1.9rem; margin:0 0 .2rem; padding:0; }}
.explain .verdict {{ font-family:{FONT_DISPLAY}; font-size:1.2rem; color:{OCHRE}; margin-bottom:1rem; }}
.explain .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:14px; margin:.4rem 0 1.1rem; }}
.explain .cell {{ background:rgba(255,255,255,.05); border-radius:12px; padding:.65rem .8rem; }}
.explain .cell .v {{ font-family:{FONT_MONO}; font-size:1.1rem; color:{INK}; }}
.explain .cell .k {{ font-family:{FONT_MONO}; font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED}; }}
.explain ol {{ margin:.2rem 0 0 1.1rem; padding:0; }}
.explain li {{ color:{INK_2}; margin-bottom:.45rem; line-height:1.55; font-size:.96rem; }}
.explain li b {{ color:{INK}; font-weight:600; }}
.hint {{ font-family:{FONT_MONO}; font-size:.76rem; color:{MUTED}; border:1px dashed rgba(255,255,255,.18); border-radius:12px; padding:.75rem 1rem; }}

/* store manager pieces */
.story {{ {GLASS} border-color:rgba(255,138,76,.35); padding:1.2rem 1.5rem; font-size:clamp(1.1rem,2vw,1.35rem); line-height:1.5; color:{INK}; }}
.goalbar {{ height:16px; background:rgba(255,255,255,.08); border-radius:9px; position:relative; margin:14px 0 10px; }}
.goalbar i {{ display:block; height:100%; border-radius:9px; }}
.goalbar span {{ position:absolute; top:-5px; bottom:-5px; left:83.3%; width:2px; background:{INK}; }}
.mv {{ display:flex; justify-content:space-between; gap:14px; padding:.6rem .85rem; border-radius:12px; background:rgba(255,255,255,.05); margin-bottom:10px; font-size:.95rem; color:{INK_2}; flex-wrap:wrap; }}
.mv b {{ color:{INK}; }}
.action {{ {GLASS} display:flex; gap:16px; padding:1rem 1.25rem; margin-bottom:14px; }}
.action .bar {{ flex:0 0 4px; border-radius:4px; }}
.action b {{ color:{INK}; }} .action p {{ margin:.25rem 0 0; color:{INK_2}; line-height:1.55; font-size:.96rem; }}
.action .tag {{ font-family:{FONT_MONO}; font-size:.66rem; margin-left:.6rem; letter-spacing:.08em; text-transform:uppercase; }}
.legend {{ display:flex; gap:18px; flex-wrap:wrap; font-size:.88rem; color:{INK_2}; }}
.legend i {{ display:inline-block; width:14px; height:14px; border-radius:5px; margin-right:6px; vertical-align:-2px; }}

.st-key-mgrbar [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap; gap:.8rem !important; }}
.st-key-mgrbar [data-testid="stColumn"] {{ min-width:0 !important; }}
/* calendar buttons: colour comes from the key given to each button */
.st-key-calgrid [data-testid="stHorizontalBlock"] {{ flex-wrap:nowrap; gap:.6rem !important; }}
.st-key-calgrid [data-testid="stColumn"] {{ min-width:0 !important; flex:1 1 0 !important; }}
.st-key-calgrid [data-testid="stVerticalBlock"] {{ gap:.6rem; }}
.st-key-calgrid button {{ width:100%; min-height:78px; padding:6px 2px; border-radius:14px !important; border:1px solid rgba(255,255,255,.1) !important; transition:transform .2s; }}
.st-key-calgrid button:hover {{ transform:translateY(-2px); }}
.st-key-calgrid button p {{ font-family:{FONT_MONO}; font-size:.86rem; line-height:1.3; color:#fff; }}
.st-key-calgrid [class*="cal_vh_"] button {{ background:#2E7D5B !important; }} .st-key-calgrid [class*="cal_hi_"] button {{ background:#1F4D3E !important; }}
.st-key-calgrid [class*="cal_no_"] button {{ background:rgba(255,255,255,.07) !important; }}
.st-key-calgrid [class*="cal_lo_"] button {{ background:#5A2A26 !important; }} .st-key-calgrid [class*="cal_vl_"] button {{ background:#9A3B32 !important; }}
.st-key-calgrid [class*="st-key-calsel"] button {{ outline:2px solid {PERSIMMON}; outline-offset:2px; }}
.calhead {{ text-align:center; font-family:{FONT_MONO}; font-size:.72rem; color:{MUTED}; }}
@media (max-width:640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left:1rem; padding-right:1rem; }}
  .st-key-mgrbar [data-testid="stHorizontalBlock"] {{ flex-wrap:wrap; }}
  .st-key-mgrbar [data-testid="stColumn"]:first-child {{ flex:1 1 100% !important; width:100% !important; }}
  .st-key-mgrbar [data-testid="stColumn"]:not(:first-child) {{ flex:1 1 0 !important; }}
  .st-key-calgrid [data-testid="stHorizontalBlock"] {{ gap:4px !important; }}
  .st-key-calgrid [data-testid="stVerticalBlock"] {{ gap:4px; }}
  .st-key-calgrid button {{ min-height:58px; padding:4px 0; border-radius:10px !important; min-width:0; }}
  .st-key-calgrid button * {{ overflow:visible !important; text-overflow:clip !important; }}
  .st-key-calgrid button p {{ font-size:.62rem; letter-spacing:-.03em; }}
}}

.stButton > button, .stDownloadButton > button {{ border-radius:99px; border:1px solid rgba(255,255,255,.22); background:rgba(255,255,255,.04); transition:all .25s; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ border-color:{PERSIMMON}; color:{PERSIMMON}; }}
[data-testid="stBaseButton-primary"] {{ background:{PERSIMMON} !important; border-color:{PERSIMMON} !important; }}
[data-testid="stBaseButton-primary"] p {{ color:#14110E !important; font-weight:600; }}
[data-testid="stWidgetLabel"] p {{ font-family:{FONT_MONO}; font-size:.7rem !important; letter-spacing:.1em; text-transform:uppercase; color:{MUTED} !important; }}
[data-testid="stPageLink"] a {{ {GLASS} padding:.7rem 1.1rem; border-radius:99px; }}
[data-testid="stPageLink"] a:hover {{ border-color:{PERSIMMON}; }}
a {{ color:{TEAL}; }}
footer {{ visibility:hidden; }}

/* cursor glow, hover and scroll pieces */
.stat, .card, .figcap, .insight, .story, .ledger-wrap, .action, .explain {{ background-image:radial-gradient(280px circle at var(--mx,-400px) var(--my,-400px), rgba(255,138,76,.14), transparent 70%); }}
.card, .stat {{ transition:transform .35s cubic-bezier(.2,.7,.1,1), border-color .35s; }}
.card:hover, .stat:hover {{ transform:translateY(-4px); border-color:rgba(255,138,76,.55); }}
#fx-bar {{ position:fixed; left:0; top:0; height:3px; width:100%; background:{PERSIMMON}; transform:scaleX(0); transform-origin:left; z-index:1000000; pointer-events:none; }}
#fx-ring {{ position:fixed; left:-18px; top:-18px; width:36px; height:36px; border-radius:50%; border:1px solid rgba(255,138,76,.75); pointer-events:none; z-index:1000000; opacity:0; will-change:transform; transition:width .2s, height .2s, left .2s, top .2s, background .2s; }}
#fx-ring.hot {{ width:58px; height:58px; left:-29px; top:-29px; background:rgba(255,138,76,.14); }}
/* dotted words explain themselves when clicked */
.term {{ border-bottom:1px dotted {PERSIMMON}; cursor:help; transition:color .2s; }}
.term:hover {{ color:{PERSIMMON}; }}
.ctl-label {{ font-family:{FONT_MONO}; font-size:.7rem; letter-spacing:.1em; text-transform:uppercase; color:{INK_2}; margin-bottom:-.9rem; }}
#term-pop {{ position:fixed; left:50%; bottom:28px; width:min(560px, calc(100vw - 28px)); max-height:calc(100vh - 90px); overflow-y:auto; transform:translateX(-50%); z-index:1000001; background:#1A1B20; border:1px solid {PERSIMMON}; border-radius:20px; padding:1.4rem 1.5rem; box-shadow:0 30px 80px rgba(0,0,0,.7); color:{INK_2}; font-family:{FONT_BODY}; display:none; }}
#term-pop h3 {{ margin:0 2rem .7rem 0; font-family:{FONT_DISPLAY}; font-size:1.5rem; font-weight:500; color:{INK}; letter-spacing:-.02em; }}
#term-pop h5 {{ margin:.8rem 0 .15rem; font-family:{FONT_MONO}; font-size:.66rem; font-weight:500; letter-spacing:.12em; text-transform:uppercase; color:{PERSIMMON}; }}
#term-pop p {{ margin:0; font-size:.97rem; line-height:1.55; }}
#term-pop button {{ position:absolute; top:14px; right:14px; width:32px; height:32px; border-radius:50%; border:1px solid rgba(255,255,255,.25); background:none; color:{INK}; font-size:18px; line-height:1; cursor:pointer; }}
#term-pop button:hover {{ border-color:{PERSIMMON}; color:{PERSIMMON}; }}

/* product bars: rounded gradient bars, numbers in straight columns */
.pbars {{ {GLASS} padding:1rem 1.3rem 1.1rem; }}
.pbar {{ display:grid; grid-template-columns:minmax(120px,190px) minmax(0,1fr) 84px 62px; gap:14px; align-items:center; padding:5px 8px; border-radius:10px; cursor:pointer; transition:background .2s; }}
.pbar:hover {{ background:rgba(255,255,255,.06); }}
.pbar.sel {{ background:rgba(255,138,76,.14); outline:1px solid rgba(255,138,76,.55); }}
.pbar.head {{ cursor:default; font-family:{FONT_MONO}; font-size:.64rem; letter-spacing:.1em; text-transform:uppercase; color:{MUTED}; }}
.pbar.head:hover {{ background:none; }}
.pbar .nm {{ font-size:.93rem; color:{INK}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.pbar .tr {{ height:14px; border-radius:99px; background:rgba(255,255,255,.06); overflow:hidden; }}
.pbar .tr i {{ display:block; height:100%; border-radius:99px; box-shadow:inset 0 1px 0 rgba(255,255,255,.28); transform-origin:left; animation:pgrow .9s cubic-bezier(.2,.7,.1,1) both; }}
@keyframes pgrow {{ from {{ transform:scaleX(0); }} to {{ transform:scaleX(1); }} }}
.pbar .num {{ text-align:right; font-family:{FONT_MONO}; font-size:.85rem; color:{INK}; font-variant-numeric:tabular-nums; }}
.pbar .chg {{ text-align:right; font-family:{FONT_MONO}; font-size:.8rem; font-variant-numeric:tabular-nums; color:{MUTED}; }}
.g-top {{ background:linear-gradient(90deg,#B4552A,#FF8A4C 62%,#F2D479); }}
.g-down {{ background:linear-gradient(90deg,#7E332E,#D65F55 60%,#F0918A); }}
.g-up {{ background:linear-gradient(90deg,#2B5560,#5F99AB 60%,#A3D3E2); }}
.st-key-pickers {{ position:absolute; width:1px; height:1px; overflow:hidden; opacity:0; pointer-events:none; }}
@media (max-width:640px) {{ .pbar {{ grid-template-columns:minmax(0,104px) minmax(0,1fr) 56px 42px; gap:8px; padding:5px 2px; }} .pbar .nm {{ font-size:.8rem; }} .pbar .num {{ font-size:.74rem; }} .pbar .chg {{ font-size:.68rem; }} .pbars {{ padding:.8rem .7rem; }} }}

/* store chooser */
.st-key-storegrid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:18px; }}
.st-key-storegrid [data-testid="stElementContainer"] {{ width:auto !important; }}
.st-key-storegrid button {{ {GLASS} width:100%; min-height:118px; justify-content:flex-start; text-align:left; padding:1rem 1.15rem; border-radius:18px !important; transition:transform .3s cubic-bezier(.2,.7,.1,1), border-color .3s, background .3s; }}
.st-key-storegrid button:hover {{ transform:translateY(-4px); border-color:{PERSIMMON} !important; background:rgba(255,138,76,.09); color:inherit !important; }}
.st-key-storegrid button > div, .st-key-storegrid button [data-testid="stMarkdownContainer"] {{ width:100%; display:block; text-align:left; }}
.st-key-storegrid button p {{ text-align:left; font-size:.9rem; line-height:1.5; color:{INK_2}; }}
.st-key-storegrid button strong {{ display:block; font-family:{FONT_DISPLAY}; font-size:1.3rem; font-weight:500; letter-spacing:-.02em; color:{INK}; margin-bottom:.2rem; }}
.flow {{ margin:0 0 .2rem; }}
.flow-t {{ font-family:{FONT_MONO}; font-size:.72rem; letter-spacing:.1em; text-transform:uppercase; color:{INK_2}; margin-bottom:.55rem; }}
.flow-b {{ display:grid; grid-auto-flow:column; grid-auto-columns:1fr; gap:6px; }}
.flow-b i {{ display:block; height:4px; border-radius:4px; background:rgba(255,255,255,.12); }}
.flow-b i.on {{ background:{PERSIMMON}; }}

/* our own menu: a bar with two panels that open as a curtain, links rising one after another */
.st-key-topnav {{ position:fixed; top:0; left:0; right:0; height:58px; z-index:999999; display:flex; flex-direction:row; align-items:center; gap:clamp(14px,3vw,40px); padding:0 clamp(14px,3vw,40px); background:rgba(14,15,17,.94); border-bottom:1px solid rgba(255,255,255,.1); }}
.st-key-topnav > div, .st-key-topnav [data-testid="stElementContainer"] {{ width:auto !important; }}
.st-key-topnav [data-testid="stPageLink"] a {{ background:none; border:0; box-shadow:none; padding:0; border-radius:0; }}
.st-key-topnav [data-testid="stPageLink"] p, .navlabel {{ font-family:{FONT_BODY}; font-size:clamp(.82rem,1.6vw,.95rem); font-weight:500; color:{INK}; white-space:nowrap; }}
.st-key-navstart [data-testid="stPageLink"] a {{ position:relative; }}
.navlabel {{ display:flex; align-items:center; gap:.55rem; height:58px; cursor:pointer; user-select:none; }}
.navlabel i {{ position:relative; display:block; width:10px; height:10px; transition:transform .45s cubic-bezier(.2,.7,.1,1); }}
.navlabel i::before, .navlabel i::after {{ content:""; position:absolute; background:{PERSIMMON}; }}
.navlabel i::before {{ left:0; right:0; top:4px; height:2px; }}
.navlabel i::after {{ top:0; bottom:0; left:4px; width:2px; }}
.navpanel {{ }}
.st-key-navp_tech, .st-key-navp_biz {{ position:fixed; top:58px; left:0; right:0; max-height:calc(100vh - 58px); overflow-y:auto; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:0 clamp(16px,3vw,48px); padding:clamp(20px,3vw,44px) clamp(14px,3vw,40px) clamp(24px,3vw,48px); background:#14151A; border-bottom:1px solid {PERSIMMON}; box-shadow:0 40px 80px rgba(0,0,0,.6); clip-path:inset(0 0 100% 0); visibility:hidden; transition:clip-path .55s cubic-bezier(.76,0,.24,1), visibility 0s .55s; counter-reset:nav -1; }}
.st-key-navp_biz {{ counter-reset:nav 0; }}
.st-key-navp_tech [data-testid="stElementContainer"], .st-key-navp_biz [data-testid="stElementContainer"] {{ width:100% !important; opacity:0; transform:translateY(28px); transition:opacity .2s, transform .2s; }}
.st-key-navp_tech [data-testid="stElementContainer"]:has(.navintro), .st-key-navp_biz [data-testid="stElementContainer"]:has(.navintro) {{ grid-column:1 / -1; }}
.navintro {{ font-family:{FONT_MONO}; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; color:{MUTED}; margin-bottom:1rem; white-space:normal; }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] a {{ display:block; position:relative; width:100%; padding:.8rem 0 .9rem; border-bottom:1px solid rgba(255,255,255,.12); overflow:hidden; transition:padding-left .35s cubic-bezier(.2,.7,.1,1); }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] a::after {{ content:""; position:absolute; left:0; right:0; bottom:-1px; height:2px; background:{PERSIMMON}; transform:scaleX(0); transform-origin:left; transition:transform .4s cubic-bezier(.76,0,.24,1); }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] a:hover {{ padding-left:14px; }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] a:hover::after {{ transform:scaleX(1); }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] p {{ font-family:{FONT_DISPLAY}; font-size:clamp(1.1rem,2.1vw,1.9rem); line-height:1.15; letter-spacing:-.02em; white-space:normal; }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] a:hover p {{ color:{PERSIMMON}; }}
.st-key-topnav [class*="st-key-navp_"] [data-testid="stPageLink"] p::before {{ counter-increment:nav; content:counter(nav, decimal-leading-zero); display:block; font-family:{FONT_MONO}; font-size:.68rem; letter-spacing:.1em; color:{PERSIMMON}; margin-bottom:.25rem; }}
/* open on hover, or on tap (the .open class); .nav-shut closes it right after a link is clicked */
body:not(.nav-shut) .st-key-navg_tech:hover .st-key-navp_tech, body:not(.nav-shut) .st-key-navg_biz:hover .st-key-navp_biz, .st-key-navg_tech.open .st-key-navp_tech, .st-key-navg_biz.open .st-key-navp_biz {{ clip-path:inset(0 0 0 0); visibility:visible; transition:clip-path .55s cubic-bezier(.76,0,.24,1), visibility 0s; }}
body:not(.nav-shut) [class*="st-key-navg_"]:hover .navlabel i, [class*="st-key-navg_"].open .navlabel i {{ transform:rotate(135deg); }}
body:not(.nav-shut) [class*="st-key-navg_"]:hover [data-testid="stElementContainer"], [class*="st-key-navg_"].open [data-testid="stElementContainer"] {{ opacity:1; transform:none; transition:opacity .5s, transform .6s cubic-bezier(.2,.7,.1,1); }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(2) {{ transition-delay:0.045s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(3) {{ transition-delay:0.090s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(4) {{ transition-delay:0.135s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(5) {{ transition-delay:0.180s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(6) {{ transition-delay:0.225s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(7) {{ transition-delay:0.270s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(8) {{ transition-delay:0.315s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(9) {{ transition-delay:0.360s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(10) {{ transition-delay:0.405s !important; }}
[class*="st-key-navp_"] [data-testid="stElementContainer"]:nth-child(11) {{ transition-delay:0.450s !important; }}
@media (max-width:760px) {{ .st-key-navp_tech, .st-key-navp_biz {{ grid-template-columns:minmax(0,1fr); }} .st-key-topnav {{ gap:14px; }} }}
.nextcard {{ {GLASS} border-color:rgba(255,138,76,.4); padding:1.5rem 1.6rem; margin-top:2.4rem; }}
.nextcard h3 {{ font-size:clamp(1.6rem,3.2vw,2.5rem); margin:0; padding:0; }}
</style>
"""


def gsap_scripts(scroll_trigger=False):
    """The GSAP files bundled in app/static, as inline script tags."""
    static = Path(__file__).resolve().parents[1] / "static"
    names = ["gsap.min.js"] + (["ScrollTrigger.min.js"] if scroll_trigger else [])
    return "".join(f"<script>{(static / n).read_text(encoding='utf-8')}</script>" for n in names)


# Site-wide motion, added from a small hidden frame. Panels are visible by default, so if a
# script is ever blocked every panel and chart still shows.
REVEAL = """
<script>
(function () {
  gsap.ticker.lagSmoothing(0);
  const doc = window.parent.document, win = window.parent;
  if (win.__fx) win.__fx.abort();
  win.__fx = new win.AbortController();
  const on = {signal: win.__fx.signal, passive: true};
  const panels = '.stat, .card, .figcap, .insight, .story, .ledger-wrap, .action, .explain';
  const reduced = win.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // the glow on each panel follows the cursor
  let glow = null;
  doc.addEventListener('mousemove', function (e) {
    const p = e.target.closest && e.target.closest(panels);
    if (!p) return;
    if (!glow) win.requestAnimationFrame(function () {
      const r = glow.p.getBoundingClientRect();
      glow.p.style.setProperty('--mx', (glow.x - r.left) + 'px');
      glow.p.style.setProperty('--my', (glow.y - r.top) + 'px');
      glow = null;
    });
    glow = {p: p, x: e.clientX, y: e.clientY};
  }, on);

  // scroll progress line at the top of the page
  doc.querySelectorAll('#fx-bar, #fx-ring').forEach(function (n) { n.remove(); });
  const bar = doc.createElement('div'); bar.id = 'fx-bar'; doc.body.appendChild(bar);
  doc.addEventListener('scroll', function (ev) {
    const main = ev.target;
    if (!main.matches || !main.matches('[data-testid="stMain"]')) return;
    const max = main.scrollHeight - main.clientHeight;
    bar.style.transform = 'scaleX(' + (max > 0 ? main.scrollTop / max : 0) + ')';
    const title = doc.querySelector('.page-title');
    if (title && !reduced) { const y = main.scrollTop; title.style.opacity = Math.max(.15, 1 - y / 420); }
  }, {signal: win.__fx.signal, passive: true, capture: true});

  // clicking a dotted word opens its explanation; clicking a product row presses its hidden button
  const pop = doc.getElementById('term-pop') || doc.body.appendChild(doc.createElement('div'));
  pop.id = 'term-pop';
  function hidePop() { pop.style.display = 'none'; }
  function showPop(key) {
    const g = GLOSSARY[key];
    if (!g) return;
    pop.innerHTML = '<button aria-label="Close">×</button><h3>' + g[1] + '</h3><h5>What it is</h5><p>' + g[2] + '</p><h5>What it does</h5><p>' + g[3] +
      '</p><h5>How it works</h5><p>' + g[4] + '</p><h5>Example</h5><p>' + g[5] + '</p>';
    pop.style.display = 'block';
    gsap.fromTo(pop, {opacity: 0, y: 24}, {opacity: 1, y: 0, duration: .35, ease: 'power3.out'});
  }
  doc.addEventListener('click', function (e) {
    const t = e.target;
    if (!t.closest) return;
    const term = t.closest('.term');
    if (term) { e.preventDefault(); e.stopPropagation(); showPop(term.dataset.term); return; }
    if (t.closest('#term-pop button') || !t.closest('#term-pop')) hidePop();
    const row = t.closest('[data-click]');
    if (row) { const b = doc.querySelector('.st-key-' + row.dataset.click + ' button'); if (b) b.click(); }
  }, {signal: win.__fx.signal, capture: true});
  doc.addEventListener('keydown', function (e) { if (e.key === 'Escape') hidePop(); }, {signal: win.__fx.signal});

  // menu: closes after a link is clicked, opens and closes by tapping on touch screens
  doc.addEventListener('click', function (e) {
    const t = e.target;
    if (!t.closest) return;
    const label = t.closest('.navlabel');
    const group = label && label.closest('[class*="st-key-navg_"]');
    doc.querySelectorAll('[class*="st-key-navg_"].open').forEach(function (g) { if (g !== group) g.classList.remove('open'); });
    if (group) { doc.body.classList.remove('nav-shut'); group.classList.toggle('open'); }
    if (t.closest('[class*="st-key-navp_"] a')) { doc.body.classList.add('nav-shut'); }
  }, {signal: win.__fx.signal});
  doc.addEventListener('mousemove', function (e) {
    if (doc.body.classList.contains('nav-shut') && !(e.target.closest && e.target.closest('.st-key-topnav'))) doc.body.classList.remove('nav-shut');
  }, on);

  if (reduced) return;

  // a ring follows the cursor and opens over anything clickable
  if (win.matchMedia('(pointer: fine)').matches) {
    const ring = doc.createElement('div'); ring.id = 'fx-ring'; doc.body.appendChild(ring);
    doc.addEventListener('mousemove', function (e) {
      ring.style.opacity = 1;
      ring.style.transform = 'translate3d(' + e.clientX + 'px,' + e.clientY + 'px,0)';
      const hot = e.target.closest && e.target.closest('a, button, [role="button"], [data-baseweb="select"], input');
      ring.classList.toggle('hot', !!hot);
    }, on);
    doc.addEventListener('mouseleave', function () { ring.style.opacity = 0; }, on);
    // embedded animations are separate pages, so they report the mouse back to the ring here
    const hooked = new WeakSet();
    function hook() {
      doc.querySelectorAll('iframe').forEach(function (f) {
        let fw, fd;
        try { fw = f.contentWindow; fd = f.contentDocument; } catch (err) { return; }
        if (!fw || !fd || !fd.body || hooked.has(fw) || fd.getElementById('field')) return;
        hooked.add(fw);
        fw.addEventListener('mousemove', function (e) {
          const r = f.getBoundingClientRect();
          ring.style.opacity = 1;
          ring.style.transform = 'translate3d(' + (r.left + e.clientX) + 'px,' + (r.top + e.clientY) + 'px,0)';
          ring.classList.toggle('hot', !!(e.target.closest && e.target.closest('a, button')));
        }, {signal: win.__fx.signal, passive: true});
      });
    }
    hook();
    const hookMo = new win.MutationObserver(hook);
    hookMo.observe(doc.body, {childList: true, subtree: true});
    const hookTimer = win.setInterval(hook, 1500);
    win.__fx.signal.addEventListener('abort', function () { hookMo.disconnect(); win.clearInterval(hookTimer); });
  }

  // panels rise and charts settle as they scroll into view
  const sel = panels + ', .chapter, [data-testid="stPlotlyChart"]';
  const seen = new WeakSet();
  const io = new win.IntersectionObserver(function (items) {
    items.forEach(function (it) {
      if (!it.isIntersecting) return;
      io.unobserve(it.target);
      const chart = it.target.matches('[data-testid="stPlotlyChart"]');
      gsap.fromTo(it.target, {opacity: 0, y: chart ? 40 : 28, scale: chart ? .97 : 1},
                  {opacity: 1, y: 0, scale: 1, duration: chart ? .9 : .7, ease: 'power3.out', clearProps: 'opacity,transform'});
    });
  }, {threshold: 0.06});
  function scan() { doc.querySelectorAll(sel).forEach(function (el) { if (!seen.has(el)) { seen.add(el); io.observe(el); } }); }
  scan();
  const mo = new win.MutationObserver(scan);
  mo.observe(doc.body, {childList: true, subtree: true});
  win.__fx.signal.addEventListener('abort', function () { mo.disconnect(); io.disconnect(); });
})();
</script>
"""


# The technical dashboard runs in this order, starting with the summary.
TECH_FLOW = [("views/home.py", "Project summary"), ("views/raw_data.py", "Raw data"), ("views/merging.py", "Merging"),
             ("views/eda_before.py", "EDA before cleaning"), ("views/cleaning.py", "Cleaning"),
             ("views/explore.py", "EDA after cleaning"), ("views/studio.py", "Chart studio"),
             ("views/features.py", "Features"), ("views/conclusion.py", "Conclusion")]


def top_menu(start, technical, business):
    """Our own menu bar. Start is a plain link; the other two open a panel of real page links."""
    with st.container(key="topnav"):
        with st.container(key="navstart"):
            st.page_link(start, label="Start")
        for key, title, intro, pages in [("tech", "Technical overview", "For analysts · the project in order", technical),
                                         ("biz", "Business overview", "For store managers · your store in plain words", business)]:
            with st.container(key=f"navg_{key}"):
                html(f'<div class="navlabel" tabindex="0">{title}<i></i></div>')
                with st.container(key=f"navp_{key}"):
                    html(f'<div class="navintro">{intro}</div>')
                    for p in pages:
                        st.page_link(p, label=p.title)


def flow_top(path):
    """Step rail at the top of each technical page. The summary comes before step 1."""
    i = [p for p, _ in TECH_FLOW].index(path)
    total = len(TECH_FLOW) - 1
    bars = "".join(f'<i class="{"on" if k < i else ""}"></i>' for k in range(total))
    label = f"Start here · {TECH_FLOW[0][1]}" if i == 0 else f"Step {i} of {total} · {TECH_FLOW[i][1]}"
    html(f'<div class="flow"><div class="flow-t">{label}</div><div class="flow-b">{bars}</div></div>')


def flow_next(path):
    """Big link to the next step at the bottom of each technical page."""
    i = [p for p, _ in TECH_FLOW].index(path)
    total = len(TECH_FLOW) - 1
    if i + 1 <= total:
        html(f'<div class="nextcard"><div class="eyebrow">Next · step {i + 1} of {total}</div><h3>{TECH_FLOW[i + 1][1]}</h3></div>')
        st.page_link(TECH_FLOW[i + 1][0], label=f"Continue to {TECH_FLOW[i + 1][1]}", icon=":material/arrow_forward:")
    else:
        html('<div class="nextcard"><div class="eyebrow">End of the technical overview</div><h3>That is the whole project.</h3></div>')
        st.page_link("views/mgr_stores.py", label="See the business overview", icon=":material/arrow_forward:")
    if i > 0:
        st.page_link(TECH_FLOW[i - 1][0], label=f"Back to {TECH_FLOW[i - 1][1]}", icon=":material/arrow_back:")


# Embedded pages grow on small screens. This keeps the frame and Streamlit's wrappers the
# same height as the content, so nothing is clipped or sits on top of the next section.
FIT = """<script>
(function () {
  function fit() {
    try {
      const f = window.frameElement, h = Math.ceil(document.body.getBoundingClientRect().height) + 2;
      f.style.height = h + 'px';
      const wrap = f.closest('[data-testid="stElementContainer"]');
      if (wrap) { wrap.style.flex = '0 0 ' + h + 'px'; wrap.style.height = h + 'px'; }
    } catch (e) {}
  }
  fit();
  new ResizeObserver(fit).observe(document.body);
  addEventListener('load', fit);
})();
</script>"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    with st.container(key="fx"):
        st.iframe(gsap_scripts() + "<script>const GLOSSARY = " + json.dumps(GLOSSARY) + ";</script>" + REVEAL, height=1)
    pio.templates["ledger"] = _template()
    pio.templates.default = "ledger"


def _template():
    t = go.layout.Template()
    axis = dict(gridcolor="rgba(255,255,255,.08)", zeroline=False, linecolor="rgba(255,255,255,.25)", automargin=True,
                tickfont=dict(family=FONT_MONO, size=11, color=INK_2), title=dict(font=dict(size=12, color=INK_2)))
    t.layout = go.Layout(
        font=dict(family=FONT_BODY, color=INK_2, size=13),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", colorway=COLORWAY,
        xaxis=axis, yaxis=axis,
        hoverlabel=dict(bgcolor="#1F2024", bordercolor=PERSIMMON, font=dict(family=FONT_MONO, color=INK, size=12)),
        legend=dict(orientation="h", y=1.1, x=0, font=dict(size=12, color=INK_2), bgcolor="rgba(0,0,0,0)", title=dict(text="")),
        margin=dict(l=10, r=14, t=44, b=10), hovermode="closest", barcornerradius=6,
        coloraxis=dict(colorscale=SEQUENTIAL, colorbar=dict(outlinewidth=0, tickfont=dict(family=FONT_MONO, size=10, color=INK_2))),
    )
    return t


PLOT_CONFIG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"],
               "toImageButtonOptions": {"format": "png", "scale": 2}}


_TERM_RE = re.compile(r"(?<![\w-])(" + "|".join(re.escape(w) for w in sorted(WORD_TO_KEY, key=len, reverse=True)) + r")(?![\w-])", re.I)
_SKIP_TAGS = ("code", "a", "button", "h1", "h2", "h3", "h4", "th", "svg", "style", "script")


def glossify(markup):
    """Make the first use of each known word in this block clickable."""
    seen, depth, out = set(), 0, []
    for part in re.split(r"(<[^>]+>)", markup):
        if part.startswith("<"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", part)
            if name and name.group(1).lower() in _SKIP_TAGS and not part.endswith("/>"):
                depth += -1 if part.startswith("</") else 1
            out.append(part)
        elif depth > 0:
            out.append(part)
        else:
            def wrap(m):
                key = WORD_TO_KEY[m.group(1).lower()]
                if key in seen or key in ("dataset_row", "column"):
                    return m.group(1)
                seen.add(key)
                return f'<span class="term" data-term="{key}">{m.group(1)}</span>'
            out.append(_TERM_RE.sub(wrap, part))
    return "".join(out)


def label(text, term):
    """A control label that explains itself when clicked."""
    st.markdown(f'<div class="ctl-label"><span class="term" data-term="{term}">{text}</span></div>', unsafe_allow_html=True)


def esc(text):
    return _html.escape(str(text))


def html(markup):
    st.markdown(glossify(markup), unsafe_allow_html=True)


def page_title(eyebrow, title_html, lede):
    html(f'<div class="page-title"><div class="eyebrow">{eyebrow}</div><h1>{title_html}</h1><p>{lede}</p></div>')


def chapter(number, title, lede=""):
    html(f'<div class="chapter"><span class="num">{number}</span><h2>{title}</h2>'
         f'{f"<div class=lede>{lede}</div>" if lede else ""}</div>')


def prose(html_text):
    html(f'<div class="prose">{html_text}</div>')


def stats(items):
    """items: list of (value, key, description, hot). hot can be True, 'good' or 'bad'."""
    cells = ""
    for i in items:
        hot = i[3] if len(i) > 3 else False
        cls = " hot" if hot is True else (f" {hot}" if hot else "")
        desc = f"<div class=d>{i[2]}</div>" if len(i) > 2 and i[2] else ""
        cells += f'<div class="stat{cls}"><div class="v">{i[0]}</div><div class="k">{i[1]}</div>{desc}</div>'
    html(f'<div class="stats">{cells}</div>')


def figcap(fig_id, kind, title, summary, how_to_read=""):
    html(f'<div class="figcap"><div class="tag">Fig. {fig_id}<span>{kind}</span></div>'
         f'<div class="body"><b>{title}</b><p>{summary}</p>'
         f'{f"<div class=read>How to read it: {how_to_read}</div>" if how_to_read else ""}</div></div>')


def insight(title, text):
    html(f'<div class="insight"><div class="t">{title}</div><p>{text}</p></div>')


def card(meta, title, text):
    return glossify(f'<div class="card"><div class="meta">{meta}</div><h4>{title}</h4><p>{text}</p></div>')


def ledger(headers, rows, numeric_cols=()):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join(
        "<tr>" + "".join(f'<td data-label="{esc(headers[j])}" class="{"n" if j in numeric_cols else ""}">{v}</td>' for j, v in enumerate(r)) + "</tr>"
        for r in rows)
    html(f'<div class="ledger-wrap"><table class="ledger"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def chart(fig, key=None, select=False, height=None):
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    if height:
        fig.update_layout(height=height)
    if select:
        return st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key, theme=None,
                               on_select="rerun", selection_mode="points")
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key, theme=None)
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
