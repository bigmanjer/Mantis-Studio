from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict

import streamlit as st
import streamlit.components.v1 as components

from app.utils.branding_assets import resolve_asset_path


def get_theme_tokens(theme: str) -> Dict[str, Dict[str, str]]:
    return {
        "Dark": {
            "bg": "#08090d",
            "bg_glow": "radial-gradient(circle at 18% 15%, rgba(35,247,192,0.18), transparent 45%), radial-gradient(circle at 85% 10%, rgba(255,178,77,0.16), transparent 42%), radial-gradient(circle at 70% 85%, rgba(72,200,255,0.08), transparent 40%)",
            "text": "#f6f1e9",
            "muted": "#b7ac9b",
            "input_bg": "#0f141c",
            "input_border": "#263245",
            "button_bg": "linear-gradient(180deg, rgba(14,20,28,0.95), rgba(10,14,20,0.98))",
            "button_border": "#273144",
            "button_hover_border": "#23f7c0",
            "primary_bg": "linear-gradient(135deg, #23f7c0, #6bff8f)",
            "primary_border": "rgba(35,247,192,0.55)",
            "primary_hover_border": "#7dffb0",
            "card_bg": "linear-gradient(180deg, rgba(12,16,22,0.96), rgba(8,11,16,0.98))",
            "card_border": "#1f2a3a",
            "sidebar_bg": "linear-gradient(180deg, #0a0d12, #0b1016)",
            "sidebar_border": "#1b2736",
            "sidebar_title": "#c8ffe9",
            "divider": "#1c2533",
            "expander_border": "#273446",
            "header_gradient": "linear-gradient(135deg, #0b1017, #121a27)",
            "header_logo_bg": "rgba(35,247,192,0.18)",
            "header_sub": "#e6dccd",
            "shadow_strong": "0 18px 40px rgba(0,0,0,0.6)",
            "shadow_button": "0 10px 24px rgba(0,0,0,0.45)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(12,16,22,0.9), rgba(9,12,17,0.98))",
            "sidebar_brand_border": "rgba(35,247,192,0.28)",
            "sidebar_logo_bg": "rgba(35,247,192,0.14)",
            "accent": "#23f7c0",
            "accent_soft": "rgba(35,247,192,0.18)",
            "accent_glow": "rgba(35,247,192,0.45)",
            "surface": "rgba(13,18,25,0.9)",
            "surface_alt": "rgba(9,13,19,0.94)",
            "success": "#28f29c",
            "warning": "#ffb347",
        },
        "Light": {
            "bg": "#f7f3ee",
            "bg_glow": "radial-gradient(circle at 18% 15%, rgba(20,207,162,0.12), transparent 45%), radial-gradient(circle at 85% 8%, rgba(244,179,98,0.12), transparent 42%)",
            "text": "#1e1a16",
            "muted": "#5b5348",
            "input_bg": "#fffdf9",
            "input_border": "#c7b8a4",
            "button_bg": "linear-gradient(180deg, #fffdf9, #f2ece4)",
            "button_border": "#c9b9a5",
            "button_hover_border": "#14cfa2",
            "primary_bg": "linear-gradient(135deg, #14cfa2, #5ee3b5)",
            "primary_border": "rgba(20,207,162,0.45)",
            "primary_hover_border": "#0fbf8a",
            "card_bg": "#fffdf9",
            "card_border": "#d1c1ad",
            "sidebar_bg": "linear-gradient(180deg, #f1e9df, #ede2d7)",
            "sidebar_border": "#d6c6b1",
            "sidebar_title": "#1f6b54",
            "divider": "#d9cbb8",
            "expander_border": "#d1c1ad",
            "header_gradient": "linear-gradient(135deg, #f2ece4, #e9e1d6)",
            "header_logo_bg": "#e7ded2",
            "header_sub": "#3b342c",
            "shadow_strong": "0 12px 24px rgba(50,40,30,0.12)",
            "shadow_button": "0 6px 14px rgba(50,40,30,0.10)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(255,253,249,0.95), rgba(246,240,232,0.95))",
            "sidebar_brand_border": "rgba(31,107,84,0.2)",
            "sidebar_logo_bg": "rgba(20,207,162,0.12)",
            "accent": "#14cfa2",
            "accent_soft": "rgba(20,207,162,0.16)",
            "accent_glow": "rgba(20,207,162,0.35)",
            "surface": "rgba(255,253,249,0.95)",
            "surface_alt": "rgba(249,244,238,0.96)",
            "success": "#189e7e",
            "warning": "#c27c2c",
        },
    }


