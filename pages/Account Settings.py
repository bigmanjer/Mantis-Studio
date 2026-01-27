from __future__ import annotations

import time
import streamlit as st

from app.utils import auth


# -----------------------------
# Styling
# -----------------------------
def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root{
            --mantis-a: rgba(120,199,190,.95);
            --mantis-b: rgba(80,160,255,.95);
            --panel: rgba(15, 23, 42, 0.55);
            --panel2: rgba(2, 6, 23, 0.65);
            --border: rgba(148, 163, 184, 0.18);
            --text-dim: rgba(226,232,240,0.72);
        }
        .acct-wrap{
            max-width: 1160px;
            margin: 0 auto;
            padding: 8px 0 24px 0;
        }
        .acct-hero{
            border-radius: 26px;
            padding: 22px 24px;
            border: 1px solid rgba(120,199,190,0.28);
            background:
              radial-gradient(1200px 380px at 20% 0%, rgba(120,199,190,0.25), transparent 55%),
              radial-gradient(900px 320px at 85% 10%, rgba(80,160,255,0.22), transparent 55%),
              linear-gradient(135deg, rgba(2, 6, 23, 0.82), rgba(15, 23, 42, 0.78));
            box-shadow: 0 18px 38px rgba(0,0,0,0.35);
            margin-bottom: 18px;
        }
        .acct-hero h1{
            margin: 0;
            font-size: 34px;
            font-weight: 800;
            letter-spacing: -0.2px;
        }
        .acct-hero p{
            margin: 8px 0 0 0;
            color: var(--text-dim);
            font-size: 14px;
            max-width: 75ch;
            line-height: 1.45;
        }
        .pill{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            margin-top: 12px;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(120,199,190,0.26);
            background: rgba(15, 23, 42, 0.55);
            color: rgba(226,232,240,0.85);
            font-size: 12px;
            width: fit-content;
        }
        .panel{
            border-radius: 22px;
            padding: 18px 18px;
            border: 1px solid var(--border);
            background: var(--panel);
        }
        .panel h3{
            margin-top: 0;
        }
        .muted{
            color: var(--text-dim);
            font-size: 13px;
            line-height: 1.45;
        }
        .statgrid{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
            margin-top: 12px;
        }
        .stat{
            border-radius: 18px;
            padding: 14px;
            border: 1px solid rgba(148,163,184,0.16);
            background: rgba(2, 6, 23, 0.35);
        }
        .stat .t{
            font-weight: 700;
            font-size: 13px;
            margin: 0;
        }
        .stat .d{
            margin: 6px 0 0 0;
            color: var(--text-dim);
            font-size: 12px;
        }
        .top-actions{
            display:flex;
            justify-content: space-between;
            gap: 10px;
            margin-bottom: 10px;
        }
        .soft-note{
            border-radius: 16px;
            padding: 12px 14px;
            border: 1px solid rgba(56, 189, 248, 0.18);
            background: rgba(30, 64, 175, 0.12);
            color: rgba(226,232,240,0.9);
            font-size: 13px;
        }
        /* Hide streamlit sidebar multipage nav for this page */
        div[data-testid="stSidebarNav"]{ display:none; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _k(name: str) -> str:
    return f"account_{name}"


# -----------------------------
# Reset cooldown (local – avoids auth.reset_cooldown_remaining crash)
# -----------------------------
_RESET_COOLDOWN_SECONDS = 60
_RESET_TS_KEY = "pw_reset_last_sent_ts"


def _reset_cooldown_remaining() -> int:
    last = st.session_state.get(_RESET_TS_KEY)
    if not last:
        return 0
    elapsed = time.time() - float(last)
    return int(max(0, _RESET_COOLDOWN_SECONDS - elapsed))


def _mark_reset_sent() -> None:
    st.session_state[_RESET_TS_KEY] = time.time()


# -----------------------------
# Navigation
# -----------------------------
def _return_to_studio(return_page: str) -> None:
    st.session_state["page"] = return_page or "home"
    # If multipage + switch_page exists, go to main entry
    if hasattr(st, "switch_page"):
        try:
            st.switch_page("Mantis_Studio.py")
            return
        except Exception:
            pass
    # Fallback
    st.info("Use the sidebar to return to the studio.")


def _render_top_actions(return_page: str, redirect_reason: str | None = None) -> None:
    c1, c2, c3 = st.columns([1, 1, 2], vertical_alignment="center")
    with c1:
        if st.button("← Return to Studio", use_container_width=True, key=_k("top_back")):
            _return_to_studio(return_page)
    with c2:
        if st.button("Continue as Guest", use_container_width=True, key=_k("top_guest")):
            # Clear redirect hints and go back
            st.session_state.pop("auth_redirect_reason", None)
            st.session_state.pop("auth_redirect_action", None)
            st.session_state.pop("auth_redirect_return_page", None)
            _return_to_studio(return_page)
    with c3:
        if redirect_reason:
            st.info(redirect_reason)


# -----------------------------
# UI blocks
# -----------------------------
def _flash_messages() -> None:
    notice = st.session_state.pop("account_notice", None)
    error = st.session_state.pop("account_error", None)
    if notice:
        st.success(notice)
    if error:
        st.error(error)


def _render_login_tabs() -> None:
    _flash_messages()

    # Make the "not configured" message look nicer and not ruin the page
    if not auth.auth_is_configured():
        st.markdown(
            "<div class='soft-note'>⚙️ Supabase isn’t configured yet. "
            "Set <code>SUPABASE_URL</code> and <code>SUPABASE_ANON_KEY</code> in Streamlit secrets to enable account creation.</div>",
            unsafe_allow_html=True,
        )
        st.write("")

    login_tab, signup_tab = st.tabs(["Log in", "Create account"])

    with login_tab:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Log in")
        st.markdown("<p class='muted'>Welcome back. Log in to sync projects and unlock exports.</p>", unsafe_allow_html=True)

        with st.form(_k("login_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_k("login_email"),
            )
            password = st.text_input(
                "Password",
                type="password",
                key=_k("login_password"),
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
                    st.session_state["auth_email"] = email.strip().lower()
                else:
                    st.session_state["account_error"] = msg
            st.rerun()

        with st.expander("Forgot password?"):
            remaining = _reset_cooldown_remaining()
            with st.form(_k("reset_form")):
                reset_email = st.text_input(
                    "Email for reset link",
                    value=email,
                    placeholder="you@example.com",
                    key=_k("reset_email"),
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
                        _mark_reset_sent()
                        st.session_state["account_notice"] = msg
                        st.session_state["auth_email"] = reset_email.strip().lower()
                    else:
                        st.session_state["account_error"] = msg
                st.rerun()

            remaining = _reset_cooldown_remaining()
            if remaining > 0:
                st.caption(f"Resend available in {remaining}s.")

        st.markdown("</div>", unsafe_allow_html=True)

    with signup_tab:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### Create account")
        st.markdown("<p class='muted'>Use email + password. You can add display name and username after logging in.</p>", unsafe_allow_html=True)

        with st.form(_k("signup_form")):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_k("signup_email"),
            )
            password = st.text_input(
                "Create password",
                type="password",
                key=_k("signup_password"),
            )
            confirm = st.text_input(
                "Confirm password",
                type="password",
                key=_k("signup_password_confirm"),
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
                    st.session_state["auth_email"] = email.strip().lower()
                else:
                    st.session_state["account_error"] = msg
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


def _render_account_settings(user: dict) -> None:
    _flash_messages()

    user_id = auth.get_user_id(user)
    email = auth.get_user_email(user)
    profile = auth.get_profile(user_id) or auth.ensure_profile(user) or {}

    display_name_value = profile.get("display_name") or auth.get_user_display_name(user)
    username_value = profile.get("username") or ""

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("### Account Settings")
    st.markdown("<p class='muted'>Update your public name and handle. Email is read-only.</p>", unsafe_allow_html=True)

    with st.form(_k("settings_form")):
        st.text_input("Email", value=email, disabled=True, key=_k("email"))
        display_name = st.text_input(
            "Display name",
            value=display_name_value,
            placeholder="Your name",
            key=_k("display_name"),
        )
        username = st.text_input(
            "Username",
            value=username_value,
            placeholder="unique-handle",
            key=_k("username"),
        )
        save = st.form_submit_button("Save changes", use_container_width=True)

    if save:
        ok, msg = auth.update_profile(user_id, email, display_name.strip(), username.strip())
        if ok:
            st.session_state["account_notice"] = msg
        else:
            st.session_state["account_error"] = msg
        st.rerun()

    # Optional extras from your auth util (if it renders email/password controls)
    auth.render_email_account_controls(email)

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")
    _inject_styles()

    return_page = st.session_state.get("auth_redirect_return_page", "home")
    redirect_reason = st.session_state.get("auth_redirect_reason")

    st.markdown('<div class="acct-wrap">', unsafe_allow_html=True)

    # Top row navigation (always visible)
    _render_top_actions(return_page=return_page, redirect_reason=redirect_reason)

    # Hero
    st.markdown(
        """
        <div class="acct-hero">
            <h1>Account Access</h1>
            <p>Create an account or log in to unlock cloud sync and exports. Guest mode stays available so you can keep writing.</p>
            <div class="pill">✨ Email login · 🔒 Secure auth · 📦 Export unlock</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Two-column layout: left explainer / right auth card
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("### What you get with an account")
        st.markdown(
            """
            <div class="statgrid">
                <div class="stat"><p class="t">☁️ Cloud sync</p><p class="d">Keep projects safe across devices.</p></div>
                <div class="stat"><p class="t">📦 Export unlock</p><p class="d">Download your work in supported formats.</p></div>
                <div class="stat"><p class="t">🧠 Saved preferences</p><p class="d">Keep your settings and profile details.</p></div>
            </div>
            <p class="muted" style="margin-top:12px;">
                You can still write in Guest mode. When you’re ready to export, create an account and continue.
            </p>
            """,
            unsafe_allow_html=True,
        )

        # Always-visible “back/guest” actions too (so user never feels trapped)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Return to Studio", use_container_width=True, key=_k("left_back")):
                _return_to_studio(return_page)
        with c2:
            if st.button("Continue as Guest", use_container_width=True, key=_k("left_guest")):
                st.session_state.pop("auth_redirect_reason", None)
                st.session_state.pop("auth_redirect_action", None)
                st.session_state.pop("auth_redirect_return_page", None)
                _return_to_studio(return_page)

        st.markdown("</div>", unsafe_allow_html=True)

        # Small footer links (still here, but not dominating)
        st.caption("Privacy · Terms · Legal hub")

    with right:
        if auth.is_authenticated():
            user = auth.get_current_user() or {}
            st.success("You're signed in.")
            _render_account_settings(user)

            # Post-login actions
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Return to Studio", type="primary", use_container_width=True, key=_k("right_back")):
                    _return_to_studio(return_page)
            with c2:
                auth.logout_button(
                    label="Log out",
                    key=_k("logout"),
                    extra_state_keys=["projects_dir", "project", "page", "_force_nav"],
                )
        else:
            _render_login_tabs()

            # Clear “continue guest” at bottom too
            if st.button("Continue in Guest mode", use_container_width=True, key=_k("continue_guest")):
                st.session_state.pop("auth_redirect_reason", None)
                st.session_state.pop("auth_redirect_action", None)
                st.session_state.pop("auth_redirect_return_page", None)
                _return_to_studio(return_page)

    st.markdown("</div>", unsafe_allow_html=True)


main()
