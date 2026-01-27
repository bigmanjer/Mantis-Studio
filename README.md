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

## Authentication (Supabase Auth)

MANTIS Studio uses Supabase Auth for account creation, login, and password reset. Guest mode is
still available, but export requires a logged-in account.

### Required secrets (template)

Add these to `.streamlit/secrets.toml` (or Streamlit Cloud secrets):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

You can also use environment variables locally:

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-public-key"
```

### Profiles table

Create a `profiles` table in Supabase so account settings can store display names and usernames.
See `docs/AUTH_SETUP.md` for the SQL snippet and full setup guide.

### Runbook + troubleshooting

For Supabase setup notes and troubleshooting tips, see `docs/streamlit-auth-runbook.md`.

### Optional environment variables

```bash
export GROQ_API_URL="https://api.groq.com/openai/v1"
export GROQ_MODEL="llama3-8b-8192"
export GROQ_TIMEOUT="300"
```

---

Need help choosing a Groq model or tuning prompts? Tell me what you’re building.

## How to configure Streamlit Cloud Secrets (Supabase)

Set the Supabase secrets in Streamlit Cloud > App settings > Secrets:

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

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
