-- v4 migration. Run this once in Supabase SQL Editor.
-- Idempotent: safe to re-run.
-- Adds the "final submission" lifecycle to contributors.

alter table contributors add column if not exists final_submitted_at timestamptz;
alter table contributors add column if not exists is_locked          boolean not null default false;

create index if not exists contributors_locked_idx on contributors(brand, is_locked);
