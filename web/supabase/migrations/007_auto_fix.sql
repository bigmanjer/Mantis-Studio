-- Fix continuity slips automatically while writing (with Undo and a History copy). On by default.
alter table public.projects add column if not exists auto_fix boolean not null default true;
