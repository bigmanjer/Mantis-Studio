"""Helper utilities for Mantis Studio."""
from __future__ import annotations

import datetime


def word_count(text: str | None) -> int:
    """Return the number of whitespace-delimited words in *text*."""
    return len((text or "").split())


def clamp(value: int | float, low: int | float, high: int | float) -> int | float:
    """Clamp *value* between *low* and *high* inclusive."""
    return max(low, min(value, high))


def current_year() -> int:
    """Return the current UTC year (avoids hard-coding)."""
    return datetime.datetime.now(datetime.timezone.utc).year


def ai_connection_warning(st) -> None:
    """Show a warning when no AI provider API keys are configured.

    Displays a ``st.warning`` banner and a navigation button so users
    know that automatic title/genre generation is unavailable and can
    quickly navigate to the AI Settings page to connect a provider.

    The check inspects ``session_state`` for explicit flags
    (``ai_configured``, ``api_keys``, ``providers``) and falls back to
    looking at the resolved ``groq_api_key`` / ``openai_api_key`` values.
    """
    ss = st.session_state

    # Fast path: explicit flags set elsewhere in the app.
    if ss.get("ai_configured"):
        return
    if ss.get("api_keys"):
        return
    if ss.get("providers"):
        return

    # Fallback: check resolved API keys written by initialize_session_state.
    if ss.get("groq_api_key") or ss.get("openai_api_key"):
        return

    st.warning(
        "AI providers are not connected. "
        "Automatic title and genre generation will be disabled "
        "until an AI provider is configured."
    )
    if st.button("Connect AI Providers", key="ai_connection_warning_btn"):
        ss["page"] = "ai"
        st.rerun()
