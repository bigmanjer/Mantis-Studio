from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import hashlib

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
    "auth_redirect_reason",
    "auth_redirect_action",
    "auth_redirect_return_page",
    "pending_action",
    "guest_continue_action",
    "guest_project",
)


def _get_auth_config() -> Dict[str, Any]:
    return st.secrets.get("auth", {}) if hasattr(st, "secrets") else {}


def _get_authz_config() -> Dict[str, Any]:
    return st.secrets.get("authz", {}) if hasattr(st, "secrets") else {}


def get_current_user() -> Optional[Any]:
    return st.user if hasattr(st, "user") else None


def is_logged_in(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
    if not auth_is_configured():
        return False
    return bool(get_user_id(user))


def auth_is_configured() -> bool:
    providers = _get_providers()
    return any(
        provider.get("client_id") and provider.get("client_secret")
        for provider in providers.values()
    )


def _normalize_list(values: Optional[Iterable[str]]) -> list[str]:
    return [value.strip().lower() for value in values or [] if value and value.strip()]


def _normalize_user_value(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (list, tuple, set)):
        for item in value:
            if item:
                return str(item)
        return None
    if isinstance(value, dict):
        for key in ("value", "email", "id"):
            if value.get(key):
                return str(value[key])
        return None
    return str(value)


def _get_user_attr(user: Any, attr: str) -> Optional[str]:
    if user is None:
        return None
    if isinstance(user, dict):
        value = user.get(attr)
    else:
        value = getattr(user, attr, None)
    return _normalize_user_value(value)


def get_user_email(user: Optional[Any] = None) -> str:
    user = user or st.user
    return (
        _get_user_attr(user, "email")
        or _get_user_attr(user, "preferred_username")
        or _get_user_attr(user, "upn")
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
        or _get_user_attr(user, "oid")
        or _get_user_attr(user, "uid")
        or _get_user_attr(user, "username")
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
    auth_config = _get_auth_config()
    providers: Dict[str, Any] = dict(auth_config.get("providers", {}))
    for key, value in auth_config.items():
        if key in {"redirect_uri", "cookie_secret", "provider_account_url"}:
            continue
        if isinstance(value, dict):
            providers.setdefault(key, value)
    return providers


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
    st.markdown(
        f"- [Apple ID recovery]({APPLE_RECOVERY_URL})"
    )


def _render_provider_cta(
    label: str,
    provider_key: str,
    ready: bool,
    *,
    disabled_label: Optional[str] = None,
    help_text: Optional[str] = None,
    key: str,
) -> None:
    if ready:
        _render_login_button(label, provider_key, disabled=False, key=key)
        return
    st.button(disabled_label or label, use_container_width=True, disabled=True, key=key)
    if help_text:
        st.caption(help_text)


def is_authenticated() -> bool:
    user = get_current_user()
    if not auth_is_configured():
        return False
    return bool(get_user_id(user))


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
        .mantis-auth-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(120, 199, 190, 0.3);
            background: rgba(15, 23, 42, 0.6);
            font-size: 12px;
            color: rgba(226, 232, 240, 0.85);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="mantis-auth-hero">
            <div class="mantis-auth-title">Create your MANTIS account</div>
            <div class="mantis-auth-sub">Sign in to sync projects across devices, unlock cloud saves, and keep drafts safe.</div>
            <div class="mantis-auth-pill">Guest mode stays open while you decide</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if intent:
        st.info(intent)
    if allow_guest:
        st.warning("Guest mode is active. Your creations won’t be saved unless you create an account.")
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
        if not any([google_ready, microsoft_ready, apple_ready, other_provider]):
            st.caption("No sign-in providers are configured yet. You can continue in Guest mode.")
        _render_provider_cta(
            "Continue with Google",
            "google",
            google_ready,
            disabled_label="Continue with Google (admin setup required)",
            help_text="Google sign-in isn’t configured yet.",
            key="login_google",
        )
        _render_provider_cta(
            "Continue with Microsoft",
            "microsoft",
            microsoft_ready,
            disabled_label="Continue with Microsoft (admin setup required)",
            help_text="Microsoft sign-in isn’t configured yet.",
            key="login_microsoft",
        )
        _render_provider_cta(
            "Continue with Apple",
            "apple",
            apple_ready,
            disabled_label="Continue with Apple (coming soon)",
            help_text="Apple sign-in can be enabled once credentials are added.",
            key="login_apple",
        )
        if other_provider:
            st.divider()
            _render_provider_cta(
                "Continue with other OIDC provider",
                other_provider,
                _provider_is_configured(other_provider),
                disabled_label="Continue with other OIDC provider (admin setup required)",
                help_text="This provider needs client credentials in secrets.",
                key="login_other_oidc",
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Why we ask you to sign in")
    st.caption(
        "Accounts keep your projects private, enable cloud sync, and protect access to your workspace."
    )
    st.markdown(
        "- [Privacy](/?page=privacy)\n- [Terms](/?page=terms)\n- [Legal hub](/pages/legal.py)"
    )
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
    user = get_current_user()
    if not is_authenticated():
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
    st.session_state["page"] = "home"
    st.session_state["guest_mode"] = True
    st.session_state["_force_nav"] = True
    try:
        st.rerun()
    except Exception:
        return


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
