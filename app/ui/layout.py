import streamlit as st

from app.utils import ui_key
from mantis.ui.layout import render_footer


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    st.markdown("<hr style='margin-top: 3rem;'>", unsafe_allow_html=True)
    links = st.columns([1, 1, 1, 1, 1, 1.2])
    with links[0]:
        if st.button("Terms", key=ui_key("footer", "terms")):
            st.query_params["page"] = "terms"
            st.rerun()
    with links[1]:
        if st.button("Privacy", key=ui_key("footer", "privacy")):
            st.query_params["page"] = "privacy"
            st.rerun()
    with links[2]:
        if st.button("Legal", key=ui_key("footer", "legal")):
            st.query_params["page"] = "legal"
            st.rerun()
    with links[3]:
        st.link_button("Support", support_url)
    with links[4]:
        st.link_button("Contact", f"mailto:{contact_email}")
    with links[5]:
        st.caption(f"Version {version}")
