import streamlit as st


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    st.markdown(
        f"""
    <hr style="margin-top: 3rem;">
    <div style="text-align: center; font-size: 0.85rem; color: #9CA3AF;">
        <a href="?page=terms">Terms</a> •
        <a href="?page=privacy">Privacy</a> •
        <a href="/pages/legal.py">Legal</a> •
        <a href="{support_url}">Support</a> •
        <a href="mailto:{contact_email}">Contact</a> •
        <span>Version {version}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )
