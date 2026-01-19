import streamlit as st
from pathlib import Path

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"


def _load_markdown(filename: str) -> str:
    return (LEGAL_DIR / filename).read_text(encoding="utf-8")


def render_terms():
    st.title("Terms of Service")
    st.markdown(_load_markdown("terms.md"))


def render_privacy():
    st.title("Privacy Policy")
    st.markdown(_load_markdown("privacy.md"))


def render_copyright():
    st.title("Copyright")
    st.markdown(_load_markdown("copyright.md"))
