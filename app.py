"""Redington Zoho CRM Discovery — Streamlit app (v3 dark redesign).

Run:    streamlit run app.py
Deploy: push to GitHub -> https://share.streamlit.io
"""
import copy as _copy
import json
import time as _time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


import config
import db
import reports
import suggestions as sg
import analysis as A
import audit
import theme
import excel_io


def _df_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> list of dicts, with NaN/NaT -> None (JSON-safe).

    Pandas' DataFrame.where(notna(), None) doesn't actually replace NaN
    in float dtypes because None can't live in a numpy float column.
    Sanitize at the dict level via db._clean_for_json (recursive).
    """
    if df is None or df.empty:
        return []
    return db._clean_for_json(df.to_dict(orient="records"))


# ---------- Cached read helpers (TTL-bounded so the UI stays snappy) ----------

@st.cache_data(ttl=10, show_spinner=False)
def _cached_brand_list(active_only: bool) -> list[dict]:
    return db.list_brands(active_only=active_only)

@st.cache_data(ttl=10, show_spinner=False)
def _cached_contrib_counts() -> dict[str, int]:
    return db.count_contributors_per_brand()

@st.cache_data(ttl=15, show_spinner=False)
def _cached_bundle(brand: str) -> dict:
    return db.get_brand_bundle(brand)

@st.cache_data(ttl=20, show_spinner=False)
def _cached_audit(limit: int, event: str | None, brand: str | None, email: str | None) -> list[dict]:
    f = {}
    if event: f["event"] = event
    if brand: f["brand"] = brand
    if email: f["email"] = email
    return audit.list_recent(limit=limit, filters=f or None)

st.set_page_config(
    page_title="Redington Zoho CRM Discovery",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="auto",
)
theme.apply(st)

# ---------- Helpers ----------

def _plotly_layout(**overrides):
    base = dict(theme.PLOTLY_LAYOUT)
    base.update(overrides)
    return base


def _hero(kicker: str, title: str, subtitle: str):
    st.markdown(f"""
<div class='hero'>
  <div class='kicker'>{kicker}</div>
  <h1>{title}</h1>
  <p>{subtitle}</p>
</div>
""", unsafe_allow_html=True)


def _intro(text: str):
    st.markdown(f"<div class='section-intro'>{text}</div>", unsafe_allow_html=True)


# ---------- Session-state defaults ----------

def _init_state():
    defaults = {
        "contributor_id": None,
        "brand": None,
        "name": "",
        "email": "",
        "role": "PAM",
        "admin_unlocked": False,
        "sec_people": {},
        "sec_partner_360": {"fields": []},
        "sec_customer_360": {"fields": []},
        "sec_sales_opp_details": {"fields": []},
        "sec_sales_contact_details": {"fields": []},
        "sec_sales_deal_details": {"fields": []},
        "sec_approvals": {"stages": [], "escalation": "", "notes": ""},
        "sec_dashboards": {"dashboards": [], "notes": ""},
        "sec_best_practices": {},
        "sec_open_notes": {},
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)
_init_state()

SECTION_STATE_KEYS = {
    "people":                "sec_people",
    "partner_360":           "sec_partner_360",
    "customer_360":          "sec_customer_360",
    "sales_opp_details":     "sec_sales_opp_details",
    "sales_contact_details": "sec_sales_contact_details",
    "sales_deal_details":    "sec_sales_deal_details",
    "approvals":             "sec_approvals",
    "dashboards":            "sec_dashboards",
    "best_practices":        "sec_best_practices",
    "open_notes":            "sec_open_notes",
}


def _load_responses_into_state(contributor_id: str):
    try:
        rows = db.get_responses_for_contributor(contributor_id)
    except Exception:
        return
    for sec_key, payload in rows.items():
        sk = SECTION_STATE_KEYS.get(sec_key)
        if sk and isinstance(payload, dict):
            st.session_state[sk] = payload


def _completion_pct() -> int:
    done = 0
    total = len(SECTION_STATE_KEYS)
    for sec_key, state_key in SECTION_STATE_KEYS.items():
        payload = st.session_state.get(state_key) or {}
        if A._section_filled(payload, sec_key):
            done += 1
    return int(round(100 * done / total))


# ---------- Sidebar ----------

PAGE_INTRO = "🏁 Start / Resume"
PAGE_FORM  = "📝 Discovery Form"
PAGE_ADMIN = "🔒 Admin"

with st.sidebar:
    st.markdown("<div style='font-weight:800; font-size:1.05rem; color:#E6EAF2'>📋 Redington</div>", unsafe_allow_html=True)
    st.markdown("<div style='color:#9AA3B2; font-size:.8rem; letter-spacing:.18em; text-transform:uppercase'>Zoho CRM Discovery</div>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigate", [PAGE_INTRO, PAGE_FORM, PAGE_ADMIN], index=0, label_visibility="collapsed")
    st.markdown("---")
    if st.session_state.contributor_id:
        st.markdown(f"<span class='pill pill-ok'>● ACTIVE</span>", unsafe_allow_html=True)
        st.markdown(f"**{st.session_state.name}**")
        st.markdown(f"<span style='color:#9AA3B2; font-size:.85rem'>{st.session_state.role} · {st.session_state.brand}</span>", unsafe_allow_html=True)
        st.progress(_completion_pct() / 100, text=f"{_completion_pct()}% complete")
    else:
        st.markdown("<span class='pill pill-violet'>NEW</span>", unsafe_allow_html=True)
        st.caption("Start a session to begin.")


# ============================================================
# Page 1 — Start / Resume
# ============================================================

def render_intro():
    _hero(
        "BRAND-BY-BRAND DISCOVERY",
        "Zoho CRM Discovery, redesigned.",
        "Capture every brand's CRM requirements in one place. Pick your brand, fill the form, "
        "and let the admin generate a polished requirements pack for the Zoho implementation team. "
        "Use the same email later to resume your session.",
    )

    # Brand stat cards (cached — TTL 10s)
    try:
        counts = _cached_contrib_counts()
        brands = _cached_brand_list(True)
    except Exception:
        counts = {}
        brands = [{"name": b, "logo_url": None} for b in config.BRANDS]

    if not brands:
        st.warning("No active brands. Admin → Brands to add one.")
    else:
        cols = st.columns(min(4, len(brands)))
        for i, b in enumerate(brands):
            with cols[i % len(cols)]:
                logo_md = ""
                if b.get("logo_url"):
                    logo_md = f"<img src='{b['logo_url']}' style='height:30px; object-fit:contain; margin-bottom:4px' />"
                st.markdown(f"""
