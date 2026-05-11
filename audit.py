"""Lightweight audit logging.

audit.log(event, **details) inserts a row into the audit_log table. IP + UA are
read from st.context.headers when available (Streamlit 1.40+). Failure is
swallowed silently — we never block the app on a logging error.
"""
from typing import Any
import streamlit as st

import db


def _request_ctx() -> dict[str, str]:
    """Pull IP + UA from Streamlit's request context, if available."""
    ip = ""
    ua = ""
    try:
        h = st.context.headers
        ip = h.get("x-forwarded-for", "").split(",")[0].strip() or h.get("x-real-ip", "") or ""
        ua = h.get("user-agent", "")
    except Exception:
        pass
    return {"ip": ip, "ua": ua}


def log(event: str,
        actor_email: str | None = None,
        brand: str | None = None,
        contributor_id: str | None = None,
        section_key: str | None = None,
        **detail: Any) -> None:
    """Insert one audit_log row. Best-effort — never raises."""
    ctx = _request_ctx()
    actor = actor_email or st.session_state.get("email") or None
    br    = brand or st.session_state.get("brand") or None
    try:
        db.client().table("audit_log").insert({
            "event":          event,
            "actor_email":    actor,
            "actor_ip":       ctx["ip"] or None,
            "actor_ua":       ctx["ua"] or None,
            "brand":          br,
            "contributor_id": contributor_id,
            "section_key":    section_key,
            "detail":         detail or None,
        }).execute()
    except Exception:
        pass


def list_recent(limit: int = 500, filters: dict | None = None) -> list[dict]:
    """For the Admin → Audit Log page."""
    try:
        q = db.client().table("audit_log").select("*").order("ts", desc=True).limit(limit)
        if filters:
            if filters.get("event"):  q = q.eq("event", filters["event"])
            if filters.get("brand"):  q = q.eq("brand", filters["brand"])
            if filters.get("email"):  q = q.ilike("actor_email", f"%{filters['email']}%")
            if filters.get("since"):  q = q.gte("ts", filters["since"])
        return q.execute().data or []
    except Exception:
        return []
