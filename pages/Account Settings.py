from __future__ import annotations

import streamlit as st

from app.utils import auth


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .mantis-account-wrap {
            max-width: 1100px;
            margin: 0 auto;
        }
        .mantis-account-header {
            padding: 26px 30px;
            border-radius: 22px;
            border: 1px solid rgba(120, 199, 190, 0.3);
            background: linear-gradient(135deg, rgba(16, 24, 36, 0.95), rgba(10, 16, 24, 0.95));
            box-shadow: 0 18px 36px rgba(0,0,0,0.35);
            margin-bottom: 24px;
        }
        .mantis-account-title {
            font-size: 28px;
            font-weight: 700;
        }
        .mantis-account-sub {
            color: rgba(226, 232, 240, 0.75);
            margin-top: 6px;
        }
        .mantis-account-card {
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(15, 23, 42, 0.5);
        }
        .mantis-account-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 22px;
        }
        .mantis-account-stat {
            border-radius: 16px;
            padding: 16px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            background: rgba(15, 23, 42, 0.4);
        }
        .mantis-account-stat h4 {
            margin: 0 0 6px 0;
            font-size: 15px;
        }
        .mantis-account-stat p {
            margin: 0;
            color: rgba(226, 232, 240, 0.7);
            font-size: 13px;
        }
        .mantis-account-section-title {
            font-size: 20px;
            font-weight: 600;
            margin-top: 10px;
        }
        .mantis-account-tag {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid rgba(120, 199, 190, 0.3);
            background: rgba(15, 23, 42, 0.6);
            font-size: 12px;
            color: rgba(226, 232, 240, 0.85);
        }
        div[data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _account_key(name: str) -> str:
    return f"account_{name}"


def _return_to_studio(return_page: str) -> None:
    st.session_state["page"] = return_page or "home"
    if hasattr(st, "switch_page"):
        st.switch_page("Mantis_Studio.py")
    else:
        st.info("Use the sidebar to return to the studio.")


def _render_login_tabs() -> None:
    if not auth.auth_is_configured():
        st.info("Supabase is not configured yet. Ask an admin to set SUPABASE_URL and SUPABASE_ANON_KEY.")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    login_tab, signup_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        with st.form(_account_key("login_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_account_key("login_email"),
            )
            password = st.text_input(
                "Password",
                type="password",
                key=_account_key("login_password"),
            )
            submit = st.form_submit_button("Log in", use_container_width=True)
        if submit:
            if "@" not in email:
                st.session_state["account_error"] = "Enter a valid email address."
            elif not password:
                st.session_state["account_error"] = "Enter your password to continue."
            else:
                ok, msg = auth.auth_login(email.strip().lower(), password)
                if ok:
                    st.session_state["account_notice"] = msg
                    st.rerun()
                else:
                    st.session_state["account_error"] = msg

        with st.expander("Forgot password?"):
            remaining = auth.reset_cooldown_remaining()
            with st.form(_account_key("reset_form")):
                reset_email = st.text_input(
                    "Email for reset link",
                    value=email,
                    placeholder="you@example.com",
                    key=_account_key("reset_email"),
                )
                reset_submit = st.form_submit_button(
                    "Send reset link",
                    use_container_width=True,
                    disabled=remaining > 0,
                )
            if reset_submit:
                if "@" not in reset_email:
                    st.session_state["account_error"] = "Enter a valid email address."
                else:
                    ok, msg = auth.auth_request_password_reset(reset_email.strip().lower())
                    if ok:
                        st.session_state["account_notice"] = msg
                        st.session_state["auth_email"] = reset_email.strip().lower()
                    else:
                        st.session_state["account_error"] = msg
            if remaining > 0:
                st.caption(f"Resend available in {remaining}s.")

    with signup_tab:
        with st.form(_account_key("signup_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_account_key("signup_email"),
            )
            password = st.text_input(
                "Create password",
                type="password",
                key=_account_key("signup_password"),
            )
            confirm = st.text_input(
                "Confirm password",
                type="password",
                key=_account_key("signup_password_confirm"),
            )
            submit = st.form_submit_button("Create account", use_container_width=True)
        if submit:
            if "@" not in email:
                st.session_state["account_error"] = "Enter a valid email address."
            elif not password or len(password) < 8:
                st.session_state["account_error"] = "Create a password with at least 8 characters."
            elif password != confirm:
                st.session_state["account_error"] = "Passwords do not match."
            else:
                ok, msg = auth.auth_signup(email.strip().lower(), password)
                if ok:
                    st.session_state["account_notice"] = msg
                    st.rerun()
                else:
                    st.session_state["account_error"] = msg


def _render_account_settings(user: dict) -> None:
    user_id = auth.get_user_id(user)
    email = auth.get_user_email(user)
    profile = auth.get_profile(user_id) or auth.ensure_profile(user) or {}

    display_name_value = profile.get("display_name") or auth.get_user_display_name(user)
    username_value = profile.get("username") or ""

    st.markdown("<div class='mantis-account-card'>", unsafe_allow_html=True)
    st.markdown("#### Account Settings")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    with st.form(_account_key("settings_form")):
        st.text_input("Email", value=email, disabled=True, key=_account_key("email"))
        display_name = st.text_input(
            "Display name",
            value=display_name_value,
            placeholder="Your name",
            key=_account_key("display_name"),
        )
        username = st.text_input(
            "Username",
            value=username_value,
            placeholder="unique-handle",
            key=_account_key("username"),
        )
        save = st.form_submit_button("Save changes", use_container_width=True)

    if save:
        ok, msg = auth.update_profile(user_id, email, display_name.strip(), username.strip())
        if ok:
            st.session_state["account_notice"] = msg
        else:
            st.session_state["account_error"] = msg
        st.rerun()

    auth.render_email_account_controls(email)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")
    _inject_styles()

    st.markdown('<div class="mantis-account-wrap">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mantis-account-header">
            <div class="mantis-account-title">Account Access</div>
            <div class="mantis-account-sub">Create an account or log in to unlock cloud sync and exports.</div>
            <div class="mantis-account-tag">Secure Supabase sign-in · Guest mode supported</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    redirect_reason = st.session_state.get("auth_redirect_reason")
    redirect_action = st.session_state.get("auth_redirect_action")
    return_page = st.session_state.get("auth_redirect_return_page", "home")

    if auth.is_authenticated():
        user = auth.get_current_user() or {}
        st.success("You're signed in.")
        _render_account_settings(user)

        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button(
                "Return to Studio",
                type="primary",
                use_container_width=True,
                key=_account_key("return_to_studio"),
            ):
                _return_to_studio(return_page)
        with action_cols[1]:
            auth.logout_button(
                label="Log out",
                key=_account_key("logout"),
                extra_state_keys=["projects_dir", "project", "page", "_force_nav"],
            )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.markdown("### Welcome back")
    st.caption("Sign in to access your synced projects, or continue in Guest mode to keep writing locally.")
    _render_login_tabs()

    if st.button("Continue in Guest mode", use_container_width=True, key=_account_key("continue_guest")):
        st.session_state["guest_continue_action"] = redirect_action
        st.session_state["pending_action"] = None
        st.session_state.pop("auth_redirect_reason", None)
        st.session_state.pop("auth_redirect_action", None)
        st.session_state.pop("auth_redirect_return_page", None)
        _return_to_studio(return_page)

    if redirect_reason:
        st.info(redirect_reason)

    st.markdown("### Need help?")
    st.markdown(
        """
        <div class="mantis-account-card">
            <strong>Common tips</strong>
            <ul>
                <li>Use the same email you registered with Supabase.</li>
                <li>Check your inbox for verification or reset links.</li>
                <li>If you just confirmed your email, return here to log in.</li>
            </ul>
            <div style="margin-top:8px;">
                <a href="/?page=privacy">Privacy</a> · <a href="/?page=terms">Terms</a> · <a href="/pages/legal.py">Legal hub</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


main()
