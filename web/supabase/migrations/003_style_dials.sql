-- 003: per-project style dials (pace, interiority, imagery, dialogue, mood), 0-100 each.
alter table public.projects add column if not exists style_dials jsonb;
