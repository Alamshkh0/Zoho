"""Redington Zoho CRM Discovery — Streamlit app.

Run:    streamlit run app.py
Deploy: push to GitHub -> https://share.streamlit.io
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import config
import db
import reports
import suggestions as sg
import analysis as A

st.set_page_config(
    page_title="Redington Zoho CRM Discovery",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="auto",
)

# ---------- Global CSS ----------
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1240px;}
    h1, h2, h3 { color: #1A1A1A; letter-spacing: -0.01em;}
    h1 { font-weight: 800;}

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #C8102E 0%, #8A0B20 60%, #1A1A1A 100%);
        color: white; border-radius: 18px; padding: 28px 32px; margin-bottom: 18px;
        box-shadow: 0 10px 30px rgba(200,16,46,.18);
    }
    .hero .kicker { font-size: 12px; letter-spacing: 2px; text-transform: uppercase; opacity: .85;}
    .hero h1 { color: white; font-size: 2.1rem; margin: 6px 0 8px 0;}
    .hero p  { color: rgba(255,255,255,.92); font-size: 1.02rem; margin: 0; max-width: 720px; line-height: 1.55;}

    /* Stat cards */
    .stat-card {
        background: linear-gradient(135deg, #FFFFFF, #FAFAFA);
        border: 1px solid #EEE; border-radius: 14px; padding: 18px 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,.04);
    }
    .stat-card:hover { box-shadow: 0 6px 18px rgba(200,16,46,.10); transform: translateY(-1px); transition: all .15s;}
    .pill {
        display: inline-block; padding: 3px 12px; border-radius: 999px;
        background: #FCE3E6; color: #C8102E; font-size: 11px; font-weight: 700; letter-spacing: 1px;
    }
    .pill-grey { background: #EEE; color: #555;}
    .pill-blue { background: #E8F4FD; color: #0F4C81;}

    /* KPI metric tweaks */
    div[data-testid="stMetricValue"] { color: #C8102E; font-weight: 800; font-size: 2rem;}
    div[data-testid="stMetricLabel"] { color: #555; font-weight: 500;}
    div[data-testid="stMetricDelta"] svg { display: none;}

    /* Buttons */
    div.stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #C8102E, #A50D26);
        border: 0; color: white; font-weight: 700; padding: 10px 16px; border-radius: 10px;
    }
    div.stButton>button[kind="primary"]:hover { background: linear-gradient(135deg, #A50D26, #8A0B20);}
    div.stButton>button {
        border-radius: 10px; border: 1px solid #DDD; font-weight: 500;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap;}
    .stTabs [data-baseweb="tab"] {
        height: 42px; padding: 0 16px; background: #F5F5F5; border-radius: 10px 10px 0 0;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background: #C8102E !important; color: white !important;}

    /* Section intro card */
    .section-intro {
        background: #FAFAFA; border-left: 4px solid #C8102E; border-radius: 6px;
        padding: 14px 18px; margin-bottom: 16px; color: #333; line-height: 1.55;
    }

    /* Mobile */
    @media (max-width: 640px) {
        .block-container { padding: 0.6rem 0.5rem 1.5rem 0.5rem;}
        .hero { padding: 18px 18px;}
        .hero h1 { font-size: 1.4rem;}
        .hero p { font-size: 0.92rem;}
        h1 { font-size: 1.5rem;}
        div[data-testid="stMetricValue"] { font-size: 1.5rem;}
    }
</style>
""", unsafe_allow_html=True)


