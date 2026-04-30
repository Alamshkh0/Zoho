"""Generate PDF / Word / CSV reports from a brand bundle (see db.get_brand_bundle).

Each brand has multiple contributors, each with up to 9 sections. Reports show
each contributor's input, plus a consolidated summary at the top.
"""
from io import BytesIO
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)
from docx import Document
from docx.shared import Pt, RGBColor

# ---------- Section metadata (display order + titles) ----------

SECTIONS = [
    ("people",                "A. People & Stakeholders"),
    ("partner_360",           "B. Partner 360 — Fields"),
    ("customer_360",          "C. Customer 360 — Fields"),
    ("sales_opp_details",     "D1. Sales — Opportunity Details"),
    ("sales_contact_details", "D2. Sales — Opportunity Contact Details"),
    ("sales_deal_details",    "D3. Sales — Opportunity Deal Details"),
    ("approvals",             "E. Approval Stages & Workflow"),
    ("dashboards",            "F. Dashboards & Reports Expected"),
    ("best_practices",        "G. Best-Practice Inputs"),
    ("open_notes",            "H. Open Notes / Pain Points / Asks"),
]

FIELD_BUILDER_SECTIONS = {"partner_360", "customer_360", "sales_opp_details", "sales_contact_details", "sales_deal_details"}


def _safe(v) -> str:
    if v is None: return ""
    if isinstance(v, list): return ", ".join(str(x) for x in v if x)
    return str(v)


# =====================================================================
# CSV
# =====================================================================

def build_csv(bundle: dict) -> bytes:
    """Long-format CSV: one row per (contributor, section, field, value)."""
    rows = []
    brand = bundle["brand"]
    for c in bundle["contributors"]:
        contrib_label = f"{c['name']} ({c['role']})"
        sections = bundle["responses_by_contributor"].get(c["id"], {})
        for sec_key, sec_title in SECTIONS:
            payload = sections.get(sec_key, {})
            if not payload:
                continue
            if sec_key in FIELD_BUILDER_SECTIONS:
                for f in payload.get("fields", []) or []:
                    rows.append({
                        "Brand": brand, "Contributor": contrib_label, "Section": sec_title,
                        "Field": f.get("field", ""), "Type": f.get("type", ""),
                        "Options": f.get("options", ""), "Mandatory": f.get("mandatory", ""),
                        "Conditional Rule": f.get("conditional_rule", ""),
                        "Value": "",
                    })
            elif sec_key == "approvals":
                for s in payload.get("stages", []) or []:
                    rows.append({
                        "Brand": brand, "Contributor": contrib_label, "Section": sec_title,
                        "Field": s.get("stage", ""), "Type": "Approval Stage",
                        "Options": s.get("approver", ""), "Mandatory": s.get("trigger", ""),
                        "Conditional Rule": f"SLA {s.get('sla_hours','')}h, can_revert={s.get('can_revert','')}",
                        "Value": "",
                    })
            elif sec_key == "dashboards":
                for d in payload.get("dashboards", []) or []:
                    rows.append({
                        "Brand": brand, "Contributor": contrib_label, "Section": sec_title,
                        "Field": d.get("dashboard", ""), "Type": "Dashboard",
                        "Options": d.get("audience", ""), "Mandatory": d.get("frequency", ""),
                        "Conditional Rule": "", "Value": "",
                    })
            else:
                for k, v in payload.items():
                    rows.append({
                        "Brand": brand, "Contributor": contrib_label, "Section": sec_title,
                        "Field": k, "Type": "", "Options": "", "Mandatory": "",
                        "Conditional Rule": "", "Value": _safe(v),
                    })
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Brand","Contributor","Section","Field","Type","Options","Mandatory","Conditional Rule","Value"])
    return df.to_csv(index=False).encode("utf-8")


def build_cross_brand_csv(bundles: list[dict]) -> bytes:
    """Cross-brand comparison: one row per (brand, section, field), columns aggregating."""
    frames = []
    for b in bundles:
        frames.append(pd.read_csv(BytesIO(build_csv(b))))
    if not frames:
        return b""
    return pd.concat(frames, ignore_index=True).to_csv(index=False).encode("utf-8")


# =====================================================================
# PDF (reportlab)
# =====================================================================

