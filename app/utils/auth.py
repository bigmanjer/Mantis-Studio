from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


# -----------------------------
# Config + state keys
# -----------------------------
_SUPABASE_URL_KEY = "SUPABASE_URL"
_SUPABASE_ANON_KEY = "SUPABASE_ANON_KEY"
_SUPABASE_REDIRECT_URL_KEY = "SUPABASE_REDIRECT_URL"  # optional

_SS_CLIENT = "_sb_client"
_SS_SESSION = "_sb_session"
_SS_USER = "_sb_user"
_SS_RESET_LAST_TS = "_sb_reset_last_ts"

RESET_COOLDOWN_SECONDS = 60


@dataclass
class AuthResult:
    ok: bool
    message: str


def _get_secret(name: str, default: str = "") -> str:
    # Streamlit Cloud + local secrets.toml
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return default


def auth_is_configured() -> bool:
    return bool(_get_secret(_SUPABASE_URL_KEY) and _get_secret(_SUPABASE_ANON_KEY) and create_client is not None)


def _client():
    if not auth_is_configured():
        return None
    if _SS_CLIENT not in st.session_state:
        url = _get_secret(_SUPABASE_URL_KEY).strip()
        key = _get_secret(_SUPABASE_ANON_KEY).strip()
        st.session_state[_SS_CLIENT] = create_client(url, key)
    return st.session_state[_SS_CLIENT]


def _set_session(session: Any) -> None:
    st.session_state[_SS_SESSION] = session
    user = getattr(session, "user", None) if session else None
    st.session_state[_SS_USER] = user


def _get_session():
    return st.session_state.get(_SS_SESSION)


def _get_user():
    return st.session_state.get(_SS_USER)


def is_authenticated() -> bool:
    # “Authenticated” = we have a user in session_state
    return _get_user() is not None


def get_current_user() -> Optional[dict]:
    u = _get_user()
    if u is None:
        return None

    # supabase-py user is usually an object; normalize to dict-ish access
    if isinstance(u, dict):
        return u
    out = {}
    for k in ("id", "email", "user_metadata", "app_metadata", "created_at"):
        out[k] = getattr(u, k, None)
    return out


def get_user_id(user: dict) -> str:
    return str(user.get("id") or "")


def get_user_email(user: dict) -> str:
    return str(user.get("email") or "")


def get_user_display_name(user: dict) -> str:
    meta = user.get("user_metadata") or {}
    return str(meta.get("display_name") or meta.get("name") or "")


def _get_redirect_url() -> Optional[str]:
    v = _get_secret(_SUPABASE_REDIRECT_URL_KEY, "").strip()
    return v or None


# -----------------------------
# Auth actions (email/password)
# -----------------------------
def auth_signup(email: str, password: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY)."

    try:
        # NOTE: Supabase may require email confirmation depending on your project settings.
        redirect_to = _get_redirect_url()
        payload: Dict[str, Any] = {"email": email, "password": password}
        if redirect_to:
            payload["options"] = {"email_redirect_to": redirect_to}

        res = c.auth.sign_up(payload)
        session = getattr(res, "session", None)
        user = getattr(res, "user", None)

        if session and user:
            _set_session(session)
            return True, "Account created and signed in."
        # If confirm-email is ON, you often get a user but no session.
        if user and not session:
            st.session_state[_SS_USER] = user
            st.session_state[_SS_SESSION] = None
            return True, "Account created. Check your email to confirm, then come back and log in."
        return True, "Account created. Check your email if confirmation is required."
    except Exception as e:
        return False, f"Sign up failed: {e}"


def auth_login(email: str, password: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY)."

    try:
        res = c.auth.sign_in_with_password({"email": email, "password": password})
        session = getattr(res, "session", None)
        user = getattr(res, "user", None)
        if session and user:
            _set_session(session)
            return True, "Signed in."
        return False, "Login failed (no session returned). If email confirmation is enabled, confirm first."
    except Exception as e:
        return False, f"Login failed: {e}"


def auth_request_password_reset(email: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY)."

    try:
        redirect_to = _get_redirect_url()
        if redirect_to:
            c.auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        else:
            c.auth.reset_password_for_email(email)
        st.session_state[_SS_RESET_LAST_TS] = int(time.time())
        return True, "Reset link sent (check your email)."
    except Exception as e:
        return False, f"Reset request failed: {e}"


def reset_cooldown_remaining() -> int:
    """
    Cooldown is local UI-only (prevents spam clicks). Not Supabase-side rate limiting.
    """
    last_ts = int(st.session_state.get(_SS_RESET_LAST_TS) or 0)
    if not last_ts:
        return 0
    remaining = (last_ts + RESET_COOLDOWN_SECONDS) - int(time.time())
    return max(0, int(remaining))


def logout_button(label: str = "Log out", key: str = "logout", extra_state_keys: Optional[list] = None):
    if st.button(label, key=key, use_container_width=True):
        try:
            c = _client()
            if c is not None:
                c.auth.sign_out()
        except Exception:
            pass
        st.session_state.pop(_SS_SESSION, None)
        st.session_state.pop(_SS_USER, None)
        if extra_state_keys:
            for k in extra_state_keys:
                st.session_state.pop(k, None)
        st.rerun()


# -----------------------------
# “Profile” storage (user_metadata)
# No database table needed.
# -----------------------------
def get_profile(user_id: str) -> Optional[dict]:
    # stored in current user's metadata; no lookup by id needed for now
    u = get_current_user() or {}
    meta = u.get("user_metadata") or {}
    return {
        "display_name": meta.get("display_name") or "",
        "username": meta.get("username") or "",
    }


def ensure_profile(user: dict) -> dict:
    # if missing, return a default shape (we'll only write on save)
    return get_profile(get_user_id(user)) or {"display_name": "", "username": ""}


def update_profile(user_id: str, email: str, display_name: str, username: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured."

    try:
        # Update auth user metadata
        c.auth.update_user({"data": {"display_name": display_name, "username": username}})
        # refresh cached user if possible
        u = _get_user()
        if u and not isinstance(u, dict):
            # best-effort mutate the object metadata
            try:
                md = getattr(u, "user_metadata", {}) or {}
                md["display_name"] = display_name
                md["username"] = username
                setattr(u, "user_metadata", md)
            except Exception:
                pass
        return True, "Profile updated."
    except Exception as e:
        return False, f"Profile update failed: {e}"


def render_email_account_controls(email: str) -> None:
    st.caption("Password is managed by MANTIS (Supabase email/password), not Google/Microsoft/Apple.")
    # If you later add OAuth providers, you can conditionally render provider-specific UI here.
