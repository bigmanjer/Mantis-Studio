# Supabase Auth Runbook

MANTIS Studio uses Supabase Auth for email/password account creation, login, and password reset.
Guest mode remains available, but export is gated behind a logged-in account.

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

Create a `profiles` table so account settings can store display names and usernames:

```sql
create table if not exists public.profiles (
  id uuid primary key,
  email text,
  display_name text,
  username text unique,
  created_at timestamp with time zone default now()
);
```

Optional: add RLS policies if you need stricter access controls.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Account Access shows “Supabase is not configured” | Secrets missing or incorrect | Verify `SUPABASE_URL` + `SUPABASE_ANON_KEY` in secrets or environment. |
| Signup succeeds but login fails | Email confirmation required | Check Supabase Auth settings and inbox for confirmation email. |
| Password reset not received | Email provider not configured | Configure SMTP in Supabase Auth settings. |
| Account settings save fails | `profiles` table missing or RLS blocks updates | Create the table and adjust RLS policies. |

## Notes

- Supabase handles email confirmations and password reset emails.
- The app rate-limits reset requests in-session to avoid abuse.
- Guest mode remains available, but export requires a signed-in account.