def apply_theme(tokens: Dict[str, str]) -> None:
    st.html(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap');
    :root {{
        --mantis-bg: {tokens["bg"]};
        --mantis-bg-glow: {tokens["bg_glow"]};
        --mantis-text: {tokens["text"]};
        --mantis-muted: {tokens["muted"]};
        --mantis-input-bg: {tokens["input_bg"]};
        --mantis-input-border: {tokens["input_border"]};
        --mantis-button-bg: {tokens["button_bg"]};
        --mantis-button-border: {tokens["button_border"]};
        --mantis-button-hover-border: {tokens["button_hover_border"]};
        --mantis-primary-bg: {tokens["primary_bg"]};
        --mantis-primary-border: {tokens["primary_border"]};
        --mantis-primary-hover-border: {tokens["primary_hover_border"]};
        --mantis-card-bg: {tokens["card_bg"]};
        --mantis-card-border: {tokens["card_border"]};
        --mantis-sidebar-bg: {tokens["sidebar_bg"]};
        --mantis-sidebar-border: {tokens["sidebar_border"]};
        --mantis-sidebar-title: {tokens["sidebar_title"]};
        --mantis-divider: {tokens["divider"]};
        --mantis-expander-border: {tokens["expander_border"]};
        --mantis-header-gradient: {tokens["header_gradient"]};
        --mantis-header-logo-bg: {tokens["header_logo_bg"]};
        --mantis-header-sub: {tokens["header_sub"]};
        --mantis-shadow-strong: {tokens["shadow_strong"]};
        --mantis-shadow-button: {tokens["shadow_button"]};
        --mantis-sidebar-brand-bg: {tokens["sidebar_brand_bg"]};
        --mantis-sidebar-brand-border: {tokens["sidebar_brand_border"]};
        --mantis-sidebar-logo-bg: {tokens["sidebar_logo_bg"]};
        --mantis-accent: {tokens["accent"]};
        --mantis-accent-soft: {tokens["accent_soft"]};
        --mantis-accent-glow: {tokens["accent_glow"]};
        --mantis-surface: {tokens["surface"]};
        --mantis-surface-alt: {tokens["surface_alt"]};
        --mantis-success: {tokens["success"]};
        --mantis-warning: {tokens["warning"]};
    }}
    .stApp {{
        background-color: var(--mantis-bg);
        background-image: var(--mantis-bg-glow);
        color: var(--mantis-text);
        font-family: 'Space Grotesk', sans-serif;
    }}
    section.main {{ padding-top: 1.8rem !important; overflow: visible !important; }}
    div[data-testid="stAppViewContainer"] {{ overflow: visible !important; }}
    div[data-testid="stAppViewContainer"] > .main {{ overflow: visible !important; }}
    .stApp {{ overflow: visible !important; }}
    .block-container {{ padding-top: 0 !important; padding-bottom: 2.2rem; max-width: 1380px; overflow: visible !important; }}
    .block-container > div:first-child {{ margin-top: 0 !important; }}
    .block-container > div[data-testid="stVerticalBlock"]:first-child {{ margin-top: 12px !important; }}
    header[data-testid="stHeader"] {{ display: none; height: 0; }}
    h1, h2 {{ letter-spacing: -0.02em; font-family: 'Source Serif 4', serif; }}
    h3 {{ letter-spacing: -0.01em; font-family: 'Space Grotesk', sans-serif; }}
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown div,
    .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label,
    .stNumberInput label, .stTextArea label {{
        color: var(--mantis-text) !important;
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
        color: var(--mantis-muted) !important;
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] p {{
        color: var(--mantis-text) !important;
    }}
    [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] p {{
        color: var(--mantis-muted) !important;
    }}
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {{
        background-color: var(--mantis-input-bg) !important;
        color: var(--mantis-text) !important;
        border: 1px solid var(--mantis-input-border) !important;
    }}
    div[data-baseweb="select"] input {{
        color: var(--mantis-text) !important;
    }}
    div[data-baseweb="select"] span {{
        color: var(--mantis-text) !important;
    }}
    div[data-baseweb="menu"] {{
        background: var(--mantis-card-bg) !important;
        border: 1px solid var(--mantis-card-border) !important;
    }}
    div[data-baseweb="option"] {{
        color: var(--mantis-text) !important;
        background: transparent !important;
    }}
    div[data-baseweb="option"]:hover {{
        background: var(--mantis-accent-soft) !important;
    }}
    .stTextArea textarea {{ background-color: var(--mantis-input-bg) !important; color: var(--mantis-text) !important; font-family: 'Source Serif 4', serif !important; font-size: 18px !important; line-height: 1.65 !important; border: 1px solid var(--mantis-input-border) !important; }}
    .stMarkdown p, .stMarkdown li {{ font-family: 'Source Serif 4', serif; font-size: 1.02rem; line-height: 1.65; }}

    .mantis-muted {{ color: var(--mantis-muted); }}
    div[data-testid="stCaptionContainer"] {{ color: var(--mantis-muted); }}

    .mantis-header {{
        display:flex;
        align-items:center;
        justify-content: space-between;
        gap:14px;
        padding:18px 24px;
        border-radius:22px;
        background: var(--mantis-header-gradient);
        border: 1px solid var(--mantis-primary-border);
        margin-top: 18px;
        margin-bottom: 18px;
        box-shadow: var(--mantis-shadow-strong);
    }}
    .mantis-header-left {{
        display:flex;
        align-items:center;
        gap:14px;
    }}
    .mantis-header-right {{
        display:flex;
        gap:10px;
        align-items:center;
    }}
    .mantis-header-logo {{
        width:236px;
        height:82px;
        border-radius:16px;
        background: var(--mantis-header-logo-bg);
        background: linear-gradient(135deg, color-mix(in srgb, var(--mantis-header-logo-bg) 82%, transparent), transparent);
        border: 1px solid var(--mantis-primary-border);
        border: 1px solid color-mix(in srgb, var(--mantis-accent) 28%, transparent);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow:
            inset 0 0 0 1px rgba(0,0,0,0.04),
            0 8px 22px var(--mantis-accent-glow),
            0 8px 22px color-mix(in srgb, var(--mantis-accent-glow) 60%, transparent);
    }}
    .mantis-header-logo img {{
        width:100%;
        max-height:62px;
        object-fit:contain;
        padding:0;
        border-radius:0;
        filter: drop-shadow(0 0 10px color-mix(in srgb, var(--mantis-accent-glow) 75%, transparent));
    }}
    .mantis-header-title {{
        font-size:22px;
        font-weight:800;
        color: var(--mantis-text);
        letter-spacing: 0.01em;
    }}
    .mantis-header-sub {{
        color: var(--mantis-header-sub);
        font-size:12px;
    }}
    .mantis-header-meta {{
        display:flex;
        flex-direction:column;
        align-items:flex-end;
        gap:4px;
        font-size:12px;
        color: var(--mantis-muted);
    }}

    .stButton>button {{
        border-radius: 16px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.1rem !important;
        transition: all 0.15s ease-in-out;
        border: 1px solid var(--mantis-button-border) !important;
        background: var(--mantis-button-bg) !important;
        color: var(--mantis-text) !important;
    }}
    .stButton>button:hover {{
        transform: translateY(-1px);
        border-color: var(--mantis-button-hover-border) !important;
        box-shadow: var(--mantis-shadow-button);
    }}
    .stButton>button:active {{ transform: translateY(0); }}
    .stButton>button:focus:not(:focus-visible) {{ outline: none !important; box-shadow: none !important; }}
    .stButton>button:focus-visible {{ outline: 2px solid var(--mantis-accent) !important; outline-offset: 2px; }}

    /* --- BUTTON HIERARCHY --- */
    .stButton>button[kind="primary"] {{
        background: var(--mantis-primary-bg) !important;
        border-color: var(--mantis-primary-border) !important;
        box-shadow: var(--mantis-shadow-button);
        color: #ffffff !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        border-color: var(--mantis-primary-hover-border) !important;
        box-shadow: var(--mantis-shadow-strong);
    }}
    .stButton>button[kind="secondary"] {{
        background: var(--mantis-button-bg) !important;
    }}


    [data-testid="stVerticalBlock"] [data-testid="stContainer"] {{ border-radius: 16px !important; }}
    .stExpander {{ border: 1px solid var(--mantis-expander-border) !important; border-radius: 16px !important; }}
    hr {{ border-color: var(--mantis-divider) !important; }}
    section[data-testid="stSidebar"] {{ background: var(--mantis-sidebar-bg); border-right: 1px solid var(--mantis-sidebar-border); }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: var(--mantis-text); }}
    div[data-testid="stToast"] {{ border-radius: 14px !important; }}

    /* --- CARD POLISH --- */
    div[data-testid="stContainer"] {{
        background: var(--mantis-card-bg);
        border-radius: 20px !important;
        padding: 22px !important;
        border: 1px solid var(--mantis-card-border) !important;
        box-shadow: var(--mantis-shadow-strong);
        margin-bottom: 18px;
    }}
    .mantis-pill {{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:6px 10px;
        border-radius:999px;
        font-size:12px;
        background: var(--mantis-accent-soft);
        border: 1px solid var(--mantis-accent-glow);
        color: var(--mantis-text);
        letter-spacing: 0.02em;
    }}
    .mantis-hero-caption {{
        font-size:12px;
        color: var(--mantis-muted);
        margin-top:4px;
    }}
    div[data-testid="stContainer"] h3 {{
        margin-top: 0;
        margin-bottom: 12px;
        color: var(--mantis-text);
    }}
    .mantis-hero {{
        background: var(--mantis-surface);
        border-radius: 22px;
        padding: 22px 24px;
        border: 1px solid var(--mantis-card-border);
        box-shadow: var(--mantis-shadow-strong);
    }}
    .mantis-hero-title {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 6px;
    }}
    .mantis-hero-sub {{
        color: var(--mantis-muted);
        font-size: 14px;
    }}
    .mantis-page-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }}
    .mantis-page-title {{
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        color: var(--mantis-text);
    }}
    .mantis-page-sub {{
        color: var(--mantis-muted);
        margin-top: 4px;
        font-size: 14px;
    }}
    .mantis-tag {{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:6px 12px;
        border-radius:999px;
        font-size:12px;
        font-weight:600;
        background: var(--mantis-accent-soft);
        color: var(--mantis-text);
        border: 1px solid var(--mantis-accent-glow);
    }}
    .mantis-kpi-grid {{
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap:12px;
        margin-top: 14px;
    }}
    .mantis-kpi-card {{
        padding: 12px 14px;
        border-radius: 16px;
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-kpi-label {{
        font-size:11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mantis-muted);
        margin-bottom: 6px;
    }}
    .mantis-kpi-value {{
        font-size:20px;
        font-weight:700;
    }}
    .mantis-section-title {{
        font-size:20px;
        font-weight:700;
        margin-bottom: 6px;
    }}
    .mantis-section-header {{
        display:flex;
        align-items:flex-end;
        justify-content:space-between;
        gap:16px;
        margin: 6px 0 14px;
    }}
    .mantis-section-caption {{
        color: var(--mantis-muted);
        font-size: 13px;
    }}
    .mantis-soft {{
        background: var(--mantis-surface-alt);
        border-radius: 16px;
        padding: 14px;
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-stat-tile {{
        display:flex;
        flex-direction:column;
        gap:6px;
        padding: 12px 14px;
        border-radius: 16px;
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-stat-icon {{
        width: 30px;
        height: 30px;
        border-radius: 10px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: var(--mantis-accent-soft);
        border: 1px solid var(--mantis-accent-glow);
        font-size: 14px;
    }}
    .mantis-stat-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mantis-muted);
    }}
    .mantis-stat-value {{
        font-size: 20px;
        font-weight: 700;
        color: var(--mantis-text);
    }}
    .mantis-stat-help {{
        font-size: 12px;
        color: var(--mantis-muted);
    }}

    /* --- SIDEBAR POLISH --- */
    section[data-testid="stSidebar"] {{
        background: var(--mantis-sidebar-bg);
        border-right: 1px solid var(--mantis-sidebar-border);
    }}
    section[data-testid="stSidebar"] h3 {{
        color: var(--mantis-sidebar-title);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-size: 12px;
    }}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {{
        color: var(--mantis-text);
    }}


    /* --- SIDEBAR BRAND --- */
    .mantis-sidebar-brand{{
        display:flex;
        flex-direction: column;
        align-items:center;
        padding:14px 12px 10px;
        margin: 6px 8px 12px;
        border-radius: 16px;
        background: var(--mantis-sidebar-brand-bg);
        border: 1px solid var(--mantis-sidebar-brand-border);
        box-shadow: var(--mantis-shadow-button);
    }}
    .mantis-sidebar-brand--modern {{
        gap: 2px;
    }}
    .mantis-sidebar-logo {
        width: 100%;
        max-width: 148px;
        margin: 0 auto 6px;
        padding: 8px;
        border-radius: 14px;
        background: var(--mantis-sidebar-logo-bg);
        background: linear-gradient(145deg, color-mix(in srgb, var(--mantis-sidebar-logo-bg) 92%, transparent), transparent);
        border: 1px solid var(--mantis-sidebar-brand-border);
        border: 1px solid color-mix(in srgb, var(--mantis-accent) 20%, transparent);
    }
    .mantis-sidebar-logo img {
        width: 100%;
        display:block;
        object-fit: contain;
        filter: drop-shadow(0 0 8px color-mix(in srgb, var(--mantis-accent-glow) 80%, transparent));
    }

    .mantis-sidebar-brand--modern [data-testid="stImage"] {{
        width: 100%;
        margin: 2px 0 4px;
    }}
    .mantis-sidebar-brand--modern [data-testid="stImage"] img{{
        width: 100%;
        max-height: 72px;
        display:block;
        margin: 0 auto;
        object-fit: contain;
        filter: drop-shadow(0 0 8px rgba(34,197,94,0.26));
        transition: transform 180ms ease, filter 180ms ease;
    }}
    .mantis-sidebar-brand--modern [data-testid="stImage"] img:hover {{
        transform: scale(1.02);
        filter: drop-shadow(0 0 10px rgba(34,197,94,0.36));
    }}
    .mantis-avatar {{
        height:44px;
        width:44px;
        border-radius:50%;
        background: var(--mantis-surface-alt);
        color: var(--mantis-text);
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:700;
        font-size:0.9rem;
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-logo-fallback {{
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--mantis-sidebar-title);
    }}
    .mantis-sidebar-meta {{
        width: 100%;
        text-align: center;
        margin-top: 2px;
        margin-bottom: 6px;
    }}
    .mantis-sidebar-version{{
        font-size:11px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--mantis-muted);
        opacity: 0.9;
    }}
    .mantis-sidebar-divider {{
        width: 100%;
        height: 1px;
        margin-top: 2px;
        background: linear-gradient(90deg, rgba(34,197,94,0), rgba(34,197,94,0.35), rgba(34,197,94,0));
    }}
    @media (max-width: 1080px) {{
        .mantis-sidebar-brand--modern [data-testid="stImage"] img{{
            max-height: 64px;
        }}
    }}
    .mantis-banner img {{
        max-height: 180px;
        object-fit: contain;
    }}

    /* --- NAV RADIO STYLE --- */
    div[role="radiogroup"] > label {{
        background: var(--mantis-surface-alt);
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid var(--mantis-card-border);
        margin-bottom: 8px;
    }}
    div[role="radiogroup"] > label span {{
        color: var(--mantis-text);
    }}
    div[role="radiogroup"] > label:has(input:checked) {{
        border-color: var(--mantis-accent);
        box-shadow: 0 0 0 1px var(--mantis-accent-glow);
    }}
</style>
    """,
    )


def render_header(version: str, logo_b64: str) -> None:
    header_logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="MANTIS logo" />'
        if logo_b64
        else '<span class="mantis-logo-fallback">M</span>'
    )
    st.html(
        f"""
        <div class="mantis-header">
            <div class="mantis-header-left">
                <div class="mantis-header-logo">
                    {header_logo_html}
                </div>
                <div style="line-height:1.15;">
                    <div class="mantis-header-title">
                        MANTIS Studio  v{version}
                    </div>
                    <div class="mantis-header-sub">
                        Modular AI Narrative Text Intelligence System
                    </div>
                </div>
            </div>
            <div class="mantis-header-right">
                <span class="mantis-pill">Workspace</span>
            </div>
        </div>
        """,
    )


import datetime as _dt

_CURRENT_YEAR = _dt.datetime.now(_dt.timezone.utc).year


def _build_footer_nav_links() -> str:
    """Generate footer navigation ``<li>`` items from the centralized config.

    The links mirror the sidebar navigation defined in
    ``app/utils/navigation.py  NAV_SECTIONS``.  To add or remove a nav entry
    edit **only** that list  the footer updates automatically.
    """
    from app.utils.navigation import get_nav_sections

    lines = []
    for _, items in get_nav_sections():
        for label, page_key, icon in items:
            if page_key == "legal":
                continue
            lines.append(
                f'<li><a href="?page={page_key}">'
                f'<span class="mantis-footer-icon">{icon}</span> {label}</a></li>'
            )
    return "\n            ".join(lines)


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    nav_links_html = _build_footer_nav_links()
    brand_logo_src = ""
    try:
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        logo_path = (
            resolve_asset_path(assets_dir, "branding/mantis_footmark.png")
            or resolve_asset_path(assets_dir, "mantis_footmark.png")
            or resolve_asset_path(assets_dir, "branding/mantis_wordmark.png")
            or resolve_asset_path(assets_dir, "mantis_wordmark.png")
            or resolve_asset_path(assets_dir, "branding/mantis_lockup.png")
            or resolve_asset_path(assets_dir, "mantis_lockup.png")
            or resolve_asset_path(assets_dir, "mantis_banner_dark.png")
        )
        if logo_path and logo_path.exists():
            payload = base64.b64encode(logo_path.read_bytes()).decode("utf-8")
            brand_logo_src = f"data:image/png;base64,{payload}"
    except Exception:
        brand_logo_src = ""
    st.html(
        f"""
    <style>
    /*  Footer container  */
    .mantis-footer {{
        margin-top: 4rem;
        border-top: 1px solid var(--mantis-divider, #143023);
        background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
        padding: 2.5rem 1.5rem 0;
    }}

    /*  Back-to-top  */
    .mantis-footer-top {{
        display: flex;
        justify-content: flex-end;
        max-width: 960px;
        margin: 0 auto 1.5rem;
    }}
    .mantis-footer-top a {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--mantis-muted, #9CA3AF);
        text-decoration: none;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        border: 1px solid var(--mantis-divider, #143023);
        transition: color 0.15s, border-color 0.15s;
    }}
    .mantis-footer-top a:hover {{
        color: var(--mantis-accent, #22c55e);
        border-color: var(--mantis-accent, #22c55e);
    }}
    .mantis-footer-top a:focus-visible {{
        outline: 2px solid var(--mantis-accent, #22c55e);
        outline-offset: 2px;
        border-radius: 999px;
    }}

    /*  Grid  */
    .mantis-footer-grid {{
        display: grid;
        grid-template-columns: 1.6fr 1fr 1fr 1fr;
        gap: 2.5rem;
        max-width: 960px;
        margin: 0 auto;
    }}

    /*  Section headings  */
    .mantis-footer-section h4 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--mantis-accent, #22c55e);
        margin: 0 0 0.85rem;
        padding-bottom: 0.45rem;
        border-bottom: 1px solid var(--mantis-divider, #143023);
    }}

    /*  Lists  */
    .mantis-footer-section ul {{
        list-style: none;
        margin: 0;
        padding: 0;
    }}
    .mantis-footer-section li {{
        margin-bottom: 0.45rem;
    }}

    /*  Links  */
    .mantis-footer-section a {{
        color: var(--mantis-text, #ecfdf5);
        text-decoration: none;
        font-size: 0.85rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.15rem 0;
        border-bottom: 1px solid transparent;
        transition: color 0.15s, border-color 0.15s;
    }}
    .mantis-footer-section a:hover {{
        color: var(--mantis-accent, #22c55e);
        border-bottom-color: var(--mantis-accent, #22c55e);
    }}
    .mantis-footer-section a:focus-visible {{
        outline: 2px solid var(--mantis-accent, #22c55e);
        outline-offset: 2px;
        border-radius: 2px;
    }}
    .mantis-footer-section a .mantis-footer-icon {{
        font-size: 0.9rem;
        line-height: 1;
        flex-shrink: 0;
    }}
    .mantis-footer-section a .mantis-footer-ext {{
        font-size: 0.7rem;
        opacity: 0.55;
    }}

    /*  Brand  */
    .mantis-footer-brand {{
        font-size: 0.85rem;
        color: var(--mantis-muted, #9CA3AF);
        line-height: 1.7;
    }}
    .mantis-footer-brand strong {{
        color: var(--mantis-text, #ecfdf5);
        font-family: 'Space Grotesk', sans-serif;
        font-size: 1rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }}
    .mantis-footer-brand .mantis-footer-tagline {{
        display: block;
        margin-top: 0.15rem;
        font-size: 0.8rem;
        color: var(--mantis-muted, #9CA3AF);
    }}
    .mantis-footer-brand .mantis-footer-logo {{
        display: block;
        width: min(210px, 100%);
        height: auto;
        margin: 0 0 0.7rem;
        opacity: 0.95;
        filter: drop-shadow(0 8px 16px rgba(0,0,0,0.32));
    }}

    /*  Bottom bar  */
    .mantis-footer-bottom {{
        max-width: 960px;
        margin: 2rem auto 0;
        padding: 1rem 0;
        border-top: 1px solid var(--mantis-divider, #143023);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.75rem;
        color: var(--mantis-muted, #9CA3AF);
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    .mantis-footer-bottom a {{
        color: var(--mantis-muted, #9CA3AF);
        text-decoration: none;
        transition: color 0.15s;
    }}
    .mantis-footer-bottom a:hover {{
        color: var(--mantis-accent, #22c55e);
    }}
    .mantis-footer-bottom a:focus-visible {{
        outline: 2px solid var(--mantis-accent, #22c55e);
        outline-offset: 2px;
        border-radius: 2px;
    }}

    /*  Responsive  */
    @media (max-width: 768px) {{
        .mantis-footer {{ padding: 2rem 1rem 0; }}
        .mantis-footer-grid {{
            grid-template-columns: 1fr 1fr;
            gap: 1.75rem;
        }}
    }}
    @media (max-width: 480px) {{
        .mantis-footer-grid {{
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }}
        .mantis-footer-bottom {{
            flex-direction: column;
            text-align: center;
        }}
    }}
    </style>
    <footer class="mantis-footer" role="contentinfo" aria-label="Site footer">
      <div class="mantis-footer-top">
        <a href="#" class="mantis-back-to-top" aria-label="Back to top">&uarr; Back to top</a>
      </div>
      <div class="mantis-footer-grid">
        <div class="mantis-footer-section mantis-footer-brand">
          {"<img class='mantis-footer-logo' src='" + brand_logo_src + "' alt='MANTIS Studio' />" if brand_logo_src else ""}
          <strong>MANTIS Studio</strong>
          <span class="mantis-footer-tagline">Modular AI Narrative Text Intelligence System</span>
        </div>
        <nav class="mantis-footer-section" aria-label="Navigation">
          <h4>Navigation</h4>
          <ul>
            {nav_links_html}
          </ul>
        </nav>
        <nav class="mantis-footer-section" aria-label="All Policies">
          <h4>All Policies</h4>
          <ul>
            <li><a href="?page=terms">Terms of Service</a></li>
            <li><a href="?page=privacy">Privacy Policy</a></li>
            <li><a href="?page=legal">All Policies</a></li>
          </ul>
        </nav>
        <nav class="mantis-footer-section" aria-label="Support">
          <h4>Support</h4>
          <ul>
            <li><a href="?page=help"><span class="mantis-footer-icon">&#9432;</span> Help</a></li>
            <li><a href="{support_url}" target="_blank" rel="noopener noreferrer">Report an Issue <span class="mantis-footer-ext">&#8599;</span></a></li>
            <li><a href="mailto:{contact_email}"><span class="mantis-footer-icon">&#9993;</span> Contact</a></li>
          </ul>
        </nav>
      </div>
      <div class="mantis-footer-bottom">
        <span>&copy; {_CURRENT_YEAR} MANTIS Studio &middot; v{version}</span>
        <span>
          <a href="{support_url}" target="_blank" rel="noopener noreferrer" aria-label="MANTIS Studio on GitHub">GitHub</a>
        </span>
      </div>
    </footer>
    """,
    )
    components.html(
        """
        <script>
          (function() {
            function scrollToTop(doc, win) {
              const targets = [
                doc.querySelector('section.main'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.documentElement,
                doc.body,
              ].filter(Boolean);
              targets.forEach((el) => {
                try {
                  if (typeof el.scrollTo === 'function') {
                    el.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                  el.scrollTop = 0;
                } catch (_) {}
              });
              try { win.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) {}
              try { win.scrollTo(0, 0); } catch (_) {}
            }
            const topWin = window.parent || window;
            const topDoc = topWin.document || document;
            const links = topDoc.querySelectorAll('.mantis-back-to-top');
            links.forEach((link) => {
              if (link.dataset.boundTop === '1') return;
              link.dataset.boundTop = '1';
              link.addEventListener('click', function(ev) {
                ev.preventDefault();
                scrollToTop(topDoc, topWin);
              });
            });
          })();
        </script>
        """,
        height=0,
    )

