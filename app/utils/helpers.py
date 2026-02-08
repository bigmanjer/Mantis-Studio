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


def _has_any_api_key(ss) -> bool:
    """Return ``True`` when at least one AI provider key is present."""
    # Explicit flags set elsewhere in the app.
    if ss.get("ai_configured"):
        return True
    if ss.get("api_keys"):
        return True
    if ss.get("providers"):
        return True

    # ai_keys dict populated when the user connects a provider via the UI.
    ai_keys = ss.get("ai_keys")
    if isinstance(ai_keys, dict) and any(ai_keys.values()):
        return True

    # ai_session_keys is the primary key storage used by get_effective_key.
    session_keys = ss.get("ai_session_keys")
    if isinstance(session_keys, dict) and any(session_keys.values()):
        return True

    # Fallback: check resolved API keys written by initialize_session_state.
    if ss.get("groq_api_key") or ss.get("openai_api_key"):
        return True

    return False


def _has_tested_connection(ss) -> bool:
    """Return ``True`` when the user has tested at least one provider."""
    groq_tests = ss.get("groq_model_tests")
    if isinstance(groq_tests, dict) and groq_tests:
        return True
    openai_tests = ss.get("openai_model_tests")
    if isinstance(openai_tests, dict) and openai_tests:
        return True
    groq_models = ss.get("groq_model_list")
    if isinstance(groq_models, list) and groq_models:
        return True
    openai_models = ss.get("openai_model_list")
    if isinstance(openai_models, list) and openai_models:
        return True
    if ss.get("groq_connection_tested"):
        return True
    if ss.get("openai_connection_tested"):
        return True
    return False


def ai_connection_warning(st) -> None:
    """Show a warning when no AI provider API keys are configured.

    Displays a ``st.warning`` banner and a navigation button so users
    know that automatic title/genre generation and all AI features are
    unavailable and can quickly navigate to the AI Settings page to
    connect a provider.

    When keys *are* present but the connection has not been tested yet,
    displays an ``st.info`` banner prompting the user to test their
    models to ensure they work correctly.

    The check inspects ``session_state`` for explicit flags
    (``ai_configured``, ``api_keys``, ``providers``), the
    ``ai_session_keys`` dict used by ``get_effective_key``, and falls
    back to the resolved ``groq_api_key`` / ``openai_api_key`` values.
    """
    ss = st.session_state

    if not _has_any_api_key(ss):
        st.warning(
            "AI providers are not connected. "
            "Automatic title and genre generation along with all AI "
            "features will be disabled until an AI provider is configured."
        )
        if st.button("Connect AI Providers", key="ai_connection_warning_btn"):
            ss["page"] = "ai"
            st.rerun()
        return

    # Keys exist but connection has not been verified yet.
    if not _has_tested_connection(ss):
        st.info(
            "AI key detected but models have not been tested yet. "
            "Please test your connection to make sure everything works."
        )
        if st.button("Go to AI Settings", key="ai_test_prompt_btn"):
            ss["page"] = "ai"
            st.rerun()
