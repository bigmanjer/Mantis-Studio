-- MANTIS Studio web schema. Paste into Supabase: SQL Editor -> New query -> Run.
-- Every user-owned table has Row Level Security so users can only ever see their own rows.
-- Billing columns on profiles are writable ONLY by the server (service role), never by the browser.

create extension if not exists "pgcrypto";

-- ---------- profiles (one per auth user) ----------
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text,
  display_name text,
  plan text not null default 'free' check (plan in ('free', 'pro', 'studio')),
  stripe_customer_id text unique,
  stripe_subscription_id text,
  subscription_status text,
  current_period_end timestamptz,
  ai_provider text not null default 'groq' check (ai_provider in ('groq', 'openai')),
  ai_model text,
  ai_key_encrypted text,           -- bring-your-own key, AES-GCM encrypted by the server
  is_admin boolean not null default false,  -- owner accounts: full access, see /app/admin
  created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "profiles: read own" on public.profiles;
create policy "profiles: read own" on public.profiles
  for select using (auth.uid() = id);
-- No insert/update/delete policies: those go through the server with the service role key.

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email) values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ---------- projects ----------
create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  title text not null default 'Untitled Project',
  author text not null default '',
  genre text not null default '',
  premise text not null default '',
  outline text not null default '',
  canon_rules text not null default '',   -- hard canon rules the AI must never break
  style_guide text not null default '',   -- voice / tone guidance for the AI
  target_words integer not null default 80000,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists projects_user_idx on public.projects(user_id, updated_at desc);

-- ---------- chapters ----------
create table if not exists public.chapters (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  position integer not null default 0,
  title text not null default 'New Chapter',
  content text not null default '',
  summary text not null default '',
  word_count integer not null default 0,
  updated_at timestamptz not null default now()
);
create index if not exists chapters_project_idx on public.chapters(project_id, position);

-- ---------- world bible entities ----------
create table if not exists public.entities (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade default auth.uid(),
  name text not null,
  category text not null default 'Character'
    check (category in ('Character', 'Location', 'Item', 'Faction', 'Lore')),
  description text not null default '',
  aliases text[] not null default '{}',
  created_at timestamptz not null default now()
);
create index if not exists entities_project_idx on public.entities(project_id, category, name);

-- Owner-only access for the three content tables.
do $$
declare t text;
begin
  foreach t in array array['projects', 'chapters', 'entities'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "%s: owner all" on public.%I', t, t);
    execute format(
      'create policy "%s: owner all" on public.%I for all using (auth.uid() = user_id) with check (auth.uid() = user_id)',
      t, t);
  end loop;
end $$;

-- Child rows must belong to a project the same user owns.
create or replace function public.check_project_owner()
returns trigger language plpgsql as $$
begin
  if not exists (select 1 from public.projects p where p.id = new.project_id and p.user_id = new.user_id) then
    raise exception 'project not owned by user';
  end if;
  return new;
end;
$$;
drop trigger if exists chapters_owner on public.chapters;
create trigger chapters_owner before insert or update on public.chapters
  for each row execute function public.check_project_owner();
drop trigger if exists entities_owner on public.entities;
create trigger entities_owner before insert or update on public.entities
  for each row execute function public.check_project_owner();

-- Plan limit: Free accounts may own at most 2 projects (keep in sync with src/lib/plans.ts).
create or replace function public.enforce_project_limit()
returns trigger language plpgsql security definer set search_path = public as $$
declare
  user_plan text;
  admin boolean;
  owned integer;
begin
  select plan, is_admin into user_plan, admin from public.profiles where id = new.user_id;
  if coalesce(admin, false) then
    return new;
  end if;
  if coalesce(user_plan, 'free') = 'free' then
    select count(*) into owned from public.projects where user_id = new.user_id;
    if owned >= 2 then
      raise exception 'PLAN_LIMIT: The Free plan includes 2 projects. Upgrade for unlimited projects.';
    end if;
  end if;
  return new;
end;
$$;
drop trigger if exists projects_limit on public.projects;
create trigger projects_limit before insert on public.projects
  for each row execute function public.enforce_project_limit();

-- ---------- AI usage metering (server-only) ----------
create table if not exists public.ai_usage (
  user_id uuid not null references auth.users(id) on delete cascade,
  period text not null,             -- 'YYYY-MM'
  requests integer not null default 0,
  tokens integer not null default 0,
  primary key (user_id, period)
);
alter table public.ai_usage enable row level security;
drop policy if exists "ai_usage: read own" on public.ai_usage;
create policy "ai_usage: read own" on public.ai_usage
  for select using (auth.uid() = user_id);

create or replace function public.add_ai_usage(p_user uuid, p_period text, p_tokens integer)
returns void language sql security definer set search_path = public as $$
  insert into public.ai_usage (user_id, period, requests, tokens)
  values (p_user, p_period, 1, p_tokens)
  on conflict (user_id, period)
  do update set requests = ai_usage.requests + 1, tokens = ai_usage.tokens + excluded.tokens;
$$;
revoke execute on function public.add_ai_usage(uuid, text, integer) from public, anon, authenticated;

-- Existing databases: add the admin flag (safe to re-run).
alter table public.profiles add column if not exists is_admin boolean not null default false;
-- Make an account admin:
-- update public.profiles set is_admin = true where email = 'you@example.com';
