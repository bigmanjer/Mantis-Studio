from __future__ import annotations

from pathlib import Path

import streamlit as st

# --------------------------------------------------------------------------
# Path to the centralized button / component CSS.
# All button styles live in assets/styles.css so that one file controls
# the visual language of every button and button-like element app-wide.
# --------------------------------------------------------------------------
_STYLES_CSS_PATH = Path(__file__).resolve().parents[2] / "assets" / "styles.css"

MANTIS_TOKENS = {
    "mantis_green": "#22c55e",
    "mantis_green_dark": "#16a34a",
    "mantis_blue": "#38bdf8",
    "mantis_bg": "#050b0f",
    "mantis_surface": "#0b141a",
    "mantis_surface_alt": "#0f1c24",
    "mantis_border": "rgba(148, 163, 184, 0.15)",
    "mantis_text": "#e2e8f0",
    "mantis_text_muted": "rgba(226, 232, 240, 0.7)",
    "mantis_shadow": "0 14px 32px rgba(0,0,0,0.4)",
}


def _load_button_css() -> str:
    """Read the unified button CSS from assets/styles.css."""
    try:
        return _STYLES_CSS_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def inject_theme() -> None:
    # Load the centralized button system CSS
    button_css = _load_button_css()

    st.markdown(
        f"""
        <style>
        :root {{
            --mantis-green: {MANTIS_TOKENS["mantis_green"]};
            --mantis-green-dark: {MANTIS_TOKENS["mantis_green_dark"]};
            --mantis-blue: {MANTIS_TOKENS["mantis_blue"]};
            --mantis-bg: {MANTIS_TOKENS["mantis_bg"]};
            --mantis-surface: {MANTIS_TOKENS["mantis_surface"]};
            --mantis-surface-alt: {MANTIS_TOKENS["mantis_surface_alt"]};
            --mantis-border: {MANTIS_TOKENS["mantis_border"]};
            --mantis-text: {MANTIS_TOKENS["mantis_text"]};
            --mantis-text-muted: {MANTIS_TOKENS["mantis_text_muted"]};
            --mantis-shadow: {MANTIS_TOKENS["mantis_shadow"]};
        }}

        .stApp {{
            background: radial-gradient(circle at top left, rgba(34,197,94,0.15), transparent 45%),
                        radial-gradient(circle at top right, rgba(56,189,248,0.12), transparent 45%),
                        var(--mantis-bg);
            color: var(--mantis-text);
        }}

        h1 {{
            font-size: 34px;
            font-weight: 700;
        }}

        h2 {{
            font-size: 24px;
            font-weight: 600;
        }}

        h3 {{
            font-size: 20px;
            font-weight: 600;
        }}

        p, li, label, input, textarea {{
            font-size: 15px;
        }}

        .mantis-card {{
            background: var(--mantis-surface);
            border: 1px solid var(--mantis-border);
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: var(--mantis-shadow);
        }}

        .mantis-card-soft {{
            background: var(--mantis-surface-alt);
            border: 1px solid var(--mantis-border);
            border-radius: 16px;
            padding: 16px 18px;
        }}

        .mantis-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 999px;
            border: 1px solid rgba(34,197,94,0.35);
            background: rgba(34,197,94,0.12);
            font-size: 12px;
            color: var(--mantis-text);
        }}

        .mantis-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 14px 18px;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(14, 26, 34, 0.95), rgba(7, 14, 18, 0.95));
            border: 1px solid rgba(34,197,94,0.2);
            box-shadow: var(--mantis-shadow);
        }}

        .mantis-nav-section {{
            margin-top: 12px;
            margin-bottom: 8px;
            font-weight: 600;
            font-size: 12px;
            color: var(--mantis-text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .mantis-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 12px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: rgba(34,197,94,0.2);
            border: 1px solid rgba(34,197,94,0.4);
            font-weight: 700;
        }}

        .mantis-quick-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 12px;
        }}

        .mantis-muted {{
            color: var(--mantis-text-muted);
        }}

        /* --- Unified button system (from assets/styles.css) --- */
        {button_css}
        </style>
        """,
        unsafe_allow_html=True,
    )
