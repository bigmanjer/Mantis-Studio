from __future__ import annotations

import streamlit as st
from app.utils import auth

with st.expander("Debug (admin)", expanded=False):
    st.write("auth_is_configured():", auth.auth_is_configured())
    st.write("SUPABASE_URL set:", bool(st.secrets.get("SUPABASE_URL", "")))
    st.write("SUPABASE_ANON_KEY set:", bool(st.secrets.get("SUPABASE_ANON_KEY", "")))
    st.write("redirect:", st.secrets.get("SUPABASE_REDIRECT_URL", ""))


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .mantis-wrap { max-width: 1100px; margin: 0 auto; padding-bottom: 40px; }
        .mantis-topbar { display:flex; justify-content: space-between; align-items:center; gap:12px; margin: 8px 0 18px; }
        .mantis-pill {
            display:inline-flex; align-items:center; gap:8px;
            padding: 8px 14px; border-radius:999px;
            border: 1px solid rgba(34,197,94,.35);
            background: rgba(2, 44, 20, .55);
            color: rgba(226,232,240,.92);
            font-size: 13px;
        }
        .mantis-hero {
            padding: 26px 28px;
            border-radius: 24px;
            border: 1px solid rgba(34,197,94,.25);
            background: radial-gradient(1200px 500px at 20% 10%, rgba(34,197,94,.18), transparent 60%),
                        linear-gradient(135deg, rgba(9, 26, 18, 0.98), rgba(7, 14, 22, 0.98));
            box-shadow: 0 18px 40px rgba(0,0,0,.40);
            margin-bottom: 18px;
        }
        .mantis-title { font-size: 34px; font-weight: 800; letter-spacing: .2px; }
        .mantis-sub { color: rgba(226,232,240,.74); margin-top: 6px; font-size: 14px; }
        .mantis-card {
            padding: 18px 20px;
            border-radius: 18px;
            border: 1px solid rgba(148,163,184,.18);
            background: rgba(15, 23, 42, .45);
            box-shadow: 0 10px 24px rgba(0,0,0,.25);
        }
        .mantis-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 14px;
        }
        .mantis-mini {
            border-radius: 16px;
            padding: 14px;
            border: 1px solid rgba(148,163,184,.16);
            background: rgba(2, 6, 23, .35);
        }
        .muted { color: rgba(226,232,240,.72); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _go_back_to_studio() -> None:
    st.session_state["page"] = "home"
    # Prefer switch_page if available
    if hasattr(st, "switch_page"):
        try:
            st.switch_page("Mantis_Studio.py")
            return
        except Exception:
            pass
    st.info("Use the app navigation to return to the Studio (Dashboard).")


def _key(name: str) -> str:
    return f"account_{name}"


def _render_login_ui() -> None:
    if not auth.auth_is_configured():
        st.warning("Supabase is not configured. Add SUPABASE_URL and SUPABASE_ANON_KEY to Streamlit secrets.")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    colA, colB = st.columns([1.2, 1], vertical_alignment="top")

    with colA:
        st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
        st.markdown("### Guest mode vs Account")
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
        st.markdown("</div>", unsafe_allow_html=True)

    with colB:
        st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
        login_tab, signup_tab = st.tabs(["Log in", "Create account"])

        with login_tab:
            with st.form(_key("login_form")):
                email = st.text_input("Email", placeholder="you@example.com", key=_key("login_email"))
                password = st.text_input("Password", type="password", key=_key("login_password"))
                submit = st.form_submit_button("Log in", use_container_width=True)
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
                    reset_email = st.text_input("Email for reset link", placeholder="you@example.com", key=_key("reset_email"))
                    reset_submit = st.form_submit_button(
                        "Send reset link",
                        use_container_width=True,
                        disabled=remaining > 0,
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

        with signup_tab:
            with st.form(_key("signup_form")):
                email = st.text_input("Email", placeholder="you@example.com", key=_key("signup_email"))
                password = st.text_input("Create password (8+ chars)", type="password", key=_key("signup_password"))
                confirm = st.text_input("Confirm password", type="password", key=_key("signup_confirm"))
                submit = st.form_submit_button("Create account", use_container_width=True)

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

        st.markdown("</div>", unsafe_allow_html=True)


def _render_settings_ui(user: dict) -> None:
    user_id = auth.get_user_id(user)
    email = auth.get_user_email(user)
    profile = auth.get_profile(user_id) or auth.ensure_profile(user) or {}

    st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
    st.markdown("### Profile & settings")

    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)

    with st.form(_key("settings_form")):
        st.text_input("Email", value=email, disabled=True)
        display_name = st.text_input("Display name", value=profile.get("display_name", ""), placeholder="Your name")
        username = st.text_input("Username", value=profile.get("username", ""), placeholder="your-handle")
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

    st.markdown('<div class="mantis-wrap">', unsafe_allow_html=True)

    top_l, top_r = st.columns([1, 1])
    with top_l:
        st.markdown('<div class="mantis-pill">🛡️ Secure account access · Supabase email/password</div>', unsafe_allow_html=True)
    with top_r:
        if st.button("← Back to Studio", use_container_width=True, key=_key("back_to_studio")):
            _go_back_to_studio()

    st.markdown(
        """
        <div class="mantis-hero">
            <div class="mantis-title">Account Access</div>
            <div class="mantis-sub">
                Create a MANTIS account to unlock exports + cloud sync. Guest mode stays available for writing and drafting.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
        st.markdown("</div>", unsafe_allow_html=True)
        return

    _render_login_ui()

    st.markdown("</div>", unsafe_allow_html=True)


main()
