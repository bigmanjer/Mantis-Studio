from mantis.services import auth as _auth
from mantis.services.auth import *  # noqa: F403

from typing import Any, Dict, Iterable, Optional

import os
import time

import streamlit as st
from supabase import Client, create_client

GOOGLE_ACCOUNT_URL = "https://myaccount.google.com/"
MICROSOFT_ACCOUNT_URL = "https://myaccount.microsoft.com/"
APPLE_ACCOUNT_URL = "https://appleid.apple.com/"
EMAIL_SIGNIN_COOLDOWN_SECONDS = 45
SESSION_USER_KEY = "mantis_auth_user"
SESSION_PROVIDER_KEY = "mantis_auth_provider"

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


def _auth_key(name: str) -> str:
    return f"auth_{name}"


def _get_supabase_config() -> Dict[str, str]:
    config = st.secrets.get("supabase", {}) if hasattr(st, "secrets") else {}
    return {
        "url": config.get("url") or os.getenv("SUPABASE_URL", ""),
        "anon_key": config.get("anon_key") or os.getenv("SUPABASE_ANON_KEY", ""),
    }


def _supabase_enabled() -> bool:
    config = _get_supabase_config()
    return bool(config.get("url") and config.get("anon_key"))


@st.cache_resource(show_spinner=False)
def _supabase_client(url: str, anon_key: str) -> Client:
    return create_client(url, anon_key)


def _get_supabase_client() -> Optional[Client]:
    if not _supabase_enabled():
        return None
    config = _get_supabase_config()
    return _supabase_client(config["url"], config["anon_key"])


def _normalize_supabase_user(user: Any) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    if isinstance(user, dict):
        user_dict = user
    else:
        user_dict = getattr(user, "__dict__", {}) or {}
    metadata = user_dict.get("user_metadata") or {}
    app_metadata = user_dict.get("app_metadata") or {}
    return {
        "id": user_dict.get("id") or user_dict.get("user_id") or user_dict.get("sub"),
        "email": user_dict.get("email") or metadata.get("email"),
        "name": metadata.get("full_name") or metadata.get("name") or user_dict.get("email"),
        "picture": metadata.get("avatar_url") or metadata.get("picture"),
        "provider": (app_metadata.get("provider") or "email"),
    }


def _set_supabase_session(user: Dict[str, Any]) -> None:
    st.session_state[SESSION_USER_KEY] = user
    st.session_state[SESSION_PROVIDER_KEY] = user.get("provider", "email")
    st.session_state["auth_provider_hint"] = user.get("provider", "email")


def _clear_supabase_session() -> None:
    st.session_state.pop(SESSION_USER_KEY, None)
    st.session_state.pop(SESSION_PROVIDER_KEY, None)


def _email_cooldown_remaining(state_key: str) -> int:
    last_sent = st.session_state.get(state_key, 0.0)
    elapsed = time.time() - float(last_sent or 0.0)
    return max(0, int(EMAIL_SIGNIN_COOLDOWN_SECONDS - elapsed))


def debug_auth_enabled() -> bool:
    return bool(_get_auth_config().get("debug_auth", False))


def get_current_user() -> Optional[Any]:
    session_user = st.session_state.get(SESSION_USER_KEY)
    if session_user:
        return session_user
    if not hasattr(st, "user"):
        return None
    try:
        return st.user
    except Exception:
        return None


