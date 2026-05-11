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

/* ---------- Data tables / data_editor (glide-data-grid) ---------- */
.stDataFrame, [data-testid="stDataFrameResizable"] {{
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 12px;
    overflow: hidden;
}}
.stDataFrame table thead th {{ background: {COLORS["surface_2"]} !important; color: {COLORS["ink"]} !important; }}
.stDataFrame table tbody tr td {{ background: {COLORS["surface"]} !important; color: {COLORS["ink"]} !important; }}

/* glide-data-grid honors CSS custom properties — set the full palette so
   typed text, headers, hovers and edit overlays all read correctly on dark */
[data-testid="stDataEditor"],
[data-testid="stDataEditorResizable"],
[data-testid="stDataFrame"] {{
    --gdg-bg-cell:                     {COLORS["surface"]};
    --gdg-bg-cell-medium:              {COLORS["surface_2"]};
    --gdg-bg-header:                   {COLORS["surface_2"]};
    --gdg-bg-header-has-focus:         {COLORS["border"]};
    --gdg-bg-header-hovered:           {COLORS["border"]};
    --gdg-bg-bubble:                   {COLORS["surface_2"]};
    --gdg-bg-bubble-selected:          rgba(0,229,255,.15);
    --gdg-bg-search-result:            rgba(0,229,255,.25);
    --gdg-text-dark:                   {COLORS["ink"]};
    --gdg-text-medium:                 {COLORS["ink_dim"]};
    --gdg-text-light:                  {COLORS["ink_dim"]};
    --gdg-text-bubble:                 {COLORS["ink"]};
    --gdg-text-header:                 {COLORS["ink"]};
    --gdg-text-header-selected:        {COLORS["accent"]};
    --gdg-text-group-header:           {COLORS["ink"]};
    --gdg-border-color:                {COLORS["border"]};
    --gdg-horizontal-border-color:     {COLORS["border"]};
    --gdg-drilldown-border:            {COLORS["border"]};
    --gdg-link-color:                  {COLORS["accent"]};
    --gdg-cell-horizontal-padding:     8px;
    --gdg-cell-vertical-padding:       3px;
    --gdg-bg-icon-header:              {COLORS["ink_dim"]};
    --gdg-fg-icon-header:              {COLORS["ink"]};
    --gdg-header-bottom-border-color:  {COLORS["border"]};
    --gdg-accent-color:                {COLORS["accent"]};
    --gdg-accent-fg:                   {COLORS["bg"]};
    --gdg-accent-light:                rgba(0,229,255,.15);
    background:                        {COLORS["surface"]};
    border: 1px solid                  {COLORS["border"]};
    border-radius: 12px;
}}
/* Inline edit overlay that pops up when you click into a cell */
[data-testid="stDataEditor"] input,
[data-testid="stDataEditor"] textarea,
[data-testid="stDataEditor"] .gdg-edit-portal input,
[data-testid="stDataEditor"] .gdg-edit-portal textarea,
.gdg-portal input, .gdg-portal textarea,
.gdg-growing-entry, .gdg-growing-entry textarea {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    caret-color: {COLORS["accent"]} !important;
}}
/* Dropdown overlay inside a data_editor cell (SelectboxColumn) */
[data-testid="stDataEditor"] [role="listbox"] {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    border: 1px solid {COLORS["border"]} !important;
}}

/* ---------- Selectbox / multiselect dropdown popovers (BaseWeb) ----------
   Streamlit dropdowns render via BaseWeb in a portal at the body root —
   they don't inherit our container styles, so we target them globally. */
div[data-baseweb="popover"],
div[data-baseweb="menu"],
ul[role="listbox"] {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    box-shadow: 0 12px 24px rgba(0,0,0,.55) !important;
}}
div[data-baseweb="popover"] *,
div[data-baseweb="menu"] *,
ul[role="listbox"] li,
[role="option"] {{
    background: transparent !important;
    color: {COLORS["ink"]} !important;
}}
ul[role="listbox"] li:hover,
[role="option"]:hover,
[role="option"][aria-selected="false"]:hover {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["accent"]} !important;
}}
[role="option"][aria-selected="true"] {{
    background: rgba(0,229,255,.10) !important;
    color: {COLORS["accent"]} !important;
}}
/* Pills inside a multi-select */
span[data-baseweb="tag"] {{
    background: rgba(0,229,255,.10) !important;
    color: {COLORS["accent"]} !important;
    border: 1px solid rgba(0,229,255,.30) !important;
}}
span[data-baseweb="tag"] svg {{ fill: {COLORS["accent"]} !important; }}

/* Display value inside the closed selectbox */
[data-baseweb="select"] > div > div {{
    color: {COLORS["ink"]} !important;
}}
[data-baseweb="select"] svg {{ fill: {COLORS["ink_dim"]} !important; }}

/* Date picker calendar pop-up */
div[data-baseweb="calendar"] {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
}}
div[data-baseweb="calendar"] * {{ color: {COLORS["ink"]} !important; }}

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

/* ---------- COMPREHENSIVE CONTRAST PASS ---------- */
/* Force ink color on every text-bearing surface Streamlit might render */
.stApp, .stApp p, .stApp span:not(.pill):not([class*="pill-"]),
.stApp label, .stApp li, .stApp small,
.stMarkdown, .stMarkdown *, .stText,
.stCaption, .stCaption span, .stCaption p,
[data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {{
    color: {COLORS["ink"]};
}}
.stCaption, .stCaption *, [data-testid="stCaptionContainer"] {{ color: {COLORS["ink_dim"]} !important; }}

/* All form inputs — typed text must be readable */
.stApp input, .stApp textarea, .stApp select,
input[type="text"], input[type="email"], input[type="number"],
input[type="password"], input[type="search"], input[type="tel"],
input[type="url"], input[type="date"] {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
    -webkit-text-fill-color: {COLORS["ink"]} !important;
    caret-color: {COLORS["accent"]} !important;
    border-color: {COLORS["border"]} !important;
}}
.stApp input::placeholder, .stApp textarea::placeholder {{
    color: {COLORS["ink_dim"]} !important;
    -webkit-text-fill-color: {COLORS["ink_dim"]} !important;
    opacity: 1;
}}

