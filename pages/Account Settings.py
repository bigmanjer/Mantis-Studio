from __future__ import annotations

import time
import streamlit as st

from app.utils import auth


# -----------------------------
# Styling (MANTIS dark + green)
# -----------------------------
def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root{
            --mantis-bg1:#071016;
            --mantis-bg2:#081a14;
            --mantis-card: rgba(10, 20, 28, 0.70);
            --mantis-card2: rgba(10, 28, 22, 0.55);
            --mantis-border: rgba(34, 197, 94, 0.22);
            --mantis-border2: rgba(56, 189, 248, 0.08);
            --mantis-text: rgba(226,232,240,0.92);
            --mantis-sub: rgba(226,232,240,0.70);
            --mantis-green: #22c55e;
            --mantis-green2: rgba(34,197,94,0.18);
            --mantis-shadow: 0 18px 50px rgba(0,0,0,0.45);
        }

        /* Hide streamlit multipage nav (you already wanted this) */
        div[data-testid="stSidebarNav"] { display: none; }

        .mantis-wrap {
            max-width: 1120px;
            margin: 0 auto;
            padding-bottom: 24px;
        }

        .mantis-topbar {
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap: 14px;
            margin: 6px 0 18px 0;
        }

        .mantis-pill {
            display:inline-flex;
            gap:10px;
            align-items:center;
            padding: 10px 14px;
            border-radius: 999px;
            border: 1px solid var(--mantis-border);
            background: linear-gradient(135deg, rgba(34,197,94,0.10), rgba(2,132,199,0.06));
            color: var(--mantis-text);
            font-size: 13px;
        }

        .mantis-hero {
            border-radius: 26px;
            border: 1px solid var(--mantis-border);
            background: radial-gradient(1200px 400px at 20% 0%, rgba(34,197,94,0.18), transparent 50%),
                        radial-gradient(1200px 400px at 80% 0%, rgba(2,132,199,0.10), transparent 45%),
                        linear-gradient(135deg, rgba(7,16,22,0.95), rgba(8,26,20,0.95));
            box-shadow: var(--mantis-shadow);
            padding: 22px 24px;
            margin-bottom: 18px;
        }

        .mantis-title {
            font-size: 30px;
            font-weight: 800;
            letter-spacing: 0.3px;
            color: var(--mantis-text);
            margin: 0;
        }
        .mantis-sub {
            margin-top: 6px;
            color: var(--mantis-sub);
            font-size: 14px;
        }

        .mantis-grid {
            display:grid;
            grid-template-columns: 1.05fr 0.95fr;
            gap: 16px;
            margin-top: 14px;
        }

        @media (max-width: 980px) {
            .mantis-grid { grid-template-columns: 1fr; }
        }

        .mantis-card {
            border-radius: 22px;
            border: 1px solid rgba(148,163,184,0.16);
            background: var(--mantis-card);
            box-shadow: 0 14px 40px rgba(0,0,0,0.35);
            padding: 18px 18px;
        }

        .mantis-card h3 {
            margin: 0 0 10px 0;
            font-size: 18px;
            font-weight: 700;
            color: var(--mantis-text);
        }

        .mantis-muted {
            color: var(--mantis-sub);
            font-size: 13px;
            line-height: 1.45;
        }

        .mantis-divider {
            height: 1px;
            background: rgba(148,163,184,0.16);
            margin: 14px 0;
        }

        .mantis-kpi {
            display:grid;
            grid-template-columns: repeat(3, minmax(0,1fr));
            gap: 10px;
            margin-top: 10px;
        }
        @media (max-width: 980px) { .mantis-kpi { grid-template-columns: 1fr; } }

        .mantis-kpi .box {
            border-radius: 16px;
            padding: 12px 12px;
            border: 1px solid rgba(34,197,94,0.16);
            background: rgba(34,197,94,0.06);
        }
        .mantis-kpi .label {
            font-size: 12px;
            color: var(--mantis-sub);
            margin: 0;
        }
        .mantis-kpi .value {
            font-size: 14px;
            font-weight: 700;
            margin: 3px 0 0 0;
            color: var(--mantis-text);
        }

        /* Make primary buttons feel like MANTIS */
        div.stButton > button[kind="primary"]{
            background: linear-gradient(135deg, rgba(34,197,94,0.95), rgba(16,185,129,0.92)) !important;
            border: 1px solid rgba(34,197,94,0.35) !important;
            color: #04110a !important;
            font-weight: 800 !important;
            border-radius: 14px !important;
        }

        /* Normal buttons */
        div.stButton > button{
            border-radius: 14px !important;
            border: 1px solid rgba(148,163,184,0.20) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _k(name: str) -> str:
    return f"acct_{name}"


def _switch_to_studio(default_page: str = "home") -> None:
    # Keep legacy behavior if your main router uses st.session_state["page"]
    st.session_state["page"] = default_page or "home"
    st.session_state["_force_nav"] = True

    # Streamlit multipage: return to main file
    if hasattr(st, "switch_page"):
        try:
            st.switch_page("Mantis_Studio.py")
        except Exception:
            # fallback
            st.info("Use the sidebar to return to the studio.")
    else:
        st.info("Use the sidebar to return to the studio.")


# -----------------------------------
# UX helpers (fix “buttons do nothing”)
# -----------------------------------
def _flash(kind: str, msg: str) -> None:
    # Store + rerun so the message shows immediately after submit
    st.session_state["account_flash_kind"] = kind
    st.session_state["account_flash_msg"] = msg
    st.rerun()


def _render_flash() -> None:
    kind = st.session_state.pop("account_flash_kind", None)
    msg = st.session_state.pop("account_flash_msg", None)
    if not kind or not msg:
        return
    if kind == "success":
        st.success(msg)
    elif kind == "warning":
        st.warning(msg)
    else:
        st.error(msg)


def _cooldown_seconds() -> int:
    """Local reset cooldown (prevents spam) without relying on auth module."""
    until = st.session_state.get("pw_reset_cooldown_until", 0.0)
    remaining = int(max(0.0, until - time.time()))
    return remaining


def _set_cooldown(seconds: int = 45) -> None:
    st.session_state["pw_reset_cooldown_until"] = time.time() + float(seconds)


# -----------------------------
# Login + signup
# -----------------------------
def _render_login_signup() -> None:
    configured = bool(getattr(auth, "auth_is_configured", lambda: False)())
    if not configured:
        st.warning(
            "Supabase is not configured yet. Set **SUPABASE_URL** and **SUPABASE_ANON_KEY** in Streamlit Secrets, then restart the app."
        )

    tabs = st.tabs(["Log in", "Create account"])

    # ---- LOG IN ----
    with tabs[0]:
        with st.form(_k("login_form"), clear_on_submit=False):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_k("login_email"),
                disabled=not configured,
            )
            password = st.text_input(
                "Password",
                type="password",
                key=_k("login_password"),
                disabled=not configured,
            )

            c1, c2 = st.columns([1, 1])
            with c1:
                submit = st.form_submit_button("Log in", use_container_width=True, disabled=not configured)
            with c2:
                guest = st.form_submit_button("Continue in Guest mode", use_container_width=True)

        if guest:
            _switch_to_studio(st.session_state.get("auth_redirect_return_page", "home"))
            return

        if submit:
            e = (email or "").strip().lower()
            if "@" not in e:
                _flash("error", "Enter a valid email address.")
            if not password:
                _flash("error", "Enter your password to continue.")

            ok, msg = auth.auth_login(e, password)
            st.session_state["auth_email"] = e
            if ok:
                _flash("success", msg or "Signed in.")
            else:
                _flash("error", msg or "Login failed.")

        with st.expander("Forgot password?"):
            remaining = _cooldown_seconds()
            st.caption("We’ll email you a **MANTIS password reset link**. (This does *not* send you to Google/Microsoft.)")

            with st.form(_k("reset_form"), clear_on_submit=False):
                reset_email = st.text_input(
                    "Email for reset link",
                    value=st.session_state.get("auth_email", ""),
                    placeholder="you@example.com",
                    key=_k("reset_email"),
                    disabled=not configured,
                )
                reset_submit = st.form_submit_button(
                    "Send reset link",
                    use_container_width=True,
                    disabled=(not configured) or (remaining > 0),
                )

            if remaining > 0:
                st.caption(f"Resend available in **{remaining}s**.")

            if reset_submit:
                e = (reset_email or "").strip().lower()
                if "@" not in e:
                    _flash("error", "Enter a valid email address.")
                ok, msg = auth.auth_request_password_reset(e)
                st.session_state["auth_email"] = e
                if ok:
                    _set_cooldown(45)
                    _flash("success", msg or "Reset link sent. Check your inbox.")
                else:
                    _flash("error", msg or "Could not send reset link.")

    # ---- SIGN UP ----
    with tabs[1]:
        with st.form(_k("signup_form"), clear_on_submit=False):
            email = st.text_input(
                "Email address",
                value=st.session_state.get("auth_email", ""),
                placeholder="you@example.com",
                key=_k("signup_email"),
                disabled=not configured,
            )
            password = st.text_input("Create password", type="password", key=_k("signup_password"), disabled=not configured)
            confirm = st.text_input(
                "Confirm password", type="password", key=_k("signup_password_confirm"), disabled=not configured
            )
            submit = st.form_submit_button("Create account", use_container_width=True, disabled=not configured)

        if submit:
            e = (email or "").strip().lower()
            if "@" not in e:
                _flash("error", "Enter a valid email address.")
            if not password or len(password) < 8:
                _flash("error", "Create a password with at least 8 characters.")
            if password != confirm:
                _flash("error", "Passwords do not match.")

            ok, msg = auth.auth_signup(e, password)
            st.session_state["auth_email"] = e
            if ok:
                _flash(
                    "success",
                    msg
                    or "Account created. Check your inbox for a verification email (if enabled), then come back and log in.",
                )
            else:
                _flash("error", msg or "Signup failed.")


