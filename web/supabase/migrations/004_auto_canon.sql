-- Automatic World Bible / canon updates while writing (original MANTIS "scan on save"). On by default.
alter table public.projects add column if not exists auto_canon boolean not null default true;