<div class='card' style='text-align:left'>
  <div class='pill'>BRAND</div>
  {logo_md}
  <div style='font-size:1.35rem; font-weight:800; color:#E6EAF2; margin-top:8px'>{b['name']}</div>
  <div style='color:#9AA3B2; font-size:.85rem; margin-top:4px'>{counts.get(b['name'], 0)} contributor(s)</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("")

    st.markdown("#### Start or resume")
    brand_names = [b["name"] for b in brands] if brands else config.BRANDS
    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", brand_names, index=0)
        name  = st.text_input("Your full name", value=st.session_state.name)
    with c2:
        role_idx = config.ROLES.index(st.session_state.role) if st.session_state.role in config.ROLES else 0
        role  = st.selectbox("Your role", config.ROLES, index=role_idx)
        email = st.text_input("Email (used to resume your session)", value=st.session_state.email)

    if email and brand:
        try:
            existing = db.find_contributor_by_email(brand, email)
            if existing:
                st.info(f"🔁 Found prior submission for **{email}** on **{brand}** (last update {existing['submitted_at'][:19].replace('T',' ')}). Click Start to resume — your earlier answers will reload.")
        except Exception:
            pass

    if st.button("➡️  Start / Resume session", type="primary", use_container_width=True):
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email.")
            return
        try:
            row = db.upsert_contributor(brand, name.strip(), email.strip(), role)
        except Exception as e:
            st.error(f"Could not connect to database. Run schema_v3.sql in Supabase. Error: {e}")
            return
        returning = bool(row.get("submitted_at") and (row.get("name") and row.get("email")))
        st.session_state.contributor_id = row["id"]
        st.session_state.brand = brand
        st.session_state.name = name.strip()
        st.session_state.email = email.strip()
        st.session_state.role = role
        _load_responses_into_state(row["id"])
        audit.log("session_start", actor_email=email.strip(), brand=brand, contributor_id=row["id"], role=role, returning=returning)
        st.success("✅ Session ready — open **Discovery Form** in the sidebar.")
        st.balloons()


# ============================================================
# Field-builder helpers (anti data-loss pattern)
# ============================================================

def _ensure_new_columns(rows: list[dict]) -> list[dict]:
    for r in rows:
        r.setdefault("integration_needed", False)
        r.setdefault("data_capture_source", "Manual")
    return rows


_DATA_SOURCES = getattr(config, "DATA_SOURCES",
    ["Manual", "CQ", "SAP", "AWS ACE", "Microsoft Partner Center", "Salesforce", "API", "Other"])
_FIELD_TYPES = getattr(config, "FIELD_TYPES",
    ["Text", "Number", "Date", "Dropdown", "Multi-select", "Yes/No"])

FIELD_COLUMNS = {
    "field":               st.column_config.TextColumn("Field name", required=True, width="medium"),
    "type":                st.column_config.SelectboxColumn("Type", options=_FIELD_TYPES, required=True, width="small"),
    "options":             st.column_config.TextColumn("Options", width="medium",
                              help="Comma-separated values for Dropdown / Multi-select types"),
    "mandatory":           st.column_config.CheckboxColumn("Mand.?", width="small"),
    "integration_needed":  st.column_config.CheckboxColumn("🔌 Int?", width="small"),
    "data_capture_source": st.column_config.SelectboxColumn("📥 Source", options=_DATA_SOURCES, width="small"),
    "conditional_rule":    st.column_config.TextColumn("Business rule", width="large",
                              help="e.g. 'Mandatory at Strong Upside', 'Required if Renewal'"),
}


def _reset_editor_state(edit_key: str):
    if edit_key in st.session_state:
        del st.session_state[edit_key]


def _ensure_init(init_key: str, state_key: str):
    cid_marker = f"_init_cid_{init_key}"
    current_cid = st.session_state.get("contributor_id")
    if init_key not in st.session_state or st.session_state.get(cid_marker) != current_cid:
        saved = _ensure_new_columns(list(st.session_state[state_key].get("fields", []) or []))
        st.session_state[init_key] = saved
        st.session_state[cid_marker] = current_cid
        _reset_editor_state(f"editor_{state_key}")


def _field_builder(label: str, state_key: str, suggestion_pool: list[dict],
                    help_text: str = "", height: int = 460) -> list[dict]:
    init_key = f"init_{state_key}"
    edit_key = f"editor_{state_key}"
    _ensure_init(init_key, state_key)

    st.markdown(f"#### {label}")
    if help_text: st.caption(help_text)

    cols = st.columns([1, 1, 1, 3])
    with cols[0]:
        if suggestion_pool and st.button("➕ Load suggestions", key=f"load_{state_key}"):
            existing = list(st.session_state[init_key])
            existing_names = {f.get("field", "").strip().lower() for f in existing}
            for s in suggestion_pool:
                if s["field"].strip().lower() not in existing_names:
                    existing.append(dict(s))
            st.session_state[init_key] = existing
            st.session_state[state_key]["fields"] = existing
            _reset_editor_state(edit_key)
    with cols[1]:
        if st.button("🗑️ Clear all", key=f"clear_{state_key}"):
            st.session_state[init_key] = []
            st.session_state[state_key]["fields"] = []
            _reset_editor_state(edit_key)
    with cols[2]:
        if st.button("📺 Fullscreen", key=f"fs_{state_key}", help="Open this table at full page size for easier editing"):
            st.session_state["_fullscreen_section"] = state_key
            st.rerun()

    rows = st.session_state[init_key]
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(FIELD_COLUMNS.keys()))
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True,
        column_config=FIELD_COLUMNS, key=edit_key, hide_index=True, height=height,
    )
    fields = _df_records(edited)
    st.session_state[state_key]["fields"] = fields
    return fields


# ============================================================
# Page 2 — Discovery Form
# ============================================================

_FS_TITLES = {
    "sec_partner_360":           "B. Partner 360 — Fields",
    "sec_customer_360":          "C. Customer 360 — Fields",
    "sec_sales_opp_details":     "D1. Sales — Opportunity Details",
    "sec_sales_contact_details": "D2. Sales — Opportunity Contact Details",
    "sec_sales_deal_details":    "D3. Sales — Opportunity Deal Details",
    "sec_approvals":             "E. Approval Stages & Workflow",
    "sec_dashboards":            "F. Dashboards & Reports Expected",
}
_FS_SUGGESTIONS = {
    "sec_partner_360":           sg.PARTNER_360_FIELDS,
    "sec_customer_360":          sg.CUSTOMER_360_FIELDS,
    "sec_sales_opp_details":     sg.REDHAT_OPPORTUNITY_DETAILS,
    "sec_sales_contact_details": sg.REDHAT_CONTACT_DETAILS,
    "sec_sales_deal_details":    sg.REDHAT_DEAL_DETAILS,
}


def _render_fullscreen_editor(state_key: str):
    """Render a single table at full-page size with sidebar hidden.

    Triggered by the 📺 Fullscreen button on any field-builder / approvals /
    dashboards editor. Exit returns to the normal form view.
    """
    # Hide the sidebar + give the editor more horizontal room while in FS mode
    st.markdown("""
<style>
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
.block-container { max-width: 100% !important; padding-left: 1.2rem; padding-right: 1.2rem; padding-top: .6rem; }
</style>
""", unsafe_allow_html=True)

    title = _FS_TITLES.get(state_key, "Editor")
    head_l, head_r = st.columns([5, 1])
    with head_l:
        st.markdown(f"### 📺 {title} — Fullscreen")
        st.caption(f"Editing as **{st.session_state.name}** ({st.session_state.role}) · {st.session_state.brand} · auto-save is on")
    with head_r:
        if st.button("✕ Exit fullscreen", type="primary", use_container_width=True, key=f"exit_fs_{state_key}"):
            st.session_state["_fullscreen_section"] = None
            st.rerun()

    st.divider()

    # Dispatch by section type
    if state_key == "sec_approvals":
        _fs_approvals()
    elif state_key == "sec_dashboards":
        _fs_dashboards()
    else:
        _field_builder(title, state_key, _FS_SUGGESTIONS.get(state_key, []),
                       help_text="", height=720)

    # Autosave still runs in fullscreen mode
    _autosave_form()


