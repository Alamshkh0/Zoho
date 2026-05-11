"""Thin Supabase client + queries.

Tables: contributors, responses, brands, audit_log (see schema.sql + schema_v3.sql).
"""
import re
from datetime import datetime
from typing import Any, Optional
from supabase import create_client, Client
import config

_client: Client | None = None

def client() -> Client:
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("Supabase URL/key missing. Check .env or Streamlit secrets.")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


# ========== CONTRIBUTORS ==========

def find_contributor_by_email(brand: str, email: str) -> Optional[dict]:
    if not email: return None
    res = client().table("contributors").select("*").eq("brand", brand).ilike("email", email.strip()).execute()
    rows = res.data or []
    return rows[0] if rows else None


def upsert_contributor(brand: str, name: str, email: str, role: str) -> dict:
    existing = find_contributor_by_email(brand, email)
    if existing:
        client().table("contributors").update({
            "name": name, "role": role,
            "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "+00:00",
        }).eq("id", existing["id"]).execute()
        return {**existing, "name": name, "role": role}
    res = client().table("contributors").insert({
        "brand": brand, "name": name, "email": email.strip(), "role": role,
    }).execute()
    return res.data[0]


def save_response(contributor_id: str, section_key: str, payload: dict[str, Any]) -> None:
    existing = client().table("responses").select("id").eq("contributor_id", contributor_id).eq("section_key", section_key).execute()
    if existing.data:
        client().table("responses").update({"payload": payload}).eq("id", existing.data[0]["id"]).execute()
    else:
        client().table("responses").insert({
            "contributor_id": contributor_id, "section_key": section_key, "payload": payload,
        }).execute()


def list_contributors(brand: str | None = None) -> list[dict]:
    q = client().table("contributors").select("*").order("submitted_at", desc=True)
    if brand:
        q = q.eq("brand", brand)
    return q.execute().data or []


def get_responses_for_contributor(contributor_id: str) -> dict[str, dict]:
    rows = client().table("responses").select("section_key,payload").eq("contributor_id", contributor_id).execute().data or []
    return {r["section_key"]: r["payload"] for r in rows}


def get_brand_bundle(brand: str) -> dict:
    contribs = list_contributors(brand)
    resp_map: dict[str, dict] = {}
    for c in contribs:
        resp_map[c["id"]] = get_responses_for_contributor(c["id"])
    return {
        "brand": brand, "contributors": contribs,
        "responses_by_contributor": resp_map,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def count_contributors_per_brand() -> dict[str, int]:
    rows = client().table("contributors").select("brand").execute().data or []
    out: dict[str, int] = {}
    for r in rows:
        out[r["brand"]] = out.get(r["brand"], 0) + 1
    return out


# ========== BRANDS ==========

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "brand"


def list_brands(active_only: bool = True) -> list[dict]:
    """Read brands from DB. Falls back to config.BRANDS if table missing."""
    try:
        q = client().table("brands").select("*").order("name")
        if active_only: q = q.eq("active", True)
        return q.execute().data or []
    except Exception:
        return [{"id": None, "name": b, "slug": _slugify(b), "logo_url": None,
                 "starter_template": None, "active": True} for b in config.BRANDS]


def brand_names(active_only: bool = True) -> list[str]:
    return [b["name"] for b in list_brands(active_only=active_only)]


def add_brand(name: str, logo_url: str | None = None,
              starter_template: dict | None = None, created_by: str | None = None) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("Brand name required")
    payload = {
        "name": name, "slug": _slugify(name),
        "logo_url": logo_url or None,
        "starter_template": starter_template or None,
        "active": True, "created_by": created_by,
    }
    res = client().table("brands").insert(payload).execute()
    return res.data[0]


def update_brand(brand_id: str, **fields) -> None:
    if not fields: return
    client().table("brands").update(fields).eq("id", brand_id).execute()


def archive_brand(brand_id: str) -> None:
    client().table("brands").update({"active": False}).eq("id", brand_id).execute()


def unarchive_brand(brand_id: str) -> None:
    client().table("brands").update({"active": True}).eq("id", brand_id).execute()
