# Streamlit Auth Runbook (MANTIS Studio)

## Overview
MANTIS Studio uses Streamlit’s native OIDC authentication (`st.login` / `st.user`). When providers are misconfigured (missing client ID/secret or redirect URI), Streamlit Cloud will show the default **Account Access** screen with the message _“Configure Google OIDC in secrets.toml to enable.”_ To avoid that, ensure secrets are configured before enabling provider buttons and confirm the redirect URLs match your deployment.

## Secrets configuration (local + Cloud)
Add the following to `.streamlit/secrets.toml` locally, or paste into **Streamlit Community Cloud → App → Settings → Secrets**.

```toml
[auth]
redirect_uri = "https://<your-app>.streamlit.app/oauth2callback"
cookie_secret = "replace-with-a-long-random-string"
provider_account_url = "https://your-idp.example.com/account"
# Optional: turn on debug panels in Account page
# debug_auth = true

[auth.google]
client_id = "replace-with-google-client-id"
client_secret = "replace-with-google-client-secret"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[auth.microsoft]
client_id = "replace-with-microsoft-client-id"
client_secret = "replace-with-microsoft-client-secret"
server_metadata_url = "https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration"

# Optional (Apple-ready)
[auth.apple]
client_id = "replace-with-apple-client-id"
client_secret = "replace-with-apple-client-secret"
server_metadata_url = "https://appleid.apple.com/.well-known/openid-configuration"

# Optional authorization controls
[authz]
allowed_domains = ["example.com"]
allowed_emails = ["admin@example.com"]
admin_emails = ["admin@example.com"]
```

### Redirect URLs
- **Local:** `http://localhost:8501/oauth2callback`
- **Streamlit Cloud:** `https://<your-app>.streamlit.app/oauth2callback`

Ensure you add both to your Google/Microsoft OIDC console (if you support local dev and production).

## Common failure modes
| Symptom | Likely cause | Fix |
| --- | --- | --- |
| “Configure Google OIDC in secrets.toml to enable.” | `st.login` called but `auth.google` is missing or incomplete. | Add `auth.google` with `client_id`, `client_secret`, `server_metadata_url`. |
| Login completes but app shows “We could not determine a user identifier.” | Provider returned a user object without `email` or `sub`. | Enable `debug_auth = true` and confirm fields; ensure provider returns `email` or `sub`. |
| Login completes but still in Guest mode | `st.user` missing or auth cookies invalid. | Clear cookies, re-login, and verify `cookie_secret` is stable. |
| Redirect loops on Cloud | Redirect URI mismatch. | Confirm the Cloud URL matches the app’s public URL and ends with `/oauth2callback`. |

## Debugging with DEBUG_AUTH
Add `debug_auth = true` under `[auth]` or as a top-level secret. This enables a **Debug auth** block on the Account page that displays:
- `st.user` keys
- chosen `user_id`
- display name + email

Disable it after troubleshooting to avoid exposing identifiers to users.
