from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

import streamlit as st

from app import auth_supabase

EMAIL_SIGNIN_COOLDOWN_SECONDS = auth_supabase.EMAIL_SIGNIN_COOLDOWN_SECONDS
SESSION_USER_KEY = auth_supabase.SESSION_USER_KEY

DEFAULT_SESSION_CLEAR_KEYS = (
    "projects_dir",
    "project",
    "page",
    "user_id",
    "auth_redirect_reason",
    "auth_redirect_action",
    "auth_redirect_return_page",
    "pending_action",
    "guest_continue_action",
    "guest_project",
)


def _auth_key(name: str) -> str:
    return f"auth_{name}"


def debug_auth_enabled() -> bool:
    secrets = st.secrets if hasattr(st, "secrets") else {}
    if isinstance(secrets, dict):
        return bool(secrets.get("debug_auth") or (secrets.get("auth", {}) or {}).get("debug_auth"))
    return False


def get_current_user() -> Optional[Any]:
    return auth_supabase.auth_get_user()


def is_logged_in(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
    return bool(get_user_id(user))


def is_authenticated() -> bool:
    return auth_supabase.auth_is_logged_in()


def auth_is_configured() -> bool:
    return auth_supabase.supabase_enabled()


def _get_authz_config() -> Dict[str, Any]:
    return st.secrets.get("authz", {}) if hasattr(st, "secrets") else {}


def _normalize_list(values: Optional[Iterable[str]]) -> list[str]:
    return [value.strip().lower() for value in values or [] if value and value.strip()]


def user_is_admin(user: Optional[Any] = None) -> bool:
    user = user or get_current_user()
    authz = _get_authz_config()
    admin_emails = _normalize_list(authz.get("admin_emails"))
    email = get_user_email(user).lower()
    return bool(email and email in admin_emails)


def auth_login(email: str, password: str) -> tuple[bool, str]:
    return auth_supabase.auth_login(email, password)


def auth_signup(email: str, password: str) -> tuple[bool, str]:
    return auth_supabase.auth_signup(email, password)


def auth_request_password_reset(email: str) -> tuple[bool, str]:
    return auth_supabase.auth_request_password_reset(email)


def reset_cooldown_remaining() -> int:
    return auth_supabase.reset_cooldown_remaining()


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
    return _get_user_attr(user, "email") or ""


def get_user_display_name(user: Optional[Any] = None) -> str:
    user = user or get_current_user()
    name = _get_user_attr(user, "display_name") or _get_user_attr(user, "name")
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
    return _get_user_attr(user, "picture") or ""


def get_user_id(user: Optional[Any] = None) -> str:
    user = user or get_current_user()
    return _get_user_attr(user, "id") or _get_user_attr(user, "user_id") or get_user_email(user)


def get_user_id_with_fallback(user: Optional[Any] = None) -> str:
    user_id = get_user_id(user)
    if user_id:
        return user_id
    fallback = st.session_state.get("user_id", "")
    return str(fallback) if fallback else ""


def get_provider_label(user: Optional[Any] = None) -> str:
    if user:
        return "Email"
    return ""


def get_manage_account_url(user: Optional[Any] = None) -> str:
    return ""


def _render_auth_notice() -> None:
    notice = st.session_state.pop("auth_notice", None)
    if notice:
        st.success(notice)


def _render_auth_error() -> None:
    error = st.session_state.pop("auth_error", None)
    if error:
        st.error(error)


def _render_password_reset(email: str) -> None:
    remaining = auth_supabase.reset_cooldown_remaining()
    with st.form(_auth_key("reset_form")):
        reset_email = st.text_input(
            "Email address",
            value=email,
            placeholder="you@example.com",
            key=_auth_key("reset_email"),
        )
        submit = st.form_submit_button(
            "Send reset link",
            use_container_width=True,
            disabled=remaining > 0,
        )
    if submit:
        if "@" not in reset_email:
            st.session_state["auth_error"] = "Enter a valid email address."
        else:
            ok, msg = auth_supabase.auth_request_password_reset(reset_email.strip().lower())
            if ok:
                st.session_state["auth_notice"] = msg
                st.session_state["auth_email"] = reset_email.strip().lower()
            else:
                st.session_state["auth_error"] = msg
    if remaining > 0:
        st.caption(f"Resend available in {remaining}s.")


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
            <div class="mantis-auth-sub">Sign in to sync projects across devices, unlock cloud saves, and keep drafts safe.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if intent:
        st.info(intent)
    if allow_guest:
        st.warning("Guest mode is active. Local saves are temporary until you create an account.")

    _render_auth_notice()
    _render_auth_error()

    if not auth_is_configured():
        st.info("Supabase is not configured yet. You can continue in Guest mode.")

    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### Why we ask for login")
        st.markdown(
            """
            - Keep your drafts synced across devices
            - Protect your projects with email + password sign-in
            - Enable cloud save + recovery when switching browsers
            """
        )
        if allow_guest:
            if st.button("Continue in Guest mode", use_container_width=True, key=_auth_key("continue_guest")):
                return True
    with right:
        st.markdown('<div class="mantis-auth-card">', unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["Log in", "Create account"])
        with login_tab:
            with st.form(_auth_key("login_form")):
                email = st.text_input(
                    "Email address",
                    value=st.session_state.get("auth_email", ""),
                    placeholder="you@example.com",
                    key=_auth_key("login_email"),
                )
                password = st.text_input("Password", type="password", key=_auth_key("login_password"))
                submit = st.form_submit_button("Log in", use_container_width=True)
            if submit:
                if "@" not in email:
                    st.session_state["auth_error"] = "Enter a valid email address."
                elif not password:
                    st.session_state["auth_error"] = "Enter your password to continue."
                else:
                    ok, msg = auth_supabase.auth_login(email.strip().lower(), password)
                    if ok:
                        st.session_state["auth_notice"] = msg
                        st.rerun()
                    else:
                        st.session_state["auth_error"] = msg
            with st.expander("Forgot password?"):
                _render_password_reset(email)

        with signup_tab:
            with st.form(_auth_key("signup_form")):
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
                    ok, msg = auth_supabase.auth_signup(email.strip().lower(), password)
                    if ok:
                        st.session_state["auth_notice"] = msg
                        st.rerun()
                    else:
                        st.session_state["auth_error"] = msg
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("#### Privacy")
    st.caption("We only store what’s needed to keep your projects synced. No selling of personal data.")
    st.markdown("- [Privacy](/?page=privacy)\n- [Terms](/?page=terms)\n- [Legal hub](/?page=legal)")
    return False


def render_email_account_controls(user_email: str) -> None:
    st.markdown("#### Password reset")
    st.caption("Send a password reset link to your inbox.")
    _render_auth_notice()
    _render_auth_error()
    remaining = auth_supabase.reset_cooldown_remaining()
    if st.button(
        "Send password reset email",
        use_container_width=True,
        disabled=remaining > 0,
        key=_auth_key("account_reset_password"),
    ):
        if "@" not in (user_email or ""):
            st.session_state["auth_error"] = "Add a valid email to receive a reset link."
        else:
            ok, msg = auth_supabase.auth_request_password_reset(user_email.strip().lower())
            if ok:
                st.session_state["auth_notice"] = msg
            else:
                st.session_state["auth_error"] = msg
    if remaining > 0:
        st.caption(f"Resend available in {remaining}s.")


def _clear_session(keys: Iterable[str]) -> None:
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


def _logout(extra_state_keys: Iterable[str]) -> None:
    _clear_session(tuple(DEFAULT_SESSION_CLEAR_KEYS) + tuple(extra_state_keys))
    auth_supabase.auth_logout()
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


def require_login() -> Any:
    user = get_current_user()
    if not is_authenticated():
        render_login_screen()
        st.stop()
    return user


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    return auth_supabase.get_profile(user_id)


def ensure_profile(user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return auth_supabase.ensure_profile(user)


def update_profile(user_id: str, email: str, display_name: str, username: str) -> tuple[bool, str]:
    return auth_supabase.update_profile(user_id, email, display_name, username)
