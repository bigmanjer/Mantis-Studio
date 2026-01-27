import base64
from datetime import date
from pathlib import Path

import streamlit as st

from app.ui.layout import render_footer
from app.utils.versioning import get_app_version

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LAST_UPDATED = date(2026, 1, 12)


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
        .mantis-legal-card {
            padding: 18px 20px;
            border-radius: 16px;
            border: 1px solid rgba(120, 199, 190, 0.2);
            background: rgba(18, 24, 30, 0.35);
        }
        .mantis-legal-card h3 {
            margin-top: 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_card(title: str, subtitle: str, content: str) -> None:
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(subtitle)
        st.markdown(content)


def main() -> None:
    st.set_page_config(page_title="Legal • MANTIS Studio", layout="wide")
    _inject_styles()
    logo_b64 = _logo_base64()

    sections = [
        ("Terms of Service", "terms.md", "Rules for using MANTIS Studio responsibly."),
        ("Privacy Policy", "privacy.md", "How we handle data and privacy."),
        ("Copyright & IP", "copyright.md", "Ownership, rights, and licensing guidance."),
        ("Acceptable Use", "Brand_ip_Clarity.md", "Safety, usage, and content rules."),
        ("Trademark & Brand", "Trademark_Path.md", "Brand use and trademark guidance."),
    ]

    header_logo = (
        f'<div class="mantis-legal-logo"><img src="data:image/png;base64,{logo_b64}" alt="Mantis logo" /></div>'
        if logo_b64
        else '<div class="mantis-legal-logo">🪲</div>'
    )
    header_cols = st.columns([3, 1])
    with header_cols[0]:
        st.markdown(
            f"""
            <div class="mantis-legal-header">
                {header_logo}
                <div>
                    <div class="mantis-page-title">Legal Hub</div>
                    <div class="mantis-page-sub">Policies, IP, and compliance documentation.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(f"Last updated: {LAST_UPDATED.strftime('%B %d, %Y')}")
    with header_cols[1]:
        if st.button("⬅ Back to Studio", use_container_width=True, key="legal_back"):
            if hasattr(st, "switch_page"):
                st.switch_page("Mantis_Studio.py")
            else:
                st.info("Use the sidebar to return to the studio.")

    st.markdown("#### Table of contents")
    toc_cols = st.columns(3)
    for idx, (title, _, _) in enumerate(sections):
        with toc_cols[idx % 3]:
            st.markdown(f"- {title}")

    st.markdown("")
    for title, filename, subtitle in sections:
        _render_card(title, subtitle, _load_markdown(filename))

    render_footer(get_app_version())


if __name__ == "__main__":
    main()
