-- Relationship map (original MANTIS "Relationship graph"): links the writer draws between
-- World Bible entries. Shared-chapter links are computed in the app and not stored.
create table if not exists public.entity_links (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  source_id uuid not null references public.entities(id) on delete cascade,
  target_id uuid not null references public.entities(id) on delete cascade,
  kind text not null check (kind in ('ally', 'rival', 'family', 'love', 'mentor', 'enemy', 'mystery', 'other')),
  note text not null default '',
  created_at timestamptz not null default now(),
  unique (source_id, target_id),
  check (source_id <> target_id)
);
create index if not exists entity_links_project_idx on public.entity_links(project_id);

alter table public.entity_links enable row level security;
drop policy if exists "entity_links: owner all" on public.entity_links;
create policy "entity_links: owner all" on public.entity_links for all
  using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop trigger if exists entity_links_owner on public.entity_links;
create trigger entity_links_owner before insert or update on public.entity_links
  for each row execute function public.check_project_owner();
