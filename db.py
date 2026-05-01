"""Thin Supabase client + queries the app uses.

Two tables: contributors and responses (see schema.sql).
A "session" for a brand = the set of contributors who picked that brand.
Uniqueness rule: one (brand, email) → one contributor row (we look up + reuse).
"""
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


def find_contributor_by_email(brand: str, email: str) -> Optional[dict]:
    """Returns the contributor row if (brand, email) already exists, else None."""
    if not email:
        return None
    res = client().table("contributors").select("*").eq("brand", brand).ilike("email", email.strip()).execute()
    rows = res.data or []
    return rows[0] if rows else None


def upsert_contributor(brand: str, name: str, email: str, role: str) -> dict:
    """One row per (brand, email). Returns the row (existing or newly created)."""
    existing = find_contributor_by_email(brand, email)
    if existing:
        client().table("contributors").update({
            "name": name, "role": role, "submitted_at": datetime.utcnow().isoformat(timespec="seconds") + "+00:00",
        }).eq("id", existing["id"]).execute()
        return {**existing, "name": name, "role": role}
    res = client().table("contributors").insert({
        "brand": brand, "name": name, "email": email.strip(), "role": role,
    }).execute()
    return res.data[0]


def save_response(contributor_id: str, section_key: str, payload: dict[str, Any]) -> None:
    """One row per (contributor, section). Update if exists, insert otherwise."""
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
    """Everything needed to render the brand dashboard / reports.
    Returns: {brand, contributors:[...], responses_by_contributor:{id: {section: payload}}, generated_at}
    """
    contribs = list_contributors(brand)
    resp_map: dict[str, dict] = {}
    for c in contribs:
        resp_map[c["id"]] = get_responses_for_contributor(c["id"])
    return {
        "brand": brand,
        "contributors": contribs,
        "responses_by_contributor": resp_map,
        "generated_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }


def count_contributors_per_brand() -> dict[str, int]:
    """For brand stat cards on landing page."""
    rows = client().table("contributors").select("brand").execute().data or []
    out: dict[str, int] = {}
    for r in rows:
        out[r["brand"]] = out.get(r["brand"], 0) + 1
    return out