def build_pdf(bundle: dict) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title=f"Redington Zoho CRM Discovery — {bundle['brand']}",
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], textColor=colors.HexColor("#C8102E"), spaceAfter=8)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=colors.HexColor("#1A1A1A"), spaceAfter=6)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], textColor=colors.HexColor("#444"), spaceAfter=4)
    body = styles["BodyText"]
    small = ParagraphStyle("small", parent=body, fontSize=8, textColor=colors.HexColor("#666"))

    story = []
    story.append(Paragraph(f"Redington Zoho CRM Discovery", h1))
    story.append(Paragraph(f"Brand: <b>{bundle['brand']}</b>", h2))
    story.append(Paragraph(f"Generated: {bundle['generated_at']}", small))
    story.append(Spacer(1, 0.4*cm))

    # Contributors
    story.append(Paragraph("Contributors", h2))
    if bundle["contributors"]:
        ctab = [["Name", "Email", "Role", "Submitted"]]
        for c in bundle["contributors"]:
            ctab.append([c["name"], c["email"], c["role"], c["submitted_at"][:19].replace("T", " ")])
        t = Table(ctab, colWidths=[4.5*cm, 5.5*cm, 2.5*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#C8102E")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.whitesmoke),
            ("FONTSIZE",   (0,0), (-1,-1), 8),
            ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
            ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("<i>No contributors yet.</i>", body))
    story.append(Spacer(1, 0.4*cm))

    # Each section, each contributor
    for sec_key, sec_title in SECTIONS:
        story.append(PageBreak())
        story.append(Paragraph(sec_title, h2))
        any_data = False
        for c in bundle["contributors"]:
            payload = bundle["responses_by_contributor"].get(c["id"], {}).get(sec_key)
            if not payload:
                continue
            any_data = True
            story.append(Paragraph(f"From {c['name']} ({c['role']})", h3))
            _render_section_pdf(story, sec_key, payload, body, small)
            story.append(Spacer(1, 0.3*cm))
        if not any_data:
            story.append(Paragraph("<i>No input captured.</i>", body))

    doc.build(story)
    return buf.getvalue()


def _render_section_pdf(story, sec_key, payload, body, small):
    if sec_key in FIELD_BUILDER_SECTIONS:
        rows = payload.get("fields", []) or []
        if rows:
            tab = [["Field", "Type", "Options", "Mandatory", "Conditional Rule"]]
            for f in rows:
                tab.append([_safe(f.get("field")), _safe(f.get("type")), _safe(f.get("options")),
                            "Yes" if f.get("mandatory") else "No", _safe(f.get("conditional_rule"))])
            t = Table(tab, colWidths=[4.5*cm, 2*cm, 4*cm, 2*cm, 4.5*cm], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F0F0F0")),
                ("FONTSIZE",   (0,0), (-1,-1), 7),
                ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
                ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ]))
            story.append(t)
        if payload.get("notes"):
            story.append(Spacer(1, 0.15*cm))
            story.append(Paragraph(f"<b>Notes:</b> {_safe(payload['notes'])}", small))

    elif sec_key == "approvals":
        rows = payload.get("stages", []) or []
        if rows:
            tab = [["Stage", "Approver", "Trigger", "SLA (h)", "Can revert?"]]
            for s in rows:
                tab.append([_safe(s.get("stage")), _safe(s.get("approver")), _safe(s.get("trigger")),
                            _safe(s.get("sla_hours")), "Yes" if s.get("can_revert") else "No"])
            t = Table(tab, colWidths=[4*cm, 3.5*cm, 5*cm, 2*cm, 2.5*cm], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F0F0F0")),
                ("FONTSIZE",   (0,0), (-1,-1), 7),
                ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
                ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ]))
            story.append(t)
        for k in ("escalation", "notes"):
            if payload.get(k):
                story.append(Paragraph(f"<b>{k.title()}:</b> {_safe(payload[k])}", small))

    elif sec_key == "dashboards":
        rows = payload.get("dashboards", []) or []
        if rows:
            tab = [["Dashboard", "Audience", "Frequency"]]
            for d in rows:
                tab.append([_safe(d.get("dashboard")), _safe(d.get("audience")), _safe(d.get("frequency"))])
            t = Table(tab, colWidths=[7*cm, 6*cm, 4*cm], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#F0F0F0")),
                ("FONTSIZE",   (0,0), (-1,-1), 7),
                ("GRID",       (0,0), (-1,-1), 0.25, colors.grey),
                ("VALIGN",     (0,0), (-1,-1), "TOP"),
            ]))
            story.append(t)
        if payload.get("notes"):
            story.append(Paragraph(f"<b>Notes:</b> {_safe(payload['notes'])}", small))

    else:
        # generic key-value
        for k, v in payload.items():
            story.append(Paragraph(f"<b>{k.replace('_',' ').title()}:</b> {_safe(v)}", body))


