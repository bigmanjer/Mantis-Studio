-- Knowledge Base (original MANTIS feature): the writer's own reference documents, split into
-- searchable passages. project_id null = available to all of the writer's books.

create table if not exists public.knowledge_docs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  project_id uuid references public.projects(id) on delete cascade,
  title text not null,
  category text not null default 'reference',
  word_count integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists knowledge_docs_user_idx on public.knowledge_docs(user_id, created_at desc);

create table if not exists public.knowledge_chunks (
  id bigint generated always as identity primary key,
  doc_id uuid not null references public.knowledge_docs(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  project_id uuid references public.projects(id) on delete cascade,
  position integer not null,
  content text not null,
  tsv tsvector generated always as (to_tsvector('english', content)) stored
);
create index if not exists knowledge_chunks_tsv_idx on public.knowledge_chunks using gin(tsv);
create index if not exists knowledge_chunks_doc_idx on public.knowledge_chunks(doc_id, position);
create index if not exists knowledge_chunks_user_idx on public.knowledge_chunks(user_id, project_id);

alter table public.knowledge_docs enable row level security;
alter table public.knowledge_chunks enable row level security;
drop policy if exists "knowledge_docs: owner all" on public.knowledge_docs;
create policy "knowledge_docs: owner all" on public.knowledge_docs for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id and (project_id is null or exists (select 1 from public.projects p where p.id = project_id and p.user_id = auth.uid())));
drop policy if exists "knowledge_chunks: owner all" on public.knowledge_chunks;
create policy "knowledge_chunks: owner all" on public.knowledge_chunks for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id and exists (select 1 from public.knowledge_docs d where d.id = doc_id and d.user_id = auth.uid()));

-- Ranked full-text search over the caller's own passages (RLS still applies: security invoker).
create or replace function public.search_knowledge(p_query text, p_project uuid, p_limit integer default 6)
returns table (doc_id uuid, title text, category text, content text, rank real)
language sql stable security invoker set search_path = public as $$
  select c.doc_id, d.title, d.category, c.content, ts_rank(c.tsv, q) as rank
  from public.knowledge_chunks c
  join public.knowledge_docs d on d.id = c.doc_id
  cross join websearch_to_tsquery('english', p_query) q
  where c.user_id = auth.uid()
    and (c.project_id is null or c.project_id = p_project)
    and c.tsv @@ q
  order by rank desc
  limit least(greatest(p_limit, 1), 20);
$$;
grant execute on function public.search_knowledge(text, uuid, integer) to authenticated;

-- Per-book settings: let the AI read the Knowledge Base, and chosen author style lenses.
alter table public.projects add column if not exists use_knowledge boolean not null default true;
alter table public.projects add column if not exists style_lenses text[] not null default '{}';
