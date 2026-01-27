from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import streamlit as st

try:
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None


# -----------------------------
# Logging
# -----------------------------
logger = logging.getLogger("mantis.auth")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


def _mask_email(email: str) -> str:
    email = (email or "").strip()
    if "@" not in email:
        return "<invalid>"
    name, domain = email.split("@", 1)
    if not name:
        return f"*@{domain}"
    if len(name) == 1:
        return f"{name}*@{domain}"
    return f"{name[0]}***@{domain}"


def _safe_str(v: Any) -> str:
    try:
        return str(v)
    except Exception:
        return "<unprintable>"


# -----------------------------
# Config + state keys
# -----------------------------
_SUPABASE_URL_KEY = "SUPABASE_URL"
_SUPABASE_ANON_KEY = "SUPABASE_ANON_KEY"          # can be legacy anon JWT or new sb_publishable_...
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

        # Helpful hint in logs if using new publishable key
        if key.startswith("sb_publishable_"):
            logger.info("[INIT] Using publishable key format (sb_publishable_...). If auth fails, try legacy anon key (eyJ...).")

        st.session_state[_SS_CLIENT] = create_client(url, key)
        logger.info("[INIT] Supabase client created url=%s", url)
    return st.session_state[_SS_CLIENT]


def _set_session(session: Any) -> None:
    st.session_state[_SS_SESSION] = session
    user = getattr(session, "user", None) if session else None
    st.session_state[_SS_USER] = user


def _get_session():
    return st.session_state.get(_SS_SESSION)


def _get_user():
    return st.session_state.get(_SS_USER)


def has_active_session() -> bool:
    return _get_session() is not None


def is_authenticated() -> bool:
    # authenticated if we have a session OR a user object (email-confirmation flow may yield user w/o session)
    return has_active_session() or (_get_user() is not None)


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
    return str((user or {}).get("id") or "")


def get_user_email(user: dict) -> str:
    return str((user or {}).get("email") or "")


def get_user_display_name(user: dict) -> str:
    meta = (user or {}).get("user_metadata") or {}
    return str(meta.get("display_name") or meta.get("name") or "")


# -----------------------------
# Compatibility helpers (fixes your crash)
# -----------------------------
def get_user_id_with_fallback(user: Any) -> str:
    """
    Mantis_Studio.py calls this. Always return a stable user id string.
    """
    if not user:
        return str(st.session_state.get("guest_user_id") or "guest")

    if isinstance(user, dict):
        uid = user.get("id") or user.get("user_id") or ""
        return str(uid) if uid else str(st.session_state.get("guest_user_id") or "guest")

    uid = getattr(user, "id", None) or getattr(user, "user_id", None)
    if uid:
        return str(uid)

    return str(st.session_state.get("guest_user_id") or "guest")


def get_user_email_with_fallback(user: Any) -> str:
    if not user:
        return ""
    if isinstance(user, dict):
        return str(user.get("email") or "")
    return str(getattr(user, "email", "") or "")


def get_user_display_name_with_fallback(user: Any) -> str:
    if not user:
        return ""
    if isinstance(user, dict):
        return get_user_display_name(user)
    meta = getattr(user, "user_metadata", None) or {}
    if isinstance(meta, dict):
        return str(meta.get("display_name") or meta.get("name") or "")
    return ""


def _get_redirect_url() -> Optional[str]:
    v = _get_secret(_SUPABASE_REDIRECT_URL_KEY, "").strip()
    return v or None


def _extract_session_user(res: Any) -> Tuple[Any, Any]:
    """
    supabase-py response shapes vary by version; normalize session/user extraction.
    """
    if res is None:
        return None, None

    # object-style
    session = getattr(res, "session", None)
    user = getattr(res, "user", None)

    # dict-style
    if session is None and isinstance(res, dict):
        session = res.get("session")
    if user is None and isinstance(res, dict):
        user = res.get("user")

    return session, user