/* Number input +/- buttons */
[data-testid="stNumberInput"] button {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["ink"]} !important;
    border-color: {COLORS["border"]} !important;
}}
[data-testid="stNumberInput"] button:hover {{ color: {COLORS["accent"]} !important; }}

/* Alerts — make sure every nested element is readable */
.stAlert, .stAlert *, .stAlert p, .stAlert span, .stAlert div,
[data-testid="stAlert"], [data-testid="stAlert"] *,
[data-baseweb="notification"], [data-baseweb="notification"] * {{
    color: {COLORS["ink"]} !important;
}}
.stAlert {{ background: rgba(31,37,48,.85) !important; border: 1px solid {COLORS["border"]} !important; }}
[data-testid="stAlert"][data-baseweb="notification"][kind="info"]    {{ border-left: 3px solid {COLORS["accent"]}    !important; }}
[data-testid="stAlert"][data-baseweb="notification"][kind="success"] {{ border-left: 3px solid {COLORS["ok"]}        !important; }}
[data-testid="stAlert"][data-baseweb="notification"][kind="warning"] {{ border-left: 3px solid {COLORS["warn"]}      !important; }}
[data-testid="stAlert"][data-baseweb="notification"][kind="error"]   {{ border-left: 3px solid {COLORS["danger"]}    !important; }}

/* Expanders */
[data-testid="stExpander"] {{
    background: {COLORS["surface"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 12px;
}}
[data-testid="stExpander"] summary, [data-testid="stExpander"] details > summary,
[data-testid="stExpander"] summary *, [data-testid="stExpander"] svg {{
    color: {COLORS["ink"]} !important;
    fill: {COLORS["ink"]} !important;
}}
[data-testid="stExpander"] summary:hover {{ color: {COLORS["accent"]} !important; }}

/* Radio / checkbox labels */
[data-testid="stRadio"] label, [data-testid="stRadio"] label *,
[data-testid="stCheckbox"] label, [data-testid="stCheckbox"] label * {{
    color: {COLORS["ink"]} !important;
}}

/* File uploader */
[data-testid="stFileUploader"] {{
    background: {COLORS["surface"]} !important;
    border: 1px dashed {COLORS["border"]} !important;
    border-radius: 12px;
}}
[data-testid="stFileUploader"] section, [data-testid="stFileUploader"] section * {{
    color: {COLORS["ink"]} !important;
    background: transparent !important;
}}
[data-testid="stFileUploaderDropzone"] {{ background: transparent !important; }}
[data-testid="stFileUploader"] small {{ color: {COLORS["ink_dim"]} !important; }}

/* Tooltips */
[role="tooltip"], div[data-baseweb="tooltip"] {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["ink"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    box-shadow: 0 8px 20px rgba(0,0,0,.5);
}}
[role="tooltip"] *, div[data-baseweb="tooltip"] * {{ color: {COLORS["ink"]} !important; }}

/* Help icons (?) on widget labels */
[data-testid="stTooltipIcon"] svg, [data-testid="stHelpIcon"] svg {{ fill: {COLORS["ink_dim"]} !important; }}

/* st.dataframe (read-only) — force every nested cell readable */
[data-testid="stTable"] table, [data-testid="stTable"] table * {{
    background: {COLORS["surface"]} !important;
    color: {COLORS["ink"]} !important;
}}
[data-testid="stTable"] thead th {{ background: {COLORS["surface_2"]} !important; }}

/* Code blocks */
.stCode, .stCode *, code, pre {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["ink"]} !important;
}}
[data-testid="stCode"], [data-testid="stCodeBlock"] {{
    background: {COLORS["surface_2"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 10px;
}}

/* Json view */
[data-testid="stJson"] {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["ink"]} !important;
    border: 1px solid {COLORS["border"]} !important;
    border-radius: 10px;
}}
[data-testid="stJson"] * {{ color: {COLORS["ink"]} !important; }}

/* Toast pop-up */
[data-testid="stToast"], [data-testid="stToast"] * {{
    background: {COLORS["surface_2"]} !important;
    color: {COLORS["ink"]} !important;
    border: 1px solid {COLORS["border"]} !important;
}}

/* Sidebar dropdowns / radios — they share the same components */
section[data-testid="stSidebar"] [role="option"],
section[data-testid="stSidebar"] [role="listbox"],
section[data-testid="stSidebar"] [data-baseweb="select"] * {{
    color: {COLORS["ink"]} !important;
}}

/* The little (?) help text shown beneath some widgets */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {{
    color: {COLORS["ink_dim"]} !important;
}}

/* st.progress label */
.stProgress [data-testid="stProgressLabel"], .stProgress p {{ color: {COLORS["ink_dim"]} !important; }}

/* st.metric the value should stay accent; label dim — already set, reinforce */
[data-testid="stMetric"] * {{ color: inherit; }}

/* Plotly modebar buttons */
.modebar-btn path {{ fill: {COLORS["ink_dim"]} !important; }}
.modebar-group {{ background: transparent !important; }}

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
