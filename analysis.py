"""Metrics, conflict detection, and rules-based recommendations from a brand bundle.

Pure functions — no DB, no UI. Used by both the Streamlit admin page and the
PDF/Word report generator. matplotlib charts are returned as PNG bytes (Agg backend)
so they embed cleanly in reportlab/python-docx.
"""
from io import BytesIO
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

FIELD_BUILDER_SECTIONS = {
    "partner_360", "customer_360",
    "sales_opp_details", "sales_contact_details", "sales_deal_details",
}
ALL_SECTION_KEYS = [
    "people", "partner_360", "customer_360",
    "sales_opp_details", "sales_contact_details", "sales_deal_details",
    "approvals", "dashboards", "best_practices", "open_notes",
]
SECTION_TITLES = {
    "people":                "People & Stakeholders",
    "partner_360":           "Partner 360",
    "customer_360":          "Customer 360",
    "sales_opp_details":     "Sales — Opportunity Details",
    "sales_contact_details": "Sales — Contact Details",
    "sales_deal_details":    "Sales — Deal Details",
    "approvals":             "Approvals",
    "dashboards":            "Dashboards",
    "best_practices":        "Best Practices",
    "open_notes":            "Open Notes",
}

# Brand palette
RED      = "#C8102E"
DARK     = "#1A1A1A"
GREY     = "#888888"
LIGHT    = "#F5F5F5"
ACCENTS  = ["#C8102E", "#1A1A1A", "#0F4C81", "#E07B00", "#2E7D32", "#6A1B9A", "#888888", "#5D4037"]


# ---------- Helpers ----------

def _all_payloads(bundle: dict, section_key: str) -> list[dict]:
    out = []
    for c in bundle["contributors"]:
        p = bundle["responses_by_contributor"].get(c["id"], {}).get(section_key)
        if p: out.append(p)
    return out

def _all_fields(bundle: dict, section_key: str) -> list[dict]:
    rows = []
    for p in _all_payloads(bundle, section_key):
        rows.extend(p.get("fields", []) or [])
    return rows

def _section_filled(payload: dict, section_key: str) -> bool:
    if not payload: return False
    if section_key in FIELD_BUILDER_SECTIONS:
        return bool(payload.get("fields"))
    if section_key == "approvals":
        return bool(payload.get("stages")) or bool(payload.get("escalation"))
    if section_key == "dashboards":
        return bool(payload.get("dashboards"))
    return any(v for v in payload.values() if v)


# ---------- Metrics ----------

def compute_metrics(bundle: dict) -> dict:
    contribs = bundle["contributors"]
    resp_map = bundle["responses_by_contributor"]

    all_fields = []
    for sk in FIELD_BUILDER_SECTIONS:
        all_fields.extend(_all_fields(bundle, sk))
    total_fields = len(all_fields)
    mandatory   = sum(1 for f in all_fields if bool(f.get("mandatory")))
    with_rule   = sum(1 for f in all_fields if str(f.get("conditional_rule") or "").strip())
    integ_needed= sum(1 for f in all_fields if bool(f.get("integration_needed")))
    sources     = [str(f.get("data_capture_source") or "").strip() for f in all_fields]
    sources     = [s for s in sources if s]
    unique_sources = len(set(sources))

    appr_names: set[str] = set()
    for p in _all_payloads(bundle, "approvals"):
        for s in p.get("stages", []) or []:
            n = (s.get("stage") or "").strip().lower()
            if n: appr_names.add(n)
    dash_names: set[str] = set()
    for p in _all_payloads(bundle, "dashboards"):
        for d in p.get("dashboards", []) or []:
            n = (d.get("dashboard") or "").strip().lower()
            if n: dash_names.add(n)

    sections_done = 0
    for sk in ALL_SECTION_KEYS:
        if any(_section_filled(resp_map.get(c["id"], {}).get(sk), sk) for c in contribs):
            sections_done += 1

    per_contrib_pcts: list[float] = []
    for c in contribs:
        sects = resp_map.get(c["id"], {})
        done = sum(1 for sk in ALL_SECTION_KEYS if _section_filled(sects.get(sk), sk))
        per_contrib_pcts.append(round(100 * done / len(ALL_SECTION_KEYS), 1))
    avg_completion = round(sum(per_contrib_pcts) / len(per_contrib_pcts), 1) if per_contrib_pcts else 0.0

    return {
        "contributors":     len(contribs),
        "total_fields":     total_fields,
        "mandatory_fields": mandatory,
        "mandatory_pct":    round(100 * mandatory / total_fields, 1) if total_fields else 0.0,
        "fields_with_rule": with_rule,
        "rule_pct":         round(100 * with_rule / total_fields, 1) if total_fields else 0.0,
        "integration_fields": integ_needed,
        "integration_pct":  round(100 * integ_needed / total_fields, 1) if total_fields else 0.0,
        "unique_sources":   unique_sources,
        "approval_stages":  len(appr_names),
        "dashboards":       len(dash_names),
        "sections_done":    sections_done,
        "sections_total":   len(ALL_SECTION_KEYS),
        "completion_pct":   round(100 * sections_done / len(ALL_SECTION_KEYS), 1),
        "avg_contributor_completion_pct": avg_completion,
    }


