-- Trash: deleted books stay restorable for 30 days instead of disappearing at once.
alter table public.projects add column if not exists deleted_at timestamptz;
create index if not exists projects_trash_idx on public.projects(user_id, deleted_at);

-- Books in the Trash don't count toward the Free plan's 2-project limit.
-- (Restoring checks the limit again in the app.)
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
    select count(*) into owned from public.projects where user_id = new.user_id and deleted_at is null;
    if owned >= 2 then
      raise exception 'PLAN_LIMIT: The Free plan includes 2 projects. Upgrade for unlimited projects.';
    end if;
  end if;
  return new;
end;
$$;
