# MANTIS Studio

## Quick start (Groq online AI)

MANTIS Studio uses Groq’s free online models via an OpenAI-compatible API.

### 1) Install dependencies

```bash
pip install -r requirements.txt
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

## Legal and policy documents

- [Copyright ownership](legal/copyright.md)
- [Terms of Service](legal/terms.md)
- [Privacy Policy](legal/privacy.md)
- [Brand / IP clarity](legal/Brand_ip_Clarity.md)
- [License](LICENSE.md)
- [Trademark path](legal/Trademark_Path.md)

## Assets

- `mantis_logo_trans.png` is the active logo asset used by the app; unused full-size variants have been removed.

## Repository layout (product-oriented)

- `app/` houses reusable application code (components, services, UI, and utilities).
- `pages/` remains at the repo root to support Streamlit multipage routing.
