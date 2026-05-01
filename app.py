"""Redington Zoho CRM Discovery — Streamlit app.

Run:    streamlit run app.py
Deploy: push to GitHub -> https://share.streamlit.io
"""
import pandas as pd
import plotly.express as px
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

# --- Light global style polish (mobile + visual) ---
st.markdown("""
<style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1200px;}
    h1, h2, h3 { color: #1A1A1A;}
    div[data-testid="stMetricValue"] { color: #C8102E; font-weight: 700;}
    div[data-testid="stMetricLabel"] { color: #555;}
    div.stButton>button[kind="primary"] {
        background: #C8102E; border: 0; font-weight: 600;
    }
    div.stButton>button[kind="primary"]:hover { background: #A50D26;}
    .brand-card {
        border: 1px solid #EEE; border-radius: 12px; padding: 14px 16px;
        background: linear-gradient(135deg, #FFF, #FAFAFA);
        box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }
    .pill {
        display: inline-block; padding: 2px 10px; border-radius: 999px;
        background: #FCE3E6; color: #C8102E; font-size: 12px; font-weight: 600;
    }
    @media (max-width: 640px) {
        .block-container { padding-left: 0.6rem; padding-right: 0.6rem;}
        h1 { font-size: 1.5rem;}
    }
</style>
""", unsafe_allow_html=True)


# ---------- Session-state ----------
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
    """Per-current-user form completion %."""
    done = 0
    total = len(SECTION_STATE_KEYS)
    for sec_key, state_key in SECTION_STATE_KEYS.items():
        payload = st.session_state.get(state_key) or {}
        if A._section_filled(payload, sec_key):
            done += 1
    return int(round(100 * done / total))


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


# =====================================================================
# Page 1 — Start (with built-in resume)
# =====================================================================
def _stat_for_brand(counts: dict[str, int], b: str) -> int:
    return counts.get(b, 0)


def render_intro():
    st.title("📋 Redington Zoho CRM — Discovery")
    st.caption("Brand-by-brand requirements gathering for Zoho CRM rollout.")

    # Brand stat cards
    try:
        counts = db.count_contributors_per_brand()
    except Exception:
        counts = {}
    cols = st.columns(len(config.BRANDS))
    for i, b in enumerate(config.BRANDS):
        with cols[i]:
            with st.container(border=True):
                st.markdown(f"<div class='pill'>BRAND</div>", unsafe_allow_html=True)
                st.markdown(f"### {b}")
                st.metric("Contributors so far", _stat_for_brand(counts, b))

    st.markdown("---")
    st.markdown("""
**How it works** — pick your brand, tell us who you are, then fill the form. **Use the same email** later to **resume / edit**. Multiple roles per brand can contribute; their inputs merge into one requirements pack.
""")

    st.subheader("Start or resume your contribution")
    c1, c2 = st.columns([1, 1])
    with c1:
        brand = st.selectbox("Brand", config.BRANDS, index=0)
        name  = st.text_input("Your full name", value=st.session_state.name)
    with c2:
        role  = st.selectbox("Your role", config.ROLES, index=config.ROLES.index(st.session_state.role) if st.session_state.role in config.ROLES else 0)
        email = st.text_input("Email (used to resume your session)", value=st.session_state.email)

    # Live resume hint
    if email and brand:
        try:
            existing = db.find_contributor_by_email(brand, email)
            if existing:
                st.info(f"🔁 Found a previous submission for **{email}** on **{brand}** (last update {existing['submitted_at'][:19].replace('T',' ')}). Click the button below to resume — your earlier answers will reload automatically.")
        except Exception:
            pass

    btn_label = "➡️ Start / Resume session"
    if st.button(btn_label, type="primary", use_container_width=True):
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email.")
            return
        try:
            row = db.upsert_contributor(brand, name.strip(), email.strip(), role)
        except Exception as e:
            st.error(f"Could not connect to database. Check that schema.sql was run in Supabase. Error: {e}")
            return
        st.session_state.contributor_id = row["id"]
        st.session_state.brand = brand
        st.session_state.name = name.strip()
        st.session_state.email = email.strip()
        st.session_state.role = role
        _load_responses_into_state(row["id"])
        st.success("✅ Session ready — open **Discovery Form** in the sidebar.")
        st.balloons()


