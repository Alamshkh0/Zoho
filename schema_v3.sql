-- v3 migration. Run this once in Supabase SQL Editor (Dashboard -> SQL -> New query).
-- Idempotent: safe to re-run.

create extension if not exists "pgcrypto";

-- ---------- Brands (managed via admin UI) ----------
create table if not exists brands (
    id uuid primary key default gen_random_uuid(),
    name text not null unique,
    slug text not null unique,
    logo_url text,
    starter_template jsonb,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    created_by text
);
create index if not exists brands_active_idx on brands(active);

-- ---------- Audit log ----------
create table if not exists audit_log (
    id bigserial primary key,
    ts timestamptz not null default now(),
    event text not null,
    actor_email text,
    actor_ip text,
    actor_ua text,
    brand text,
    contributor_id uuid,
    section_key text,
    detail jsonb
);
create index if not exists audit_log_ts_idx     on audit_log(ts desc);
create index if not exists audit_log_brand_idx  on audit_log(brand, ts desc);
create index if not exists audit_log_email_idx  on audit_log(actor_email, ts desc);
create index if not exists audit_log_event_idx  on audit_log(event, ts desc);

alter table brands    enable row level security;
alter table audit_log enable row level security;

drop policy if exists brands_all on brands;
drop policy if exists audit_all  on audit_log;

create policy brands_all on brands    for all using (true) with check (true);
create policy audit_all  on audit_log for all using (true) with check (true);

-- ---------- Seed default brands (only if table is empty) ----------
insert into brands (name, slug, active)
select v.name, v.slug, true
from (values
  ('AWS',       'aws'),
  ('Microsoft', 'microsoft'),
  ('Red Hat',   'red-hat')
) as v(name, slug)
where not exists (select 1 from brands);
