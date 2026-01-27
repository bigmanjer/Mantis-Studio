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

## Keycloak self-registration + OIDC client (optional)
Use this when you want Keycloak to handle sign up + login for MANTIS Studio.

### 1) Enable account creation in Keycloak
In the Keycloak Admin Console for your realm:
- **Realm Settings → Login**
  - **User registration** = ON (shows **Register** link on login screen).
  - **Forgot password** = ON (shows **Forgot password?** on login screen).
  - **Verify email** = ON (recommended).
  - **Login with email** = ON (optional; allows email instead of username).

> If you enable **Verify email** or **Forgot password**, you must configure SMTP under **Realm Settings → Email**. Otherwise these flows will fail.

### 2) Configure the Keycloak OIDC client
Create/verify a Keycloak client (OpenID Connect):
- **Client type:** OpenID Connect
- **Standard flow:** ON (authorization code flow)
- **Client authentication:** ON (confidential client; required for `client_secret`)
- **Valid Redirect URIs (must match exactly):**
  - `http://localhost:8501/oauth2callback`
  - `https://mantis-studio.streamlit.app/oauth2callback`
- **Web Origins:**
  - `http://localhost:8501`
  - `https://mantis-studio.streamlit.app`

> Most “can’t login / can’t create account” issues are due to a redirect URI mismatch.

### 3) Point Streamlit to Keycloak
Keycloak discovery URL format:
`https://<YOUR_KEYCLOAK_HOST>/realms/<REALM>/.well-known/openid-configuration`

Add a provider block to secrets:
```toml
[auth]
redirect_uri = "https://mantis-studio.streamlit.app/oauth2callback"
cookie_secret = "replace-with-a-long-random-string"

[auth.keycloak]
client_id = "mantis"
client_secret = "YOUR_CLIENT_SECRET"
server_metadata_url = "https://KEYCLOAK_HOST/realms/YOUR_REALM/.well-known/openid-configuration"
```

For local testing, use `redirect_uri = "http://localhost:8501/oauth2callback"` and ensure the localhost redirect URI is registered in Keycloak.

### 4) How “Create account” works in MANTIS
Streamlit’s `st.login()` uses a standard OIDC redirect flow and does not expose custom OIDC parameters (such as `prompt=create`) yet. The easiest path is:
- Show a **Sign in / Create account** button that calls `st.login()`.
- Users click **Register** on the Keycloak login page if self-registration is enabled.

### 5) Local profile creation (recommended)
Even with Keycloak, create a local profile for each user (plan tier, preferences, saved AI keys, etc.) on first login.

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
