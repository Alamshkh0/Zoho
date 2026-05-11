"""Single source of truth for the app's visual identity.

Clean enterprise light + indigo accents — premium-modern feel that works
WITH Streamlit's defaults (dropdowns, tooltips, data_editor) so contrast
is reliable. Charts use the same palette via PLOTLY_LAYOUT / MPL_RC.
"""

COLORS = {
    "bg":         "#F7F8FB",   # app background (soft off-white)
    "surface":    "#FFFFFF",   # cards / panels
    "surface_2":  "#F0F2F7",   # raised / hover
    "border":     "#E3E6EE",
    "border_2":   "#C9CFDB",
    "ink":        "#1B1F3B",   # primary text (deep navy)
    "ink_dim":    "#5A6178",   # secondary text
    "ink_muted":  "#8A91A5",
    "accent":     "#4F46E5",   # indigo
    "accent_2":   "#14B8A6",   # teal
    "ok":         "#16A34A",
    "warn":       "#F59E0B",
    "danger":     "#EF4444",
    "gold":       "#D97706",
    "violet":     "#7C3AED",
}

CHART_PALETTE = [
    COLORS["accent"], COLORS["accent_2"], COLORS["violet"],
    COLORS["gold"], COLORS["ok"], COLORS["warn"], COLORS["danger"], COLORS["ink_muted"],
]

PLOTLY_LAYOUT = dict(
    paper_bgcolor=COLORS["surface"],
    plot_bgcolor=COLORS["surface"],
    font=dict(color=COLORS["ink"], family="Inter, -apple-system, sans-serif", size=12),
    title=dict(font=dict(color=COLORS["ink"], size=14)),
    xaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], color=COLORS["ink_dim"]),
    yaxis=dict(gridcolor=COLORS["border"], zerolinecolor=COLORS["border"], color=COLORS["ink_dim"]),
    legend=dict(font=dict(color=COLORS["ink_dim"])),
    margin=dict(l=20, r=20, t=44, b=20),
)

MPL_RC = {
    "figure.facecolor":  COLORS["surface"],
    "axes.facecolor":    COLORS["surface"],
    "axes.edgecolor":    COLORS["border_2"],
    "axes.labelcolor":   COLORS["ink_dim"],
    "axes.titlecolor":   COLORS["ink"],
    "xtick.color":       COLORS["ink_dim"],
    "ytick.color":       COLORS["ink_dim"],
    "grid.color":        COLORS["border"],
    "text.color":        COLORS["ink"],
    "savefig.facecolor": COLORS["surface"],
    "axes.grid":         True,
    "grid.linewidth":    0.6,
    "font.size":         9,
}


CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ---------- Base ---------- */
html, body, .stApp {{
    background: {COLORS["bg"]} !important;
    color: {COLORS["ink"]};
    font-family: 'Inter', -apple-system, system-ui, sans-serif;
    letter-spacing: -0.005em;
}}
.block-container {{
    padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1280px;
}}
h1, h2, h3, h4 {{
    color: {COLORS["ink"]};
    letter-spacing: -0.02em;
    font-weight: 700;
}}
h1 {{ font-weight: 800; }}
p, label, span, li {{ color: {COLORS["ink"]}; }}
small, .stCaption {{ color: {COLORS["ink_dim"]} !important; }}
hr {{ border-color: {COLORS["border"]} !important; }}

/* ---------- Hero banner ---------- */
.hero {{
    position: relative;
    background:
        radial-gradient(1100px 320px at 0% 0%,   rgba(79,70,229,.10), transparent 60%),
        radial-gradient(900px 360px at 100% 100%, rgba(20,184,166,.10), transparent 60%),
        linear-gradient(135deg, #FFFFFF 0%, #F7F8FB 100%);
    color: {COLORS["ink"]};
    border-radius: 18px;
    padding: 26px 32px;
    margin-bottom: 18px;
    border: 1px solid {COLORS["border"]};
    box-shadow: 0 14px 36px rgba(31,40,90,.06);
    overflow: hidden;
}}
.hero::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, {COLORS["accent"]}, {COLORS["accent_2"]});
}}
.hero .kicker {{
    font-size: 11px; letter-spacing: 3px; text-transform: uppercase;
    color: {COLORS["accent"]}; font-weight: 700;
}}
.hero h1 {{ color: {COLORS["ink"]}; font-size: 2.1rem; margin: 6px 0 8px 0; }}
.hero p  {{ color: {COLORS["ink_dim"]}; font-size: 1.0rem; margin: 0; max-width: 760px; line-height: 1.55; }}