# =====================================================================
# Word (python-docx)
# =====================================================================

def build_docx(bundle: dict) -> bytes:
    doc = Document()

    title = doc.add_heading("Redington Zoho CRM Discovery", level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0xC8, 0x10, 0x2E)

    doc.add_heading(f"Brand: {bundle['brand']}", level=1)
    p = doc.add_paragraph(f"Generated: {bundle['generated_at']}")
    p.runs[0].font.size = Pt(9)

    # Contributors
    doc.add_heading("Contributors", level=1)
    if bundle["contributors"]:
        tbl = doc.add_table(rows=1, cols=4)
        tbl.style = "Light Grid Accent 1"
        hdr = tbl.rows[0].cells
        for i, h in enumerate(["Name", "Email", "Role", "Submitted"]):
            hdr[i].text = h
        for c in bundle["contributors"]:
            row = tbl.add_row().cells
            row[0].text = c["name"]; row[1].text = c["email"]
            row[2].text = c["role"]; row[3].text = c["submitted_at"][:19].replace("T", " ")
    else:
        doc.add_paragraph("No contributors yet.").italic = True

    for sec_key, sec_title in SECTIONS:
        doc.add_page_break()
        doc.add_heading(sec_title, level=1)
        any_data = False
        for c in bundle["contributors"]:
            payload = bundle["responses_by_contributor"].get(c["id"], {}).get(sec_key)
            if not payload:
                continue
            any_data = True
            doc.add_heading(f"From {c['name']} ({c['role']})", level=2)
            _render_section_docx(doc, sec_key, payload)
        if not any_data:
            doc.add_paragraph("No input captured.").italic = True

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _render_section_docx(doc: Document, sec_key, payload):
    if sec_key in FIELD_BUILDER_SECTIONS:
        rows = payload.get("fields", []) or []
        if rows:
            tbl = doc.add_table(rows=1, cols=5)
            tbl.style = "Light Grid Accent 1"
            for i, h in enumerate(["Field", "Type", "Options", "Mandatory", "Conditional Rule"]):
                tbl.rows[0].cells[i].text = h
            for f in rows:
                cells = tbl.add_row().cells
                cells[0].text = _safe(f.get("field"))
                cells[1].text = _safe(f.get("type"))
                cells[2].text = _safe(f.get("options"))
                cells[3].text = "Yes" if f.get("mandatory") else "No"
                cells[4].text = _safe(f.get("conditional_rule"))
        if payload.get("notes"):
            doc.add_paragraph(f"Notes: {_safe(payload['notes'])}")

    elif sec_key == "approvals":
        rows = payload.get("stages", []) or []
        if rows:
            tbl = doc.add_table(rows=1, cols=5)
            tbl.style = "Light Grid Accent 1"
            for i, h in enumerate(["Stage", "Approver", "Trigger", "SLA (h)", "Can revert?"]):
                tbl.rows[0].cells[i].text = h
            for s in rows:
                cells = tbl.add_row().cells
                cells[0].text = _safe(s.get("stage")); cells[1].text = _safe(s.get("approver"))
                cells[2].text = _safe(s.get("trigger")); cells[3].text = _safe(s.get("sla_hours"))
                cells[4].text = "Yes" if s.get("can_revert") else "No"
        for k in ("escalation", "notes"):
            if payload.get(k):
                doc.add_paragraph(f"{k.title()}: {_safe(payload[k])}")

    elif sec_key == "dashboards":
        rows = payload.get("dashboards", []) or []
        if rows:
            tbl = doc.add_table(rows=1, cols=3)
            tbl.style = "Light Grid Accent 1"
            for i, h in enumerate(["Dashboard", "Audience", "Frequency"]):
                tbl.rows[0].cells[i].text = h
            for d in rows:
                cells = tbl.add_row().cells
                cells[0].text = _safe(d.get("dashboard")); cells[1].text = _safe(d.get("audience"))
                cells[2].text = _safe(d.get("frequency"))
        if payload.get("notes"):
            doc.add_paragraph(f"Notes: {_safe(payload['notes'])}")

    else:
        for k, v in payload.items():
            doc.add_paragraph(f"{k.replace('_',' ').title()}: {_safe(v)}")