def fields_per_section_count(bundle: dict) -> dict[str, int]:
    return {SECTION_TITLES[sk]: len(_all_fields(bundle, sk)) for sk in FIELD_BUILDER_SECTIONS}

def mandatory_per_section_pct(bundle: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for sk in FIELD_BUILDER_SECTIONS:
        fs = _all_fields(bundle, sk)
        out[SECTION_TITLES[sk]] = round(100 * sum(1 for f in fs if bool(f.get("mandatory"))) / len(fs), 1) if fs else 0.0
    return out

def integration_per_section_pct(bundle: dict) -> dict[str, float]:
    out: dict[str, float] = {}
    for sk in FIELD_BUILDER_SECTIONS:
        fs = _all_fields(bundle, sk)
        out[SECTION_TITLES[sk]] = round(100 * sum(1 for f in fs if bool(f.get("integration_needed"))) / len(fs), 1) if fs else 0.0
    return out

def data_source_breakdown(bundle: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for sk in FIELD_BUILDER_SECTIONS:
        for f in _all_fields(bundle, sk):
            src = str(f.get("data_capture_source") or "").strip() or "Unspecified"
            counts[src] = counts.get(src, 0) + 1
    return counts


def readiness_scores(metrics: dict) -> dict[str, float]:
    """6-axis readiness score (0-100) for radar chart."""
    def cap(v): return max(0.0, min(100.0, float(v)))
    coverage     = min(100.0, metrics["contributors"] * 33.0)         # 3+ contributors = full coverage
    completeness = metrics["completion_pct"]
    field_depth  = min(100.0, (metrics["total_fields"] / 30.0) * 100) # 30 fields = full depth
    rules_logic  = min(100.0, metrics["rule_pct"] * 3)                # 33% rules = full
    approvals    = min(100.0, metrics["approval_stages"] * 25.0)      # 4 stages = full
    dashboards   = min(100.0, metrics["dashboards"] * 12.5)           # 8 dashboards = full
    return {
        "Coverage": cap(coverage),
        "Completeness": cap(completeness),
        "Field depth": cap(field_depth),
        "Workflow rules": cap(rules_logic),
        "Approvals": cap(approvals),
        "Dashboards": cap(dashboards),
    }


def overall_readiness_pct(metrics: dict) -> float:
    s = readiness_scores(metrics)
    return round(sum(s.values()) / len(s), 1)


# ---------- Conflicts ----------

def detect_conflicts(bundle: dict) -> list[dict]:
    out: list[dict] = []
    for sk in FIELD_BUILDER_SECTIONS:
        idx_mand: dict[str, set] = {}
        idx_src:  dict[str, set] = {}
        idx_int:  dict[str, set] = {}
        for c in bundle["contributors"]:
            p = bundle["responses_by_contributor"].get(c["id"], {}).get(sk) or {}
            for f in p.get("fields", []) or []:
                name = (f.get("field") or "").strip().lower()
                if not name: continue
                idx_mand.setdefault(name, set()).add(bool(f.get("mandatory")))
                idx_src .setdefault(name, set()).add(str(f.get("data_capture_source") or "").strip())
                idx_int .setdefault(name, set()).add(bool(f.get("integration_needed")))
        for name, vals in idx_mand.items():
            if len(vals) > 1:
                out.append({"section": SECTION_TITLES[sk], "type": "Mandatory disagreement",
                            "item": name.title(), "detail": "Contributors disagree on whether this field is mandatory."})
        for name, vals in idx_src.items():
            vals = {v for v in vals if v}
            if len(vals) > 1:
                out.append({"section": SECTION_TITLES[sk], "type": "Source disagreement",
                            "item": name.title(), "detail": f"Different data sources proposed: {', '.join(sorted(vals))}"})
        for name, vals in idx_int.items():
            if len(vals) > 1:
                out.append({"section": SECTION_TITLES[sk], "type": "Integration disagreement",
                            "item": name.title(), "detail": "Contributors disagree on whether this field needs integration."})

    sla_idx: dict[str, set] = {}
    for p in _all_payloads(bundle, "approvals"):
        for s in p.get("stages", []) or []:
            n = (s.get("stage") or "").strip().lower()
            if not n: continue
            sla_idx.setdefault(n, set()).add(s.get("sla_hours"))
    for n, vals in sla_idx.items():
        if len(vals) > 1:
            out.append({"section": "Approvals", "type": "SLA disagreement",
                        "item": n.title(), "detail": f"SLA values differ: {sorted(str(v) for v in vals)}"})
    return out


# ---------- Recommendations ----------

def generate_recommendations(bundle: dict, metrics: dict, conflicts: list[dict]) -> list[dict]:
    recs: list[dict] = []
    m = metrics

    if m["contributors"] == 0:
        recs.append({"priority": "High", "topic": "Coverage",
                     "text": "No contributors yet. Share the link with PAM, BSM, PM, and Pre-Sales for this brand."})
        return recs

    if m["contributors"] == 1:
        recs.append({"priority": "Medium", "topic": "Coverage",
                     "text": "Only one contributor so far. At least 2-3 perspectives (PAM + BSM + PM) usually surface gaps. Invite more roles."})

    if m["completion_pct"] < 60:
        recs.append({"priority": "High", "topic": "Completion",
                     "text": f"Only {m['completion_pct']}% of sections are filled. Schedule a 30-min working session with the brand lead to close the gaps."})

    if m["total_fields"] == 0:
        recs.append({"priority": "High", "topic": "Field structure",
                     "text": "No fields proposed in any section. Use 'Load suggestions' as a starting point and tailor."})
    else:
        if m["mandatory_pct"] < 30:
            recs.append({"priority": "Medium", "topic": "Data quality",
                         "text": f"Only {m['mandatory_pct']}% of fields are marked mandatory. Tighter mandatory rules reduce dirty data — review."})
        if m["mandatory_pct"] > 80:
            recs.append({"priority": "Low", "topic": "Adoption",
                         "text": f"{m['mandatory_pct']}% of fields are mandatory. Very strict — risk of users abandoning forms or entering junk."})
        if m["rule_pct"] < 15:
            recs.append({"priority": "Medium", "topic": "Workflow logic",
                         "text": f"Only {m['rule_pct']}% of fields have conditional rules. Capture stage-based mandatory rules (e.g. 'becomes mandatory at Strong Upside') to mirror real-world process."})
        if m["integration_pct"] > 70:
            recs.append({"priority": "High", "topic": "Integrations",
                         "text": f"{m['integration_pct']}% of fields are flagged as needing integration. That's a big Phase-2 backlog — sequence integrations carefully and avoid blocking go-live."})
        if m["integration_pct"] == 0 and m["total_fields"] > 0:
            recs.append({"priority": "Low", "topic": "Integrations",
                         "text": "No fields flagged as needing integration. Validate — even basic Zoho rollouts usually integrate with SAP / Outlook / partner portals."})
        if m["unique_sources"] >= 4:
            recs.append({"priority": "Medium", "topic": "Data sources",
                         "text": f"Data is sourced from {m['unique_sources']} different systems. Define source-of-truth for each entity to avoid conflicts."})

    if m["approval_stages"] == 0:
        recs.append({"priority": "High", "topic": "Approval workflow",
                     "text": "No approval stages defined. Even a 2-stage flow (BSM → Business Head) is a good baseline. Add stages and SLAs."})
    elif m["approval_stages"] < 3:
        recs.append({"priority": "Low", "topic": "Approval workflow",
                     "text": f"Only {m['approval_stages']} approval stage(s). Consider whether finance / credit / cluster head approvals are needed."})

    if m["dashboards"] == 0:
        recs.append({"priority": "High", "topic": "Dashboards",
                     "text": "No dashboards listed. Without target dashboards, Zoho cannot validate the data model supports reporting."})
    elif m["dashboards"] < 4:
        recs.append({"priority": "Medium", "topic": "Dashboards",
                     "text": f"Only {m['dashboards']} dashboard(s) requested. Cover at least: Pipeline by stage, Renewal vs Net New, Forecast vs Actual, Revenue/Margin."})

    if conflicts:
        recs.append({"priority": "High", "topic": "Conflicts",
                     "text": f"{len(conflicts)} conflict(s) detected between contributors. Resolve before handover (see 'Conflicts to resolve' section)."})

    bp_any = any(any((p.get("data_hygiene"), p.get("integrations_wishlist"), p.get("dedup_sops")))
                 for p in _all_payloads(bundle, "best_practices"))
    if not bp_any:
        recs.append({"priority": "Medium", "topic": "Best practices",
                     "text": "No best-practice notes captured. Add at least dedup rules and integration wishlist — these guide Zoho's Phase-2 plan."})

    open_any = any(p.get("pain_points") for p in _all_payloads(bundle, "open_notes"))
    if not open_any:
        recs.append({"priority": "Low", "topic": "Pain points",
                     "text": "No current-tool pain points captured. These are gold for Zoho — they tell the team what NOT to repeat."})

    if not recs:
        recs.append({"priority": "Info", "topic": "Status",
                     "text": "Discovery looks healthy across all dimensions. Ready for Zoho handover."})
    return recs


# ---------- Charts (PNG bytes for embedding) ----------

def _style_axes(ax):
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="both", colors=DARK, labelsize=9)
    ax.yaxis.label.set_color(DARK); ax.xaxis.label.set_color(DARK)
    ax.title.set_color(DARK); ax.title.set_fontsize(11); ax.title.set_fontweight("bold")
    ax.grid(axis="y", color="#EEE", linewidth=0.8)


def chart_fields_per_section_png(bundle: dict) -> bytes:
    data = fields_per_section_count(bundle)
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    labels = list(data.keys()); vals = list(data.values())
    bars = ax.bar(range(len(labels)), vals, color=RED, width=0.55)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=8)
    ax.set_ylabel("# fields proposed")
    ax.set_title("Fields proposed per section")
    for b, v in zip(bars, vals):
        if v: ax.text(b.get_x() + b.get_width()/2, v + 0.2, str(v), ha="center", fontsize=8, color=DARK)
    _style_axes(ax); fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()