/* ---------- Glass / cards ---------- */
.card {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
    padding: 14px 18px;
    box-shadow: 0 4px 14px rgba(31,40,90,.04);
}}

[data-testid="stMetric"] {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
    padding: 14px 16px !important;
    box-shadow: 0 4px 14px rgba(31,40,90,.04);
}}
[data-testid="stMetricValue"] {{
    color: {COLORS["accent"]} !important;
    font-weight: 800 !important;
    font-size: 1.9rem !important;
}}
[data-testid="stMetricLabel"] {{
    color: {COLORS["ink_dim"]} !important;
    font-size: .76rem !important;
    letter-spacing: .14em;
    text-transform: uppercase;
    font-weight: 600 !important;
}}
[data-testid="stMetricDelta"] {{ color: {COLORS["ok"]} !important; }}

/* Bordered containers */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 14px !important;
}}

/* ---------- Buttons ---------- */
div.stButton > button {{
    background: {COLORS["surface"]};
    color: {COLORS["ink"]};
    border: 1px solid {COLORS["border_2"]};
    border-radius: 10px;
    font-weight: 600;
    padding: .45rem 1rem;
    transition: all .15s ease;
    box-shadow: 0 1px 2px rgba(31,40,90,.04);
}}
div.stButton > button:hover {{
    border-color: {COLORS["accent"]};
    color: {COLORS["accent"]};
    background: rgba(79,70,229,.04);
}}
div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {COLORS["accent"]}, {COLORS["violet"]});
    color: #FFFFFF !important;
    border: 0;
    box-shadow: 0 8px 20px rgba(79,70,229,.30);
}}
div.stButton > button[kind="primary"]:hover {{
    transform: translateY(-1px);
    box-shadow: 0 12px 26px rgba(79,70,229,.36);
}}
div.stDownloadButton > button {{
    background: {COLORS["surface"]};
    color: {COLORS["ink"]};
    border: 1px solid {COLORS["border_2"]};
    border-radius: 10px;
    font-weight: 600;
}}
div.stDownloadButton > button:hover {{ border-color: {COLORS["accent"]}; color: {COLORS["accent"]}; }}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea,
.stNumberInput input, .stDateInput input,
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    border-color: {COLORS["border_2"]} !important;
    border-radius: 10px;
}}
.stTextInput input:focus, .stTextArea textarea:focus,
.stNumberInput input:focus {{
    border-color: {COLORS["accent"]} !important;
    box-shadow: 0 0 0 3px rgba(79,70,229,.12) !important;
}}
.stTextInput label, .stTextArea label, .stSelectbox label, .stMultiSelect label,
.stNumberInput label, .stDateInput label, .stRadio label, .stCheckbox label,
[data-testid="stWidgetLabel"] {{
    color: {COLORS["ink_dim"]} !important;
    font-size: .85rem !important;
    font-weight: 500;
}}

/* Selectbox closed state */
[data-baseweb="select"] > div {{
    background: {COLORS["surface"]} !important;
    border-color: {COLORS["border_2"]} !important;
    color: {COLORS["ink"]} !important;
}}
[data-baseweb="select"] > div * {{ color: {COLORS["ink"]} !important; }}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
    border-bottom: 1px solid {COLORS["border"]};
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    color: {COLORS["ink_dim"]};
    border-radius: 10px 10px 0 0;
    padding: 8px 14px;
    font-weight: 500;
}}
.stTabs [data-baseweb="tab"]:hover {{
    color: {COLORS["ink"]};
    background: {COLORS["surface_2"]};
}}
.stTabs [aria-selected="true"] {{
    color: {COLORS["accent"]} !important;
    border-bottom: 2px solid {COLORS["accent"]} !important;
    background: rgba(79,70,229,.05) !important;
    font-weight: 600;
}}