def _fs_approvals():
    appr_init = "init_sec_approvals"; appr_edit = "editor_approvals"
    cid_marker = f"_init_cid_{appr_init}"
    if appr_init not in st.session_state or st.session_state.get(cid_marker) != st.session_state.contributor_id:
        st.session_state[appr_init] = list(st.session_state.sec_approvals.get("stages", []) or [])
        st.session_state[cid_marker] = st.session_state.contributor_id
        _reset_editor_state(appr_edit)

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("➕ Load suggestions", key="load_approvals_fs"):
            existing = list(st.session_state[appr_init])
            names = {s.get("stage","").strip().lower() for s in existing}
            for s in sg.APPROVAL_STAGE_SUGGESTIONS:
                if s["stage"].strip().lower() not in names: existing.append(dict(s))
            st.session_state[appr_init] = existing
            st.session_state.sec_approvals["stages"] = existing
            _reset_editor_state(appr_edit)
    with c2:
        if st.button("🗑️ Clear all", key="clear_approvals_fs"):
            st.session_state[appr_init] = []
            st.session_state.sec_approvals["stages"] = []
            _reset_editor_state(appr_edit)

    rows = st.session_state[appr_init]
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["stage","approver","trigger","sla_hours","can_revert"])
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key=appr_edit, hide_index=True, height=720,
        column_config={
            "stage":      st.column_config.TextColumn("Stage", required=True, width="medium"),
            "approver":   st.column_config.TextColumn("Approver / Role", width="medium"),
            "trigger":    st.column_config.TextColumn("Trigger / Condition", width="large"),
            "sla_hours":  st.column_config.NumberColumn("SLA (h)", min_value=0, step=1, width="small"),
            "can_revert": st.column_config.CheckboxColumn("Revert?", width="small"),
        },
    )
    st.session_state.sec_approvals["stages"] = _df_records(edited)


def _fs_dashboards():
    dash_init = "init_sec_dashboards"; dash_edit = "editor_dash"
    cid_marker = f"_init_cid_{dash_init}"
    if dash_init not in st.session_state or st.session_state.get(cid_marker) != st.session_state.contributor_id:
        st.session_state[dash_init] = list(st.session_state.sec_dashboards.get("dashboards", []) or [])
        st.session_state[cid_marker] = st.session_state.contributor_id
        _reset_editor_state(dash_edit)

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("➕ Load suggestions", key="load_dash_fs"):
            existing = list(st.session_state[dash_init])
            names = {d.get("dashboard","").strip().lower() for d in existing}
            for s in sg.DASHBOARD_SUGGESTIONS:
                if s["dashboard"].strip().lower() not in names: existing.append(dict(s))
            st.session_state[dash_init] = existing
            st.session_state.sec_dashboards["dashboards"] = existing
            _reset_editor_state(dash_edit)
    with c2:
        if st.button("🗑️ Clear all", key="clear_dash_fs"):
            st.session_state[dash_init] = []
            st.session_state.sec_dashboards["dashboards"] = []
            _reset_editor_state(dash_edit)

    rows = st.session_state[dash_init]
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["dashboard","audience","frequency"])
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True, key=dash_edit, hide_index=True, height=720,
        column_config={
            "dashboard": st.column_config.TextColumn("Dashboard / Report", required=True, width="large"),
            "audience":  st.column_config.TextColumn("Audience (roles)", width="medium"),
            "frequency": st.column_config.SelectboxColumn("Frequency", options=["Real-time","Daily","Weekly","Monthly","Quarterly","On-demand"], width="small"),
        },
    )
    st.session_state.sec_dashboards["dashboards"] = _df_records(edited)


