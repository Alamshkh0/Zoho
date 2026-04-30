-- Run this once in Supabase SQL Editor (Dashboard -> SQL -> New query -> paste -> Run)
-- This creates the tables the app needs.

create extension if not exists "pgcrypto";

create table if not exists contributors (
    id uuid primary key default gen_random_uuid(),
    brand text not null,
    name text not null,
    email text not null,
    role text not null,
    submitted_at timestamptz not null default now()
);

create table if not exists responses (
    id uuid primary key default gen_random_uuid(),
    contributor_id uuid not null references contributors(id) on delete cascade,
    section_key text not null,
    payload jsonb not null
);

create index if not exists responses_contrib_idx on responses(contributor_id);
create index if not exists contributors_brand_idx on contributors(brand);

-- Allow the anon key (used by the public Streamlit app) to read/insert.
-- For an internal discovery tool this is acceptable. Tighten later if needed.
alter table contributors enable row level security;
alter table responses    enable row level security;

drop policy if exists contrib_all on contributors;
drop policy if exists resp_all    on responses;

create policy contrib_all on contributors for all using (true) with check (true);
create policy resp_all    on responses    for all using (true) with check (true);
