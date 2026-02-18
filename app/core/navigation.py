"""Navigation utilities for Mantis Studio."""

from __future__ import annotations


def navigate(page: str) -> None:
    """Navigate to a specific page.
    
    Args:
        page: The page key to navigate to (e.g., 'projects', 'chapters', 'dashboard')
    """
    import streamlit as st
    
    st.session_state.current_page = page
    # Also update the main page key used by the router
    st.session_state.page = page
    st.rerun()
