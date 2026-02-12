from __future__ import annotations

from typing import Dict

import streamlit as st


def get_theme_tokens(theme: str) -> Dict[str, Dict[str, str]]:
    return {
        "Dark": {
            "bg": "#020617",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)",
            "text": "#ecfdf5",
            "muted": "#b6c3d1",
            "input_bg": "#0b1216",
            "input_border": "#166534",
            "button_bg": "linear-gradient(180deg, #0f1a15, #0b1411)",
            "button_border": "#163f2a",
            "button_hover_border": "#22c55e",
            "primary_bg": "linear-gradient(135deg, #15803d, #22c55e)",
            "primary_border": "rgba(34,197,94,0.55)",
            "primary_hover_border": "#4ade80",
            "card_bg": "linear-gradient(180deg, rgba(6,18,14,0.95), rgba(4,12,10,0.95))",
            "card_border": "#163523",
            "sidebar_bg": "linear-gradient(180deg, #020617, #07150f)",
            "sidebar_border": "#123123",
            "sidebar_title": "#7dd3a7",
            "divider": "#143023",
            "expander_border": "#1f3b2d",
            "header_gradient": "linear-gradient(135deg, #0b1216, #0f1a15)",
            "header_logo_bg": "rgba(34,197,94,0.2)",
            "header_sub": "#c7f2da",
            "shadow_strong": "0 18px 40px rgba(0,0,0,0.55)",
            "shadow_button": "0 10px 22px rgba(0,0,0,0.4)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(6,18,14,0.85), rgba(4,10,8,0.95))",
            "sidebar_brand_border": "rgba(34,197,94,0.25)",
            "sidebar_logo_bg": "rgba(34,197,94,0.12)",
            "accent": "#22c55e",
            "accent_soft": "rgba(34,197,94,0.18)",
            "accent_glow": "rgba(34,197,94,0.35)",
            "surface": "rgba(6,18,14,0.85)",
            "surface_alt": "rgba(5,14,11,0.9)",
            "success": "#22c55e",
            "warning": "#f59e0b",
        },
        "Light": {
            "bg": "#f4f6f5",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.08), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.06), transparent 40%)",
            "text": "#1a2e23",
            "muted": "#3d4f47",
            "input_bg": "#fafbfa",
            "input_border": "#6a8a7b",
            "button_bg": "linear-gradient(180deg, #fafbfa, #f0f5f2)",
            "button_border": "#6a8a7b",
            "button_hover_border": "#16a34a",
            "primary_bg": "linear-gradient(135deg, #16a34a, #15803d)",
            "primary_border": "rgba(22,163,74,0.5)",
            "primary_hover_border": "#15803d",
            "card_bg": "#fafbfa",
            "card_border": "#708a7e",
            "sidebar_bg": "linear-gradient(180deg, #eef1ef, #e4e9e6)",
            "sidebar_border": "#708378",
            "sidebar_title": "#15803d",
            "divider": "#7a8e82",
            "expander_border": "#708a7e",
            "header_gradient": "linear-gradient(135deg, #e2f3e8, #d0eddb)",
            "header_logo_bg": "#ddf0e4",
            "header_sub": "#276740",
            "shadow_strong": "0 12px 24px rgba(20,40,30,0.12)",
            "shadow_button": "0 6px 14px rgba(20,40,30,0.10)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(250,251,250,0.95), rgba(243,247,245,0.95))",
            "sidebar_brand_border": "rgba(20,40,30,0.18)",
            "sidebar_logo_bg": "rgba(22,163,74,0.10)",
            "accent": "#16a34a",
            "accent_soft": "rgba(22,163,74,0.12)",
            "accent_glow": "rgba(22,163,74,0.30)",
            "surface": "rgba(250,251,250,0.95)",
            "surface_alt": "rgba(243,247,245,0.95)",
            "success": "#15803d",
            "warning": "#b45309",
        },
    }