def render_form():
    if not st.session_state.contributor_id:
        st.warning("Please start a session first (sidebar → 🏁 Start)."); return

    # Fullscreen short-circuit: a section was promoted to full-page mode
    fs_section = st.session_state.get("_fullscreen_section")
    if fs_section:
        _render_fullscreen_editor(fs_section); return

    _hero(
        "BRAND DISCOVERY",
        f"📝 {st.session_state.brand} — Discovery Form",
        f"Contributing as <b style='color:#00E5FF'>{st.session_state.name}</b> ({st.session_state.role}). "
        "Eight sections. Press Enter or Tab out of a cell to commit. Autosave is on.",
    )

    pct = _completion_pct()
    k1, k2, k3, k4 = st.columns(4)
    sections_done = sum(1 for sk,sv in SECTION_STATE_KEYS.items()
                        if A._section_filled(st.session_state.get(sv) or {}, sk))
    fld_count = sum(len((st.session_state.get(sv) or {}).get('fields', []) or [])
                    for sk,sv in SECTION_STATE_KEYS.items() if sk in A.FIELD_BUILDER_SECTIONS)
    integ_count = sum(1 for sk,sv in SECTION_STATE_KEYS.items() if sk in A.FIELD_BUILDER_SECTIONS
                      for f in ((st.session_state.get(sv) or {}).get('fields') or []) if f.get('integration_needed'))
    k1.metric("✅ Completion",      f"{pct}%")
    k2.metric("📂 Sections",         f"{sections_done} / {len(SECTION_STATE_KEYS)}")
    k3.metric("🧱 Fields",           fld_count)
    k4.metric("🔌 Need integration", integ_count)
    st.progress(pct / 100)
    st.divider()

    tabs = st.tabs([
        "A. People", "B. Partner 360", "C. Customer 360",
        "D. Sales / Opportunity", "E. Approvals", "F. Dashboards",
        "G. Best Practices", "H. Open Notes",
    ])

    # A. People
    with tabs[0]:
        _intro("""<b>Why this matters</b> — Zoho needs to know who uses the system, in what role, and who signs off.
        Capture the human side: lead, decision-maker, contributing roles, rough user counts.
        Drives license counts, role-based permissions, and stakeholder communication.""")
        s = st.session_state.sec_people
        c1, c2 = st.columns(2)
        with c1:
            s["brand_lead_name"]  = st.text_input("Brand lead name",  value=s.get("brand_lead_name", ""))
            s["decision_maker"]   = st.text_input("Decision-maker / sign-off", value=s.get("decision_maker", ""))
            s["daily_users"]      = st.text_input("Approx. daily users",      value=s.get("daily_users", ""))
        with c2:
            s["brand_lead_email"] = st.text_input("Brand lead email", value=s.get("brand_lead_email", ""))
            s["roles_involved"]   = st.multiselect("Roles involved", config.ROLES, default=s.get("roles_involved", []))
            s["occasional_users"] = st.text_input("Approx. occasional users", value=s.get("occasional_users", ""))
        s["notes"] = st.text_area("Anything else about the people side?", value=s.get("notes", ""), height=80)

    # B. Partner 360
    with tabs[1]:
        _intro("""<b>Partner 360</b> — the master partner record, shared across every brand.
        Capture the fields you need on every partner, mandatory flags, integration need, and data-capture source.""")
        _field_builder("Partner 360 — Fields", "sec_partner_360", sg.PARTNER_360_FIELDS,
            "Use 'Load suggestions' for common starter fields, then edit/delete/add freely.")
        st.session_state.sec_partner_360["notes"] = st.text_area(
            "Notes (source of truth, dedup approach, hierarchy)",
            value=st.session_state.sec_partner_360.get("notes", ""), height=80)

    # C. Customer 360
    with tabs[2]:
        _intro("""<b>Customer 360</b> — the master customer / end-user record, shared across brands.
        Mandatory fields, hierarchy needs, brand-specific extensions, plus integration + source per field.""")
        _field_builder("Customer 360 — Fields", "sec_customer_360", sg.CUSTOMER_360_FIELDS, "")
        st.session_state.sec_customer_360["notes"] = st.text_area(
            "Notes (renewals, hierarchies, dedup)",
            value=st.session_state.sec_customer_360.get("notes", ""), height=80)

    # D. Sales
    with tabs[3]:
        _intro("""<b>Sales — Opportunity / Lead / Deal</b>: three sub-sections.
        Define the fields Zoho should capture on each opportunity.
        Red Hat starter = partner-funnel-shaped, AWS starter = project-shaped. Mix and match.""")

        def _seed_into(state_key: str, source: list[dict]):
            init_key = f"init_{state_key}"
            _ensure_init(init_key, state_key)
            existing = list(st.session_state[init_key])
            names = {f.get("field","").strip().lower() for f in existing}
            for sx in source:
                if sx["field"].strip().lower() not in names:
                    existing.append(dict(sx))
            st.session_state[init_key] = existing
            st.session_state[state_key]["fields"] = existing
            _reset_editor_state(f"editor_{state_key}")

        with st.expander("**D1. Opportunity Details**", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Use Red Hat starter (Opportunity)", key="seed_redhat_d1"):
                    _seed_into("sec_sales_opp_details", sg.REDHAT_OPPORTUNITY_DETAILS)
            with c2:
                if st.button("Use AWS starter (Customer)", key="seed_aws_d1"):
                    _seed_into("sec_sales_opp_details", sg.AWS_CUSTOMER_DETAILS)
            _field_builder("Opportunity Details fields", "sec_sales_opp_details", [], "")
            st.session_state.sec_sales_opp_details["notes"] = st.text_area(
                "Notes — D1", value=st.session_state.sec_sales_opp_details.get("notes", ""), height=70, key="notes_d1")

        with st.expander("**D2. Opportunity Contact Details**", expanded=False):
            if st.button("Use Red Hat starter (Contacts)", key="seed_redhat_d2"):
                _seed_into("sec_sales_contact_details", sg.REDHAT_CONTACT_DETAILS)
            _field_builder("Contact Details fields", "sec_sales_contact_details", [], "People involved (PAM, BSM, PM, Pre-sales).")
            st.session_state.sec_sales_contact_details["notes"] = st.text_area(
                "Notes — D2", value=st.session_state.sec_sales_contact_details.get("notes", ""), height=70, key="notes_d2")

        with st.expander("**D3. Opportunity Deal Details**", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Use Red Hat starter (Deal)", key="seed_redhat_d3"):
                    _seed_into("sec_sales_deal_details", sg.REDHAT_DEAL_DETAILS)
            with c2:
                if st.button("Use AWS starter (Project)", key="seed_aws_d3"):
                    _seed_into("sec_sales_deal_details", sg.AWS_PROJECT_DETAILS)
            _field_builder("Deal Details fields", "sec_sales_deal_details", [], "Commercials, products, services, target close date.")
            st.session_state.sec_sales_deal_details["notes"] = st.text_area(
                "Notes — D3", value=st.session_state.sec_sales_deal_details.get("notes", ""), height=70, key="notes_d3")

    # E. Approvals
    with tabs[4]:
        _intro("""<b>Approval workflow</b> — every brand has different rules. Define stages, approvers, triggers, SLAs.
        Missing data here is the #1 cause of delayed go-lives.""")
        appr_init = "init_sec_approvals"; appr_edit = "editor_approvals"
        cid_marker = f"_init_cid_{appr_init}"
        if appr_init not in st.session_state or st.session_state.get(cid_marker) != st.session_state.contributor_id:
            st.session_state[appr_init] = list(st.session_state.sec_approvals.get("stages", []) or [])
            st.session_state[cid_marker] = st.session_state.contributor_id
            _reset_editor_state(appr_edit)

        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        with c1:
            if st.button("➕ Load suggestions", key="load_approvals"):
                existing = list(st.session_state[appr_init])
                names = {s.get("stage","").strip().lower() for s in existing}
                for s in sg.APPROVAL_STAGE_SUGGESTIONS:
                    if s["stage"].strip().lower() not in names: existing.append(dict(s))
                st.session_state[appr_init] = existing
                st.session_state.sec_approvals["stages"] = existing
                _reset_editor_state(appr_edit)
        with c2:
            if st.button("🗑️ Clear all", key="clear_approvals"):
                st.session_state[appr_init] = []
                st.session_state.sec_approvals["stages"] = []
                _reset_editor_state(appr_edit)
        with c3:
            if st.button("📺 Fullscreen", key="fs_approvals"):
                st.session_state["_fullscreen_section"] = "sec_approvals"; st.rerun()

        rows = st.session_state[appr_init]
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["stage","approver","trigger","sla_hours","can_revert"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key=appr_edit, hide_index=True, height=400,
            column_config={
                "stage":      st.column_config.TextColumn("Stage", required=True),
                "approver":   st.column_config.TextColumn("Approver / Role"),
                "trigger":    st.column_config.TextColumn("Trigger / Condition"),
                "sla_hours":  st.column_config.NumberColumn("SLA (h)", min_value=0, step=1),
                "can_revert": st.column_config.CheckboxColumn("Revert?"),
            },
        )
        st.session_state.sec_approvals["stages"]     = _df_records(edited)
        st.session_state.sec_approvals["escalation"] = st.text_area("Escalation rules (what if SLA breached?)", value=st.session_state.sec_approvals.get("escalation", ""), height=80)
        st.session_state.sec_approvals["notes"]      = st.text_area("Other workflow notes", value=st.session_state.sec_approvals.get("notes", ""), height=80)

    # F. Dashboards
    with tabs[5]:
        _intro("""<b>Dashboards & reports</b> — the views people look at every day.
        List every dashboard, who watches it, how often. <b>Without dashboards listed, Zoho cannot validate reporting.</b>""")
        dash_init = "init_sec_dashboards"; dash_edit = "editor_dash"
        cid_marker_d = f"_init_cid_{dash_init}"
        if dash_init not in st.session_state or st.session_state.get(cid_marker_d) != st.session_state.contributor_id:
            st.session_state[dash_init] = list(st.session_state.sec_dashboards.get("dashboards", []) or [])
            st.session_state[cid_marker_d] = st.session_state.contributor_id
            _reset_editor_state(dash_edit)

        c1, c2, c3, _ = st.columns([1, 1, 1, 3])
        with c1:
            if st.button("➕ Load suggestions", key="load_dash"):
                existing = list(st.session_state[dash_init])
                names = {d.get("dashboard","").strip().lower() for d in existing}
                for s in sg.DASHBOARD_SUGGESTIONS:
                    if s["dashboard"].strip().lower() not in names: existing.append(dict(s))
                st.session_state[dash_init] = existing
                st.session_state.sec_dashboards["dashboards"] = existing
                _reset_editor_state(dash_edit)
        with c2:
            if st.button("🗑️ Clear all", key="clear_dash"):
                st.session_state[dash_init] = []
                st.session_state.sec_dashboards["dashboards"] = []
                _reset_editor_state(dash_edit)
        with c3:
            if st.button("📺 Fullscreen", key="fs_dash"):
                st.session_state["_fullscreen_section"] = "sec_dashboards"; st.rerun()

        rows = st.session_state[dash_init]
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["dashboard","audience","frequency"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key=dash_edit, hide_index=True, height=400,
            column_config={
                "dashboard": st.column_config.TextColumn("Dashboard / Report", required=True),
                "audience":  st.column_config.TextColumn("Audience (roles)"),
                "frequency": st.column_config.SelectboxColumn("Frequency", options=["Real-time","Daily","Weekly","Monthly","Quarterly","On-demand"]),
            },
        )
        st.session_state.sec_dashboards["dashboards"] = _df_records(edited)
        st.session_state.sec_dashboards["notes"]      = st.text_area("Notes (exports, drill-downs, scheduled emails)", value=st.session_state.sec_dashboards.get("notes", ""), height=80)

    # G. Best Practices
    with tabs[6]:
        _intro("""<b>Best-practice inputs</b> — recommendations for the Zoho team. Not for deep config in v1.""")
        s = st.session_state.sec_best_practices
        s["data_hygiene"]          = st.text_area("Data-hygiene asks (dedup, mandatory rules, naming)", value=s.get("data_hygiene", ""), height=110)
        s["integrations_wishlist"] = st.text_area("Integrations wishlist (Zoho ↔ ERP / Outlook / Teams / vendor portals)", value=s.get("integrations_wishlist", ""), height=110)
        s["dedup_sops"]            = st.text_area("SOPs to document later", value=s.get("dedup_sops", ""), height=110)
        with st.expander("💡 Common additional clauses (copy/paste if relevant)"):
            for c in sg.ADDITIONAL_CLAUSE_SUGGESTIONS:
                st.markdown(f"- {c}")

    # H. Open Notes
    with tabs[7]:
        _intro("""<b>Open notes</b> — the qualitative side. Pain points are gold for Zoho — they tell the team what NOT to repeat.""")
        s = st.session_state.sec_open_notes
        c1, c2 = st.columns(2)
        with c1:
            s["pain_points"]   = st.text_area("Current pain points",  value=s.get("pain_points", ""), height=130)
            s["nice_to_haves"] = st.text_area("Nice-to-haves",        value=s.get("nice_to_haves", ""), height=130)
            s["risks"]         = st.text_area("Risks / blockers",    value=s.get("risks", ""), height=130)
        with c2:
            s["must_haves"]         = st.text_area("Must-haves",                 value=s.get("must_haves", ""), height=130)
            s["questions_for_zoho"] = st.text_area("Questions for the Zoho team", value=s.get("questions_for_zoho", ""), height=130)

    st.divider()
    save, info = st.columns([1, 4])
    with save:
        if st.button("💾 Save & Submit", type="primary", use_container_width=True):
            try:
                filled = []
                for sec_key, state_key in SECTION_STATE_KEYS.items():
                    payload = st.session_state.get(state_key) or {}
                    db.save_response(st.session_state.contributor_id, sec_key, payload)
                    if A._section_filled(payload, sec_key): filled.append(sec_key)
                audit.log("submit", contributor_id=st.session_state.contributor_id, sections_filled=len(filled))
                st.success("✅ Saved. Use the same email to come back anytime.")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with info:
        st.info("💡 Auto-save runs on every change. Use the **same email** later to resume. Multiple roles per brand contribute — answers merge into one report.")

    _autosave_form()


_AUTOSAVE_DEBOUNCE_SEC = 1.5

def _autosave_form():
    cid = st.session_state.get("contributor_id")
    if not cid:
        return

    # Debounce: skip if we just saved less than _AUTOSAVE_DEBOUNCE_SEC ago.
    # Without this every keystroke can fire a DB round-trip because Streamlit
    # re-runs the entire script on each commit.
    now = _time.time()
    last = st.session_state.get("_autosave_last_run", 0.0)
    if now - last < _AUTOSAVE_DEBOUNCE_SEC:
        return
    st.session_state["_autosave_last_run"] = now

    if st.session_state.get("_autosave_cid") != cid:
        st.session_state["_autosave_cid"] = cid
        for sk in SECTION_STATE_KEYS:
            st.session_state.pop(f"_saved_{sk}", None)

    saved = []
    for sec_key, state_key in SECTION_STATE_KEYS.items():
        payload = st.session_state.get(state_key) or {}
        last_payload = st.session_state.get(f"_saved_{sec_key}")
        if payload != last_payload:
            try:
                db.save_response(cid, sec_key, payload)
                st.session_state[f"_saved_{sec_key}"] = _copy.deepcopy(payload)
                saved.append(sec_key)
                audit.log("autosave", contributor_id=cid, section_key=sec_key,
                          fields_count=len((payload or {}).get("fields", []) or []))
            except Exception as e:
                st.session_state["_autosave_last_error"] = str(e)

    # Invalidate the brand bundle cache so admin views see fresh data
    if saved:
        try:
            _cached_bundle.clear()
            _cached_contrib_counts.clear()
        except Exception: pass
        try: st.toast(f"💾 Auto-saved {len(saved)} section(s)", icon="✅")
        except Exception: pass


# ============================================================
# Page 3 — Admin (multi-page)
# ============================================================

def render_admin():
    if not st.session_state.admin_unlocked:
        _hero("ADMIN", "🔒 Admin Console", "Per-brand dashboard, cross-brand comparison, analytics, brand management, bulk import and the audit log.")
        with st.container(border=True):
            st.markdown("Enter the admin passcode to unlock the dashboard.")
            pc = st.text_input("Admin passcode", type="password")
            if st.button("Unlock", type="primary"):
                if pc == config.ADMIN_PASSCODE:
                    st.session_state.admin_unlocked = True
                    audit.log("admin_unlock", success=True)
                    st.rerun()
                else:
                    audit.log("admin_unlock", success=False)
                    st.error("Wrong passcode.")
        return

    _hero("ADMIN CONSOLE", "🔒 Brand Insights & Tools",
          "All admin tools in one place. Pick a tab.")

    tabs = st.tabs([
        "📊 Brand Dashboard", "🔄 Cross-Brand", "📈 Analytics",
        "🩺 Diagnostics", "🏷️ Brands", "📥 Bulk Import", "🛡️ Audit Log",
    ])

    with tabs[0]: _admin_brand_dashboard()
    with tabs[1]: _admin_cross_brand()
    with tabs[2]: _admin_analytics()
    with tabs[3]: _admin_diagnostics()
    with tabs[4]: _admin_brands()
    with tabs[5]: _admin_bulk_import()
    with tabs[6]: _admin_audit_log()


def _admin_brand_dashboard():
    brand_names = [b["name"] for b in _cached_brand_list(False)] or config.BRANDS
    brand = st.selectbox("Brand", brand_names, key="brand_dash_select")
    try:
        bundle = _cached_bundle(brand)
    except Exception as e:
        st.error(f"DB error: {e}"); return
    metrics   = A.compute_metrics(bundle)
    conflicts = A.detect_conflicts(bundle)
    recs      = A.generate_recommendations(bundle, metrics, conflicts)

    st.subheader(f"🏷️ {brand}")
    st.caption(f"Generated {bundle['generated_at']}")

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("👥 Contributors", metrics["contributors"])
    c2.metric("🧱 Fields",         metrics["total_fields"])
    c3.metric("✅ Mandatory",      f"{metrics['mandatory_pct']}%")
    c4.metric("🔌 Integration",    f"{metrics['integration_pct']}%")
    c5.metric("🔁 Approvals",      metrics["approval_stages"])
    c6.metric("📊 Dashboards",     metrics["dashboards"])

    st.progress(metrics["completion_pct"] / 100,
                text=f"Section completion: {metrics['completion_pct']}%   ·   Brand readiness: {A.overall_readiness_pct(metrics):.0f}/100")

    if not bundle["contributors"]:
        st.warning("No contributors yet for this brand."); return

    # Row 1: fields per section + mandatory %
    cc1, cc2 = st.columns(2)
    with cc1:
        data = A.fields_per_section_count(bundle)
        df = pd.DataFrame({"Section": list(data.keys()), "Fields": list(data.values())})
        fig = px.bar(df, x="Section", y="Fields", color_discrete_sequence=[theme.COLORS["accent"]], title="Fields proposed per section")
        fig.update_layout(**_plotly_layout(height=320))
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        data = A.mandatory_per_section_pct(bundle)
        df = pd.DataFrame({"Section": list(data.keys()), "Mandatory %": list(data.values())})
        fig = px.bar(df, x="Mandatory %", y="Section", orientation="h",
                     color_discrete_sequence=[theme.COLORS["accent_2"]], title="Mandatory % per section")
        fig.update_layout(**_plotly_layout(height=320, xaxis_range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True)

    # Row 2: integration %, source mix, readiness radar
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        data = A.integration_per_section_pct(bundle)
        df = pd.DataFrame({"Section": list(data.keys()), "Integration %": list(data.values())})
        fig = px.bar(df, x="Integration %", y="Section", orientation="h",
                     color_discrete_sequence=[theme.COLORS["gold"]], title="Integration intensity")
        fig.update_layout(**_plotly_layout(height=340, xaxis_range=[0, 100]))
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        data = A.data_source_breakdown(bundle) or {"No data": 1}
        df = pd.DataFrame({"Source": list(data.keys()), "Count": list(data.values())})
        fig = px.pie(df, names="Source", values="Count", hole=.55,
                     color_discrete_sequence=theme.CHART_PALETTE, title="Data-capture source mix")
        fig.update_layout(**_plotly_layout(height=340))
        st.plotly_chart(fig, use_container_width=True)
    with cc3:
        scores = A.readiness_scores(metrics)
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(scores.values()) + [list(scores.values())[0]],
            theta=list(scores.keys()) + [list(scores.keys())[0]],
            fill="toself", line_color=theme.COLORS["accent"],
            fillcolor="rgba(0,229,255,0.20)", name="Readiness",
        ))
        fig.update_layout(
            **_plotly_layout(
                height=340,
                title=f"Brand readiness — {A.overall_readiness_pct(metrics):.0f}/100",
                polar=dict(bgcolor=theme.COLORS["surface"],
                           radialaxis=dict(range=[0, 100], visible=True, gridcolor=theme.COLORS["border"], color=theme.COLORS["ink_dim"]),
                           angularaxis=dict(gridcolor=theme.COLORS["border"], color=theme.COLORS["ink_dim"])),
                showlegend=False,
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    # Conflicts + Recommendations
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("### 🚨 Conflicts to resolve")
        st.caption("Mandatory / integration / source / SLA disagreements between contributors.")
        if conflicts:
            st.dataframe(pd.DataFrame(conflicts), use_container_width=True, hide_index=True)
        else:
            st.success("No conflicts detected.")
    with cc2:
        st.markdown("### 💡 Insights & Recommendations")
        if recs:
            rdf = pd.DataFrame(recs)
            st.dataframe(rdf, use_container_width=True, hide_index=True)

    # Contributors
    st.markdown("### 👥 Contributors")
    cdf = pd.DataFrame([{
        "Name": c["name"], "Role": c["role"], "Email": c["email"],
        "Last update": c["submitted_at"][:19].replace("T"," "),
    } for c in bundle["contributors"]])
    st.dataframe(cdf, use_container_width=True, hide_index=True)

    # Downloads
    st.markdown("### 📥 Download requirements pack")
    d1, d2, d3 = st.columns(3)
    with d1:
        if st.download_button("⬇️ PDF",  data=reports.build_pdf(bundle),
                              file_name=f"Redington_Discovery_{brand}.pdf",  mime="application/pdf", use_container_width=True):
            audit.log("report_downloaded", brand=brand, format="pdf")
    with d2:
        if st.download_button("⬇️ Word", data=reports.build_docx(bundle),
                              file_name=f"Redington_Discovery_{brand}.docx",
                              mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True):
            audit.log("report_downloaded", brand=brand, format="docx")
    with d3:
        if st.download_button("⬇️ CSV",  data=reports.build_csv(bundle),
                              file_name=f"Redington_Discovery_{brand}.csv",  mime="text/csv", use_container_width=True):
            audit.log("report_downloaded", brand=brand, format="csv")

    # Inline preview
    st.markdown("### 🔍 Inline view of merged inputs")
    for sec_key, sec_title in reports.SECTIONS:
        with st.expander(sec_title, expanded=False):
            any_data = False
            for c in bundle["contributors"]:
                payload = bundle["responses_by_contributor"].get(c["id"], {}).get(sec_key)
                if not payload: continue
                any_data = True
                st.markdown(f"**From {c['name']} ({c['role']})**")
                if sec_key in reports.FIELD_BUILDER_SECTIONS:
                    rows = payload.get("fields", []) or []
                    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    if payload.get("notes"): st.caption(f"Notes: {payload['notes']}")
                elif sec_key == "approvals":
                    rows = payload.get("stages", []) or []
                    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    if payload.get("escalation"): st.caption(f"Escalation: {payload['escalation']}")
                    if payload.get("notes"): st.caption(f"Notes: {payload['notes']}")
                elif sec_key == "dashboards":
                    rows = payload.get("dashboards", []) or []
                    if rows: st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                    if payload.get("notes"): st.caption(f"Notes: {payload['notes']}")
                else:
                    for k, v in payload.items():
                        if v: st.markdown(f"- **{k.replace('_',' ').title()}:** {v}")
                st.markdown("---")
            if not any_data:
                st.caption("_No input captured yet._")


def _admin_cross_brand():
    st.subheader("🔄 Cross-brand comparison")
    st.caption("Side-by-side view across every brand.")
    brand_names = [b["name"] for b in _cached_brand_list(False)] or config.BRANDS
    bundles = []
    for b in brand_names:
        try: bundles.append(_cached_bundle(b))
        except Exception: pass
    rows = []
    for b in bundles:
        m = A.compute_metrics(b)
        rows.append({"Brand": b["brand"], "Contributors": m["contributors"], "Fields": m["total_fields"],
                     "Mandatory %": m["mandatory_pct"], "Integration %": m["integration_pct"],
                     "Approvals": m["approval_stages"], "Dashboards": m["dashboards"],
                     "Completion %": m["completion_pct"], "Readiness /100": A.overall_readiness_pct(m)})
    cdf = pd.DataFrame(rows)
    st.dataframe(cdf, use_container_width=True, hide_index=True)

    if not cdf.empty:
        fig = px.bar(cdf, x="Brand", y=["Contributors","Fields","Approvals","Dashboards"], barmode="group",
                     title="Brand-by-brand totals",
                     color_discrete_sequence=theme.CHART_PALETTE)
        fig.update_layout(**_plotly_layout(height=380))
        st.plotly_chart(fig, use_container_width=True)

        cc1, cc2 = st.columns(2)
        with cc1:
            fig2 = px.bar(cdf, x="Brand", y="Completion %", color_discrete_sequence=[theme.COLORS["accent"]], title="Section-completion %")
            fig2.update_layout(**_plotly_layout(height=320, yaxis_range=[0,100]))
            st.plotly_chart(fig2, use_container_width=True)
        with cc2:
            fig3 = px.bar(cdf, x="Brand", y="Readiness /100", color_discrete_sequence=[theme.COLORS["accent_2"]], title="Brand readiness score")
            fig3.update_layout(**_plotly_layout(height=320, yaxis_range=[0,100]))
            st.plotly_chart(fig3, use_container_width=True)

        radar = go.Figure()
        for b in bundles:
            m = A.compute_metrics(b); s = A.readiness_scores(m)
            radar.add_trace(go.Scatterpolar(
                r=list(s.values()) + [list(s.values())[0]],
                theta=list(s.keys()) + [list(s.keys())[0]],
                fill="toself", name=b["brand"], opacity=0.55,
            ))
        radar.update_layout(
            **_plotly_layout(
                height=440, title="Cross-brand readiness radar",
                polar=dict(bgcolor=theme.COLORS["surface"],
                           radialaxis=dict(range=[0, 100], visible=True, gridcolor=theme.COLORS["border"], color=theme.COLORS["ink_dim"]),
                           angularaxis=dict(gridcolor=theme.COLORS["border"], color=theme.COLORS["ink_dim"])),
            )
        )
        st.plotly_chart(radar, use_container_width=True)

    if st.download_button("⬇️ Download cross-brand CSV", data=reports.build_cross_brand_csv(bundles),
                          file_name="Redington_Discovery_AllBrands.csv", mime="text/csv"):
        audit.log("cross_brand_export", brands_count=len(bundles))


def _admin_analytics():
    st.subheader("📈 Analytics")
    st.caption("Velocity, role contribution, gap analysis, and time-to-completion.")

    brand_names = [b["name"] for b in _cached_brand_list(False)] or config.BRANDS
    bundles = []
    for b in brand_names:
        try: bundles.append(_cached_bundle(b))
        except Exception: pass

    try:
        audit_rows = _cached_audit(500, None, None, None)
    except Exception:
        audit_rows = []

    # KPI strip
    total_contrib = sum(len(b["contributors"]) for b in bundles)
    total_fields  = sum(A.compute_metrics(b)["total_fields"] for b in bundles)
    health = A.cross_brand_health_score(bundles)
    avg_health = round(sum(h["health"] for h in health) / len(health), 1) if health else 0.0
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("👥 Total contributors", total_contrib)
    k2.metric("🧱 Total fields",       total_fields)
    k3.metric("📈 Avg readiness",      f"{avg_health}/100")
    k4.metric("🛡️ Audit events",       len(audit_rows))

    # Velocity (daily activity)
    daily = A.daily_activity_series(audit_rows)
    if daily:
        dfd = pd.DataFrame(daily)
        fig = px.line(dfd, x="day", y=["sessions", "autosaves", "downloads"],
                      title="Daily activity (audit log)", markers=True,
                      color_discrete_sequence=theme.CHART_PALETTE)
        fig.update_layout(**_plotly_layout(height=340))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No audit events yet. Start a session, save a section, or download a report — events will populate here.")

    # Per-brand views
    pick = st.selectbox("Brand for drill-down", brand_names, key="analytics_brand_select")
    bundle = next((b for b in bundles if b["brand"] == pick), None)
    if not bundle: st.warning("Select a brand."); return

    # Role × Section heatmap
    rcm = A.role_contribution_matrix(bundle)
    if rcm:
        dfr = pd.DataFrame(rcm).pivot_table(index="role", columns="section", values="fields", aggfunc="sum", fill_value=0)
        fig = go.Figure(data=go.Heatmap(
            z=dfr.values, x=dfr.columns.tolist(), y=dfr.index.tolist(),
            colorscale=[[0, theme.COLORS["surface_2"]], [0.5, theme.COLORS["accent_2"]], [1, theme.COLORS["accent"]]],
            colorbar=dict(title="Fields"),
        ))
        fig.update_layout(**_plotly_layout(height=340, title=f"Role × Section heatmap — {pick}"))
        st.plotly_chart(fig, use_container_width=True)

    # Gap analysis
    gaps = A.gap_analysis(bundle)
    if gaps:
        gdf = pd.DataFrame(gaps)
        fig = px.bar(gdf, x="section", y=["proposed", "floor"], barmode="group",
                     title=f"Gap analysis — {pick}",
                     color_discrete_sequence=[theme.COLORS["accent"], theme.COLORS["ink_dim"]])
        fig.update_layout(**_plotly_layout(height=320))
        st.plotly_chart(fig, use_container_width=True)
        bad = [g for g in gaps if g["status"] in ("Missing", "Under-spec", "Empty")]
        if bad:
            st.warning(f"⚠️ {len(bad)} section(s) under target floor.")
            st.dataframe(pd.DataFrame(bad), use_container_width=True, hide_index=True)

    # Time-to-completion
    ttc = A.time_to_completion(bundle, audit_rows=audit_rows)
    if ttc:
        ttcdf = pd.DataFrame(ttc)
        fig = px.bar(ttcdf, x="name", y="minutes", color="role",
                     title=f"Time-to-completion (minutes) — {pick}",
                     color_discrete_sequence=theme.CHART_PALETTE)
        fig.update_layout(**_plotly_layout(height=320))
        st.plotly_chart(fig, use_container_width=True)


def _admin_diagnostics():
    st.subheader("🩺 Diagnostics — every contributor across every brand")
    st.caption("Shows who started a session and whether each section has data saved.")
    try:
        all_contribs = db.list_contributors()
    except Exception as e:
        st.error(f"DB error: {e}"); return

    if not all_contribs:
        st.info("No contributors in the database yet.")
        return

    diag_rows = []
    for c in all_contribs:
        try: resp = db.get_responses_for_contributor(c["id"])
        except Exception: resp = {}
        filled, empty = [], []
        for sk in A.ALL_SECTION_KEYS:
            payload = resp.get(sk, {}) or {}
            (filled if A._section_filled(payload, sk) else empty).append(sk)
        diag_rows.append({
            "Brand": c["brand"], "Name": c["name"], "Email": c["email"], "Role": c["role"],
            "Last update": c["submitted_at"][:19].replace("T"," "),
            "Sections filled": len(filled), "Sections total": len(A.ALL_SECTION_KEYS),
            "Status": "✅ Has data" if filled else "⚠️ Empty",
            "Empty sections": ", ".join(empty) if empty else "—",
        })
    diag_df = pd.DataFrame(diag_rows).sort_values(["Brand", "Last update"], ascending=[True, False])
    st.dataframe(diag_df, use_container_width=True, hide_index=True)

    empties = [r for r in diag_rows if r["Status"].startswith("⚠️")]
    if empties:
        st.warning(f"⚠️ {len(empties)} contributor(s) with NO data. Ask them to re-open with the same email; autosave will persist this time.")


def _admin_brands():
    st.subheader("🏷️ Brands — manage what appears in the brand picker")
    st.caption("Add a new brand (name + optional logo + optional starter template). Archive to remove from the picker without deleting historical data.")

    try:
        brands = _cached_brand_list(False)
        # The fallback returns dicts with id=None — that means the brands table doesn't exist
        if brands and all(b.get("id") is None for b in brands):
            st.warning("📌 **Setup needed** — the `brands` table doesn't exist in Supabase yet. "
                       "Open your Supabase project → SQL Editor → paste the contents of `schema_v3.sql` from the repo → click Run. "
                       "Then refresh this page. Until then the brand picker uses the hard-coded fallback list (AWS / Microsoft / Red Hat).")
            return
    except Exception as e:
        st.error(f"DB error: {e}. Did you run schema_v3.sql in Supabase?"); return

    if not brands:
        st.info("No brands in DB yet — add the first one below.")
    else:
        try:
            counts = db.count_contributors_per_brand()
        except Exception:
            counts = {}
        rows = [{
            "Name": b["name"], "Slug": b.get("slug", ""),
            "Active": "✅" if b.get("active") else "⛔",
            "Logo": "🖼️" if b.get("logo_url") else "—",
            "Contributors": counts.get(b["name"], 0),
            "Created": (b.get("created_at") or "")[:19].replace("T", " "),
        } for b in brands]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        cols = st.columns(2)
        with cols[0]:
            archive_pick = st.selectbox("Archive brand", [b["name"] for b in brands if b.get("active")] or ["(none active)"], key="archive_pick")
            if st.button("⛔ Archive selected"):
                target = next((b for b in brands if b["name"] == archive_pick), None)
                if target and target.get("id"):
                    db.archive_brand(target["id"])
                    audit.log("brand_archived", brand_name=archive_pick)
                    _cached_brand_list.clear()
                    st.success(f"Archived {archive_pick}"); st.rerun()
        with cols[1]:
            unarchive_pick = st.selectbox("Unarchive brand", [b["name"] for b in brands if not b.get("active")] or ["(none archived)"], key="unarchive_pick")
            if st.button("♻️ Unarchive selected"):
                target = next((b for b in brands if b["name"] == unarchive_pick), None)
                if target and target.get("id"):
                    db.unarchive_brand(target["id"])
                    audit.log("brand_unarchived", brand_name=unarchive_pick)
                    _cached_brand_list.clear()
                    st.success(f"Unarchived {unarchive_pick}"); st.rerun()

    st.markdown("---")
    st.markdown("#### ➕ Add a new brand")
    st.caption("New brands use the same form structure and shared starter library as existing brands — contributors get the same Load Suggestions / Red Hat / AWS starters.")
    with st.form("add_brand_form", clear_on_submit=True):
        name = st.text_input("Brand name", placeholder="e.g. Google Cloud, Oracle, VMware")
        logo = st.text_input("Logo URL (optional)", placeholder="https://...")
        submit = st.form_submit_button("Add brand", type="primary")
        if submit:
            if not name.strip():
                st.error("Brand name is required.")
            else:
                try:
                    row = db.add_brand(name.strip(),
                                       logo_url=logo.strip() or None,
                                       starter_template=None,
                                       created_by=st.session_state.get("email"))
                    audit.log("brand_added", brand_name=name.strip(), has_logo=bool(logo.strip()))
                    _cached_brand_list.clear()
                    st.success(f"✅ Added {row['name']}"); st.rerun()
                except Exception as e:
                    msg = str(e)
                    if "brands" in msg.lower() and ("schema cache" in msg.lower() or "does not exist" in msg.lower()):
                        st.error("The `brands` table doesn't exist in your Supabase project yet. "
                                 "Open Supabase → SQL Editor → paste the contents of `schema_v3.sql` from the repo → click Run, "
                                 "then come back and add the brand.")
                    else:
                        st.error(f"Add failed: {msg}")


def _admin_bulk_import():
    st.subheader("📥 Bulk Excel import / export")
    st.caption("Download a per-brand workbook, fill offline, upload back. The import is logged in the audit trail under the contributor email you enter on the Cover sheet.")

    brand_names = [b["name"] for b in _cached_brand_list(False)] or config.BRANDS
    brand = st.selectbox("Brand", brand_names, key="bulk_brand_select")

    st.markdown("##### 1) Download template")
    try:
        tmpl = excel_io.download_template(brand)
        st.download_button("⬇️ Download Excel template", data=tmpl,
                           file_name=f"Redington_Discovery_Template_{brand}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.error(f"Could not generate template: {e}")

    st.markdown("##### 2) Upload filled template")
    uploaded = st.file_uploader("Upload .xlsx", type=["xlsx"], key="bulk_upload")
    if uploaded:
        try:
            parsed = excel_io.import_template(uploaded.read())
        except Exception as e:
            st.error(f"Could not parse the file: {e}"); return

        contrib = parsed.get("contributor", {})
        sections = parsed.get("sections", {})
        if not contrib.get("email"):
            st.error("Cover sheet is missing Email — that's required.")
            return
        st.success(f"Parsed ✅ — contributor {contrib.get('name','(no name)')} ({contrib.get('email')}, {contrib.get('role','Other')}), {len(sections)} section(s).")

        # Preview
        for sk, payload in sections.items():
            with st.expander(f"Section preview — {sk}"):
                if isinstance(payload, dict):
                    if payload.get("fields"):     st.dataframe(pd.DataFrame(payload["fields"]),     use_container_width=True, hide_index=True)
                    elif payload.get("stages"):    st.dataframe(pd.DataFrame(payload["stages"]),     use_container_width=True, hide_index=True)
                    elif payload.get("dashboards"):st.dataframe(pd.DataFrame(payload["dashboards"]), use_container_width=True, hide_index=True)
                    else:
                        st.json(payload, expanded=False)

        if st.button("✅ Apply import", type="primary"):
            try:
                row = db.upsert_contributor(brand, contrib.get("name") or "Bulk Import",
                                            contrib["email"], contrib.get("role") or "Other")
                for sk, payload in sections.items():
                    db.save_response(row["id"], sk, payload)
                audit.log("bulk_import", brand=brand, contributor_id=row["id"],
                          sections=list(sections.keys()), filename=uploaded.name)
                _cached_bundle.clear(); _cached_contrib_counts.clear()
                st.success(f"✅ Imported {len(sections)} section(s) under {row['email']}")
            except Exception as e:
                st.error(f"Import failed: {e}")


def _admin_audit_log():
    st.subheader("🛡️ Audit Log")
    st.caption("Every action with email + IP + timestamp. Filter, then export.")

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        event_filter = st.selectbox("Event", ["(all)", "session_start", "autosave", "submit",
                                              "report_downloaded", "admin_unlock", "brand_added",
                                              "brand_archived", "brand_unarchived", "bulk_import",
                                              "cross_brand_export"])
    with f2:
        _br_options = ["(all)"] + ([b["name"] for b in _cached_brand_list(False)] or config.BRANDS)
        brand_filter = st.selectbox("Brand", _br_options, key="audit_brand")
    with f3:
        email_filter = st.text_input("Email contains")
    with f4:
        limit = st.number_input("Limit", min_value=50, max_value=5000, value=500, step=50)

    filters = {}
    if event_filter != "(all)": filters["event"] = event_filter
    if brand_filter != "(all)": filters["brand"] = brand_filter
    if email_filter.strip():     filters["email"] = email_filter.strip()

    rows = _cached_audit(int(limit),
                         filters.get("event"), filters.get("brand"), filters.get("email"))
    if not rows:
        st.info("No audit events match.")
        return

    rdf = pd.DataFrame(rows)
    # Compact view
    show = rdf[["ts", "event", "actor_email", "actor_ip", "brand", "section_key", "detail"]].copy()
    show["ts"] = show["ts"].str[:19].str.replace("T", " ")
    show["detail"] = show["detail"].apply(lambda d: json.dumps(d, separators=(",", ":")) if d else "")
    st.dataframe(show, use_container_width=True, hide_index=True, height=520)

    csv = rdf.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Export filtered CSV", data=csv, file_name="audit_log.csv", mime="text/csv")


# ---------- Router ----------
if page == PAGE_INTRO:
    render_intro()
elif page == PAGE_FORM:
    render_form()
elif page == PAGE_ADMIN:
    render_admin()
