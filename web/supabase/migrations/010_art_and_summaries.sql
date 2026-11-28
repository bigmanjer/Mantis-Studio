-- Book art: AI covers and scene illustrations. Images are regenerated on demand from these
-- settings (prompt + seed + size), so nothing large is stored.
create table if not exists public.book_images (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  chapter_id uuid references public.chapters(id) on delete cascade,
  kind text not null check (kind in ('cover', 'illustration')),
  prompt text not null,
  seed integer not null,
  width integer not null,
  height integer not null,
  caption text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists book_images_project_idx on public.book_images(project_id, kind, created_at);
alter table public.book_images enable row level security;
drop policy if exists "book_images: owner all" on public.book_images;
create policy "book_images: owner all" on public.book_images for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
drop trigger if exists book_images_owner on public.book_images;
create trigger book_images_owner before insert or update on public.book_images
  for each row execute function public.check_project_owner();

-- The chosen cover and how its title is laid out.
alter table public.projects add column if not exists cover_id uuid references public.book_images(id) on delete set null;
alter table public.projects add column if not exists cover_style jsonb;

-- Chapter summaries written by the AI keep refreshing as the chapter changes; one the writer
-- typed is never overwritten.
alter table public.chapters add column if not exists summary_auto boolean not null default false;
