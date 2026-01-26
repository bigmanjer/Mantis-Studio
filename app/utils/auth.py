from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import streamlit as st

GOOGLE_ACCOUNT_URL = "https://myaccount.google.com/"
MICROSOFT_ACCOUNT_URL = "https://myaccount.microsoft.com/"
APPLE_ACCOUNT_URL = "https://appleid.apple.com/"
GOOGLE_RECOVERY_URL = "https://accounts.google.com/signin/recovery"
MICROSOFT_RECOVERY_URL = "https://account.live.com/password/reset"
APPLE_RECOVERY_URL = "https://iforgot.apple.com/password/verify/appleid"

DEFAULT_SESSION_CLEAR_KEYS = (
    "projects_dir",
    "project",
    "page",
    "user_id",
    "auth_provider_hint",
)


def _get_auth_config() -> Dict[str, Any]:
    return st.secrets.get("auth", {}) if hasattr(st, "secrets") else {}


def _get_authz_config() -> Dict[str, Any]:
    return st.secrets.get("authz", {}) if hasattr(st, "secrets") else {}


def _normalize_list(values: Optional[Iterable[str]]) -> list[str]:
    return [value.strip().lower() for value in values or [] if value and value.strip()]


def _get_user_attr(user: Any, attr: str) -> Optional[str]:
    if user is None:
        return None
    if isinstance(user, dict):
        value = user.get(attr)
    else:
        value = getattr(user, attr, None)
    return value if value is not None else None


def get_user_email(user: Optional[Any] = None) -> str:
    user = user or st.user
    return (
        _get_user_attr(user, "email")
        or _get_user_attr(user, "preferred_username")
        or ""
    )


def get_user_display_name(user: Optional[Any] = None) -> str:
    user = user or st.user
    name = (
        _get_user_attr(user, "name")
        or _get_user_attr(user, "display_name")
        or _get_user_attr(user, "given_name")
    )
    if name:
        return str(name)
    email = get_user_email(user)
    if email:
        return email.split("@", maxsplit=1)[0]
    return "Account"


def get_user_initials(user: Optional[Any] = None) -> str:
    display_name = get_user_display_name(user)
    parts = [part for part in display_name.replace("@", " ").split() if part]
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[1][0]}".upper()
    if parts:
        return parts[0][:2].upper()
    return "ME"


def get_user_avatar_url(user: Optional[Any] = None) -> str:
    user = user or st.user
    return _get_user_attr(user, "picture") or _get_user_attr(user, "avatar") or ""


def get_user_id(user: Optional[Any] = None) -> str:
    user = user or st.user
    return (
        _get_user_attr(user, "sub")
        or _get_user_attr(user, "id")
        or _get_user_attr(user, "user_id")
        or get_user_email(user)
    )


def _get_provider_key(user: Optional[Any] = None) -> str:
    user = user or st.user
    provider = (
        _get_user_attr(user, "auth_provider")
        or _get_user_attr(user, "identity_provider")
        or _get_user_attr(user, "provider")
        or ""
    )
    issuer = _get_user_attr(user, "issuer") or _get_user_attr(user, "iss") or ""
    if issuer:
        issuer_lower = issuer.lower()
        if "google" in issuer_lower:
            return "google"
        if "microsoft" in issuer_lower or "login.microsoftonline.com" in issuer_lower:
            return "microsoft"
        return issuer_lower
    if provider:
        return str(provider).lower()
    return str(st.session_state.get("auth_provider_hint", "")).lower()


def get_manage_account_url(user: Optional[Any] = None) -> str:
    provider_key = _get_provider_key(user)
    if "google" in provider_key:
        return GOOGLE_ACCOUNT_URL
    if "microsoft" in provider_key or "entra" in provider_key:
        return MICROSOFT_ACCOUNT_URL
    if "apple" in provider_key:
        return APPLE_ACCOUNT_URL
    return _get_auth_config().get("provider_account_url", "")


def _get_providers() -> Dict[str, Any]:
    return _get_auth_config().get("providers", {})


def _provider_is_configured(provider_key: str) -> bool:
    providers = _get_providers()
    provider = providers.get(provider_key, {})
    return bool(provider.get("client_id") and provider.get("client_secret"))


def _render_login_button(label: str, provider_key: str, disabled: bool, key: str) -> None:
    if st.button(label, use_container_width=True, disabled=disabled, key=key):
        st.session_state["auth_provider_hint"] = provider_key
        try:
            st.login(provider_key)
        except Exception:
            st.session_state["auth_error"] = (
                f"We couldn't sign you in with {label}. Please try again."
            )


def _render_login_error() -> None:
    error_message = st.session_state.get("auth_error")
    if error_message:
        st.error(error_message)
        if st.button("Try again", use_container_width=True, key="auth_try_again"):
            st.session_state.pop("auth_error", None)