# -----------------------------
# Auth actions (email/password)
# -----------------------------
def auth_signup(email: str, password: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY), or supabase package missing."

    email = (email or "").strip().lower()

    try:
        redirect_to = _get_redirect_url()
        payload: Dict[str, Any] = {"email": email, "password": password}
        if redirect_to:
            payload["options"] = {"email_redirect_to": redirect_to}

        logger.info("[SIGNUP] email=%s redirect_to=%s configured=%s", _mask_email(email), _safe_str(redirect_to), auth_is_configured())
        res = c.auth.sign_up(payload)
        session, user = _extract_session_user(res)

        logger.info("[SIGNUP] session=%s user=%s", bool(session), bool(user))

        if session and user:
            _set_session(session)
            return True, "Account created and signed in."

        if user and not session:
            # Email confirmation ON: you get user but no session
            st.session_state[_SS_USER] = user
            st.session_state[_SS_SESSION] = None
            return True, "Account created. Check your email to confirm, then come back and log in."

        return True, "Account created. Check your email if confirmation is required."
    except Exception as e:
        logger.exception("[SIGNUP] exception")
        return False, f"Sign up failed: {type(e).__name__}: {e}"


def auth_login(email: str, password: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY), or supabase package missing."

    email = (email or "").strip().lower()

    try:
        logger.info("[LOGIN] email=%s", _mask_email(email))
        res = c.auth.sign_in_with_password({"email": email, "password": password})
        session, user = _extract_session_user(res)

        logger.info("[LOGIN] session=%s user=%s", bool(session), bool(user))

        if session and user:
            _set_session(session)
            return True, "Signed in."

        return False, "Login failed (no session returned). If email confirmation is enabled, confirm first."
    except Exception as e:
        logger.exception("[LOGIN] exception")
        return False, f"Login failed: {type(e).__name__}: {e}"


def auth_request_password_reset(email: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured (missing SUPABASE_URL / SUPABASE_ANON_KEY), or supabase package missing."

    email = (email or "").strip().lower()

    try:
        redirect_to = _get_redirect_url()
        logger.info("[RESET] email=%s redirect_to=%s", _mask_email(email), _safe_str(redirect_to))
        if redirect_to:
            c.auth.reset_password_for_email(email, {"redirect_to": redirect_to})
        else:
            c.auth.reset_password_for_email(email)

        st.session_state[_SS_RESET_LAST_TS] = int(time.time())
        return True, "Reset link sent (check your email)."
    except Exception as e:
        logger.exception("[RESET] exception")
        return False, f"Reset request failed: {type(e).__name__}: {e}"


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
# Optional: Login gate helper (if Mantis_Studio.py uses it later)
# -----------------------------
def require_login(
    reason: str = "Please sign in to continue.",
    action: Optional[str] = None,
    return_page: str = "home",
) -> bool:
    """
    If not logged in, redirect to Account Settings page and stop execution.
    """
    if is_authenticated():
        return True

    st.session_state["auth_redirect_reason"] = reason
    st.session_state["auth_redirect_action"] = action
    st.session_state["auth_redirect_return_page"] = return_page

    try:
        if hasattr(st, "switch_page"):
            # Streamlit multipage path
            st.switch_page("pages/Account Settings.py")
    except Exception:
        pass

    st.stop()
    return False


# -----------------------------
# “Profile” storage (user_metadata)
# No database table needed.
# -----------------------------
def get_profile(user_id: str) -> Optional[dict]:
    u = get_current_user() or {}
    meta = u.get("user_metadata") or {}
    return {
        "display_name": meta.get("display_name") or "",
        "username": meta.get("username") or "",
    }


def ensure_profile(user: dict) -> dict:
    return get_profile(get_user_id(user)) or {"display_name": "", "username": ""}


def update_profile(user_id: str, email: str, display_name: str, username: str) -> Tuple[bool, str]:
    c = _client()
    if c is None:
        return False, "Supabase is not configured."

    try:
        c.auth.update_user({"data": {"display_name": display_name, "username": username}})

        # refresh cached user best-effort
        u = _get_user()
        if u and not isinstance(u, dict):
            try:
                md = getattr(u, "user_metadata", {}) or {}
                if isinstance(md, dict):
                    md["display_name"] = display_name
                    md["username"] = username
                    setattr(u, "user_metadata", md)
            except Exception:
                pass

        return True, "Profile updated."
    except Exception as e:
        logger.exception("[PROFILE] exception")
        return False, f"Profile update failed: {type(e).__name__}: {e}"


def render_email_account_controls(email: str) -> None:
    st.caption("Password is managed by MANTIS (Supabase email/password), not Google/Microsoft/Apple.")
