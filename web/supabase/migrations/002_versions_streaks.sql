-- 002: chapter version history, daily writing log, daily goal. Safe to re-run.

-- ---------- chapter versions (snapshots) ----------
create table if not exists public.chapter_versions (
  id uuid primary key default gen_random_uuid(),
  chapter_id uuid not null references public.chapters(id) on delete cascade,
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  title text not null default '',
  content text not null default '',
  word_count integer not null default 0,
  reason text not null default 'Autosave',
  created_at timestamptz not null default now()
);
create index if not exists chapter_versions_chapter_idx on public.chapter_versions(chapter_id, created_at desc);

alter table public.chapter_versions enable row level security;
drop policy if exists "chapter_versions: owner all" on public.chapter_versions;
create policy "chapter_versions: owner all" on public.chapter_versions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

drop trigger if exists chapter_versions_owner on public.chapter_versions;
create trigger chapter_versions_owner before insert on public.chapter_versions
  for each row execute function public.check_project_owner();

-- Keep the newest 50 versions per chapter.
create or replace function public.prune_chapter_versions()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  delete from public.chapter_versions
  where chapter_id = new.chapter_id
    and id not in (
      select id from public.chapter_versions
      where chapter_id = new.chapter_id
      order by created_at desc
      limit 50
    );
  return null;
end;
$$;
drop trigger if exists chapter_versions_prune on public.chapter_versions;
create trigger chapter_versions_prune after insert on public.chapter_versions
  for each row execute function public.prune_chapter_versions();

-- ---------- daily writing log (for goals and streaks) ----------
create table if not exists public.writing_days (
  user_id uuid not null references auth.users(id) on delete cascade,
  day date not null,
  words integer not null default 0,
  primary key (user_id, day)
);
alter table public.writing_days enable row level security;
drop policy if exists "writing_days: read own" on public.writing_days;
create policy "writing_days: read own" on public.writing_days
  for select using (auth.uid() = user_id);

-- Record words written today for the signed-in user. Ignores negatives and absurd jumps
-- (e.g. pasting a whole manuscript) so streaks reflect real writing.
create or replace function public.log_words(p_words integer, p_day date)
returns void language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null or p_words is null or p_words <= 0 or p_words > 5000 then
    return;
  end if;
  if p_day < current_date - 1 or p_day > current_date + 1 then
    return;
  end if;
  insert into public.writing_days (user_id, day, words)
  values (auth.uid(), p_day, p_words)
  on conflict (user_id, day) do update set words = writing_days.words + excluded.words;
end;
$$;
revoke execute on function public.log_words(integer, date) from public, anon;
grant execute on function public.log_words(integer, date) to authenticated;

-- ---------- daily word goal ----------
alter table public.profiles add column if not exists daily_goal integer not null default 500;
