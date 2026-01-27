# Auth Setup (Supabase + Optional OIDC)

This app supports **MANTIS accounts** via Supabase Auth (email/password + magic link + password reset). OIDC buttons (Google/Microsoft/Apple) remain optional.

## Supabase (required for email signup/login)

1. Create a Supabase project.
2. Enable **Email/Password** and/or **Magic Link** in Supabase Auth settings.
3. Copy the project **URL** and **anon public key**.

### Streamlit secrets

Add to `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
[supabase]
url = "https://your-project.supabase.co"
anon_key = "your-anon-public-key"
```

Environment variable alternative:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-public-key"
```

## Optional OIDC providers

If you want Google/Microsoft/Apple buttons, configure `auth` providers in secrets:

```toml
[auth]
cookie_secret = "streamlit-cookie-secret"

[auth.providers.google]
client_id = "..."
client_secret = "..."

[auth.providers.microsoft]
client_id = "..."
client_secret = "..."

[auth.providers.apple]
client_id = "..."
client_secret = "..."
```

## Notes

- Email sign-in requires Supabase; without it the email form will be disabled.
- Password reset and magic-link sends are rate-limited in-app to avoid abuse.
- Guest mode remains available, but export is gated behind sign-in.
