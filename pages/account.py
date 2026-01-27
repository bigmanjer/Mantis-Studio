from __future__ import annotations

import streamlit as st

from app.utils import auth


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
    st.markdown(
        """
        <style>
        .mantis-account-wrap {
            max-width: 1100px;
            margin: 0 auto;
        }
        .mantis-account-header {
            padding: 24px 28px;
            border-radius: 20px;
            border: 1px solid rgba(120, 199, 190, 0.3);
            background: linear-gradient(135deg, rgba(16, 24, 36, 0.95), rgba(10, 16, 24, 0.95));
            box-shadow: 0 16px 32px rgba(0,0,0,0.3);
            margin-bottom: 24px;
        }
        .mantis-account-title {
            font-size: 28px;
            font-weight: 700;
        }
        .mantis-account-sub {
            color: rgba(226, 232, 240, 0.75);
            margin-top: 4px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        st.success("Login complete. We’re finishing your request.")
        st.caption("You can safely return to the studio while we complete your action.")
        if st.button("Continue to Studio", type="primary", use_container_width=True):
            _return_to_studio(return_page)
        _render_debug_auth(st.user if hasattr(st, "user") else None)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    continue_guest = auth.render_login_screen(
        intent=redirect_reason or "Guest mode: creations are not saved. Create an account to save projects.",
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