# -----------------------------
# Logged-in settings view
# -----------------------------
def _render_account_settings(user: dict) -> None:
    user_id = auth.get_user_id(user)
    email = auth.get_user_email(user)

    profile = auth.get_profile(user_id) or auth.ensure_profile(user) or {}
    display_name_value = profile.get("display_name") or auth.get_user_display_name(user)
    username_value = profile.get("username") or ""

    st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
    st.markdown("### Profile & settings")
    st.caption("Update your public profile info for MANTIS Studio.")

    with st.form(_k("settings_form"), clear_on_submit=False):
        st.text_input("Email", value=email or "", disabled=True, key=_k("email"))
        display_name = st.text_input("Display name", value=display_name_value or "", placeholder="Your name", key=_k("display"))
        username = st.text_input("Username", value=username_value or "", placeholder="unique-handle", key=_k("username"))
        save = st.form_submit_button("Save changes", use_container_width=True)

    if save:
        ok, msg = auth.update_profile(user_id, email, (display_name or "").strip(), (username or "").strip())
        if ok:
            _flash("success", msg or "Saved.")
        else:
            _flash("error", msg or "Could not save profile.")

    # Email/password controls (optional; keep guarded)
    if hasattr(auth, "render_email_account_controls"):
        auth.render_email_account_controls(email)

    st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Main
