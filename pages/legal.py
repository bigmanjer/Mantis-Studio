import base64
from pathlib import Path

import streamlit as st

from app.utils import auth

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"


def _logo_base64() -> str:
    logo_path = ASSETS_DIR / "mantis_logo_trans.png"
    if not logo_path.exists():
        return ""
    return base64.b64encode(logo_path.read_bytes()).decode("utf-8")


def _load_markdown(filename: str) -> str:
    path = LEGAL_DIR / filename
    if not path.exists():
        return "Content unavailable."
    return path.read_text(encoding="utf-8")


def render_section(title: str, filename: str) -> None:
    st.markdown(f"### {title}")
    st.markdown(_load_markdown(filename))


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        .mantis-legal-header {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(120, 199, 190, 0.35);
            background: linear-gradient(135deg, rgba(24, 36, 45, 0.92), rgba(28, 44, 54, 0.92));
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
        }
        .mantis-legal-logo {
            width: 48px;
            height: 48px;
            border-radius: 14px;
            background: rgba(120, 199, 190, 0.12);
            border: 1px solid rgba(120, 199, 190, 0.35);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .mantis-legal-logo img {
            width: 32px;
            height: 32px;
            object-fit: contain;
        }
        .mantis-legal-title {
            font-size: 26px;
            font-weight: 700;
            margin: 0;
        }
        .mantis-legal-subtitle {
            color: rgba(230, 240, 245, 0.72);
            margin: 4px 0 0 0;
        }
        .mantis-legal-card {
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(120, 199, 190, 0.2);
            background: rgba(18, 24, 30, 0.35);
        }
        .mantis-legal-nav {
            margin-top: 8px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="Legal • MANTIS Studio", layout="wide")
    auth.require_login()
    _inject_styles()
    logo_b64 = _logo_base64()

    sections = [
        ("Terms of Service", "terms.md"),
        ("Privacy Policy", "privacy.md"),
        ("Copyright", "copyright.md"),
        ("Brand IP Clarity", "Brand_ip_Clarity.md"),
        ("Trademark Path", "Trademark_Path.md"),
    ]

    with st.sidebar:
        st.markdown("### Legal")
        selected_title = st.radio(
            "Legal sections",
            [title for title, _ in sections],
            label_visibility="collapsed",
            key="legal__section_nav",
        )

    header_logo = (
        f'<div class="mantis-legal-logo"><img src="data:image/png;base64,{logo_b64}" alt="Mantis logo" /></div>'
        if logo_b64
        else '<div class="mantis-legal-logo">🪲</div>'
    )
    st.markdown(
        f"""
        <div class="mantis-legal-header">
            {header_logo}
            <div>
                <div class="mantis-legal-title">Legal</div>
                <div class="mantis-legal-subtitle">Policies and documentation for MANTIS Studio.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    with st.container(border=True):
        st.markdown('<div class="mantis-legal-card">', unsafe_allow_html=True)
        for title, filename in sections:
            if title == selected_title:
                render_section(title, filename)
                break
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
