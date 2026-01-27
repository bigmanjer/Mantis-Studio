from __future__ import annotations

import streamlit as st

from app.ui.components import card_end, card_start, header_bar
from app.ui.theme import inject_theme as inject_mantis_theme
from app.utils import auth, ui_key


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .mantis-wrap { max-width: 1100px; margin: 0 auto; padding-bottom: 40px; }
        .mantis-topbar { display:flex; justify-content: space-between; align-items:center; gap:12px; margin: 8px 0 18px; }
        .mantis-hero {
            padding: 26px 28px;
            border-radius: 24px;
            border: 1px solid rgba(34,197,94,.25);
            background: radial-gradient(1200px 500px at 20% 10%, rgba(34,197,94,.18), transparent 60%),
                        linear-gradient(135deg, rgba(11, 20, 26, 0.98), rgba(7, 14, 20, 0.98));
            box-shadow: var(--mantis-shadow);
            margin-bottom: 18px;
        }
        .mantis-title { font-size: 34px; font-weight: 800; letter-spacing: .2px; }
        .mantis-sub { color: var(--mantis-text-muted); margin-top: 6px; font-size: 14px; }
        .mantis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
        }
        .mantis-mini {
            border-radius: 16px;
            padding: 14px;
            border: 1px solid var(--mantis-border);
            background: var(--mantis-surface-alt);
        }
        .muted { color: var(--mantis-text-muted); }
        .mantis-callout {
            padding: 12px 16px;
            border-radius: 16px;
            border: 1px solid rgba(34,197,94,.2);
            background: rgba(34,197,94,.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_theme() -> None:
    inject_mantis_theme()
    _inject_styles()


def _go_back_to_studio() -> None:
    st.session_state["page"] = "home"
    if hasattr(st, "switch_page"):
        try:
            st.switch_page("Mantis_Studio.py")
            return
        except Exception:
            pass
    st.info("Use the app navigation to return to the Studio (Dashboard).")
    st.rerun()


def _key(name: str) -> str:
    return ui_key("account", name)


def _debug_enabled() -> bool:
    try:
        secrets = st.secrets
    except Exception:
        secrets = {}
    if isinstance(secrets, dict):
        return bool(secrets.get("DEBUG")) or bool(st.session_state.get("debug"))
    try:
        return bool(secrets["DEBUG"]) or bool(st.session_state.get("debug"))
    except Exception:
        return bool(st.session_state.get("debug"))


def _render_debug_panel() -> None:
    if not _debug_enabled():
        return
    with st.expander("Debug (admin)", expanded=False):
        st.write("auth_is_configured():", auth.auth_is_configured())
        st.write("SUPABASE_URL set:", bool(st.secrets.get("SUPABASE_URL", "")))
        st.write("SUPABASE_ANON_KEY set:", bool(st.secrets.get("SUPABASE_ANON_KEY", "")))
        st.write("redirect_url:", auth.get_redirect_url() or "")
        ok, msg, meta = auth.auth_self_test()
        st.write("self_test_ok:", ok)
        st.write("self_test_message:", msg)
        st.write("self_test_meta:", meta)


def _render_login_ui() -> None:
    configured = auth.auth_is_configured()
    if not configured:
        st.warning("Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets.")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    st.markdown(
        """
        <div class="mantis-hero">
            <div class="mantis-title">Account Access</div>
            <div class="mantis-sub">Secure your workspace, unlock exports, and sync settings across devices.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    colA, colB = st.columns([1.25, 1], vertical_alignment="top")

    with colA:
        card_start("Guest mode vs Account")
        st.markdown(
            """
            <div class="mantis-grid">
              <div class="mantis-mini">
                <b>Guest mode</b>
                <div class="muted" style="margin-top:6px;">
                  Draft, generate outlines/chapters, and test AI settings in-session.
                </div>
              </div>
              <div class="mantis-mini">
                <b>Account unlocks</b>
                <div class="muted" style="margin-top:6px;">
                  Export (PDF/DOCX/ZIP), cloud sync (when enabled), and profile settings.
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        card_end()

    with colB:
        card_start("Sign in or create an account")
        login_tab, signup_tab = st.tabs(["Log in", "Create account"])

        with login_tab:
            with st.form(_key("login_form")):
                email = st.text_input("Email", placeholder="you@example.com", key=_key("login_email"))
                password = st.text_input("Password", type="password", key=_key("login_password"))
                submit = st.form_submit_button("Log in", use_container_width=True, disabled=not configured)
            if submit:
                email = (email or "").strip().lower()
                if "@" not in email:
                    st.session_state["account_error"] = "Enter a valid email address."
                    st.rerun()
                if not password:
                    st.session_state["account_error"] = "Enter your password."
                    st.rerun()
                ok, msg = auth.auth_login(email, password)
                if ok:
                    st.session_state["account_notice"] = msg
                else:
                    st.session_state["account_error"] = msg
                st.rerun()

            with st.expander("Forgot password?"):
                remaining = auth.reset_cooldown_remaining()
                with st.form(_key("reset_form")):
                    reset_email = st.text_input(
                        "Email for reset link",
                        placeholder="you@example.com",
                        key=_key("reset_email"),
                    )
                    reset_submit = st.form_submit_button(
                        "Send reset link",
                        use_container_width=True,
                        disabled=(remaining > 0 or not configured),
                    )
                if reset_submit:
                    reset_email = (reset_email or "").strip().lower()
                    if "@" not in reset_email:
                        st.session_state["account_error"] = "Enter a valid email address."
                    else:
                        ok, msg = auth.auth_request_password_reset(reset_email)
                        if ok:
                            st.session_state["account_notice"] = msg
                        else:
                            st.session_state["account_error"] = msg
                    st.rerun()

                if remaining > 0:
                    st.caption(f"Resend available in {remaining}s.")
                st.caption("Password resets are handled by MANTIS (Supabase email/password).")

        with signup_tab:
            with st.form(_key("signup_form")):
                email = st.text_input("Email", placeholder="you@example.com", key=_key("signup_email"))
                password = st.text_input("Create password (8+ chars)", type="password", key=_key("signup_password"))
                confirm = st.text_input("Confirm password", type="password", key=_key("signup_confirm"))
                submit = st.form_submit_button("Create account", use_container_width=True, disabled=not configured)

            if submit:
                email = (email or "").strip().lower()
                if "@" not in email:
                    st.session_state["account_error"] = "Enter a valid email address."
                    st.rerun()
                if not password or len(password) < 8:
                    st.session_state["account_error"] = "Password must be at least 8 characters."
                    st.rerun()
                if password != confirm:
                    st.session_state["account_error"] = "Passwords do not match."
                    st.rerun()

                ok, msg = auth.auth_signup(email, password)
                if ok:
                    st.session_state["account_notice"] = msg
                else:
                    st.session_state["account_error"] = msg
                st.rerun()

        card_end()

    st.markdown(
        """
        <div class="mantis-callout">
            Need help? Check your inbox for verification links or reset emails, then return here to sign in.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_settings_ui(user: dict) -> None:
    user_id = auth.get_user_id(user)
    email = auth.get_user_email(user)
    profile = auth.get_profile(user_id) or auth.ensure_profile(user) or {}

    card_start("Profile & settings")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    with st.form(_key("settings_form")):
        st.text_input("Email", value=email, disabled=True, key=_key("settings_email"))
        display_name = st.text_input(
            "Display name",
            value=profile.get("display_name", ""),
            placeholder="Your name",
            key=_key("settings_display_name"),
        )
        username = st.text_input(
            "Username",
            value=profile.get("username", ""),
            placeholder="your-handle",
            key=_key("settings_username"),
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
    card_end()


def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")
    inject_theme()

    header_bar(
        "Account Access",
        "Create a MANTIS account to unlock exports + cloud sync. Guest mode stays available.",
        pill="Secure access",
    )
    if st.button("← Back to Studio", use_container_width=True, key=_key("back_to_studio")):
        _go_back_to_studio()

    _render_debug_panel()

    if auth.is_authenticated():
        user = auth.get_current_user() or {}
        st.success("You're signed in.")
        _render_settings_ui(user)

        cols = st.columns(2)
        with cols[0]:
            if st.button("Return to Studio", type="primary", use_container_width=True, key=_key("return_to_studio2")):
                _go_back_to_studio()
        with cols[1]:
            auth.logout_button(label="Log out", key=_key("logout"), extra_state_keys=["page", "_force_nav"])
        return

    _render_login_ui()


main()