# ---------- Session-state ----------
def _init_state():
    defaults = {
        "contributor_id": None,
        "brand": None, "name": "", "email": "", "role": "PAM",
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
    done = sum(1 for sk, sv in SECTION_STATE_KEYS.items()
               if A._section_filled(st.session_state.get(sv) or {}, sk))
    return int(round(100 * done / len(SECTION_STATE_KEYS)))


# ---------- Sidebar ----------
PAGE_INTRO = "🏁 Start"
PAGE_FORM  = "📝 Discovery Form"
PAGE_ADMIN = "🔒 Admin & Reports"

with st.sidebar:
    st.markdown("### 📋 Redington")
    st.caption("Zoho CRM Discovery")
    page = st.radio("Navigate", [PAGE_INTRO, PAGE_FORM, PAGE_ADMIN], index=0, label_visibility="collapsed")
    st.markdown("---")
    if st.session_state.contributor_id:
        st.success(f"**{st.session_state.name}**\n\n📛 {st.session_state.role}\n\n🏷️ {st.session_state.brand}")
        st.progress(_completion_pct() / 100, text=f"{_completion_pct()}% complete")
    else:
        st.info("Start a session →")
    st.markdown("---")
    st.markdown("##### 📚 Quick guide")
    st.caption("**1. Start** — pick your brand and identify yourself.\n\n**2. Form** — eight tabs. Use 'Load suggestions' for starter fields, then tailor freely.\n\n**3. Save** — your email is the key. Come back anytime to edit.")


# =====================================================================
# Page 1 — Start
# =====================================================================
def render_intro():
    # Hero
    st.markdown("""
<div class="hero">
  <div class="kicker">REDINGTON · CLOUD & AI PRACTICE</div>
  <h1>📋 Zoho CRM Discovery — Brand by Brand</h1>
  <p>A structured way to capture <b>what every brand needs</b> from Zoho CRM before we hand off to the implementation team.
  Each brand (Red Hat, AWS, Microsoft …) defines its own fields, workflow, approvals, dashboards, integrations and data sources —
  because every practice is different. Multiple stakeholders contribute; the system merges everything into a single
  branded requirements pack (PDF / Word / CSV).</p>
</div>
""", unsafe_allow_html=True)

    # Objective & how-it-works in 3 cards
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""<div class='stat-card'>
<span class='pill'>OBJECTIVE</span>
<h4 style='margin-top:10px'>Capture the truth, brand by brand</h4>
<p style='color:#555; font-size:14px; line-height:1.55'>
Avoid one-size-fits-all assumptions. Capture each brand's real-world fields, workflows, and dashboards directly from the people who run the business.
</p></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class='stat-card'>
<span class='pill pill-blue'>APPROACH</span>
<h4 style='margin-top:10px'>Multi-contributor, mergeable</h4>
<p style='color:#555; font-size:14px; line-height:1.55'>
PAM, BSM, PM and Pre-sales each fill the form for their brand. One email = one row; same email returns to your draft and lets you edit.
</p></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class='stat-card'>
<span class='pill pill-grey'>OUTCOME</span>
<h4 style='margin-top:10px'>Branded handover pack</h4>
<p style='color:#555; font-size:14px; line-height:1.55'>
A polished PDF + Word + CSV per brand, plus auto-generated insights, conflicts, recommendations, and integration / data-source maps for the Zoho team.
</p></div>""", unsafe_allow_html=True)

    st.markdown("### 📊 Live brand stats")
    st.caption("How many contributors per brand have started so far.")
    try:
        counts = db.count_contributors_per_brand()
    except Exception:
        counts = {}
    cols = st.columns(len(config.BRANDS))
    for i, b in enumerate(config.BRANDS):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"<span class='pill'>BRAND</span>", unsafe_allow_html=True)
                st.markdown(f"### {b}")
                st.metric("Contributors", counts.get(b, 0))

    st.markdown("---")
    st.markdown("### 🚀 Start or resume your contribution")
    st.caption("Use the **same email** later to come back and edit. Multiple roles per brand can contribute — answers merge.")

    c1, c2 = st.columns(2)
    with c1:
        brand = st.selectbox("Brand", config.BRANDS, index=0)
        name  = st.text_input("Your full name", value=st.session_state.name, placeholder="e.g. Alam Shaikh")
    with c2:
        role  = st.selectbox("Your role", config.ROLES, index=config.ROLES.index(st.session_state.role) if st.session_state.role in config.ROLES else 0)
        email = st.text_input("Email (used to resume your session)", value=st.session_state.email, placeholder="you@redington.com")

    if email and brand:
        try:
            existing = db.find_contributor_by_email(brand, email)
            if existing:
                st.info(f"🔁 Found a previous submission for **{email}** on **{brand}** — last update {existing['submitted_at'][:19].replace('T',' ')}. Click below to **resume** — your earlier answers reload automatically.")
        except Exception:
            pass

    if st.button("➡️ Start / Resume session", type="primary", use_container_width=True):
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email."); return
        try:
            row = db.upsert_contributor(brand, name.strip(), email.strip(), role)
        except Exception as e:
            st.error(f"Could not connect to database. Check that schema.sql was run in Supabase. Error: {e}"); return
        st.session_state.contributor_id = row["id"]
        st.session_state.brand = brand
        st.session_state.name = name.strip()
        st.session_state.email = email.strip()
        st.session_state.role = role
        _load_responses_into_state(row["id"])
        st.success("✅ Session ready — open **📝 Discovery Form** in the sidebar.")
        st.balloons()


# =====================================================================
# Field-builder UI
# =====================================================================
# Defensive: fall back if a stale deployed config.py is missing DATA_SOURCES
_DATA_SOURCES = getattr(config, "DATA_SOURCES",
    ["Manual", "CQ", "SAP", "AWS ACE", "Microsoft Partner Center", "Salesforce", "API", "Other"])
_FIELD_TYPES  = getattr(config, "FIELD_TYPES",
    ["Text", "Number", "Date", "Dropdown", "Multi-select", "Yes/No"])

FIELD_COLUMNS = {
    "field":               st.column_config.TextColumn("Field name", required=True),
    "type":                st.column_config.SelectboxColumn("Type", options=_FIELD_TYPES, required=True),
    "options":             st.column_config.TextColumn("Options"),
    "mandatory":           st.column_config.CheckboxColumn("Mand.?"),
    "integration_needed":  st.column_config.CheckboxColumn("🔌 Integ.?"),
    "data_capture_source": st.column_config.SelectboxColumn("📥 Source", options=_DATA_SOURCES),
    "conditional_rule":    st.column_config.TextColumn("Conditional / business rule"),
}


def _ensure_new_columns(rows: list[dict]) -> list[dict]:
    """Backfill the new columns onto any row that came from old saved data."""
    for r in rows:
        r.setdefault("integration_needed", False)
        r.setdefault("data_capture_source", "Manual")
    return rows


def _field_builder(label: str, state_key: str, suggestion_pool: list[dict], help_text: str = "") -> list[dict]:
    st.markdown(f"#### {label}")
    if help_text: st.caption(help_text)
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if suggestion_pool and st.button("➕ Load suggestions", key=f"load_{state_key}"):
            existing = _ensure_new_columns(st.session_state[state_key].get("fields", []))
            existing_names = {f.get("field", "").strip().lower() for f in existing}
            for s in suggestion_pool:
                if s["field"].strip().lower() not in existing_names:
                    existing.append(dict(s))
            st.session_state[state_key]["fields"] = existing
            st.rerun()
    with cols[1]:
        if st.button("🗑️ Clear all", key=f"clear_{state_key}"):
            st.session_state[state_key]["fields"] = []
            st.rerun()

    rows = _ensure_new_columns(st.session_state[state_key].get("fields", []))
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(FIELD_COLUMNS.keys()))
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True,
        column_config=FIELD_COLUMNS, key=f"editor_{state_key}", hide_index=True,
    )
    fields = edited.to_dict(orient="records")
    st.session_state[state_key]["fields"] = fields
    return fields


def _intro(text: str):
    st.markdown(f"<div class='section-intro'>{text}</div>", unsafe_allow_html=True)


# =====================================================================
# Page 2 — Form
# =====================================================================
def render_form():
    if not st.session_state.contributor_id:
        st.warning("Please start a session first (sidebar → 🏁 Start)."); return

    st.markdown(f"""
<div class='hero' style='padding:20px 24px'>
  <div class='kicker'>BRAND DISCOVERY</div>
  <h1 style='font-size:1.6rem; margin:4px 0 6px 0'>📝 {st.session_state.brand} — Discovery Form</h1>
  <p>Contributing as <b>{st.session_state.name}</b> ({st.session_state.role}). Eight sections — fill what you know,
  skip what you don't, hit <b>Save & Submit</b> at the bottom. You can come back anytime with the same email.</p>
</div>
""", unsafe_allow_html=True)

    pct = _completion_pct()
    k1, k2, k3, k4 = st.columns(4)
    sections_done = sum(1 for sk,sv in SECTION_STATE_KEYS.items() if A._section_filled(st.session_state.get(sv) or {}, sk))
    fld_count = sum(len((st.session_state.get(sv) or {}).get('fields', []) or [])
                    for sk,sv in SECTION_STATE_KEYS.items() if sk in A.FIELD_BUILDER_SECTIONS)
    integ_count = sum(1 for sk,sv in SECTION_STATE_KEYS.items() if sk in A.FIELD_BUILDER_SECTIONS
                      for f in ((st.session_state.get(sv) or {}).get('fields') or []) if f.get('integration_needed'))
    k1.metric("✅ Completion", f"{pct}%")
    k2.metric("📂 Sections done", f"{sections_done} / {len(SECTION_STATE_KEYS)}")
    k3.metric("🧱 Fields proposed", fld_count)
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
        _intro("""<b>Why this section matters</b> — Zoho needs to know <i>who</i> uses the system, in <i>what role</i>, and <i>who signs off</i> on configuration changes.
        Capture the human side of the brand: lead, decision-maker, contributing roles, and rough user counts.
        This drives license counts, role-based permissions, and stakeholder communication for the rollout.""")
        s = st.session_state.sec_people
        c1, c2 = st.columns(2)
        with c1:
            s["brand_lead_name"]  = st.text_input("Brand lead name",  value=s.get("brand_lead_name", ""))
            s["decision_maker"]   = st.text_input("Decision-maker / sign-off", value=s.get("decision_maker", ""))
            s["daily_users"]      = st.text_input("Approx. daily users",      value=s.get("daily_users", ""))
        with c2:
            s["brand_lead_email"] = st.text_input("Brand lead email", value=s.get("brand_lead_email", ""))
            s["roles_involved"]   = st.multiselect("Roles involved", config.ROLES, default=s.get("roles_involved", []))
            s["occasional_users"] = st.text_input("Approx. occasional users",  value=s.get("occasional_users", ""))
        s["notes"] = st.text_area("Anything else about the people side?", value=s.get("notes", ""), height=80)

    # B. Partner 360
    with tabs[1]:
        _intro("""<b>Partner 360</b> — the master partner record, shared across every brand.
        Capture the fields you need on every partner (name, type, tier, region, certifications, …),
        whether each one is mandatory, whether it needs <b>integration</b> from another system, and the
        <b>data-capture source</b> (Manual entry, CQ, SAP, AWS ACE, etc.). This becomes the source-of-truth
        contract for partner master data.""")
        _field_builder(
            "Partner 360 — Fields", "sec_partner_360", sg.PARTNER_360_FIELDS,
            "Use 'Load suggestions' for common starter fields, then edit/delete/add freely.",
        )
        st.session_state.sec_partner_360["notes"] = st.text_area(
            "Notes (source of truth, dedup approach, hierarchy)",
            value=st.session_state.sec_partner_360.get("notes", ""), height=80,
        )

    # C. Customer 360
    with tabs[2]:
        _intro("""<b>Customer 360</b> — the master customer / end-user record, shared across brands.
        Same idea as Partner 360 but for customers: name, industry, size, key contacts, hierarchy, renewals.
        For each field, also flag whether it must be integrated and where the data lives today.""")
        _field_builder(
            "Customer 360 — Fields", "sec_customer_360", sg.CUSTOMER_360_FIELDS,
            "Capture mandatory fields, hierarchy needs (parent/child accounts), and brand-specific extensions.",
        )
        st.session_state.sec_customer_360["notes"] = st.text_area(
            "Notes (renewals, hierarchies, dedup)",
            value=st.session_state.sec_customer_360.get("notes", ""), height=80,
        )

    # D. Sales / Opportunity
    with tabs[3]:
        _intro("""<b>Sales — Opportunity / Lead / Deal</b>: three sub-sections.
        Define the fields Zoho should capture on each opportunity. The Red Hat starter is partner-funnel-shaped
        (Neutral → Upside → Strong Upside → Commit), the AWS starter is project-shaped
        (Customer details → Project details with sales-activity progression).
        <b>Mix and match — every brand owns its own structure.</b> Don't forget integration flag + data source on every field.""")

        with st.expander("**D1. Opportunity Details**", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Use Red Hat starter (Opportunity)", key="seed_redhat_d1"):
                    e = _ensure_new_columns(st.session_state.sec_sales_opp_details.get("fields", [])); names = {f.get("field","").lower() for f in e}
                    for s in sg.REDHAT_OPPORTUNITY_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = e; st.rerun()
            with c2:
                if st.button("Use AWS starter (Customer)", key="seed_aws_d1"):
                    e = _ensure_new_columns(st.session_state.sec_sales_opp_details.get("fields", [])); names = {f.get("field","").lower() for f in e}
                    for s in sg.AWS_CUSTOMER_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = e; st.rerun()
            _field_builder("Opportunity Details fields", "sec_sales_opp_details", [], "")
            st.session_state.sec_sales_opp_details["notes"] = st.text_area(
                "Notes — D1", value=st.session_state.sec_sales_opp_details.get("notes", ""), height=70, key="notes_d1")

        with st.expander("**D2. Opportunity Contact Details**", expanded=False):
            if st.button("Use Red Hat starter (Contacts)", key="seed_redhat_d2"):
                e = _ensure_new_columns(st.session_state.sec_sales_contact_details.get("fields", [])); names = {f.get("field","").lower() for f in e}
                for s in sg.REDHAT_CONTACT_DETAILS:
                    if s["field"].lower() not in names: e.append(dict(s))
                st.session_state.sec_sales_contact_details["fields"] = e; st.rerun()
            _field_builder("Contact Details fields", "sec_sales_contact_details", [], "People involved (PAM, BSM, PM, Pre-sales).")
            st.session_state.sec_sales_contact_details["notes"] = st.text_area(
                "Notes — D2", value=st.session_state.sec_sales_contact_details.get("notes", ""), height=70, key="notes_d2")

        with st.expander("**D3. Opportunity Deal Details**", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Use Red Hat starter (Deal)", key="seed_redhat_d3"):
                    e = _ensure_new_columns(st.session_state.sec_sales_deal_details.get("fields", [])); names = {f.get("field","").lower() for f in e}
                    for s in sg.REDHAT_DEAL_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = e; st.rerun()
            with c2:
                if st.button("Use AWS starter (Project)", key="seed_aws_d3"):
                    e = _ensure_new_columns(st.session_state.sec_sales_deal_details.get("fields", [])); names = {f.get("field","").lower() for f in e}
                    for s in sg.AWS_PROJECT_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = e; st.rerun()
            _field_builder("Deal Details fields", "sec_sales_deal_details", [], "Commercials, products, services, target close date.")
            st.session_state.sec_sales_deal_details["notes"] = st.text_area(
                "Notes — D3", value=st.session_state.sec_sales_deal_details.get("notes", ""), height=70, key="notes_d3")

    # E. Approvals
    with tabs[4]:
        _intro("""<b>Approval workflow</b> — every brand has different rules for when an opportunity needs approval
        (deal value, discount, special pricing, credit). Define stages, approvers, triggers, SLAs, and whether a stage
        can be reverted. Zoho turns this into the actual workflow rules; missing data here is the #1 cause of delayed go-lives.""")
        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("➕ Load suggestions", key="load_approvals"):
                e = st.session_state.sec_approvals.get("stages", []); names = {s.get("stage","").lower() for s in e}
                for s in sg.APPROVAL_STAGE_SUGGESTIONS:
                    if s["stage"].lower() not in names: e.append(dict(s))
                st.session_state.sec_approvals["stages"] = e; st.rerun()
        with c2:
            if st.button("🗑️ Clear all", key="clear_approvals"):
                st.session_state.sec_approvals["stages"] = []; st.rerun()
        rows = st.session_state.sec_approvals.get("stages", [])
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["stage","approver","trigger","sla_hours","can_revert"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key="editor_approvals", hide_index=True,
            column_config={
                "stage":      st.column_config.TextColumn("Stage", required=True),
                "approver":   st.column_config.TextColumn("Approver / Role"),
                "trigger":    st.column_config.TextColumn("Trigger / Condition"),
                "sla_hours":  st.column_config.NumberColumn("SLA (h)", min_value=0, step=1),
                "can_revert": st.column_config.CheckboxColumn("Revert?"),
            },
        )
        st.session_state.sec_approvals["stages"]     = edited.to_dict(orient="records")
        st.session_state.sec_approvals["escalation"] = st.text_area("Escalation rules (what if SLA breached?)", value=st.session_state.sec_approvals.get("escalation", ""), height=80)
        st.session_state.sec_approvals["notes"]      = st.text_area("Other workflow notes", value=st.session_state.sec_approvals.get("notes", ""), height=80)

    # F. Dashboards
    with tabs[5]:
        _intro("""<b>Dashboards & reports</b> — the views people actually look at every day.
        List every dashboard the team needs (Pipeline by stage, Renewal vs Net New, Forecast, Margin %, etc.),
        who watches it, and how often. <b>Without dashboards listed, Zoho cannot validate the data model supports reporting</b>.""")
        c1, c2 = st.columns([1, 5])
        with c1:
            if st.button("➕ Load suggestions", key="load_dash"):
                e = st.session_state.sec_dashboards.get("dashboards", []); names = {d.get("dashboard","").lower() for d in e}
                for s in sg.DASHBOARD_SUGGESTIONS:
                    if s["dashboard"].lower() not in names: e.append(dict(s))
                st.session_state.sec_dashboards["dashboards"] = e; st.rerun()
        with c2:
            if st.button("🗑️ Clear all", key="clear_dash"):
                st.session_state.sec_dashboards["dashboards"] = []; st.rerun()
        rows = st.session_state.sec_dashboards.get("dashboards", [])
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["dashboard","audience","frequency"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key="editor_dash", hide_index=True,
            column_config={
                "dashboard": st.column_config.TextColumn("Dashboard / Report", required=True),
                "audience":  st.column_config.TextColumn("Audience (roles)"),
                "frequency": st.column_config.SelectboxColumn("Frequency", options=["Real-time","Daily","Weekly","Monthly","Quarterly","On-demand"]),
            },
        )
        st.session_state.sec_dashboards["dashboards"] = edited.to_dict(orient="records")
        st.session_state.sec_dashboards["notes"]      = st.text_area("Notes (exports, drill-downs, scheduled emails)", value=st.session_state.sec_dashboards.get("notes", ""), height=80)

    # G. Best Practices
    with tabs[6]:
        _intro("""<b>Best-practice inputs</b> — captured as recommendations the Zoho team should keep in mind, not for deep config in v1.
        Note your data-hygiene asks (dedup rules, mandatory enforcement, naming conventions), the integrations you'll want eventually,
        and SOPs that need to be documented post-rollout.""")
        s = st.session_state.sec_best_practices
        s["data_hygiene"]          = st.text_area("Data-hygiene asks (dedup, mandatory rules, naming)", value=s.get("data_hygiene", ""), height=110)
        s["integrations_wishlist"] = st.text_area("Integrations wishlist (Zoho ↔ ERP / Outlook / Teams / vendor portals)", value=s.get("integrations_wishlist", ""), height=110)
        s["dedup_sops"]            = st.text_area("SOPs to document later (lead→opp, partner onboarding, customer creation)", value=s.get("dedup_sops", ""), height=110)
        with st.expander("💡 Common additional clauses (copy/paste if relevant)"):
            for c in sg.ADDITIONAL_CLAUSE_SUGGESTIONS:
                st.markdown(f"- {c}")

    # H. Open Notes
    with tabs[7]:
        _intro("""<b>Open notes</b> — the qualitative side. Pain points with the current tool are gold for Zoho;
        they tell the team what NOT to repeat. Must-haves, nice-to-haves, risks, and direct questions for the implementation team also go here.""")
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
                for sec_key, state_key in SECTION_STATE_KEYS.items():
                    db.save_response(st.session_state.contributor_id, sec_key, st.session_state.get(state_key) or {})
                st.success("✅ Saved. You can keep editing — your email is the key, just come back anytime.")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with info:
        st.info("💡 Use the **same email** later to come back and edit. Multiple roles per brand contribute — answers merge into one report.")


# =====================================================================
# Page 3 — Admin
# =====================================================================
def render_admin():
    if not st.session_state.admin_unlocked:
        st.markdown("""
<div class='hero' style='padding:22px 26px'>
  <div class='kicker'>ADMIN DASHBOARD</div>
  <h1 style='font-size:1.6rem; margin:4px 0 6px 0'>🔒 Brand Insights & Reports</h1>
  <p>Per-brand KPIs, charts (fields per section, mandatory %, integration intensity, data-source mix, brand-readiness radar),
  auto-detected conflicts between contributors, rules-based recommendations, and downloadable PDF / Word / CSV requirement packs.
  Cross-brand comparison is in the second tab.</p>
</div>
""", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("Enter the admin passcode to unlock the dashboard.")
            pc = st.text_input("Admin passcode", type="password")
            if st.button("Unlock", type="primary"):
                if pc == config.ADMIN_PASSCODE:
                    st.session_state.admin_unlocked = True; st.rerun()
                else:
                    st.error("Wrong passcode.")
        return

    st.markdown("""
<div class='hero' style='padding:22px 26px'>
  <div class='kicker'>ADMIN DASHBOARD</div>
  <h1 style='font-size:1.6rem; margin:4px 0 6px 0'>🔒 Brand Insights & Reports</h1>
  <p>Pick a brand below to see live metrics, charts, conflicts, and recommendations — and download the branded handover pack.</p>
</div>
""", unsafe_allow_html=True)

    tab_brand, tab_compare = st.tabs(["📊 Brand Dashboard", "🔄 Cross-Brand Comparison"])

    # ---------- Brand Dashboard ----------
    with tab_brand:
        brand = st.selectbox("Brand", config.BRANDS)
        try:
            bundle = db.get_brand_bundle(brand)
        except Exception as e:
            st.error(f"DB error: {e}"); return
        metrics    = A.compute_metrics(bundle)
        conflicts  = A.detect_conflicts(bundle)
        recs       = A.generate_recommendations(bundle, metrics, conflicts)

        st.subheader(f"Brand — {brand}")
        st.caption(f"Generated {bundle['generated_at']} · {len(bundle['contributors'])} contributor(s)")

        # KPI strip — 6 metrics
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("👥 Contributors",    metrics["contributors"])
        c2.metric("🧱 Fields",          metrics["total_fields"])
        c3.metric("✅ Mandatory",       f"{metrics['mandatory_pct']}%")
        c4.metric("🔌 Integration",     f"{metrics['integration_pct']}%")
        c5.metric("🔁 Approvals",       metrics["approval_stages"])
        c6.metric("📊 Dashboards",      metrics["dashboards"])

        st.progress(metrics["completion_pct"] / 100, text=f"Section completion: {metrics['completion_pct']}%   ·   Brand readiness: {A.overall_readiness_pct(metrics):.0f}/100")

        if not bundle["contributors"]:
            st.warning("No contributors yet for this brand."); return

        # Row 1 charts: fields per section + mandatory %
        cc1, cc2 = st.columns(2)
        with cc1:
            data = A.fields_per_section_count(bundle)
            df = pd.DataFrame({"Section": list(data.keys()), "Fields": list(data.values())})
            fig = px.bar(df, x="Section", y="Fields", color_discrete_sequence=["#C8102E"], title="Fields proposed per section")
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0), plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        with cc2:
            data = A.mandatory_per_section_pct(bundle)
            df = pd.DataFrame({"Section": list(data.keys()), "Mandatory %": list(data.values())})
            fig = px.bar(df, x="Mandatory %", y="Section", orientation="h", color_discrete_sequence=["#1A1A1A"], title="Mandatory % per section")
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0), plot_bgcolor="white", xaxis_range=[0,100])
            st.plotly_chart(fig, use_container_width=True)

        # Row 2: integration % + source breakdown + readiness radar
        cc1, cc2, cc3 = st.columns([1, 1, 1])
        with cc1:
            data = A.integration_per_section_pct(bundle)
            df = pd.DataFrame({"Section": list(data.keys()), "Integration %": list(data.values())})
            fig = px.bar(df, x="Integration %", y="Section", orientation="h", color_discrete_sequence=["#0F4C81"], title="Integration intensity per section")
            fig.update_layout(height=340, margin=dict(l=0,r=0,t=40,b=0), plot_bgcolor="white", xaxis_range=[0,100])
            st.plotly_chart(fig, use_container_width=True)
        with cc2:
            data = A.data_source_breakdown(bundle) or {"No data": 1}
            df = pd.DataFrame({"Source": list(data.keys()), "Count": list(data.values())})
            fig = px.pie(df, names="Source", values="Count", hole=.5,
                         color_discrete_sequence=["#C8102E","#1A1A1A","#0F4C81","#E07B00","#2E7D32","#6A1B9A","#888888","#5D4037"],
                         title="Data-capture source mix")
            fig.update_layout(height=340, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with cc3:
            scores = A.readiness_scores(metrics)
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=list(scores.values()) + [list(scores.values())[0]],
                theta=list(scores.keys()) + [list(scores.keys())[0]],
                fill="toself", line_color="#C8102E", fillcolor="rgba(200,16,46,0.20)", name="Readiness",
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                showlegend=False, height=340, margin=dict(l=20,r=20,t=40,b=20),
                title=f"Brand readiness — {A.overall_readiness_pct(metrics):.0f}/100",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Conflicts + Recommendations side-by-side
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("### 🚨 Conflicts to resolve")
            st.caption("Where contributors disagree on mandatory, integration, source, or SLA.")
            if conflicts:
                st.dataframe(pd.DataFrame(conflicts), use_container_width=True, hide_index=True)
            else:
                st.success("No conflicts detected between contributors.")
        with cc2:
            st.markdown("### 💡 Insights & Recommendations")
            st.caption("Auto-generated. Color-coded by priority.")
            if recs:
                rdf = pd.DataFrame(recs)
                color_map = {"High":"#FCE3E6","Medium":"#FFF4E0","Low":"#E8F4FD","Info":"#EAF7EE"}
                styled = rdf.style.apply(lambda r: [f"background-color: {color_map.get(r['priority'], '#FFF')}"] * len(r), axis=1)
                st.dataframe(styled, use_container_width=True, hide_index=True)

        # Contributors
        st.markdown("### 👥 Contributors")
        cdf = pd.DataFrame([{
            "Name": c["name"], "Role": c["role"], "Email": c["email"],
            "Last update": c["submitted_at"][:19].replace("T"," "),
        } for c in bundle["contributors"]])
        st.dataframe(cdf, use_container_width=True, hide_index=True)

        # Downloads
        st.markdown("### 📥 Download requirements pack")
        st.caption("Polished PDF (cover, KPIs, charts, conflicts, recommendations, full detail) · editable Word · long-format CSV.")
        d1, d2, d3 = st.columns(3)
        with d1:
            st.download_button("⬇️ PDF",  data=reports.build_pdf(bundle),  file_name=f"Redington_Discovery_{brand}.pdf",  mime="application/pdf",  use_container_width=True)
        with d2:
            st.download_button("⬇️ Word", data=reports.build_docx(bundle), file_name=f"Redington_Discovery_{brand}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
        with d3:
            st.download_button("⬇️ CSV",  data=reports.build_csv(bundle),  file_name=f"Redington_Discovery_{brand}.csv",  mime="text/csv",         use_container_width=True)

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

    # ---------- Cross-brand comparison ----------
    with tab_compare:
        st.subheader("🔄 Cross-brand comparison")
        st.caption("Side-by-side view across every brand to spot alignment and divergence.")
        bundles = []
        for b in config.BRANDS:
            try: bundles.append(db.get_brand_bundle(b))
            except Exception: pass
        rows = []
        for b in bundles:
            m = A.compute_metrics(b)
            rows.append({"Brand": b["brand"], "Contributors": m["contributors"], "Fields": m["total_fields"],
                         "Mandatory %": m["mandatory_pct"], "Integration %": m["integration_pct"],
                         "Approvals": m["approval_stages"], "Dashboards": m["dashboards"],
                         "Completion %": m["completion_pct"],
                         "Readiness /100": A.overall_readiness_pct(m)})
        cdf = pd.DataFrame(rows)
        st.dataframe(cdf, use_container_width=True, hide_index=True)

        if not cdf.empty:
            fig = px.bar(cdf, x="Brand", y=["Contributors","Fields","Approvals","Dashboards"], barmode="group",
                         title="Brand-by-brand totals",
                         color_discrete_sequence=["#C8102E", "#1A1A1A", "#0F4C81", "#E07B00"])
            fig.update_layout(height=380, margin=dict(l=0,r=0,t=40,b=0), plot_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)

            cc1, cc2 = st.columns(2)
            with cc1:
                fig2 = px.bar(cdf, x="Brand", y="Completion %", color_discrete_sequence=["#C8102E"], title="Section-completion %")
                fig2.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0), yaxis_range=[0,100], plot_bgcolor="white")
                st.plotly_chart(fig2, use_container_width=True)
            with cc2:
                fig3 = px.bar(cdf, x="Brand", y="Readiness /100", color_discrete_sequence=["#0F4C81"], title="Brand readiness score")
                fig3.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0), yaxis_range=[0,100], plot_bgcolor="white")
                st.plotly_chart(fig3, use_container_width=True)

            # Cross-brand readiness radar
            radar = go.Figure()
            for b in bundles:
                m = A.compute_metrics(b); s = A.readiness_scores(m)
                radar.add_trace(go.Scatterpolar(
                    r=list(s.values()) + [list(s.values())[0]],
                    theta=list(s.keys()) + [list(s.keys())[0]],
                    fill="toself", name=b["brand"], opacity=0.5,
                ))
            radar.update_layout(
                polar=dict(radialaxis=dict(range=[0, 100], visible=True)),
                title="Cross-brand readiness radar", height=440, margin=dict(l=20,r=20,t=40,b=20),
            )
            st.plotly_chart(radar, use_container_width=True)

        st.download_button(
            "⬇️ Download cross-brand CSV",
            data=reports.build_cross_brand_csv(bundles),
            file_name="Redington_Discovery_AllBrands.csv", mime="text/csv",
        )


# ---------- Router ----------
if page == PAGE_INTRO:
    render_intro()
elif page == PAGE_FORM:
    render_form()
elif page == PAGE_ADMIN:
    render_admin()
