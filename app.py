"""Redington Zoho CRM Discovery — Streamlit app.

Run:    streamlit run app.py
Deploy: push to GitHub, connect to https://share.streamlit.io (free).
"""
import pandas as pd
import streamlit as st

import config
import db
import reports
import suggestions as sg

st.set_page_config(page_title="Redington Zoho CRM Discovery", page_icon="📋", layout="wide")

# ---------- Session-state defaults ----------
def _init_state():
    defaults = {
        "contributor_id": None,
        "brand": None,
        "name": "",
        "email": "",
        "role": "",
        "admin_unlocked": False,
        # one key per section to hold the in-memory edit state
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


# ---------- Sidebar nav ----------
PAGE_INTRO   = "🏁 Start"
PAGE_FORM    = "📝 Fill Discovery Form"
PAGE_ADMIN   = "🔒 Admin Dashboard & Reports"

with st.sidebar:
    st.markdown("### Redington Discovery")
    st.caption("Zoho CRM internal rollout")
    page = st.radio("Go to", [PAGE_INTRO, PAGE_FORM, PAGE_ADMIN], index=0)
    st.markdown("---")
    if st.session_state.contributor_id:
        st.success(f"✅ Logged in as {st.session_state.name}\nBrand: **{st.session_state.brand}**\nRole: {st.session_state.role}")
    else:
        st.info("Start a session first.")


# =====================================================================
# Page 1 — Start
# =====================================================================
def render_intro():
    st.title("📋 Redington Zoho CRM — Discovery Session")
    st.markdown("""
Welcome! This app captures **what your brand needs from Zoho CRM** so the implementation team can configure it correctly.

**How it works**
1. Pick your **brand** and tell us **who you are**
2. Fill in the discovery form — sections for People, Partner 360, Customer 360, Sales fields, Approvals, Dashboards, and Best Practices
3. Multiple people from the same brand can contribute. Click **Save & Submit** when you're done.
4. Your inputs are merged into a single per-brand requirements pack the admin downloads as **PDF / Word / CSV**.

**Nothing is forced.** Every brand defines its own fields, workflow, dashboards, and rules.
You can load **starter suggestions** (from previous brand discoveries) and edit/delete them, or start from scratch.
""")
    st.divider()
    st.subheader("Start your contribution")

    col1, col2 = st.columns(2)
    with col1:
        brand = st.selectbox("Brand", config.BRANDS, index=0)
        name  = st.text_input("Your full name", value=st.session_state.name)
    with col2:
        role  = st.selectbox("Your role", config.ROLES, index=0)
        email = st.text_input("Email", value=st.session_state.email)

    if st.button("➡️ Start session", type="primary", use_container_width=True):
        if not name.strip() or not email.strip():
            st.error("Please enter your name and email.")
            return
        try:
            cid = db.add_contributor(brand, name.strip(), email.strip(), role)
        except Exception as e:
            st.error(f"Could not connect to database. Did you run schema.sql in Supabase? Error: {e}")
            return
        st.session_state.contributor_id = cid
        st.session_state.brand = brand
        st.session_state.name = name.strip()
        st.session_state.email = email.strip()
        st.session_state.role = role
        st.success("Session created. Open **Fill Discovery Form** in the sidebar.")
        st.balloons()


# =====================================================================
# Helpers — field-builder UI
# =====================================================================
FIELD_COLUMNS = {
    "field":            st.column_config.TextColumn("Field name", required=True),
    "type":             st.column_config.SelectboxColumn("Type", options=config.FIELD_TYPES, required=True),
    "options":          st.column_config.TextColumn("Options (comma-separated, if applicable)"),
    "mandatory":        st.column_config.CheckboxColumn("Mandatory?"),
    "conditional_rule": st.column_config.TextColumn("Conditional / business rule"),
}

def _field_builder(label: str, state_key: str, suggestion_pool: list[dict], help_text: str = "") -> list[dict]:
    """Render a data_editor for field rows + a 'Load suggestions' button.
    Returns the current list of field dicts.
    """
    st.markdown(f"#### {label}")
    if help_text:
        st.caption(help_text)
    cols = st.columns([1, 1, 4])
    with cols[0]:
        if st.button("➕ Load suggestions", key=f"load_{state_key}"):
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
        column_config=FIELD_COLUMNS, key=f"editor_{state_key}",
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

    st.title(f"📝 Discovery Form — {st.session_state.brand}")
    st.caption(f"Contributing as **{st.session_state.name}** ({st.session_state.role})")

    tab_a, tab_b, tab_c, tab_d, tab_e, tab_f, tab_g, tab_h = st.tabs([
        "A. People",
        "B. Partner 360",
        "C. Customer 360",
        "D. Sales / Opportunity",
        "E. Approvals",
        "F. Dashboards",
        "G. Best Practices",
        "H. Open Notes",
    ])

    # ---- A: People & Stakeholders ----
    with tab_a:
        st.markdown("#### People & Stakeholders for this brand")
        s = st.session_state.sec_people
        s["brand_lead_name"]   = st.text_input("Brand lead name",  value=s.get("brand_lead_name", ""))
        s["brand_lead_email"]  = st.text_input("Brand lead email", value=s.get("brand_lead_email", ""))
        s["roles_involved"]    = st.multiselect("Which roles are involved in this brand?", config.ROLES, default=s.get("roles_involved", []))
        s["decision_maker"]    = st.text_input("Who signs off on the requirements?", value=s.get("decision_maker", ""))
        c1, c2 = st.columns(2)
        with c1:
            s["daily_users"]       = st.text_input("Approx. number of daily users",       value=s.get("daily_users", ""))
        with c2:
            s["occasional_users"]  = st.text_input("Approx. number of occasional users",  value=s.get("occasional_users", ""))
        s["notes"] = st.text_area("Anything else about the people side?", value=s.get("notes", ""), height=80)

    # ---- B: Partner 360 ----
    with tab_b:
        _field_builder(
            "Partner 360 — Fields you want captured for partners",
            "sec_partner_360", sg.PARTNER_360_FIELDS,
            help_text="These fields are SHARED across all brands (master partner data). Use 'Load suggestions' to seed common fields, then edit/delete/add freely.",
        )
        st.session_state.sec_partner_360["notes"] = st.text_area(
            "Notes (source of truth, dedup approach, hierarchy needs, etc.)",
            value=st.session_state.sec_partner_360.get("notes", ""), height=100,
        )

    # ---- C: Customer 360 ----
    with tab_c:
        _field_builder(
            "Customer 360 — Fields you want captured for customers / end users",
            "sec_customer_360", sg.CUSTOMER_360_FIELDS,
            help_text="Shared across brands. Capture mandatory fields, hierarchy needs (parent/child accounts), and any brand-specific extensions.",
        )
        st.session_state.sec_customer_360["notes"] = st.text_area(
            "Notes (renewal handling, hierarchies, dedup rules, etc.)",
            value=st.session_state.sec_customer_360.get("notes", ""), height=100,
        )

    # ---- D: Sales / Opportunity ----
    with tab_d:
        st.markdown("### Sales — Opportunity / Lead / Deal fields")
        st.caption("Three sub-sections. Define the fields you need on Opportunities. Suggestions are inspired by Red Hat (deal-funnel) and AWS (project-style). Mix and match — every brand owns its own structure.")

        with st.expander("D1. Opportunity Details", expanded=True):
            colA, colB = st.columns(2)
            with colA:
                if st.button("Use Red Hat starter (Opportunity Details)", key="seed_redhat_d1"):
                    existing = st.session_state.sec_sales_opp_details.get("fields", [])
                    names = {f.get("field","").lower() for f in existing}
                    for s in sg.REDHAT_OPPORTUNITY_DETAILS:
                        if s["field"].lower() not in names:
                            existing.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = existing
                    st.rerun()
            with colB:
                if st.button("Use AWS starter (Customer Details)", key="seed_aws_d1"):
                    existing = st.session_state.sec_sales_opp_details.get("fields", [])
                    names = {f.get("field","").lower() for f in existing}
                    for s in sg.AWS_CUSTOMER_DETAILS:
                        if s["field"].lower() not in names:
                            existing.append(dict(s))
                    st.session_state.sec_sales_opp_details["fields"] = existing
                    st.rerun()
            _field_builder("Opportunity Details fields", "sec_sales_opp_details", [], help_text="(Use the buttons above to load starter suggestions.)")
            st.session_state.sec_sales_opp_details["notes"] = st.text_area(
                "Notes — D1", value=st.session_state.sec_sales_opp_details.get("notes", ""), height=70, key="notes_d1",
            )

        with st.expander("D2. Opportunity Contact Details", expanded=False):
            if st.button("Use Red Hat starter (Contact Details)", key="seed_redhat_d2"):
                existing = st.session_state.sec_sales_contact_details.get("fields", [])
                names = {f.get("field","").lower() for f in existing}
                for s in sg.REDHAT_CONTACT_DETAILS:
                    if s["field"].lower() not in names:
                        existing.append(dict(s))
                st.session_state.sec_sales_contact_details["fields"] = existing
                st.rerun()
            _field_builder("Contact Details fields", "sec_sales_contact_details", [], help_text="People involved in each opportunity (PAM, BSM, PM, Pre-sales, etc.)")
            st.session_state.sec_sales_contact_details["notes"] = st.text_area(
                "Notes — D2", value=st.session_state.sec_sales_contact_details.get("notes", ""), height=70, key="notes_d2",
            )

        with st.expander("D3. Opportunity Deal Details", expanded=False):
            colA, colB = st.columns(2)
            with colA:
                if st.button("Use Red Hat starter (Deal Details)", key="seed_redhat_d3"):
                    existing = st.session_state.sec_sales_deal_details.get("fields", [])
                    names = {f.get("field","").lower() for f in existing}
                    for s in sg.REDHAT_DEAL_DETAILS:
                        if s["field"].lower() not in names:
                            existing.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = existing
                    st.rerun()
            with colB:
                if st.button("Use AWS starter (Project Details)", key="seed_aws_d3"):
                    existing = st.session_state.sec_sales_deal_details.get("fields", [])
                    names = {f.get("field","").lower() for f in existing}
                    for s in sg.AWS_PROJECT_DETAILS:
                        if s["field"].lower() not in names:
                            existing.append(dict(s))
                    st.session_state.sec_sales_deal_details["fields"] = existing
                    st.rerun()
            _field_builder("Deal Details fields", "sec_sales_deal_details", [], help_text="Commercials, products, services, target close date, etc.")
            st.session_state.sec_sales_deal_details["notes"] = st.text_area(
                "Notes — D3", value=st.session_state.sec_sales_deal_details.get("notes", ""), height=70, key="notes_d3",
            )

    # ---- E: Approvals ----
    with tab_e:
        st.markdown("#### Approval Stages & Workflow")
        cols = st.columns([1,1,4])
        with cols[0]:
            if st.button("➕ Load suggestions", key="load_approvals"):
                existing = st.session_state.sec_approvals.get("stages", [])
                existing_names = {s.get("stage","").lower() for s in existing}
                for s in sg.APPROVAL_STAGE_SUGGESTIONS:
                    if s["stage"].lower() not in existing_names:
                        existing.append(dict(s))
                st.session_state.sec_approvals["stages"] = existing
                st.rerun()
        with cols[1]:
            if st.button("🗑️ Clear all", key="clear_approvals"):
                st.session_state.sec_approvals["stages"] = []
                st.rerun()

        rows = st.session_state.sec_approvals.get("stages", [])
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["stage","approver","trigger","sla_hours","can_revert"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key="editor_approvals",
            column_config={
                "stage":      st.column_config.TextColumn("Stage", required=True),
                "approver":   st.column_config.TextColumn("Approver / Role"),
                "trigger":    st.column_config.TextColumn("Trigger / Condition"),
                "sla_hours":  st.column_config.NumberColumn("SLA (hours)", min_value=0, step=1),
                "can_revert": st.column_config.CheckboxColumn("Can revert?"),
            },
        )
        st.session_state.sec_approvals["stages"] = edited.to_dict(orient="records")
        st.session_state.sec_approvals["escalation"] = st.text_area(
            "Escalation rules (what happens if SLA breached?)", value=st.session_state.sec_approvals.get("escalation", ""), height=80,
        )
        st.session_state.sec_approvals["notes"] = st.text_area(
            "Other workflow notes", value=st.session_state.sec_approvals.get("notes", ""), height=80,
        )

    # ---- F: Dashboards ----
    with tab_f:
        st.markdown("#### Dashboards & Reports Expected")
        cols = st.columns([1,1,4])
        with cols[0]:
            if st.button("➕ Load suggestions", key="load_dash"):
                existing = st.session_state.sec_dashboards.get("dashboards", [])
                names = {d.get("dashboard","").lower() for d in existing}
                for s in sg.DASHBOARD_SUGGESTIONS:
                    if s["dashboard"].lower() not in names:
                        existing.append(dict(s))
                st.session_state.sec_dashboards["dashboards"] = existing
                st.rerun()
        with cols[1]:
            if st.button("🗑️ Clear all", key="clear_dash"):
                st.session_state.sec_dashboards["dashboards"] = []
                st.rerun()

        rows = st.session_state.sec_dashboards.get("dashboards", [])
        df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["dashboard","audience","frequency"])
        edited = st.data_editor(
            df, num_rows="dynamic", use_container_width=True, key="editor_dash",
            column_config={
                "dashboard": st.column_config.TextColumn("Dashboard / Report", required=True),
                "audience":  st.column_config.TextColumn("Audience (roles)"),
                "frequency": st.column_config.SelectboxColumn("Frequency", options=["Real-time","Daily","Weekly","Monthly","Quarterly","On-demand"]),
            },
        )
        st.session_state.sec_dashboards["dashboards"] = edited.to_dict(orient="records")
        st.session_state.sec_dashboards["notes"] = st.text_area(
            "Notes (export needs, scheduled emails, drill-downs, etc.)", value=st.session_state.sec_dashboards.get("notes", ""), height=80,
        )

    # ---- G: Best practices ----
    with tab_g:
        st.markdown("#### Best-Practice Inputs")
        st.caption("Captured as recommendations for the Zoho team — not for deep config in v1.")
        s = st.session_state.sec_best_practices
        s["data_hygiene"]          = st.text_area("Data-hygiene asks (dedup rules, mandatory-field enforcement, naming conventions)", value=s.get("data_hygiene", ""), height=100)
        s["integrations_wishlist"] = st.text_area("Integrations wishlist (Zoho ↔ ERP / Outlook / Teams / vendor portals — list, no deep dive)", value=s.get("integrations_wishlist", ""), height=100)
        s["dedup_sops"]            = st.text_area("SOPs to document later (lead → opp conversion, partner onboarding, customer creation, etc.)", value=s.get("dedup_sops", ""), height=100)

        st.markdown("**Common additional clauses (suggestions)** — copy/paste into your notes if relevant:")
        for c in sg.ADDITIONAL_CLAUSE_SUGGESTIONS:
            st.markdown(f"- {c}")

    # ---- H: Open notes ----
    with tab_h:
        st.markdown("#### Open Notes / Pain Points / Asks")
        s = st.session_state.sec_open_notes
        s["pain_points"]         = st.text_area("Current pain points with the existing tool", value=s.get("pain_points", ""), height=100)
        s["must_haves"]          = st.text_area("Must-haves",                                  value=s.get("must_haves", ""), height=100)
        s["nice_to_haves"]       = st.text_area("Nice-to-haves",                               value=s.get("nice_to_haves", ""), height=100)
        s["risks"]               = st.text_area("Risks / blockers",                            value=s.get("risks", ""), height=100)
        s["questions_for_zoho"]  = st.text_area("Questions for the Zoho team",                 value=s.get("questions_for_zoho", ""), height=100)

    # ---- Save ----
    st.divider()
    save_col, info_col = st.columns([1, 3])
    with save_col:
        if st.button("💾 Save & Submit", type="primary", use_container_width=True):
            try:
                section_map = {
                    "people":                st.session_state.sec_people,
                    "partner_360":           st.session_state.sec_partner_360,
                    "customer_360":          st.session_state.sec_customer_360,
                    "sales_opp_details":     st.session_state.sec_sales_opp_details,
                    "sales_contact_details": st.session_state.sec_sales_contact_details,
                    "sales_deal_details":    st.session_state.sec_sales_deal_details,
                    "approvals":             st.session_state.sec_approvals,
                    "dashboards":            st.session_state.sec_dashboards,
                    "best_practices":        st.session_state.sec_best_practices,
                    "open_notes":            st.session_state.sec_open_notes,
                }
                for sec_key, payload in section_map.items():
                    db.save_response(st.session_state.contributor_id, sec_key, payload)
                st.success("Saved! You can keep editing and click Save & Submit again, or share the link with another team member.")
            except Exception as e:
                st.error(f"Save failed: {e}")
    with info_col:
        st.info("💡 You can save partial progress at any time. Multiple people can fill in the form for the same brand — their inputs are merged into the final report.")


