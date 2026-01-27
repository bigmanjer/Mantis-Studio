# MANTIS Studio

## Quick start (Groq online AI)

MANTIS Studio uses Groq’s free online models via an OpenAI-compatible API.

### 1) Install dependencies

```bash
pip install -r app/requirements.txt
```

### 2) Set your Groq API key

```bash
export GROQ_API_KEY="your-key-here"
```

### 3) Run the app

```bash
python -m streamlit run Mantis_Studio.py
```

## Authentication (Streamlit native OIDC)

MANTIS Studio uses Streamlit’s built-in authentication (st.login/st.user/st.logout). Password
management and recovery are handled by your identity provider (Google, Microsoft Entra, etc.), or by
your configured email/passwordless provider.

### How to set up Google OIDC

1. In Google Cloud Console, create an OAuth 2.0 Client ID (Web application).
2. Add your redirect URI:
   - Local: `http://localhost:8501/oauth2callback`
   - Streamlit Cloud: `https://<your-app>.streamlit.app/oauth2callback`
3. Add the client ID and client secret to `.streamlit/secrets.toml` under `[auth.google]`.

### How to set up Microsoft Entra OIDC

1. In Microsoft Entra, register an application and create a client secret.
2. Add your redirect URI:
   - Local: `http://localhost:8501/oauth2callback`
   - Streamlit Cloud: `https://<your-app>.streamlit.app/oauth2callback`
3. Use the tenant metadata URL in secrets:
   - Single tenant: `https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration`
   - Multi-tenant: `https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration`
4. Add the client ID and client secret to `.streamlit/secrets.toml` under `[auth.microsoft]`.

### How to set up Keycloak OIDC (self-registration)
1. In Keycloak Admin Console (Realm Settings → Login), enable:
   - **User registration** (Register link on login screen).
   - **Forgot password** (optional but recommended).
   - **Verify email** (recommended).
   - **Login with email** (optional).
2. If you enable **Verify email** or **Forgot password**, configure SMTP under **Realm Settings → Email**.
3. Create/verify a **confidential** Keycloak OIDC client:
   - **Standard flow**: ON
   - **Client authentication**: ON (so you have a `client_secret`)
   - **Valid Redirect URIs**:
     - `http://localhost:8501/oauth2callback`
     - `https://mantis-studio.streamlit.app/oauth2callback`
   - **Web Origins**:
     - `http://localhost:8501`
     - `https://mantis-studio.streamlit.app`
4. Add a Keycloak provider block in `.streamlit/secrets.toml`:
   ```toml
   [auth.keycloak]
   client_id = "mantis"
   client_secret = "YOUR_CLIENT_SECRET"
   server_metadata_url = "https://KEYCLOAK_HOST/realms/YOUR_REALM/.well-known/openid-configuration"
   ```

### Apple Sign In (placeholder + future support)

Streamlit-native OIDC does not ship with an Apple preset. To enable Apple, add a provider block
under `[auth.apple]` with Apple’s OIDC metadata and credentials. The app hides the button if Apple
is not configured.

### Runbook + troubleshooting

For a full Streamlit Cloud runbook (secrets, redirect URIs, and common failure modes), see:
`docs/streamlit-auth-runbook.md`.

### Required secrets (template)

See `.streamlit/secrets.toml` (or the copyable `.streamlit/secrets.toml.example`) for a full template including optional allowlists and admin emails.
At minimum, provide:

```toml
[auth]
redirect_uri = "https://<your-app>.streamlit.app/oauth2callback"
cookie_secret = "replace-with-a-long-random-string"
debug_auth = false

[auth.google]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[auth.microsoft]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration"

[auth.apple]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://appleid.apple.com/.well-known/openid-configuration"

[auth.email]
client_id = "..."
client_secret = "..."
server_metadata_url = "https://your-email-idp.example.com/.well-known/openid-configuration"
```

### Optional authorization controls

Use allowlists to restrict access or flag admins:

```toml
[authz]
allowed_domains = ["example.com"]
allowed_emails = ["editor@example.com"]
admin_emails = ["admin@example.com"]
```

### Streamlit Cloud deploy notes

- Set secrets in Streamlit Cloud > App settings > Secrets (do not commit real secrets).
- Ensure the redirect URI matches your Streamlit Cloud app URL.

### Optional environment variables

```bash
export GROQ_API_URL="https://api.groq.com/openai/v1"
export GROQ_MODEL="llama3-8b-8192"
export GROQ_TIMEOUT="300"
```

---

Need help choosing a Groq model or tuning prompts? Tell me what you’re building.

## How to configure Streamlit Cloud Secrets (OIDC)

Streamlit-native OIDC uses `st.login()` and reads provider configuration from `.streamlit/secrets.toml`. The **required** format is shown below. Replace the values with your provider settings.

### Local development (`localhost:8501/oauth2callback`)

```toml
[auth]
cookie_secret = "replace-with-a-long-random-string"

[auth.google]
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
redirect_uri = "http://localhost:8501/oauth2callback"

[auth.microsoft]
server_metadata_url = "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
client_id = "YOUR_MICROSOFT_CLIENT_ID"
client_secret = "YOUR_MICROSOFT_CLIENT_SECRET"
redirect_uri = "http://localhost:8501/oauth2callback"
```

### Streamlit Cloud (`https://mantis-studio.streamlit.app/oauth2callback`)

```toml
[auth]
cookie_secret = "replace-with-a-long-random-string"

[auth.google]
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
client_id = "YOUR_GOOGLE_CLIENT_ID"
client_secret = "YOUR_GOOGLE_CLIENT_SECRET"
redirect_uri = "https://mantis-studio.streamlit.app/oauth2callback"

[auth.microsoft]
server_metadata_url = "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
client_id = "YOUR_MICROSOFT_CLIENT_ID"
client_secret = "YOUR_MICROSOFT_CLIENT_SECRET"
redirect_uri = "https://mantis-studio.streamlit.app/oauth2callback"
```

> Tip: If you only want one provider, you can omit the other provider block. The app will show a friendly message instead of disabled buttons when a provider is missing.

## Legal and policy documents

- [Copyright ownership](legal/copyright.md)
- [Terms of Service](legal/terms.md)
- [Privacy Policy](legal/privacy.md)
- [Brand / IP clarity](legal/Brand_ip_Clarity.md)
- [License](LICENSE.md)
- [Trademark path](legal/Trademark_Path.md)

## Assets

- Brand assets live in `assets/` and are used for the Streamlit icon, sidebar branding, and dashboard banner.

## Repository layout (product-oriented)

- `app/` houses reusable application code (components, services, UI, and utilities).
- `pages/` remains at the repo root to support Streamlit multipage routing.
