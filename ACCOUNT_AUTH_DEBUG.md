# MANTIS Account Auth Debug Guide

## Required Streamlit secrets
Configure these in Streamlit Cloud → App → Settings → Secrets (or `.streamlit/secrets.toml` locally).

- `SUPABASE_URL` (string)
- `SUPABASE_ANON_KEY` (string; use the anon/public key, not the service role key)
- `SUPABASE_REDIRECT_URL` (optional; where password reset/email confirmation should return)

## Supabase checklist
In Supabase → Authentication:

1. **Providers**
   - Email provider **ON**
   - “Confirm email” optional but recommended
2. **Settings**
   - “Enable signups” **ON**
   - “Site URL” set to your Streamlit Cloud app URL
   - Add your Streamlit Cloud URL to **Redirect URLs** (match `SUPABASE_REDIRECT_URL` if used)

## Where to see logs
Streamlit Cloud → “Manage app” → “Logs”.  
Auth events are logged with prefixes like `[SIGNUP]`, `[LOGIN]`, `[RESET]`, and `[SELFTEST]` **when debug mode is on**.

## How to verify new users
Supabase → Authentication → **Users**.  
Check **Logs → Auth** for any errors returned by Supabase.

## Safe debug panel
The Account page shows a “Debug (admin)” expander with:

- `auth_is_configured()` status
- Secrets presence (boolean only)
- Redirect URL in use
- A lightweight self-test status

No secrets or full emails are printed.