def _render_recovery_links() -> None:
    st.markdown("#### Account recovery")
    st.markdown(
        f"- [Google account recovery]({GOOGLE_RECOVERY_URL})"
    )
    st.markdown(
        f"- [Microsoft account recovery]({MICROSOFT_RECOVERY_URL})"
    )
    st.markdown(
        f"- [Apple ID recovery]({APPLE_RECOVERY_URL})"
    )


def is_authenticated() -> bool:
    return bool(getattr(st, "user", None))


def is_user_allowed(user: Optional[Any] = None) -> bool:
    return _user_is_allowed(user)


def render_login_screen(intent: Optional[str] = None, allow_guest: bool = False) -> bool:
    st.markdown(
        """
        <style>
        .mantis-auth-hero {
            padding: 26px 28px;
            border-radius: 22px;
            border: 1px solid rgba(120, 199, 190, 0.28);
            background: linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(8, 14, 20, 0.95));
            box-shadow: 0 16px 32px rgba(0,0,0,0.3);
        }
        .mantis-auth-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 4px;
        }
        .mantis-auth-sub {
            color: rgba(226, 232, 240, 0.75);
            font-size: 15px;
        }
        .mantis-auth-card {
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.5);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mantis-auth-hero">
            <div class="mantis-auth-title">Create your MANTIS account</div>
            <div class="mantis-auth-sub">Sync projects across devices, unlock cloud saves, and keep your drafts safe.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if intent:
        st.info(intent)
    _render_login_error()

    providers = _get_providers()
    google_ready = _provider_is_configured("google")
    microsoft_ready = _provider_is_configured("microsoft")
    apple_ready = _provider_is_configured("apple")
    other_providers = [
        key
        for key in providers.keys()
        if key not in {"google", "microsoft", "apple"}
    ]
    other_provider = other_providers[0] if other_providers else ""

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Why we ask for login")
        st.markdown(
            """
            - Keep your drafts synced across devices
            - Protect your projects with your identity provider
            - Enable cloud save + recovery when switching browsers
            """
        )
        st.markdown("**Privacy reassurance**")
        st.caption("We only store what’s needed to keep your projects synced. No selling of personal data.")
        if allow_guest:
            if st.button("Continue in Guest mode", use_container_width=True, key="auth_continue_guest"):
                return True
    with right:
        st.markdown('<div class="mantis-auth-card">', unsafe_allow_html=True)
        _render_login_button(
            "Continue with Google",
            "google",
            disabled=not google_ready,
            key="login_google",
        )
        if not google_ready:
            st.caption("Configure Google OIDC in secrets.toml to enable.")
        _render_login_button(
            "Continue with Microsoft",
            "microsoft",
            disabled=not microsoft_ready,
            key="login_microsoft",
        )
        if not microsoft_ready:
            st.caption("Configure Microsoft Entra OIDC in secrets.toml to enable.")
        _render_login_button(
            "Continue with Apple",
            "apple",
            disabled=not apple_ready,
            key="login_apple",
        )
        if not apple_ready:
            st.caption("Apple Sign In needs custom OIDC metadata. Coming soon—see README for setup notes.")
        if other_provider:
            st.divider()
            _render_login_button(
                "Continue with other OIDC provider",
                other_provider,
                disabled=not _provider_is_configured(other_provider),
                key="login_other_oidc",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    _render_recovery_links()
    return False


def _user_is_allowed(user: Optional[Any] = None) -> bool:
    user = user or st.user
    authz = _get_authz_config()
    allowed_domains = _normalize_list(authz.get("allowed_domains"))
    allowed_emails = _normalize_list(authz.get("allowed_emails"))
    if not allowed_domains and not allowed_emails:
        return True
    email = get_user_email(user).lower()
    if allowed_emails and email in allowed_emails:
        return True
    domain = email.split("@")[-1] if "@" in email else ""
    return bool(domain and domain in allowed_domains)


def user_is_admin(user: Optional[Any] = None) -> bool:
    user = user or st.user
    authz = _get_authz_config()
    admin_emails = _normalize_list(authz.get("admin_emails"))
    email = get_user_email(user).lower()
    return bool(email and email in admin_emails)


def require_login() -> Any:
    user = st.user
    if not user:
        render_login_screen()
        st.stop()
    if not _user_is_allowed(user):
        st.error("Your account is not authorized to access this workspace.")
        logout_button(label="Sign out", key="auth_denied_logout")
        st.stop()
    return user


def _clear_session(keys: Iterable[str]) -> None:
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def _logout(extra_state_keys: Iterable[str]) -> None:
    _clear_session(tuple(DEFAULT_SESSION_CLEAR_KEYS) + tuple(extra_state_keys))
    try:
        st.logout()
    except Exception:
        st.session_state["auth_error"] = "Sign out failed. Please try again."


def logout_button(
    label: str = "Sign out",
    key: str = "logout_button",
    extra_state_keys: Optional[Iterable[str]] = None,
) -> bool:
    return st.button(
        label,
        use_container_width=True,
        key=key,
        on_click=_logout,
        kwargs={"extra_state_keys": extra_state_keys or []},
    )
