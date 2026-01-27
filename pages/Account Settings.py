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
        div[data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_debug_auth(user: object | None) -> None:
    if not auth.debug_auth_enabled():
        return
    keys: list[str] = []
    if isinstance(user, dict):
        keys = list(user.keys())
    elif user is not None:
        keys = list(getattr(user, "__dict__", {}).keys())
    st.markdown("### Debug auth")
    st.caption("Visible only when `debug_auth = true` in secrets.")
    st.code(
        {
            "user_keys": keys,
            "user_id": auth.get_user_id_with_fallback(user),
            "user_display_name": auth.get_user_display_name(user),
            "user_email": auth.get_user_email(user),
        },
        language="json",
    )


def _return_to_studio(return_page: str) -> None:
    st.session_state["page"] = return_page or "home"
    if hasattr(st, "switch_page"):
        st.switch_page("Mantis_Studio.py")
    else:
        st.info("Use the sidebar to return to the studio.")


def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")
    _inject_styles()

    st.markdown('<div class="mantis-account-wrap">', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="mantis-account-header">
            <div class="mantis-account-title">Account Access</div>
            <div class="mantis-account-sub">Create an account or sign in to unlock cloud save and collaboration.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    redirect_reason = st.session_state.get("auth_redirect_reason")
    redirect_action = st.session_state.get("auth_redirect_action")
    return_page = st.session_state.get("auth_redirect_return_page", "home")

    if auth.is_authenticated():
        st.success("You're signed in.")
        profile_cols = st.columns([1, 2.2])
        user = auth.get_current_user()
        with profile_cols[0]:
            avatar_url = auth.get_user_avatar_url(user)
            if avatar_url:
                st.image(avatar_url, width=72)
            else:
                st.markdown(
                    f"<div class='mantis-avatar'>{auth.get_user_initials(user)}</div>",
                    unsafe_allow_html=True,
                )
        with profile_cols[1]:
            st.markdown(f"**{auth.get_user_display_name(user)}**")
            email = auth.get_user_email(user)
            if email:
                st.caption(email)
            provider_label = auth.get_provider_label(user)
            if provider_label and not auth.is_email_provider(user):
                st.caption(f"Signed in with {provider_label}.")
            if auth.is_email_provider(user):
                auth.render_email_account_controls(email)
            manage_url = auth.get_manage_account_url(user)
            if manage_url:
                st.link_button("Manage account", manage_url, use_container_width=True)
        action_cols = st.columns(2)
        with action_cols[0]:
            if st.button(
                "Return to Studio",
                type="primary",
                use_container_width=True,
                key="account_return_to_studio",
            ):
                _return_to_studio(return_page)
        with action_cols[1]:
            auth.logout_button(
                label="Sign out",
                key="account_page_logout",
                extra_state_keys=["projects_dir", "project", "page", "_force_nav"],
            )
        _render_debug_auth(user)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    continue_guest = auth.render_login_screen(
        intent=redirect_reason or "Guest mode: local saves are temporary. Create an account to sync and export.",
        allow_guest=True,
    )
    if continue_guest:
        st.session_state["guest_continue_action"] = redirect_action
        st.session_state["pending_action"] = None
        st.session_state.pop("auth_redirect_reason", None)
        st.session_state.pop("auth_redirect_action", None)
        st.session_state.pop("auth_redirect_return_page", None)
        _return_to_studio(return_page)

    _render_debug_auth(st.user if hasattr(st, "user") else None)
    st.markdown("</div>", unsafe_allow_html=True)


main()
