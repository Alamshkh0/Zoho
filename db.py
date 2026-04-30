"""Thin Supabase client + queries the app uses.

Two tables: contributors and responses (see schema.sql).
A "session" for a brand is just the set of contributors who picked that brand.
"""
from datetime import datetime
from typing import Any
from supabase import create_client, Client
import config

_client: Client | None = None

def client() -> Client:
    global _client
    if _client is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError("Supabase URL/key missing. Check .env file.")
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def add_contributor(brand: str, name: str, email: str, role: str) -> str:
    res = client().table("contributors").insert({
        "brand": brand, "name": name, "email": email, "role": role,
    }).execute()
    return res.data[0]["id"]


def save_response(contributor_id: str, section_key: str, payload: dict[str, Any]) -> None:
    # one row per (contributor, section). Update if exists, insert otherwise.
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
    Returns: {brand, contributors:[...], responses_by_contributor:{id: {section: payload}}}
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
