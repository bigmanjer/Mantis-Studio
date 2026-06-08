"""Transactional email helpers for MANTIS Studio."""
from __future__ import annotations

import os
from typing import Any, Dict, Tuple

import requests


RESEND_API_URL = "https://api.resend.com/emails"
DEFAULT_FROM = "MANTIS Studio <rebusinessmatters@gmail.com>"
DEFAULT_APP_URL = "https://mantis-studio.streamlit.app"


def _secret_value(key: str, default: str = "") -> str:
    value = os.getenv(key, "")
    if value:
        return value.strip()
    try:
        import streamlit as st  # type: ignore

        secret_value = st.secrets.get(key, "")
        if secret_value:
            return str(secret_value).strip()
    except Exception:
        pass
    return default


def email_settings() -> Dict[str, str]:
    """Return email settings from env vars or Streamlit secrets."""
    return {
        "provider": _secret_value("MANTIS_EMAIL_PROVIDER", "resend").lower(),
        "api_key": _secret_value("RESEND_API_KEY", ""),
        "from": _secret_value("MANTIS_EMAIL_FROM", DEFAULT_FROM),
        "app_url": _secret_value("MANTIS_APP_URL", DEFAULT_APP_URL).rstrip("/"),
    }


def is_email_ready() -> Tuple[bool, str]:
    settings = email_settings()
    if settings["provider"] != "resend":
        return False, "Email provider must be set to resend."
    if not settings["api_key"]:
        return False, "Add RESEND_API_KEY to Streamlit secrets."
    if not settings["from"]:
        return False, "Add MANTIS_EMAIL_FROM to Streamlit secrets."
    if not settings["app_url"].startswith("https://") and not settings["app_url"].startswith("http://"):
        return False, "MANTIS_APP_URL must be a full URL."
    return True, "Email reset is ready."


def send_password_reset_email(*, to_email: str, reset_url: str) -> Tuple[bool, str]:
    """Send a password reset email through Resend."""
    ready, ready_msg = is_email_ready()
    if not ready:
        return False, ready_msg

    settings = email_settings()
    payload: Dict[str, Any] = {
        "from": settings["from"],
        "to": [to_email],
        "subject": "Reset your MANTIS Studio password",
        "html": (
            "<p>You asked to reset your MANTIS Studio password.</p>"
            f"<p><a href=\"{reset_url}\">Reset your password</a></p>"
            "<p>This link expires in 1 hour. If you did not request this, you can ignore this email.</p>"
        ),
        "text": (
            "You asked to reset your MANTIS Studio password.\n\n"
            f"Reset your password: {reset_url}\n\n"
            "This link expires in 1 hour. If you did not request this, you can ignore this email."
        ),
    }
    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {settings['api_key']}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
    except requests.RequestException as exc:
        return False, f"Email provider request failed: {exc}"

    if response.status_code >= 400:
        detail = response.text[:240] if response.text else response.reason
        return False, f"Resend rejected the reset email: {detail}"
    return True, "Password reset email sent."