def chart_mandatory_pct_png(bundle: dict) -> bytes:
    data = mandatory_per_section_pct(bundle)
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    labels = list(data.keys()); vals = list(data.values())
    ax.barh(range(len(labels)), vals, color=DARK, height=0.55)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("% mandatory"); ax.set_xlim(0, 100)
    ax.set_title("Mandatory % per section")
    for i, v in enumerate(vals):
        if v: ax.text(v + 1, i, f"{v}%", va="center", fontsize=8, color=DARK)
    _style_axes(ax); fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()


def chart_integration_per_section_png(bundle: dict) -> bytes:
    data = integration_per_section_pct(bundle)
    fig, ax = plt.subplots(figsize=(7, 3.4), dpi=150)
    labels = list(data.keys()); vals = list(data.values())
    ax.barh(range(len(labels)), vals, color="#0F4C81", height=0.55)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("% needing integration"); ax.set_xlim(0, 100)
    ax.set_title("Integration intensity per section")
    for i, v in enumerate(vals):
        if v: ax.text(v + 1, i, f"{v}%", va="center", fontsize=8, color=DARK)
    _style_axes(ax); fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()


def chart_source_breakdown_png(bundle: dict) -> bytes:
    data = data_source_breakdown(bundle) or {"No data": 1}
    fig, ax = plt.subplots(figsize=(5.5, 3.8), dpi=150)
    labels = list(data.keys()); vals = list(data.values())
    colors = (ACCENTS * (len(labels)//len(ACCENTS) + 1))[:len(labels)]
    wedges, _ = ax.pie(vals, colors=colors, startangle=90, wedgeprops={"width": 0.42, "edgecolor": "white"})
    ax.set_title("Data-capture source mix", color=DARK, fontsize=11, fontweight="bold")
    ax.legend(wedges, [f"{l} ({v})" for l, v in zip(labels, vals)], loc="center left",
              bbox_to_anchor=(1.0, 0.5), fontsize=8, frameon=False)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight"); plt.close(fig)
    return buf.getvalue()


def chart_completion_donut_png(metrics: dict) -> bytes:
    pct = metrics.get("completion_pct", 0.0)
    fig, ax = plt.subplots(figsize=(3.4, 3.4), dpi=150)
    ax.pie([pct, max(0.001, 100 - pct)], colors=[RED, "#EEE"], startangle=90,
           wedgeprops={"width": 0.32, "edgecolor": "white"})
    ax.text(0, 0.05, f"{pct:.0f}%", ha="center", va="center", fontsize=22, color=DARK, weight="bold")
    ax.text(0, -0.25, "Section completion", ha="center", va="center", fontsize=8, color=GREY)
    ax.set_aspect("equal"); fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()


def chart_readiness_radar_png(metrics: dict) -> bytes:
    scores = readiness_scores(metrics)
    labels = list(scores.keys()); vals = list(scores.values())
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
    vals_loop = vals + [vals[0]]; angles_loop = angles + [angles[0]]
    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=150, subplot_kw={"projection": "polar"})
    ax.plot(angles_loop, vals_loop, color=RED, linewidth=2)
    ax.fill(angles_loop, vals_loop, color=RED, alpha=0.20)
    ax.set_xticks(angles); ax.set_xticklabels(labels, fontsize=8, color=DARK)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7, color=GREY)
    ax.set_ylim(0, 100); ax.spines["polar"].set_color(GREY)
    ax.set_title(f"Brand readiness — {overall_readiness_pct(metrics):.0f}/100",
                 color=DARK, fontsize=11, fontweight="bold", pad=18)
    fig.tight_layout()
    buf = BytesIO(); fig.savefig(buf, format="png"); plt.close(fig)
    return buf.getvalue()
