"""OAuth provider helpers for MANTIS Studio."""
from __future__ import annotations

import secrets
import time
import base64
import hashlib
import hmac
import json
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
DEFAULT_GOOGLE_CLIENT_ID = "1089899786902-85r6u83hstmskkjbniva160d29fdko4c.apps.googleusercontent.com"
HOSTED_GOOGLE_REDIRECT_URI = "https://mantis-studio.streamlit.app/?oauth_provider=google"
LOCAL_GOOGLE_REDIRECT_URI = "http://localhost:8501/?oauth_provider=google"
GOOGLE_SECRET_ENV_VARS = (
    "MANTIS_GOOGLE_CLIENT_SECRET",
    "GOOGLE_CLIENT_SECRET",
)
GOOGLE_CLIENT_ID_ENV_VARS = (
    "MANTIS_GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_ID",
)
GOOGLE_REDIRECT_URI_ENV_VARS = (
    "MANTIS_GOOGLE_REDIRECT_URI",
    "GOOGLE_REDIRECT_URI",
)
GOOGLE_SECRET_STREAMLIT_KEYS = (
    "MANTIS_GOOGLE_CLIENT_SECRET",
    "GOOGLE_CLIENT_SECRET",
    "google_client_secret",
    "oauth_google_client_secret",
)
GOOGLE_CLIENT_ID_STREAMLIT_KEYS = (
    "MANTIS_GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_ID",
    "google_client_id",
    "oauth_google_client_id",
)
GOOGLE_REDIRECT_URI_STREAMLIT_KEYS = (
    "MANTIS_GOOGLE_REDIRECT_URI",
    "GOOGLE_REDIRECT_URI",
    "google_redirect_uri",
    "oauth_google_redirect_uri",
)
OAUTH_STATE_TTL_SECONDS = 10 * 60


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


def _get_external_value(env_vars: Tuple[str, ...], streamlit_keys: Tuple[str, ...]) -> Tuple[str, str]:
    for env_var in env_vars:
        value = os.getenv(env_var, "").strip()
        if value:
            return value, env_var
    for key in streamlit_keys:
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
    external_client_id, client_id_source = _get_external_value(
        GOOGLE_CLIENT_ID_ENV_VARS,
        GOOGLE_CLIENT_ID_STREAMLIT_KEYS,
    )
    external_redirect_uri, redirect_uri_source = _get_external_value(
        GOOGLE_REDIRECT_URI_ENV_VARS,
        GOOGLE_REDIRECT_URI_STREAMLIT_KEYS,
    )
    secret = protected_secret or external_secret
    secret_source = "protected storage" if protected_secret else external_source
    client_id = str(data.get("oauth_google_client_id") or external_client_id or DEFAULT_GOOGLE_CLIENT_ID).strip()
    redirect_uri = str(
        data.get("oauth_google_redirect_uri") or external_redirect_uri or HOSTED_GOOGLE_REDIRECT_URI
    ).strip()
    return {
        "enabled": bool(data.get("oauth_google_enabled", True)),
        "client_id": client_id,
        "client_secret": secret,
        "redirect_uri": redirect_uri,
        "scopes": data.get("oauth_google_scopes", DEFAULT_GOOGLE_SCOPES) or DEFAULT_GOOGLE_SCOPES,
        "secret_saved": bool(secret),
        "secret_source": secret_source,
        "client_id_source": "saved config" if data.get("oauth_google_client_id") else (client_id_source or "app default"),
        "redirect_uri_source": "saved config" if data.get("oauth_google_redirect_uri") else (redirect_uri_source or "hosted default"),
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
    redirect_uri_clean = (redirect_uri or HOSTED_GOOGLE_REDIRECT_URI).strip()
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
            external_secret, _external_source = _get_external_google_client_secret()
            if external_secret:
                return True, "Google OAuth settings saved. Using external Google client secret."
            return (
                False,
                "Protected secret storage is unavailable, so the client secret was not saved. "
                "Add google_client_secret in Streamlit Cloud secrets, then leave "
                "the Client Secret field blank when saving settings.",
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


def _state_signing_key(cfg: Dict[str, Any]) -> bytes:
    secret = str(cfg.get("client_secret") or "")
    client_id = str(cfg.get("client_id") or "")
    return hashlib.sha256(f"{secret}:{client_id}:mantis-google-oauth".encode("utf-8")).digest()


def _encode_state(payload: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(_state_signing_key(cfg), body, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(body + signature).decode("ascii").rstrip("=")


def _decode_state(state: str, cfg: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    raw_state = (state or "").strip()
    if not raw_state:
        return False, "OAuth state check failed. Try signing in again.", {}
    try:
        padded = raw_state + ("=" * (-len(raw_state) % 4))
        decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    except Exception:
        return False, "OAuth state check failed. Try signing in again.", {}
    if len(decoded) <= 32:
        return False, "OAuth state check failed. Try signing in again.", {}
    body = decoded[:-32]
    signature = decoded[-32:]
    expected = hmac.new(_state_signing_key(cfg), body, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        return False, "OAuth state check failed. Try signing in again.", {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception:
        return False, "OAuth state check failed. Try signing in again.", {}
    started_at = float(payload.get("iat") or 0)
    if not started_at or (time.time() - started_at) > OAUTH_STATE_TTL_SECONDS:
        return False, "OAuth sign-in expired. Try again.", {}
    return True, "OAuth state valid.", payload


def build_google_authorization_url(session_state: Any) -> Tuple[bool, str, str]:
    ready, msg, cfg = is_google_oauth_ready()
    if not ready:
        return False, msg, ""
    nonce = secrets.token_urlsafe(24)
    state = _encode_state(
        {
            "provider": "google",
            "nonce": nonce,
            "iat": time.time(),
        },
        cfg,
    )
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
    ready, msg, cfg = is_google_oauth_ready()
    if not ready:
        return False, msg, {}
    state_ok, state_msg, state_payload = _decode_state(state, cfg)
    if not state_ok:
        return False, state_msg, {}
    if state_payload.get("provider") != "google":
        return False, "OAuth state check failed. Try signing in again.", {}

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
