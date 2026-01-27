import streamlit as st


def render_footer():
    st.markdown(
        """
    <hr style="margin-top: 3rem;">
    <div style="text-align: center; font-size: 0.85rem; color: #9CA3AF;">
        © 2026 MANTIS Studio •
        <a href="?page=privacy">Privacy</a> •
        <a href="?page=terms">Terms</a> •
        <a href="?page=copyright">Copyright</a>
    </div>
    """,
        unsafe_allow_html=True,
    )
