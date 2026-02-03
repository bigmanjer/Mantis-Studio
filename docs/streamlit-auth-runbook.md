# Supabase Auth Runbook

MANTIS Studio uses Supabase Auth (email/password) for account access. This runbook covers setup
and troubleshooting for local dev and Streamlit Cloud.

## 1) Configure Supabase

1. Create a Supabase project.
2. Enable **Email/Password** in Supabase Auth settings.
3. Copy the project **URL** and **anon public key**.

## 2) Configure Streamlit secrets

Add to `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

Local environment variables also work:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-public-key"
```

## 3) Profiles table

Create a `profiles` table to store display names and usernames:

```sql
create table if not exists public.profiles (
  id uuid primary key,
  email text,
  display_name text,
  username text unique,
  created_at timestamp with time zone default now()
);
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Account Access shows “Supabase is not configured” | Secrets missing or incorrect | Verify `SUPABASE_URL` + `SUPABASE_ANON_KEY` in secrets or environment. |
| Signup succeeds but login fails | Email confirmation required | Check Supabase Auth settings and inbox for confirmation email. |
| Password reset not received | Email provider not configured | Configure SMTP in Supabase Auth settings. |
| Account settings save fails | `profiles` table missing or RLS blocks updates | Create the table and adjust RLS policies. |

## Notes

- Supabase handles email confirmations and password reset emails.
- Guest mode is always available, but export is locked for guests.
