"""Enterprise top navigation bar for MANTIS Studio."""

from __future__ import annotations

from typing import Dict

import streamlit as st

_PAGE_LABELS: Dict[str, str] = {
    "home": "Dashboard",
    "projects": "Projects",
    "outline": "Modules",
    "chapters": "Modules",
    "world": "Intelligence",
    "export": "Exports",
    "ai": "Settings",
    "legal": "Settings",
    "terms": "Settings",
    "privacy": "Settings",
}


def current_module_label(page: str) -> str:
    return _PAGE_LABELS.get(page or "home", "Dashboard")


def render_top_navbar(version: str, ai_ready: bool, is_processing: bool = False) -> None:
    module = current_module_label(st.session_state.get("page", "home"))
    status_label = "Processing" if is_processing else ("AI Ready" if ai_ready else "Limited")
    status_class = "processing" if is_processing else ("ready" if ai_ready else "limited")

    cols = st.columns([2.2, 2.4, 1.2, 0.7])
    with cols[0]:
        st.html(
            f"""
            <div class="mantis-topnav-brand">
                <div class="mantis-topnav-title">MANTIS</div>
                <div class="mantis-topnav-sub">{module} · v{version}</div>
            </div>
            """
        )
    with cols[1]:
        st.html(
            '<div style="height:38px;border:1px solid var(--mantis-card-border);border-radius:10px;display:flex;align-items:center;padding:0 12px;color:var(--mantis-muted);background:#0f141d;">🔎 Search projects, chapters, entities...</div>'
        )
    with cols[2]:
        st.html(f'<div class="mantis-status-badge {status_class}"><span class="dot"></span>{status_label}</div>')
    with cols[3]:
        st.html('<div class="mantis-avatar">U</div>')
