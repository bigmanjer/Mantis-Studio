"""Main-app theme token bridge styles.

This module centralizes the token alias and shell layout CSS previously
injected inline from ``app/main.py``.
"""

from __future__ import annotations

import streamlit as st


def inject_main_theme_tokens() -> None:
    """Inject token aliases and app-shell layout CSS used by main.py."""
    st.html(
        """
        <style>
        :root {
            --mantis-bg-primary: var(--mantis-bg);
            --mantis-bg-secondary: var(--mantis-surface);
            --mantis-accent-enterprise: #23f7c0;
            --mantis-accent-teal: #4be5ff;
            --mantis-success: var(--mantis-success, #28f29c);
            --mantis-warning: var(--mantis-warning, #ffb347);
            --mantis-danger: var(--mantis-danger, #ff6b6b);
        }
        [data-testid="stAppViewContainer"] { background: var(--mantis-bg-primary); }
        :root { --mantis-top-offset: 0.9rem; }
        section.main { padding-top: var(--mantis-top-offset) !important; overflow: visible !important; }
        div[data-testid="stAppViewContainer"] { overflow: visible !important; }
        div[data-testid="stAppViewContainer"] > .main { overflow: visible !important; }
        div[data-testid="stMainBlockContainer"] { padding-top: 0.2rem !important; }
        .stApp { overflow: visible !important; }
        .block-container { max-width: 1440px; padding-top: 0.55rem !important; overflow: visible !important; }
        .block-container > div:first-child { margin-top: 0 !important; }
        .block-container > div[data-testid="stVerticalBlock"]:first-child { margin-top: 0.65rem !important; }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 0 !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
            padding-bottom: 0.6rem !important;
        }
        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
            padding-top: 0 !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 0 !important;
        }
        /* Prevent first-page headings from clipping under the top bar */
        h1, h2, h3,
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
            line-height: 1.25 !important;
            padding-top: 0.12em !important;
            overflow: visible !important;
        }
        .block-container > div:first-child h1,
        .block-container > div:first-child h2,
        .block-container > div:first-child h3 {
            margin-top: 0.25rem !important;
        }
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"],
        div[data-testid="stStatusWidget"] {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
        }
        button[data-testid="collapsedControl"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        /* Hide Streamlit's sidebar top collapse chevron (<<) */
        section[data-testid="stSidebar"] button[data-testid="stBaseButton-headerNoPadding"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }
        section[data-testid="stSidebar"] {
            transform: translateX(0) !important;
            margin-left: 0 !important;
            min-width: 280px !important;
        }
        .mantis-topnav-brand { display:flex; flex-direction:column; justify-content:center; }
        .mantis-topnav-title { font-size:1.1rem; letter-spacing:0.08em; font-weight:800; }
        .mantis-topnav-sub { font-size:0.78rem; color:var(--mantis-muted); }
        .mantis-status-badge { margin-top:2px; display:inline-flex; gap:8px; align-items:center; padding:8px 12px; border-radius:999px; font-size:0.8rem; border:1px solid var(--mantis-card-border); }
        .mantis-status-badge .dot { width:8px; height:8px; border-radius:50%; display:inline-block; }
        .mantis-status-badge.ready .dot { background: var(--mantis-success); box-shadow: 0 0 12px var(--mantis-success); }
        .mantis-status-badge.processing .dot { background: var(--mantis-warning); animation: mantisPulse 1.2s infinite; }
        .mantis-status-badge.limited .dot { background: var(--mantis-danger); }
        .mantis-enterprise-hero { display:flex; justify-content:space-between; align-items:flex-start; gap:20px; padding: 20px 22px; border-radius:16px; background: var(--mantis-surface); border:1px solid var(--mantis-card-border); }
        .mantis-enterprise-hero h1 { margin:0; font-size:2rem; letter-spacing:-0.02em; }
        .mantis-enterprise-hero p { margin:6px 0 0 0; color:var(--mantis-muted); }
        .mantis-status-pill { border:1px solid var(--mantis-primary-border); background:var(--mantis-accent-soft); color:var(--mantis-text); border-radius:999px; padding:8px 12px; font-size:0.82rem; display:inline-flex; align-items:center; gap:8px; }
        .mantis-status-pill span { width:8px; height:8px; border-radius:50%; background:var(--mantis-success); box-shadow:0 0 10px var(--mantis-success); }
        .mantis-metric-card { border-radius:14px; padding:16px; border:1px solid var(--mantis-card-border); background:var(--mantis-bg-secondary); min-height:104px; transition:transform .16s ease, border-color .16s ease; }
        .mantis-metric-card:hover { transform: translateY(-2px); border-color: var(--mantis-accent-teal); }
        .mantis-metric-label { font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--mantis-muted); }
        .mantis-metric-value { margin-top:8px; font-size:1.6rem; font-weight:750; }
        .mantis-activity-item { display:grid; grid-template-columns: 120px 120px 1fr; gap:12px; padding:10px 0; border-bottom:1px solid var(--mantis-card-border); }
        .mantis-activity-time { color:var(--mantis-muted); font-size:0.78rem; }
        .mantis-activity-status { font-size:0.78rem; color:var(--mantis-text); }
        .mantis-activity-text { font-size:0.9rem; }
        .mantis-project-chip { border:1px solid var(--mantis-card-border); border-radius:12px; padding:10px 12px; background:var(--mantis-surface-alt); }
        .mantis-project-chip__title { font-size:0.88rem; font-weight:650; }
        .mantis-project-chip__meta { font-size:0.74rem; color:var(--mantis-muted); margin-top:4px; }
        @keyframes mantisPulse { 0%{opacity:1;} 50%{opacity:.3;} 100%{opacity:1;} }
        </style>
        """
    )


__all__ = ["inject_main_theme_tokens"]