/* ---------- Tables (read-only stDataFrame) ---------- */
.stDataFrame, [data-testid="stDataFrameResizable"] {{
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 12px;
    overflow: hidden;
}}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {{
    background: {COLORS["surface"]} !important;
    border-right: 1px solid {COLORS["border"]};
}}
section[data-testid="stSidebar"] * {{ color: {COLORS["ink"]}; }}
section[data-testid="stSidebar"] .stRadio label {{ color: {COLORS["ink_dim"]} !important; }}

/* ---------- Alerts ---------- */
.stAlert {{
    background: {COLORS["surface"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(31,40,90,.04);
}}
.stAlert, .stAlert * {{ color: {COLORS["ink"]} !important; }}
[data-testid="stAlert"][kind="info"]    {{ border-left: 3px solid {COLORS["accent"]}    !important; }}
[data-testid="stAlert"][kind="success"] {{ border-left: 3px solid {COLORS["ok"]}        !important; }}
[data-testid="stAlert"][kind="warning"] {{ border-left: 3px solid {COLORS["warn"]}      !important; }}
[data-testid="stAlert"][kind="error"]   {{ border-left: 3px solid {COLORS["danger"]}    !important; }}

/* ---------- Pills ---------- */
.pill {{
    display: inline-block; padding: 3px 12px; border-radius: 999px;
    background: rgba(79,70,229,.10); color: {COLORS["accent"]};
    font-size: 11px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase;
    border: 1px solid rgba(79,70,229,.25);
}}
.pill-violet {{ background: rgba(124,58,237,.10); color: {COLORS["violet"]};   border-color: rgba(124,58,237,.25); }}
.pill-gold   {{ background: rgba(217,119,6,.10); color: {COLORS["gold"]};     border-color: rgba(217,119,6,.25); }}
.pill-ok     {{ background: rgba(22,163,74,.10); color: {COLORS["ok"]};       border-color: rgba(22,163,74,.25); }}
.pill-warn   {{ background: rgba(245,158,11,.10); color: {COLORS["warn"]};    border-color: rgba(245,158,11,.25); }}
.pill-danger {{ background: rgba(239,68,68,.10); color: {COLORS["danger"]};   border-color: rgba(239,68,68,.25); }}

/* ---------- Section intro callout ---------- */
.section-intro {{
    background: rgba(79,70,229,.04);
    border: 1px solid rgba(79,70,229,.18);
    border-left: 3px solid {COLORS["accent"]};
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

/* ---------- Expanders ---------- */
[data-testid="stExpander"] {{
    background: {COLORS["surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}
[data-testid="stExpander"] summary {{ color: {COLORS["ink"]} !important; font-weight: 600; }}
[data-testid="stExpander"] summary:hover {{ color: {COLORS["accent"]} !important; }}

/* ---------- File uploader ---------- */
[data-testid="stFileUploader"] {{
    background: {COLORS["surface"]};
    border: 1px dashed {COLORS["border_2"]} !important;
    border-radius: 12px;
}}

/* ---------- Mobile ---------- */
@media (max-width: 768px) {{
    .block-container {{ padding-left: .6rem; padding-right: .6rem;}}
    .hero {{ padding: 18px 18px; }}
    .hero h1 {{ font-size: 1.5rem; }}
    h1 {{ font-size: 1.5rem; }}
    [data-testid="stMetricValue"] {{ font-size: 1.4rem !important; }}
}}
</style>
"""


def apply(st):
    """Inject CSS once. Call right after st.set_page_config()."""
    st.markdown(CSS, unsafe_allow_html=True)
