from __future__ import annotations

import base64
from datetime import date
from pathlib import Path
from typing import List

import streamlit as st

LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
LAST_UPDATED = date(2026, 1, 12)

SECTIONS = [
    {"title": "Terms of Service", "filename": "terms.md", "updated": "2024-06-01"},
    {"title": "Privacy Policy", "filename": "privacy.md", "updated": "2024-06-01"},
    {"title": "Cookie Policy", "filename": "cookie.md", "updated": "2024-06-01"},
    {"title": "Contact", "filename": "contact.md", "updated": "2024-06-01"},
    {"title": "Copyright", "filename": "copyright.md", "updated": "2024-06-01"},
    {"title": "Brand IP Clarity", "filename": "Brand_ip_Clarity.md", "updated": "2024-06-01"},
    {"title": "Trademark Path", "filename": "Trademark_Path.md", "updated": "2024-06-01"},
]


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


def _extract_toc(markdown_text: str) -> List[str]:
    toc = []
    for line in markdown_text.splitlines():
        if line.startswith("## "):
            toc.append(line.replace("##", "").strip())
    return toc


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
        .mantis-legal-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid rgba(120, 199, 190, 0.35);
            background: rgba(15, 23, 42, 0.5);
            color: rgba(226, 232, 240, 0.85);
            font-size: 12px;
        }
        .mantis-legal-summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin: 18px 0 8px;
        }
        .mantis-legal-card {
            padding: 14px 16px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.25);
            background: rgba(15, 23, 42, 0.55);
        }
        .mantis-legal-sidebar {
            position: sticky;
            top: 16px;
            padding: 16px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            background: rgba(7, 12, 18, 0.7);
        }
        .mantis-legal-sidebar h4 {
            margin-top: 0;
        }
        .stMarkdown p, .stMarkdown li {
            font-size: 16px;
            line-height: 1.7;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_footer() -> None:
    st.markdown("---")
    f1, f2 = st.columns([1, 1])
    with f1:
        if st.button("⬅ Back to Studio", use_container_width=True, key="legal_footer_back"):
            if hasattr(st, "switch_page"):
                st.switch_page("Mantis_Studio.py")
            else:
                st.info("Use the sidebar to return to the studio.")
    with f2:
        st.caption("© MANTIS Studio • Built with Streamlit")


def main() -> None:
    st.set_page_config(page_title="Legal • MANTIS Studio", layout="wide")
    _inject_styles()
    logo_b64 = _logo_base64()

    titles = [section["title"] for section in SECTIONS]
    with st.sidebar:
        st.markdown("### Legal")
        st.caption("Terms • Privacy • Cookie • Contact")
        selected_title = st.radio(
            "Legal sections",
            titles,
            label_visibility="collapsed",
            key="legal__section_nav",
        )

    section = next((entry for entry in SECTIONS if entry["title"] == selected_title), SECTIONS[0])
    markdown = _load_markdown(section["filename"])
    toc = _extract_toc(markdown)

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
                    <div class="mantis-legal-title">Legal Center</div>
                    <div class="mantis-legal-subtitle">Readable policies, clear updates, and trust-first explanations.</div>
                    <div class="mantis-legal-chip">Last updated {LAST_UPDATED.strftime('%B %d, %Y')}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="mantis-legal-summary">
                <div class="mantis-legal-card">
                    <strong>Clarity first</strong>
                    <div>Short summaries, plain-language details, and clear next steps.</div>
                </div>
                <div class="mantis-legal-card">
                    <strong>Trust & safety</strong>
                    <div>We highlight how data is handled and where responsibilities sit.</div>
                </div>
                <div class="mantis-legal-card">
                    <strong>Support ready</strong>
                    <div>Questions? Reach out anytime at legal@mantis-studio.example.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with header_cols[1]:
        if st.button("⬅ Back to Studio", use_container_width=True, key="legal_back"):
            if hasattr(st, "switch_page"):
                st.switch_page("Mantis_Studio.py")
            else:
                st.info("Use the sidebar to return to the studio.")

    st.markdown("")
    main_cols = st.columns([3, 1], gap="large")
    with main_cols[0]:
        with st.container(border=True):
            st.markdown(f"## {section['title']}")
            st.caption(f"Last updated: {section['updated']}")
            if toc:
                st.markdown("#### Table of contents")
                for item in toc:
                    st.markdown(f"- {item}")
                st.divider()
            st.markdown(markdown)
    with main_cols[1]:
        links_html = "".join(f"<li><strong>{item['title']}</strong></li>" for item in SECTIONS)
        st.markdown(
            f"""
            <div class="mantis-legal-sidebar">
                <h4>Quick links</h4>
                <p>Jump to core policies and support resources.</p>
                <ul>
                    {links_html}
                </ul>
                <hr style="border-color: rgba(148, 163, 184, 0.25); margin: 12px 0;">
                <strong>Need help?</strong>
                <div>support@mantis-studio.example</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    _render_footer()


if __name__ == "__main__":
    main()