def is_logged_in(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
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
    user = user or get_current_user()
    return (
        _get_user_attr(user, "email")
        or _get_user_attr(user, "preferred_username")
        or _get_user_attr(user, "upn")
        or ""
    )


def get_user_display_name(user: Optional[Any] = None) -> str:
    user = user or get_current_user()
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
    user = user or get_current_user()
    return _get_user_attr(user, "picture") or _get_user_attr(user, "avatar") or ""


def get_user_id(user: Optional[Any] = None) -> str:
    user = user or get_current_user()
    return (
        _get_user_attr(user, "sub")
        or _get_user_attr(user, "id")
        or _get_user_attr(user, "user_id")
        or _get_user_attr(user, "oid")
        or _get_user_attr(user, "uid")
        or _get_user_attr(user, "username")
        or get_user_email(user)
    )


def get_user_id_with_fallback(user: Optional[Any] = None) -> str:
    user_id = get_user_id(user)
    if user_id:
        return user_id
    fallback = st.session_state.get("user_id", "")
    return str(fallback) if fallback else ""


def _get_provider_key(user: Optional[Any] = None) -> str:
    user = user or get_current_user()
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


def get_provider_label(user: Optional[Any] = None) -> str:
    provider_key = _get_provider_key(user)
    if "google" in provider_key:
        return "Google"
    if "microsoft" in provider_key or "entra" in provider_key:
        return "Microsoft"
    if "apple" in provider_key:
        return "Apple"
    if "email" in provider_key or "magic" in provider_key:
        return "Email"
    if provider_key:
        return provider_key.replace("_", " ").replace("-", " ").title()
    return ""


def is_email_provider(user: Optional[Any] = None) -> bool:
    provider_key = _get_provider_key(user)
    return "email" in provider_key or "magic" in provider_key


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

def _render_auth_notice() -> None:
    notice = st.session_state.pop("auth_notice", None)
    if notice:
        st.success(notice)


def _extract_supabase_user(response: Any) -> tuple[Optional[Dict[str, Any]], bool]:
    if response is None:
        return None, False
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
    normalized = _normalize_supabase_user(user)
    return normalized, bool(session)


def render_email_signin_area() -> None:
    st.markdown("#### Continue with email")
    _render_auth_notice()
    client = _get_supabase_client()
    if not client:
        st.caption("Email sign-in requires Supabase configuration.")
        return

    signin_tab, signup_tab, reset_tab = st.tabs(["Sign in", "Create account", "Forgot password"])

    with signin_tab:
        with st.form(_auth_key("email_signin_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_auth_key("signin_email"),
            )
            password = st.text_input(
                "Password",
                type="password",
                key=_auth_key("signin_password"),
            )
            submit = st.form_submit_button("Sign in", use_container_width=True)
        if submit:
            if "@" not in email:
                st.session_state["auth_error"] = "Enter a valid email address."
            elif not password:
                st.session_state["auth_error"] = "Enter your password to continue."
            else:
                try:
                    response = client.auth.sign_in_with_password(
                        {"email": email.strip().lower(), "password": password}
                    )
                    user, _ = _extract_supabase_user(response)
                    if user:
                        _set_supabase_session(user)
                        st.session_state["auth_notice"] = "Signed in successfully."
                        st.rerun()
                    else:
                        st.session_state["auth_error"] = "Sign-in failed. Check your credentials."
                except Exception:
                    st.session_state["auth_error"] = "Sign-in failed. Please try again."

        st.divider()
        magic_remaining = _email_cooldown_remaining("magic_link_sent_at")
        with st.form(_auth_key("magic_link_form")):
            magic_email = st.text_input(
                "Send a magic link",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_auth_key("magic_email"),
            )
            magic_submit = st.form_submit_button(
                "Email me a sign-in link",
                use_container_width=True,
                disabled=magic_remaining > 0,
            )
        if magic_submit:
            if "@" not in magic_email:
                st.session_state["auth_error"] = "Enter a valid email address to receive a link."
            else:
                try:
                    client.auth.sign_in_with_otp({"email": magic_email.strip().lower()})
                    st.session_state["magic_link_sent_at"] = time.time()
                    st.session_state["auth_notice"] = "Magic link sent. Check your inbox to finish sign-in."
                    st.session_state["auth_email"] = magic_email.strip().lower()
                except Exception:
                    st.session_state["auth_error"] = "We couldn't send the sign-in link. Try again."
        if magic_remaining > 0:
            st.caption(f"Resend available in {magic_remaining}s.")

    with signup_tab:
        with st.form(_auth_key("email_signup_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_auth_key("signup_email"),
            )
            password = st.text_input(
                "Create password",
                type="password",
                key=_auth_key("signup_password"),
            )
            confirm = st.text_input(
                "Confirm password",
                type="password",
                key=_auth_key("signup_password_confirm"),
            )
            submit = st.form_submit_button("Create account", use_container_width=True)
        if submit:
            if "@" not in email:
                st.session_state["auth_error"] = "Enter a valid email address."
            elif not password or len(password) < 8:
                st.session_state["auth_error"] = "Create a password with at least 8 characters."
            elif password != confirm:
                st.session_state["auth_error"] = "Passwords do not match."
            else:
                try:
                    response = client.auth.sign_up(
                        {"email": email.strip().lower(), "password": password}
                    )
                    user, has_session = _extract_supabase_user(response)
                    if user and has_session:
                        _set_supabase_session(user)
                        st.session_state["auth_notice"] = "Account created and signed in."
                        st.rerun()
                    elif user:
                        st.session_state["auth_notice"] = (
                            "Account created. Check your email to confirm and sign in."
                        )
                        st.session_state["auth_email"] = email.strip().lower()
                    else:
                        st.session_state["auth_error"] = "Signup failed. Please try again."
                except Exception:
                    st.session_state["auth_error"] = "Signup failed. Please try again."

    with reset_tab:
        remaining = _email_cooldown_remaining("password_reset_sent_at")
        with st.form(_auth_key("email_reset_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_auth_key("reset_email"),
            )
            submit = st.form_submit_button(
                "Send reset link",
                use_container_width=True,
                disabled=remaining > 0,
            )
        if submit:
            if "@" not in email:
                st.session_state["auth_error"] = "Enter a valid email address."
            else:
                try:
                    client.auth.reset_password_email(email.strip().lower())
                    st.session_state["password_reset_sent_at"] = time.time()
                    st.session_state["auth_notice"] = "Password reset email sent."
                    st.session_state["auth_email"] = email.strip().lower()
                except Exception:
                    st.session_state["auth_error"] = "Reset failed. Please try again."
        if remaining > 0:
            st.caption(f"Resend available in {remaining}s.")


def render_email_account_controls(user_email: str) -> None:
    st.markdown("#### Email account")
    st.caption("Send a password reset link or update your email sign-in.")
    _render_auth_notice()
    _render_login_error()
    client = _get_supabase_client()
    if not client:
        st.info("Email account management requires Supabase configuration.")
        return
    remaining = _email_cooldown_remaining("password_reset_sent_at")
    if st.button(
        "Send password reset email",
        use_container_width=True,
        disabled=remaining > 0,
        key=_auth_key("account_reset_password"),
    ):
        if "@" not in (user_email or ""):
            st.session_state["auth_error"] = "Add a valid email to receive a reset link."
        else:
            try:
                client.auth.reset_password_email(user_email.strip().lower())
                st.session_state["password_reset_sent_at"] = time.time()
                st.session_state["auth_notice"] = "Password reset email sent."
            except Exception:
                st.session_state["auth_error"] = "Reset failed. Please try again."
    if remaining > 0:
        st.caption(f"Resend available in {remaining}s.")


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
    if user and get_user_id(user):
        return True
    return False


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
        st.warning("Guest mode is active. Local saves are temporary until you create an account.")
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
            disabled_label="Continue with Apple (admin setup required)",
            help_text="Apple sign-in isn’t configured yet.",
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
        st.divider()
        st.markdown('<div style="text-align:center; font-weight:600;">or</div>', unsafe_allow_html=True)
        render_email_signin_area()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Why we ask you to sign in")
    st.caption(
        "Accounts keep your projects private, enable cloud sync, and protect access to your workspace."
    )
    st.markdown(
        "- [Privacy](/?page=privacy)\n- [Terms](/?page=terms)\n- [Legal hub](/?page=legal)"
    )
    st.divider()
    st.caption("Need help? Check your inbox for confirmation or reset links, or contact support.")
    return False


def _user_is_allowed(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
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
    user = user or get_current_user()
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
    if st.session_state.get(SESSION_USER_KEY):
        client = _get_supabase_client()
        if client:
            try:
                client.auth.sign_out()
            except Exception:
                st.session_state["auth_error"] = "Sign out failed. Please try again."
        _clear_supabase_session()
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
