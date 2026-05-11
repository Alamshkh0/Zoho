"""Single source of truth for the app's visual identity.

Modern dark + electric-accent. Import once from app.py:
    import theme; theme.apply(st)
Charts use theme.PLOTLY_LAYOUT and theme.MPL_RC for matching dark styling.
"""

COLORS = {
    "bg":        "#0E1116",
    "surface":   "#161B22",
    "surface_2": "#1F2530",
    "border":    "#262E3A",
    "ink":       "#E6EAF2",
    "ink_dim":   "#9AA3B2",
    "accent":    "#00E5FF",
    "accent_2":  "#7C5CFF",
    "ok":        "#25D366",
    "warn":      "#FFB020",
    "danger":    "#FF4D6D",
    "gold":      "#F5C542",
}

CHART_PALETTE = [
    COLORS["accent"], COLORS["accent_2"], COLORS["gold"],
    COLORS["ok"], COLORS["warn"], COLORS["danger"], COLORS["ink_dim"], "#5D4037",
]

# Plotly figure-level defaults (use figure.update_layout(**PLOTLY_LAYOUT))
PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["surface"],
    font=dict(color=COLORS["ink"], family="Inter, -apple-system, sans-serif", size=12),
    title=dict(font=dict(color=COLORS["ink"], size=14)),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], color=COLORS["ink_dim"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], color=COLORS["ink_dim"]),
    legend=dict(font=dict(color=COLORS["ink_dim"])),
    margin=dict(l=20, r=20, t=44, b=20),
)

# Matplotlib rcParams snapshot (applied via plt.rcParams.update at chart time)
MPL_RC = {
    "figure.facecolor":  COLORS["bg"],
    "axes.facecolor":    COLORS["surface"],
    "axes.edgecolor":    COLORS["border"],
    "axes.labelcolor":   COLORS["ink_dim"],
    "axes.titlecolor":   COLORS["ink"],
    "xtick.color":       COLORS["ink_dim"],
    "ytick.color":       COLORS["ink_dim"],
    "grid.color":        COLORS["border"],
    "text.color":        COLORS["ink"],
    "savefig.facecolor": COLORS["bg"],
    "axes.grid":         True,
    "grid.linewidth":    0.5,
    "font.size":         9,
}


