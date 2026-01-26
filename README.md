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
