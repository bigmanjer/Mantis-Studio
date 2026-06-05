"""OAuth provider helpers for MANTIS Studio."""
from __future__ import annotations

import secrets
import time
from typing import Any, Dict, Tuple
from urllib.parse import parse_qs, urlencode, urlparse
import os

import requests

from app.config.settings import load_app_config, save_app_config
from app.security.secret_store import protect_secret, protected_storage_available, reveal_secret


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
DEFAULT_GOOGLE_SCOPES = "openid email profile"
HOSTED_GOOGLE_REDIRECT_URI = "https://mantisstudio.streamlit.app/?oauth_provider=google"
LOCAL_GOOGLE_REDIRECT_URI = "http://localhost:8501/?oauth_provider=google"
GOOGLE_SECRET_ENV_VARS = (
    "MANTIS_GOOGLE_CLIENT_SECRET",
    "GOOGLE_CLIENT_SECRET",
)
GOOGLE_SECRET_STREAMLIT_KEYS = (
    "google_client_secret",
    "oauth_google_client_secret",
)


def _read_streamlit_secret(key: str) -> str:
    try:
        import streamlit as st
    except Exception:
        return ""
    try:
        value = st.secrets.get(key, "")
    except Exception:
        return ""
    return str(value or "").strip()


def _get_external_google_client_secret() -> Tuple[str, str]:
    for env_var in GOOGLE_SECRET_ENV_VARS:
        value = os.getenv(env_var, "").strip()
        if value:
            return value, env_var
    for key in GOOGLE_SECRET_STREAMLIT_KEYS:
        value = _read_streamlit_secret(key)
        if value:
            return value, f"Streamlit secrets: {key}"
    return "", ""


def _validate_google_redirect_uri(redirect_uri: str) -> Tuple[bool, str]:
    uri = (redirect_uri or "").strip()
    if not uri:
        return False, "Google OAuth missing: redirect URI."

    parsed = urlparse(uri)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return (
            False,
            "Google OAuth redirect URI must be a full URL, for example "
            f"{HOSTED_GOOGLE_REDIRECT_URI}.",
        )

    query = parse_qs(parsed.query)
    if "google" not in query.get("oauth_provider", []):
        return (
            False,
            "Google OAuth redirect URI must include ?oauth_provider=google so "
            "MANTIS can detect the callback.",
        )

    return True, "Redirect URI valid."


def get_google_oauth_config() -> Dict[str, Any]:
    data = load_app_config()
    protected_secret = reveal_secret(data.get("oauth_google_client_secret_protected") or {})
    external_secret, external_source = _get_external_google_client_secret()
    secret = protected_secret or external_secret
    secret_source = "protected storage" if protected_secret else external_source
    return {
        "enabled": bool(data.get("oauth_google_enabled", False)),
        "client_id": data.get("oauth_google_client_id", ""),
        "client_secret": secret,
        "redirect_uri": data.get("oauth_google_redirect_uri", ""),
        "scopes": data.get("oauth_google_scopes", DEFAULT_GOOGLE_SCOPES) or DEFAULT_GOOGLE_SCOPES,
        "secret_saved": bool(secret),
        "secret_source": secret_source,
        "external_secret": bool(external_secret),
        "protected_storage": protected_storage_available(),
    }


def save_google_oauth_config(
    *,
    enabled: bool,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    scopes: str = DEFAULT_GOOGLE_SCOPES,
    clear_secret: bool = False,
) -> Tuple[bool, str]:
    redirect_uri_clean = (redirect_uri or "").strip()
    if enabled:
        ok, msg = _validate_google_redirect_uri(redirect_uri_clean)
        if not ok:
            return False, msg

    data = load_app_config()
    data["oauth_google_enabled"] = bool(enabled)
    data["oauth_google_client_id"] = (client_id or "").strip()
    data["oauth_google_redirect_uri"] = redirect_uri_clean
    data["oauth_google_scopes"] = (scopes or DEFAULT_GOOGLE_SCOPES).strip()
    if clear_secret:
        data.pop("oauth_google_client_secret_protected", None)
    elif client_secret:
        if not protected_storage_available():
            save_app_config(data)
            return (
                False,
                "Protected secret storage is unavailable, so the client secret was not saved. "
                "Set MANTIS_GOOGLE_CLIENT_SECRET or a Streamlit secret named "
                "google_client_secret instead.",
            )
        data["oauth_google_client_secret_protected"] = protect_secret(client_secret.strip())
    save_app_config(data)
    return True, "Google OAuth settings saved."


def is_google_oauth_ready() -> Tuple[bool, str, Dict[str, Any]]:
    cfg = get_google_oauth_config()
    missing = []
    if not cfg.get("enabled"):
        missing.append("enabled")
    if not cfg.get("client_id"):
        missing.append("client ID")
    if not cfg.get("client_secret"):
        missing.append("client secret")
    if not cfg.get("redirect_uri"):
        missing.append("redirect URI")
    if missing:
        return False, f"Google OAuth missing: {', '.join(missing)}.", cfg
    ok, msg = _validate_google_redirect_uri(str(cfg.get("redirect_uri") or ""))
    if not ok:
        return False, msg, cfg
    return True, "Google OAuth ready.", cfg


def build_google_authorization_url(session_state: Any) -> Tuple[bool, str, str]:
    ready, msg, cfg = is_google_oauth_ready()
    if not ready:
        return False, msg, ""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(24)
    session_state["oauth_google_state"] = state
    session_state["oauth_google_nonce"] = nonce
    session_state["oauth_google_started_at"] = time.time()
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": cfg["redirect_uri"],
        "response_type": "code",
        "scope": cfg["scopes"],
        "state": state,
        "nonce": nonce,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return True, "Redirecting to Google.", f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def complete_google_oauth(*, code: str, state: str, session_state: Any) -> Tuple[bool, str, Dict[str, Any]]:
    expected_state = session_state.get("oauth_google_state")
    started_at = float(session_state.get("oauth_google_started_at") or 0)
    if not expected_state or not state or not secrets.compare_digest(str(expected_state), str(state)):
        return False, "OAuth state check failed. Try signing in again.", {}
    if started_at and (time.time() - started_at) > 600:
        return False, "OAuth sign-in expired. Try again.", {}

    ready, msg, cfg = is_google_oauth_ready()
    if not ready:
        return False, msg, {}

    token_resp = requests.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": cfg["client_id"],
            "client_secret": cfg["client_secret"],
            "redirect_uri": cfg["redirect_uri"],
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if token_resp.status_code >= 400:
        return False, f"Google token exchange failed: HTTP {token_resp.status_code}.", {}
    tokens = token_resp.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return False, "Google did not return an ID token.", {}

    info_resp = requests.get(
        GOOGLE_TOKENINFO_URL,
        params={"id_token": id_token},
        timeout=20,
    )
    if info_resp.status_code >= 400:
        return False, f"Google ID token validation failed: HTTP {info_resp.status_code}.", {}
    profile = info_resp.json()
    if profile.get("aud") != cfg["client_id"]:
        return False, "Google token audience did not match this app.", {}
    if profile.get("email_verified") not in (True, "true", "True", "1"):
        return False, "Google email is not verified.", {}
    return True, "Google profile verified.", {
        "sub": profile.get("sub", ""),
        "email": profile.get("email", ""),
        "name": profile.get("name", ""),
        "picture": profile.get("picture", ""),
    }
