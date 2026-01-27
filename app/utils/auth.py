from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import streamlit as st

GOOGLE_ACCOUNT_URL = "https://myaccount.google.com/"
MICROSOFT_ACCOUNT_URL = "https://myaccount.microsoft.com/"
GOOGLE_RECOVERY_URL = "https://accounts.google.com/signin/recovery"
MICROSOFT_RECOVERY_URL = "https://account.live.com/password/reset"

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


def get_current_user() -> Optional[Any]:
    return st.user if hasattr(st, "user") else None


def is_logged_in(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
    return bool(user)


def auth_is_configured() -> bool:
    providers = _get_auth_config().get("providers", {})
    return any(
        provider.get("client_id") and provider.get("client_secret")
        for provider in providers.values()
    )


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
    return _get_auth_config().get("provider_account_url", "")


def _get_providers() -> Dict[str, Any]:
    return _get_auth_config().get("providers", {})


def get_provider_keys() -> list[str]:
    return list(_get_providers().keys())


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


def render_login_screen() -> None:
    st.markdown("## Create your MANTIS Studio account")
    st.write("Save projects, sync across devices, and unlock cloud backups.")
    _render_login_error()

    providers = _get_providers()
    google_ready = _provider_is_configured("google")
    microsoft_ready = _provider_is_configured("microsoft")
    other_providers = [
        key
        for key in providers.keys()
        if key not in {"google", "microsoft"}
    ]
    other_provider = other_providers[0] if other_providers else ""

    with st.container(border=True):
        st.markdown("### Continue with")
        col1, col2 = st.columns(2)
        with col1:
            if google_ready:
                _render_login_button(
                    "Continue with Google",
                    "google",
                    disabled=False,
                    key="login_google",
                )
            else:
                st.caption("Google sign-in not configured.")
        with col2:
            if microsoft_ready:
                _render_login_button(
                    "Continue with Microsoft",
                    "microsoft",
                    disabled=False,
                    key="login_microsoft",
                )
            else:
                st.caption("Microsoft sign-in not configured.")

        st.button(
            "Continue with Apple (Coming soon)",
            use_container_width=True,
            disabled=True,
            help="Apple login can be added later via a generic OIDC provider.",
            key="login_apple_disabled",
        )

        if other_provider:
            st.divider()
            _render_login_button(
                "Continue with other OIDC provider",
                other_provider,
                disabled=not _provider_is_configured(other_provider),
                key="login_other_oidc",
            )

    if not auth_is_configured():
        st.info(
            "Admin setup required: configure Google or Microsoft OIDC in secrets.toml to enable sign-in."
        )
        with st.expander("Admin setup instructions"):
            st.markdown(
                """
1. Open `.streamlit/secrets.toml`
2. Add providers under `[auth.providers]`
3. Include `client_id` and `client_secret` for Google/Microsoft
                """
            )

    st.markdown("#### Why we ask you to sign in")
    st.caption(
        "Accounts keep your projects private, enable cloud sync, and protect access to your workspace."
    )
    st.markdown(
        "- [Privacy](/?page=privacy)\n- [Terms](/?page=terms)\n- [Legal hub](/pages/legal.py)"
    )
    st.divider()
    _render_recovery_links()


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