CSS = f"""
<style>
/* ---------- Reset / base ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {{
    background: {COLORS["bg"]} !important;
    color: {COLORS["ink"]};
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
    letter-spacing: -0.005em;
}}
.block-container {{
    padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1280px;
}}
h1, h2, h3, h4 {{ color: {COLORS["ink"]}; letter-spacing: -0.02em; font-weight: 700; }}
h1 {{ font-weight: 800; }}
p, label, span, div {{ color: {COLORS["ink"]}; }}
hr {{ border-color: {COLORS["border"]} !important; }}

/* ---------- Hero banner ---------- */
.hero {{
    position: relative;
    background:
        radial-gradient(1200px 320px at 0% 0%, rgba(0,229,255,.10), transparent 60%),
        radial-gradient(900px 380px at 100% 100%, rgba(124,92,255,.12), transparent 60%),
        linear-gradient(135deg, #0E1116 0%, #161B22 60%, #1F2530 100%);
    color: {COLORS["ink"]};
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 18px;
    border: 1px solid {COLORS["border"]};
    box-shadow: 0 22px 40px rgba(0,0,0,.40), inset 0 1px 0 rgba(255,255,255,.04);
    overflow: hidden;
}}
.hero::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, {COLORS["accent"]}, {COLORS["accent_2"]}, transparent);
    opacity: .8;
}}
.hero .kicker {{ font-size: 11px; letter-spacing: 3px; text-transform: uppercase; color: {COLORS["accent"]}; font-weight: 700; }}
.hero h1 {{ color: {COLORS["ink"]}; font-size: 2.2rem; margin: 6px 0 8px 0; }}
.hero p  {{ color: {COLORS["ink_dim"]}; font-size: 1.0rem; margin: 0; max-width: 760px; line-height: 1.55; }}

/* ---------- Glass cards ---------- */
.card, [data-testid="stMetric"], div[data-testid="stMetric"] {{
    background: linear-gradient(180deg, rgba(31,37,48,.55), rgba(22,27,34,.55)) !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 14px !important;
    padding: 14px 16px !important;
    box-shadow: 0 6px 18px rgba(0,0,0,.22);
    backdrop-filter: blur(8px);
}}
div[data-testid="stMetricValue"] {{ color: {COLORS["accent"]} !important; font-weight: 800 !important; font-size: 1.9rem !important;}}
div[data-testid="stMetricLabel"] {{ color: {COLORS["ink_dim"]} !important; font-size: .78rem; letter-spacing: .1em; text-transform: uppercase;}}
div[data-testid="stMetricDelta"] {{ color: {COLORS["ok"]} !important; }}

/* Container "border=True" — make it match our cards */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: rgba(22,27,34,.55) !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 14px !important;
}}

/* ---------- Buttons ---------- */
div.stButton > button {{
    background: {COLORS["surface_2"]};
    color: {COLORS["ink"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    font-weight: 600;
    padding: .45rem 1rem;
    transition: all .15s ease;
}}
div.stButton > button:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
    background: rgba(0,229,255,.06);
}}
div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COLORS["accent"]}, #1FB6FF);
    color: #0E1116 !important;
    border: 0;
    box-shadow: 0 8px 22px rgba(0,229,255,.30);
}}
div.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 12px 28px rgba(0,229,255,.40);
    color: #0E1116 !important;
}}
div.stDownloadButton > button {{
    background: {COLORS["surface_2"]};
    color: {COLORS["ink"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    font-weight: 600;
}}
div.stDownloadButton > button:hover {{ border-color: {COLORS["accent"]}; color: {COLORS["accent"]}; }}

/* ---------- Inputs ---------- */
input, textarea, select, [data-baseweb="select"] > div {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    border-color: {COLORS["border"]} !important;
}}
[data-baseweb="input"] > div, [data-baseweb="textarea"] > div {{
    background: {COLORS["surface"]} !important;
    border-color: {COLORS["border"]} !important;
}}
label, .stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label {{
    color: {COLORS["ink_dim"]} !important;
    font-size: .82rem !important;
}}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px; border-bottom: 1px solid {COLORS["border"]};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {COLORS["ink_dim"]};
    border-radius: 10px 10px 0 0;
    padding: 8px 14px;
    font-weight: 500;
}}
.stTabs [data-baseweb="tab"]:hover {{ color: {COLORS["ink"]}; background: {COLORS["surface"]}; }}
.stTabs [aria-selected="true"] {{
    color: {COLORS["accent"]} !important;
    border-bottom: 2px solid {COLORS["accent"]} !important;
    background: rgba(0,229,255,.06) !important;
}}

/* ---------- Data tables / data_editor ---------- */
.stDataFrame, [data-testid="stDataFrameResizable"] {{
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 12px;
    overflow: hidden;
}}
.stDataFrame table thead th {{ background: {COLORS["surface_2"]} !important; color: {COLORS["ink"]} !important; }}
.stDataFrame table tbody tr td {{ background: {COLORS["surface"]} !important; color: {COLORS["ink"]} !important; }}
[data-testid="stDataEditor"] {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #0B0E13, #0E1116) !important;
    border-right: 1px solid {COLORS["border"]};
}}
section[data-testid="stSidebar"] * {{ color: {COLORS["ink"]} !important; }}
section[data-testid="stSidebar"] .stRadio label {{ color: {COLORS["ink_dim"]} !important; }}

/* ---------- Alerts ---------- */
div[data-baseweb="notification"] {{
    background: {COLORS["surface_2"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    color: {COLORS["ink"]} !important;
    border-radius: 12px;
}}
.stAlert {{ background: {COLORS["surface_2"]} !important; border: 1px solid {COLORS["border"]} !important; color: {COLORS["ink"]} !important; border-radius: 12px;}}

/* ---------- Pill ---------- */
.pill {{
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    background: rgba(0,229,255,.10); color: {COLORS["accent"]};
    font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase;
    border: 1px solid rgba(0,229,255,.25);
}}
.pill-violet {{ background: rgba(124,92,255,.10); color: {COLORS["accent_2"]}; border-color: rgba(124,92,255,.25); }}
.pill-gold   {{ background: rgba(245,197,66,.10); color: {COLORS["gold"]};    border-color: rgba(245,197,66,.25); }}
.pill-ok     {{ background: rgba(37,211,102,.10); color: {COLORS["ok"]};      border-color: rgba(37,211,102,.25); }}
.pill-warn   {{ background: rgba(255,176,32,.10); color: {COLORS["warn"]};    border-color: rgba(255,176,32,.25); }}
.pill-danger {{ background: rgba(255,77,109,.10); color: {COLORS["danger"]};  border-color: rgba(255,77,109,.25); }}

/* ---------- Section intro callout ---------- */
.section-intro {{
    background: rgba(124,92,255,.06);
    border: 1px solid rgba(124,92,255,.20);
    border-left: 3px solid {COLORS["accent_2"]};
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 16px;
    color: {COLORS["ink_dim"]};
    font-size: .92rem;
    line-height: 1.55;
}}
.section-intro b {{ color: {COLORS["ink"]}; }}

/* ---------- Progress bar ---------- */
.stProgress > div > div > div > div {{
    background: linear-gradient(90deg, {COLORS["accent"]}, {COLORS["accent_2"]}) !important;
}}

/* ---------- Mobile breakpoint ---------- */
@media (max-width: 768px) {{
    .block-container {{ padding-left: .6rem; padding-right: .6rem;}}
    .hero {{ padding: 18px 18px; }}
    .hero h1 {{ font-size: 1.5rem; }}
    h1 {{ font-size: 1.5rem; }}
    div[data-testid="stMetricValue"] {{ font-size: 1.4rem !important; }}
}}
</style>
"""


def apply(st):
    """Inject CSS once. Call right after st.set_page_config()."""
    st.markdown(CSS, unsafe_allow_html=True)
