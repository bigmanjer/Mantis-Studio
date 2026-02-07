import streamlit as st

from app.utils import ui_key


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    def _navigate(page: str) -> None:
        st.session_state.page = page
        st.query_params.clear()
        st.rerun()

    st.markdown("<hr style='margin-top: 3rem;'>", unsafe_allow_html=True)
    links = st.columns([1, 1, 1, 1, 1, 1.2])
    with links[0]:
        if st.button("Terms", key=ui_key("footer", "terms")):
            _navigate("terms")
    with links[1]:
        if st.button("Privacy", key=ui_key("footer", "privacy")):
            _navigate("privacy")
    with links[2]:
        if st.button("Legal", key=ui_key("footer", "legal")):
            _navigate("legal")
    with links[3]:
        st.link_button("Support", support_url)
    with links[4]:
        st.link_button("Contact", f"mailto:{contact_email}")
    with links[5]:
        st.caption(f"Version {version}")
