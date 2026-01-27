# Auth Setup (Supabase)

MANTIS Studio uses Supabase Auth for email/password account creation, login, and password reset.
Guest mode remains available, but export is gated behind a logged-in account.

## Supabase project

1. Create a Supabase project.
2. Enable **Email/Password** in Supabase Auth settings.
3. Copy the project **URL** and **anon public key**.

## Streamlit secrets

Add to `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

Environment variable alternative:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-public-key"
```

## Profiles table

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

## Notes

- Password reset and sign-up confirmation emails are sent by Supabase.
- The app rate-limits reset requests in-session to avoid abuse.
- Guest mode remains available, but export requires a signed-in account.
