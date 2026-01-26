import streamlit as st
from pathlib import Path

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"


def _load_markdown(filename: str) -> str:
    path = LEGAL_DIR / filename
    if not path.exists():
        return "Content unavailable."
    return path.read_text(encoding="utf-8")


def render_section(title: str, filename: str) -> None:
    st.subheader(title)
    st.markdown(_load_markdown(filename))


def main() -> None:
    st.set_page_config(page_title="Legal • MANTIS Studio", layout="wide")
    st.title("Legal")
    st.caption("Policies and documentation for MANTIS Studio.")

    sections = [
        ("Terms of Service", "terms.md"),
        ("Privacy Policy", "privacy.md"),
        ("Copyright", "copyright.md"),
        ("Brand IP Clarity", "Brand_ip_Clarity.md"),
        ("Trademark Path", "Trademark_Path.md"),
    ]

    tabs = st.tabs([title for title, _ in sections])
    for tab, (title, filename) in zip(tabs, sections):
        with tab:
            render_section(title, filename)


if __name__ == "__main__":
    main()