# -----------------------------
def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")
    _inject_styles()

    st.markdown("<div class='mantis-wrap'>", unsafe_allow_html=True)

    # Top bar + back button
    top_l, top_r = st.columns([0.72, 0.28])
    with top_l:
        st.markdown("<div class='mantis-pill'>🛡️ Secure account access • Supabase email/password</div>", unsafe_allow_html=True)
    with top_r:
        if st.button("← Back to Studio", use_container_width=True, key=_k("back_top")):
            _switch_to_studio(st.session_state.get("auth_redirect_return_page", "home"))

    # Hero
    st.markdown(
        """
        <div class="mantis-hero">
            <div class="mantis-title">Account Access</div>
            <div class="mantis-sub">
                Create a MANTIS account to unlock cloud sync and exports.
                Guest mode stays available for writing and drafting.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_flash()

    # Redirect context (if export is gated elsewhere)
    redirect_reason = st.session_state.get("auth_redirect_reason")
    if redirect_reason:
        st.info(redirect_reason)

    # Logged in?
    if auth.is_authenticated():
        user = auth.get_current_user() or {}

        st.markdown("<div class='mantis-grid'>", unsafe_allow_html=True)
        # Left: settings
        st.markdown("<div>", unsafe_allow_html=True)
        _render_account_settings(user)
        st.markdown("</div>", unsafe_allow_html=True)

        # Right: actions/status
        st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
        st.markdown("### You’re signed in ✅")
        st.markdown(
            "<div class='mantis-muted'>You can now export and sync (if enabled). Guest restrictions should no longer apply.</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='mantis-divider'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Return to Studio", type="primary", use_container_width=True, key=_k("back_logged")):
                _switch_to_studio(st.session_state.get("auth_redirect_return_page", "home"))
        with c2:
            auth.logout_button(
                label="Log out",
                key=_k("logout"),
                extra_state_keys=["projects_dir", "project", "page", "_force_nav"],
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    # Not logged in: show login/signup + guest info
    st.markdown("<div class='mantis-grid'>", unsafe_allow_html=True)

    # Left: explanation
    st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
    st.markdown("### Guest mode vs Account")
    st.markdown(
        """
        <div class="mantis-muted">
        <b>Guest mode</b> is great for drafting and generating outlines/chapters.
        <br/><br/>
        <b>Account</b> unlocks:
        <ul>
            <li>Exports (PDF/Docx/Zip)</li>
            <li>Cloud sync (when enabled)</li>
            <li>Account profile (display name / username)</li>
            <li>Password reset managed by <b>MANTIS</b> (not Google/Microsoft)</li>
        </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="mantis-kpi">
            <div class="box"><p class="label">Drafting</p><p class="value">Allowed in Guest</p></div>
            <div class="box"><p class="label">AI generation</p><p class="value">Allowed in Guest</p></div>
            <div class="box"><p class="label">Export</p><p class="value">Requires Account</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Right: forms
    st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
    st.markdown("### Sign in / Create account")
    st.caption("Use email + password. No Keycloak, no external recovery links.")
    _render_login_signup()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


main()