def apply_theme(tokens: Dict[str, str]) -> None:
    st.html(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap');
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
        font-family: 'Inter', sans-serif;
    }}
    .block-container {{ padding-top: 2.6rem; padding-bottom: 2.6rem; max-width: 1380px; }}
    header[data-testid="stHeader"] {{ height: 2.6rem; }}
    h1, h2, h3 {{ letter-spacing: -0.02em; font-family: 'Space Grotesk', sans-serif; }}
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown div,
    .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label,
    .stNumberInput label, .stTextArea label {{
        color: var(--mantis-text) !important;
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
    .stTextArea textarea {{ background-color: var(--mantis-input-bg) !important; color: var(--mantis-text) !important; font-family: 'Crimson Pro', serif !important; font-size: 18px !important; line-height: 1.65 !important; border: 1px solid var(--mantis-input-border) !important; }}

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
        width:88px;
        height:88px;
        border-radius:18px;
        background: var(--mantis-header-logo-bg);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow:
            inset 0 0 0 1px rgba(0,0,0,0.06),
            0 0 18px var(--mantis-accent-glow);
    }}
    .mantis-header-logo img {{
        height:60px;
        width:auto;
        padding:0;
        border-radius:0;
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
        gap:12px;
        align-items:center;
        padding:14px 12px 12px 12px;
        margin: 4px 8px 10px 8px;
        border-radius: 16px;
        background: var(--mantis-sidebar-brand-bg);
        border: 1px solid var(--mantis-sidebar-brand-border);
        box-shadow: var(--mantis-shadow-button);
    }}
    .mantis-sidebar-logo{{
        width:70px;
        height:70px;
        border-radius: 14px;
        background: var(--mantis-sidebar-logo-bg);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05), 0 6px 16px rgba(0,0,0,0.2);
        flex: 0 0 auto;
    }}
    .mantis-sidebar-logo img{{
        height:48px;
        width:auto;
        display:block;
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
    .mantis-sidebar-title{{
        font-weight:800;
        font-size:14px;
        color: var(--mantis-text);
        line-height:1.1;
    }}
    .mantis-sidebar-sub{{
        font-size:12px;
        color: var(--mantis-muted);
        margin-top:2px;
        line-height:1.1;
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
                        MANTIS Studio — v{version}
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
    ``app/utils/navigation.py → NAV_ITEMS``.  To add or remove a nav entry
    edit **only** that list — the footer updates automatically.
    """
    from app.utils.navigation import get_nav_items

    lines = []
    for label, page_key, icon in get_nav_items():
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
    st.html(
        f"""
    <style>
    /* ── Footer container ── */
    .mantis-footer {{
        margin-top: 4rem;
        border-top: 1px solid var(--mantis-divider, #143023);
        background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
        padding: 2.5rem 1.5rem 0;
    }}

    /* ── Back-to-top ── */
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

    /* ── Grid ── */
    .mantis-footer-grid {{
        display: grid;
        grid-template-columns: 1.6fr 1fr 1fr 1fr;
        gap: 2.5rem;
        max-width: 960px;
        margin: 0 auto;
    }}

    /* ── Section headings ── */
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

    /* ── Lists ── */
    .mantis-footer-section ul {{
        list-style: none;
        margin: 0;
        padding: 0;
    }}
    .mantis-footer-section li {{
        margin-bottom: 0.45rem;
    }}

    /* ── Links ── */
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

    /* ── Brand ── */
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

    /* ── Bottom bar ── */
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

    /* ── Responsive ── */
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
        <a href="#" onclick="var el=window.parent.document.querySelector('section.main');if(el)el.scrollTo({{top:0,behavior:'smooth'}});else window.parent.scrollTo({{top:0,behavior:'smooth'}});return false;" aria-label="Back to top">&uarr; Back to top</a>
      </div>
      <div class="mantis-footer-grid">
        <div class="mantis-footer-section mantis-footer-brand">
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