# =====================================================================
# Page 3 — Admin
# =====================================================================
def render_admin():
    st.title("🔒 Admin — Brand Dashboard & Reports")

    if not st.session_state.admin_unlocked:
        pc = st.text_input("Admin passcode", type="password")
        if st.button("Unlock"):
            if pc == config.ADMIN_PASSCODE:
                st.session_state.admin_unlocked = True
                st.rerun()
            else:
                st.error("Wrong passcode.")
        return

    tab_brand, tab_compare = st.tabs(["📊 Per-Brand Dashboard", "🔄 Cross-Brand Comparison"])

    with tab_brand:
        brand = st.selectbox("Pick a brand", config.BRANDS)
        bundle = db.get_brand_bundle(brand)

        st.subheader(f"Brand: {brand}")
        st.caption(f"Generated: {bundle['generated_at']} · Contributors: {len(bundle['contributors'])}")

        if not bundle["contributors"]:
            st.warning("No contributors yet for this brand.")
        else:
            st.markdown("### 👥 Contributors")
            cdf = pd.DataFrame([{
                "Name": c["name"], "Email": c["email"], "Role": c["role"], "Submitted": c["submitted_at"][:19].replace("T"," "),
            } for c in bundle["contributors"]])
            st.dataframe(cdf, use_container_width=True, hide_index=True)

            # Download buttons
            st.markdown("### 📥 Download requirements pack")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button(
                    "⬇️ PDF", data=reports.build_pdf(bundle),
                    file_name=f"Redington_Discovery_{brand}.pdf", mime="application/pdf",
                    use_container_width=True,
                )
            with c2:
                st.download_button(
                    "⬇️ Word", data=reports.build_docx(bundle),
                    file_name=f"Redington_Discovery_{brand}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )
            with c3:
                st.download_button(
                    "⬇️ CSV", data=reports.build_csv(bundle),
                    file_name=f"Redington_Discovery_{brand}.csv", mime="text/csv",
                    use_container_width=True,
                )

            # Inline preview
            st.markdown("### 🔍 Inline view of merged inputs")
            for sec_key, sec_title in reports.SECTIONS:
                with st.expander(sec_title, expanded=False):
                    any_data = False
                    for c in bundle["contributors"]:
                        payload = bundle["responses_by_contributor"].get(c["id"], {}).get(sec_key)
                        if not payload:
                            continue
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
                        st.caption("_No input captured for this section yet._")

    with tab_compare:
        st.subheader("Cross-brand comparison")
        st.caption("Long-format CSV — one row per (brand, contributor, section, field). Open in Excel and pivot freely.")
        bundles = [db.get_brand_bundle(b) for b in config.BRANDS]
        st.download_button(
            "⬇️ Download cross-brand CSV",
            data=reports.build_cross_brand_csv(bundles),
            file_name="Redington_Discovery_AllBrands.csv", mime="text/csv",
        )
        for b in bundles:
            st.markdown(f"**{b['brand']}** — {len(b['contributors'])} contributor(s)")


# ---------- Router ----------
if page == PAGE_INTRO:
    render_intro()
elif page == PAGE_FORM:
    render_form()
elif page == PAGE_ADMIN:
    render_admin()
