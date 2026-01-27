from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import os
import time

import streamlit as st
from supabase import Client, create_client

EMAIL_SIGNIN_COOLDOWN_SECONDS = 45
SESSION_USER_KEY = "mantis_auth_user"
SESSION_ACCESS_TOKEN_KEY = "mantis_auth_access_token"
SESSION_REFRESH_TOKEN_KEY = "mantis_auth_refresh_token"
SESSION_RESET_SENT_AT_KEY = "mantis_auth_reset_sent_at"


def _get_supabase_config() -> Dict[str, str]:
    secrets = st.secrets if hasattr(st, "secrets") else {}
    supabase_block = secrets.get("supabase", {}) if hasattr(secrets, "get") else {}
    url = (
        secrets.get("SUPABASE_URL")
        or supabase_block.get("url")
        or os.getenv("SUPABASE_URL", "")
    )
    anon_key = (
        secrets.get("SUPABASE_ANON_KEY")
        or supabase_block.get("anon_key")
        or os.getenv("SUPABASE_ANON_KEY", "")
    )
    return {"url": url or "", "anon_key": anon_key or ""}


def supabase_enabled() -> bool:
    config = _get_supabase_config()
    return bool(config.get("url") and config.get("anon_key"))


@st.cache_resource(show_spinner=False)
def _supabase_client(url: str, anon_key: str) -> Client:
    return create_client(url, anon_key)


def get_supabase_client() -> Optional[Client]:
    if not supabase_enabled():
        return None
    config = _get_supabase_config()
    return _supabase_client(config["url"], config["anon_key"])


def _normalize_user(user: Any) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    if isinstance(user, dict):
        user_dict = user
    else:
        user_dict = getattr(user, "__dict__", {}) or {}
    metadata = user_dict.get("user_metadata") or {}
    return {
        "id": user_dict.get("id") or user_dict.get("user_id"),
        "email": user_dict.get("email") or metadata.get("email"),
        "display_name": metadata.get("full_name") or metadata.get("name"),
    }


def _extract_response(response: Any) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    if response is None:
        return None, None
    user = None
    session = None
    if isinstance(response, dict):
        user = response.get("user") or (response.get("data") or {}).get("user")
        session = response.get("session") or (response.get("data") or {}).get("session")
    else:
        user = getattr(response, "user", None)
        session = getattr(response, "session", None)
        if user is None and hasattr(response, "data"):
            data = response.data
            if isinstance(data, dict):
                user = data.get("user")
                session = data.get("session")
            else:
                user = getattr(data, "user", None)
                session = getattr(data, "session", None)
    return _normalize_user(user), session if isinstance(session, dict) else None


def _set_session(user: Dict[str, Any], session: Optional[Dict[str, Any]]) -> None:
    st.session_state[SESSION_USER_KEY] = user
    if session:
        st.session_state[SESSION_ACCESS_TOKEN_KEY] = session.get("access_token")
        st.session_state[SESSION_REFRESH_TOKEN_KEY] = session.get("refresh_token")


def _clear_session() -> None:
    for key in (SESSION_USER_KEY, SESSION_ACCESS_TOKEN_KEY, SESSION_REFRESH_TOKEN_KEY):
        st.session_state.pop(key, None)


def auth_get_user() -> Optional[Dict[str, Any]]:
    session_user = st.session_state.get(SESSION_USER_KEY)
    if session_user:
        return session_user
    return None


def auth_is_logged_in() -> bool:
    user = auth_get_user()
    return bool(user and user.get("id"))


def auth_signup(email: str, password: str) -> Tuple[bool, str]:
    client = get_supabase_client()
    if not client:
        return False, "Supabase is not configured."
    try:
        response = client.auth.sign_up({"email": email, "password": password})
        user, session = _extract_response(response)
        if not user:
            return False, "Signup failed. Please try again."
        _set_session(user, session)
        ensure_profile(user)
        if session:
            return True, "Account created and signed in."
        return True, "Account created. Check your email to confirm before signing in."
    except Exception:
        return False, "Signup failed. Please try again."


def auth_login(email: str, password: str) -> Tuple[bool, str]:
    client = get_supabase_client()
    if not client:
        return False, "Supabase is not configured."
    try:
        response = client.auth.sign_in_with_password({"email": email, "password": password})
        user, session = _extract_response(response)
        if not user:
            return False, "Sign-in failed. Check your credentials."
        _set_session(user, session)
        ensure_profile(user)
        return True, "Signed in successfully."
    except Exception:
        return False, "Sign-in failed. Please try again."


def auth_logout() -> None:
    client = get_supabase_client()
    if client:
        try:
            client.auth.sign_out()
        except Exception:
            pass
    _clear_session()


def reset_cooldown_remaining() -> int:
    last_sent = st.session_state.get(SESSION_RESET_SENT_AT_KEY, 0.0)
    elapsed = time.time() - float(last_sent or 0.0)
    return max(0, int(EMAIL_SIGNIN_COOLDOWN_SECONDS - elapsed))


def auth_request_password_reset(email: str) -> Tuple[bool, str]:
    client = get_supabase_client()
    if not client:
        return False, "Supabase is not configured."
    remaining = reset_cooldown_remaining()
    if remaining > 0:
        return False, f"Please wait {remaining}s before requesting another reset."
    try:
        client.auth.reset_password_email(email)
        st.session_state[SESSION_RESET_SENT_AT_KEY] = time.time()
        return True, "Password reset email sent."
    except Exception:
        return False, "Reset failed. Please try again."


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    if not user_id:
        return None
    client = get_supabase_client()
    if not client:
        return None
    try:
        response = (
            client.table("profiles")
            .select("id,email,display_name,username,created_at")
            .eq("id", user_id)
            .single()
            .execute()
        )
        data = response.data
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def ensure_profile(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    user_id = (user or {}).get("id")
    if not user_id:
        return None
    existing = get_profile(user_id)
    if existing:
        return existing
    client = get_supabase_client()
    if not client:
        return None
    email = (user or {}).get("email")
    display_name = (user or {}).get("display_name") or (email or "").split("@", maxsplit=1)[0]
    payload = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "username": None,
    }
    try:
        response = client.table("profiles").insert(payload).execute()
        data = response.data
        if isinstance(data, list) and data:
            return data[0]
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def update_profile(
    user_id: str,
    email: str,
    display_name: str,
    username: str,
) -> Tuple[bool, str]:
    if not user_id:
        return False, "Missing user ID."
    client = get_supabase_client()
    if not client:
        return False, "Supabase is not configured."
    payload = {
        "email": email,
        "display_name": display_name,
        "username": username or None,
    }
    try:
        client.table("profiles").update(payload).eq("id", user_id).execute()
        return True, "Account settings updated."
    except Exception:
        return False, "Update failed. Please try again."
