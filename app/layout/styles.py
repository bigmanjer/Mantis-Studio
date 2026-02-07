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
            "bg": "#f8fafc",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)",
            "text": "#0f172a",
            "muted": "#6b7280",
            "input_bg": "#ffffff",
            "input_border": "#cce5d6",
            "button_bg": "linear-gradient(180deg, #ffffff, #ecfdf3)",
            "button_border": "#cdebd9",
            "button_hover_border": "#22c55e",
            "primary_bg": "linear-gradient(135deg, #34d399, #22c55e)",
            "primary_border": "rgba(34,197,94,0.25)",
            "primary_hover_border": "#16a34a",
            "card_bg": "#ffffff",
            "card_border": "#e1efe6",
            "sidebar_bg": "linear-gradient(180deg, #f3f4f6, #e5e7eb)",
            "sidebar_border": "#d1d5db",
            "sidebar_title": "#166534",
            "divider": "#deeee3",
            "expander_border": "#d7e9df",
            "header_gradient": "linear-gradient(135deg, #e6f9ef, #c7f4dc)",
            "header_logo_bg": "#e7fdf1",
            "header_sub": "#2f6f43",
            "shadow_strong": "0 12px 24px rgba(12,26,18,0.08)",
            "shadow_button": "0 8px 16px rgba(12,26,18,0.12)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(255,255,255,0.9), rgba(243,244,246,0.95))",
            "sidebar_brand_border": "rgba(15,23,42,0.08)",
            "sidebar_logo_bg": "rgba(15,23,42,0.08)",
            "accent": "#22c55e",
            "accent_soft": "rgba(34,197,94,0.18)",
            "accent_glow": "rgba(34,197,94,0.35)",
            "surface": "rgba(255,255,255,0.9)",
            "surface_alt": "rgba(241,245,249,0.95)",
            "success": "#16a34a",
            "warning": "#d97706",
        },
    }


def apply_theme(tokens: Dict[str, str]) -> None:
    st.markdown(
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
        background: rgba(0,0,0,0.35);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.15),
            0 0 18px rgba(34,197,94,0.45);
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
    .stButton>button:focus {{ outline: none !important; box-shadow: none !important; }}

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
        unsafe_allow_html=True,
    )


def render_header(version: str, logo_b64: str) -> None:
    header_logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="MANTIS logo" />'
        if logo_b64
        else '<span class="mantis-logo-fallback">M</span>'
    )
    st.markdown(
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
                        Modular narrative workspace
                    </div>
                </div>
            </div>
            <div class="mantis-header-right">
                <span class="mantis-pill">Workspace</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    st.markdown(
        f"""
    <style>
    .mantis-footer {{
        margin-top: 3rem;
        border-top: 1px solid var(--mantis-divider, #143023);
        padding: 2rem 1rem 1.5rem;
    }}
    .mantis-footer-grid {{
        display: grid;
        grid-template-columns: 1.5fr 1fr 1fr 1fr;
        gap: 2rem;
        max-width: 960px;
        margin: 0 auto;
    }}
    .mantis-footer-section h4 {{
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mantis-muted, #9CA3AF);
        margin: 0 0 0.75rem;
    }}
    .mantis-footer-section ul {{
        list-style: none;
        margin: 0;
        padding: 0;
    }}
    .mantis-footer-section li {{
        margin-bottom: 0.4rem;
    }}
    .mantis-footer-section a {{
        color: var(--mantis-text, #ecfdf5);
        text-decoration: none;
        font-size: 0.85rem;
        transition: color 0.15s;
    }}
    .mantis-footer-section a:hover {{
        color: var(--mantis-accent, #22c55e);
    }}
    .mantis-footer-section a:focus-visible {{
        outline: 2px solid var(--mantis-accent, #22c55e);
        outline-offset: 2px;
        border-radius: 2px;
    }}
    .mantis-footer-brand {{
        font-size: 0.85rem;
        color: var(--mantis-muted, #9CA3AF);
        line-height: 1.6;
    }}
    .mantis-footer-brand strong {{
        color: var(--mantis-text, #ecfdf5);
        font-size: 0.95rem;
    }}
    @media (max-width: 640px) {{
        .mantis-footer-grid {{
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}
    }}
    @media (max-width: 400px) {{
        .mantis-footer-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    <footer class="mantis-footer" role="contentinfo" aria-label="Site footer">
      <div class="mantis-footer-grid">
        <div class="mantis-footer-section mantis-footer-brand">
          <strong>MANTIS Studio</strong><br>
          Modular narrative workspace<br>
          <small>&copy; 2024 MANTIS Studio &middot; v{version}</small>
        </div>
        <nav class="mantis-footer-section" aria-label="Navigation">
          <h4>Navigation</h4>
          <ul>
            <li><a href="?page=home">Dashboard</a></li>
            <li><a href="?page=projects">Projects</a></li>
            <li><a href="?page=outline">Outline</a></li>
            <li><a href="?page=export">Export</a></li>
          </ul>
        </nav>
        <nav class="mantis-footer-section" aria-label="Legal Center">
          <h4>Legal Center</h4>
          <ul>
            <li><a href="?page=terms">Terms of Service</a></li>
            <li><a href="?page=privacy">Privacy Policy</a></li>
            <li><a href="?page=legal">All Policies</a></li>
          </ul>
        </nav>
        <nav class="mantis-footer-section" aria-label="Support">
          <h4>Support</h4>
          <ul>
            <li><a href="?page=help">Help</a></li>
            <li><a href="{support_url}" target="_blank" rel="noopener noreferrer">Report an Issue</a></li>
            <li><a href="mailto:{contact_email}">Contact</a></li>
          </ul>
        </nav>
      </div>
    </footer>
    """,
        unsafe_allow_html=True,
    )
