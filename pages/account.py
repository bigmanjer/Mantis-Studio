from __future__ import annotations

import streamlit as st

from app.utils import auth


def _return_to_studio(return_page: str) -> None:
    st.session_state["page"] = return_page or "home"
    if hasattr(st, "switch_page"):
        st.switch_page("Mantis_Studio.py")
    else:
        st.info("Use the sidebar to return to the studio.")


def main() -> None:
    st.set_page_config(page_title="Account Access • MANTIS Studio", layout="wide")

    redirect_reason = st.session_state.get("auth_redirect_reason")
    redirect_action = st.session_state.get("auth_redirect_action")
    return_page = st.session_state.get("auth_redirect_return_page", "home")

    if auth.is_authenticated():
        st.markdown("### Welcome back")
        st.caption("Your account is already connected.")
        st.markdown(f"**{auth.get_user_display_name()}**")
        email = auth.get_user_email()
        if email:
            st.caption(email)
        if st.button("Back to Studio", type="primary", use_container_width=True):
            _return_to_studio(return_page)
        return

    continue_guest = auth.render_login_screen(
        intent=redirect_reason or "Guest mode: creations are not saved. Create an account to save projects.",
        allow_guest=True,
    )
    if continue_guest:
        st.session_state["guest_continue_action"] = redirect_action
        st.session_state.pop("auth_redirect_reason", None)
        st.session_state.pop("auth_redirect_action", None)
        st.session_state.pop("auth_redirect_return_page", None)
        _return_to_studio(return_page)


if __name__ == "__main__":
    main()