# =====================================================================
# Field-builder UI
# =====================================================================
FIELD_COLUMNS = {
    "field":            st.column_config.TextColumn("Field name", required=True),
    "type":             st.column_config.SelectboxColumn("Type", options=config.FIELD_TYPES, required=True),
    "options":          st.column_config.TextColumn("Options"),
    "mandatory":        st.column_config.CheckboxColumn("Mand.?"),
    "conditional_rule": st.column_config.TextColumn("Conditional / business rule"),
}


def _field_builder(label: str, state_key: str, suggestion_pool: list[dict], help_text: str = "") -> list[dict]:
    st.markdown(f"#### {label}")
    if help_text: st.caption(help_text)
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if suggestion_pool and st.button("➕ Load suggestions", key=f"load_{state_key}"):
            existing = st.session_state[state_key].get("fields", [])
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

    rows = st.session_state[state_key].get("fields", [])
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=list(FIELD_COLUMNS.keys()))
    edited = st.data_editor(
        df, num_rows="dynamic", use_container_width=True,
        column_config=FIELD_COLUMNS, key=f"editor_{state_key}", hide_index=True,
    )
    fields = edited.to_dict(orient="records")
    st.session_state[state_key]["fields"] = fields
    return fields


# =====================================================================
# Page 2 — Form
# =====================================================================
def render_form():
    if not st.session_state.contributor_id:
        st.warning("Please start a session first (sidebar → 🏁 Start).")
        return

    st.title(f"📝 {st.session_state.brand} — Discovery Form")
    st.caption(f"Contributing as **{st.session_state.name}** ({st.session_state.role}) · You can keep editing — same email, same draft.")

    # Top KPI strip
    pct = _completion_pct()
    k1, k2, k3 = st.columns(3)
    k1.metric("Completion", f"{pct}%")
    k2.metric("Sections done", f"{sum(1 for sk,sv in SECTION_STATE_KEYS.items() if A._section_filled(st.session_state.get(sv) or {}, sk))} / {len(SECTION_STATE_KEYS)}")
    fld_count = sum(len((st.session_state.get(sv) or {}).get('fields', []) or [])
                    for sk,sv in SECTION_STATE_KEYS.items() if sk in A.FIELD_BUILDER_SECTIONS)
    k3.metric("Fields proposed", fld_count)
    st.progress(pct / 100)
    st.divider()

    tabs = st.tabs([
        "A. People", "B. Partner 360", "C. Customer 360",
        "D. Sales / Opportunity", "E. Approvals", "F. Dashboards",
        "G. Best Practices", "H. Open Notes",
    ])

    with tabs[0]:
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

    with tabs[1]:
        _field_builder(
            "Partner 360 — Fields", "sec_partner_360", sg.PARTNER_360_FIELDS,
            "Shared across brands. 'Load suggestions' for common starter fields, then edit/delete/add freely.",
        )
        st.session_state.sec_partner_360["notes"] = st.text_area(
            "Notes (source of truth, dedup, hierarchy)",
            value=st.session_state.sec_partner_360.get("notes", ""), height=80,
        )

    with tabs[2]:
        _field_builder(
            "Customer 360 — Fields", "sec_customer_360", sg.CUSTOMER_360_FIELDS,
            "Capture mandatory fields, hierarchy needs (parent/child accounts), brand-specific extensions.",
        )
        st.session_state.sec_customer_360["notes"] = st.text_area(
            "Notes (renewals, hierarchies, dedup)",
            value=st.session_state.sec_customer_360.get("notes", ""), height=80,
        )

    with tabs[3]:
        st.markdown("### Sales — Opportunity / Lead / Deal fields")
        st.caption("Three sub-sections. Suggestions inspired by Red Hat (deal-funnel) + AWS (project-style). Mix and match — every brand owns its structure.")

        with st.expander("**D1. Opportunity Details**", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Use Red Hat starter (Opportunity)", key="seed_redhat_d1"):
                    e = st.session_state.sec_sales_opp_details.get("fields", []); names = {f.get("field","").lower() for f in e}
                    for s in sg.REDHAT_OPPORTUNITY_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = e; st.rerun()
            with c2:
                if st.button("Use AWS starter (Customer)", key="seed_aws_d1"):
                    e = st.session_state.sec_sales_opp_details.get("fields", []); names = {f.get("field","").lower() for f in e}
                    for s in sg.AWS_CUSTOMER_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = e; st.rerun()
            _field_builder("Opportunity Details fields", "sec_sales_opp_details", [], "")
            st.session_state.sec_sales_opp_details["notes"] = st.text_area(
                "Notes — D1", value=st.session_state.sec_sales_opp_details.get("notes", ""), height=70, key="notes_d1")

        with st.expander("**D2. Opportunity Contact Details**", expanded=False):
            if st.button("Use Red Hat starter (Contacts)", key="seed_redhat_d2"):
                e = st.session_state.sec_sales_contact_details.get("fields", []); names = {f.get("field","").lower() for f in e}
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
                    e = st.session_state.sec_sales_deal_details.get("fields", []); names = {f.get("field","").lower() for f in e}
                    for s in sg.REDHAT_DEAL_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = e; st.rerun()
            with c2:
                if st.button("Use AWS starter (Project)", key="seed_aws_d3"):
                    e = st.session_state.sec_sales_deal_details.get("fields", []); names = {f.get("field","").lower() for f in e}
                    for s in sg.AWS_PROJECT_DETAILS:
                        if s["field"].lower() not in names: e.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = e; st.rerun()
            _field_builder("Deal Details fields", "sec_sales_deal_details", [], "Commercials, products, services, target close date.")
            st.session_state.sec_sales_deal_details["notes"] = st.text_area(
                "Notes — D3", value=st.session_state.sec_sales_deal_details.get("notes", ""), height=70, key="notes_d3")

    with tabs[4]:
        st.markdown("#### Approval Stages & Workflow")
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
        st.session_state.sec_approvals["stages"] = edited.to_dict(orient="records")
        st.session_state.sec_approvals["escalation"] = st.text_area("Escalation rules", value=st.session_state.sec_approvals.get("escalation", ""), height=80)
        st.session_state.sec_approvals["notes"]      = st.text_area("Other workflow notes", value=st.session_state.sec_approvals.get("notes", ""), height=80)

    with tabs[5]:
        st.markdown("#### Dashboards & Reports Expected")
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

    with tabs[6]:
        st.markdown("#### Best-Practice Inputs")
        s = st.session_state.sec_best_practices
        s["data_hygiene"]          = st.text_area("Data hygiene asks (dedup, mandatory rules, naming)", value=s.get("data_hygiene", ""), height=100)
        s["integrations_wishlist"] = st.text_area("Integrations wishlist (just list — Zoho ↔ ERP / Outlook / Teams)", value=s.get("integrations_wishlist", ""), height=100)
        s["dedup_sops"]            = st.text_area("SOPs to document later (lead→opp, partner onboarding, customer creation)", value=s.get("dedup_sops", ""), height=100)
        with st.expander("💡 Common additional clauses (copy/paste if relevant)"):
            for c in sg.ADDITIONAL_CLAUSE_SUGGESTIONS:
                st.markdown(f"- {c}")

    with tabs[7]:
        s = st.session_state.sec_open_notes
        c1, c2 = st.columns(2)
        with c1:
            s["pain_points"]   = st.text_area("Current pain points",  value=s.get("pain_points", ""), height=120)
            s["nice_to_haves"] = st.text_area("Nice-to-haves",        value=s.get("nice_to_haves", ""), height=120)
            s["risks"]         = st.text_area("Risks / blockers",    value=s.get("risks", ""), height=120)
        with c2:
            s["must_haves"]         = st.text_area("Must-haves",                 value=s.get("must_haves", ""), height=120)
            s["questions_for_zoho"] = st.text_area("Questions for the Zoho team", value=s.get("questions_for_zoho", ""), height=120)

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
        st.info("💡 Use the **same email** later to come back and edit. Multiple roles per brand can contribute — answers merge into one report.")


# =====================================================================
# Page 3 — Admin
# =====================================================================
def render_admin():
    st.title("🔒 Admin — Brand Dashboard & Reports")

    if not st.session_state.admin_unlocked:
        with st.container(border=True):
            st.markdown("Enter the admin passcode to unlock per-brand dashboards, charts, and report downloads.")
            pc = st.text_input("Admin passcode", type="password")
            if st.button("Unlock", type="primary"):
                if pc == config.ADMIN_PASSCODE:
                    st.session_state.admin_unlocked = True; st.rerun()
                else:
                    st.error("Wrong passcode.")
        return

    tab_brand, tab_compare = st.tabs(["📊 Brand Dashboard", "🔄 Cross-Brand Comparison"])

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
        st.caption(f"Generated {bundle['generated_at']}")

        # KPI row
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("👥 Contributors",  metrics["contributors"])
        c2.metric("🧱 Fields",         metrics["total_fields"])
        c3.metric("✅ Mandatory",      f"{metrics['mandatory_pct']}%")
        c4.metric("🔁 Approvals",      metrics["approval_stages"])
        c5.metric("📊 Dashboards",     metrics["dashboards"])

        st.progress(metrics["completion_pct"] / 100, text=f"Section completion: {metrics['completion_pct']}%")

        if not bundle["contributors"]:
            st.warning("No contributors yet for this brand.")
            return

        # Charts
        cc1, cc2 = st.columns(2)
        with cc1:
            data = A.fields_per_section_count(bundle)
            df = pd.DataFrame({"Section": list(data.keys()), "Fields": list(data.values())})
            fig = px.bar(df, x="Section", y="Fields", color_discrete_sequence=["#C8102E"], title="Fields proposed per section")
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)
        with cc2:
            data = A.mandatory_per_section_pct(bundle)
            df = pd.DataFrame({"Section": list(data.keys()), "Mandatory %": list(data.values())})
            fig = px.bar(df, x="Mandatory %", y="Section", orientation="h", color_discrete_sequence=["#1A1A1A"], title="Mandatory % per section")
            fig.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)

        # Conflicts + Recommendations
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("### 🚨 Conflicts to resolve")
            if conflicts:
                st.dataframe(pd.DataFrame(conflicts), use_container_width=True, hide_index=True)
            else:
                st.success("No conflicts detected between contributors.")
        with cc2:
            st.markdown("### 💡 Insights & Recommendations")
            if recs:
                rdf = pd.DataFrame(recs)
                def color(p):
                    return {"High":"#FCE3E6","Medium":"#FFF4E0","Low":"#E8F4FD","Info":"#EAF7EE"}.get(p, "#FFF")
                styled = rdf.style.apply(lambda r: [f"background-color: {color(r['priority'])}"] * len(r), axis=1)
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

    with tab_compare:
        st.subheader("Cross-brand comparison")
        bundles = []
        for b in config.BRANDS:
            try:
                bundles.append(db.get_brand_bundle(b))
            except Exception:
                pass
        rows = []
        for b in bundles:
            m = A.compute_metrics(b)
            rows.append({"Brand": b["brand"], "Contributors": m["contributors"], "Fields": m["total_fields"],
                         "Mandatory %": m["mandatory_pct"], "Approvals": m["approval_stages"],
                         "Dashboards": m["dashboards"], "Completion %": m["completion_pct"]})
        cdf = pd.DataFrame(rows)
        st.dataframe(cdf, use_container_width=True, hide_index=True)

        if not cdf.empty:
            fig = px.bar(cdf, x="Brand", y=["Contributors","Fields","Approvals","Dashboards"], barmode="group",
                         title="Brand-by-brand totals", color_discrete_sequence=["#C8102E", "#1A1A1A", "#666666", "#999999"])
            fig.update_layout(height=380, margin=dict(l=0,r=0,t=40,b=0))
            st.plotly_chart(fig, use_container_width=True)

            fig2 = px.bar(cdf, x="Brand", y="Completion %", color_discrete_sequence=["#C8102E"], title="Section-completion %")
            fig2.update_layout(height=320, margin=dict(l=0,r=0,t=40,b=0), yaxis_range=[0,100])
            st.plotly_chart(fig2, use_container_width=True)

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
