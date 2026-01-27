# ---- Password reset cooldown helpers (prevents spam + fixes missing attribute) ----
import time
import streamlit as st

_RESET_COOLDOWN_SECONDS = 60
_RESET_TS_KEY = "pw_reset_last_sent_ts"


def reset_cooldown_remaining() -> int:
    """Seconds until another password-reset email can be sent."""
    last = st.session_state.get(_RESET_TS_KEY)
    if not last:
        return 0
    elapsed = time.time() - float(last)
    return int(max(0, _RESET_COOLDOWN_SECONDS - elapsed))


def mark_reset_sent() -> None:
    """Call this after successfully sending a reset email."""
    st.session_state[_RESET_TS_KEY] = time.time()

