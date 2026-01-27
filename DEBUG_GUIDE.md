# Debug Guide

## Enable debug mode

Debug output is shown when **either** of the following is true:

1. `st.secrets["DEBUG"] == True`
2. `st.session_state.debug == True`

### Option A — Streamlit secrets (recommended)

Add this to `.streamlit/secrets.toml` (or your Streamlit Cloud secrets):

```toml
DEBUG = true
```

Restart the app. The sidebar will show a **Debug** panel with:

- Current page name
- Last clicked action
- Last exception string

### Option B — Session state (local/dev)

If you are running locally and want to toggle via Python:

```python
st.session_state.debug = True
```

This can be set in a temporary local scratch panel or via `streamlit run` with a one-off snippet.

## Exception handling

Unhandled exceptions are logged and surfaced as a friendly error message.
When debug mode is enabled, the full exception stack is shown in the UI.
