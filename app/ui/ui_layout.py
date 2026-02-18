from __future__ import annotations

from collections.abc import Callable
from typing import Optional

import streamlit as st


def render_section_header(title: str, subtitle: Optional[str] = None) -> None:
    subtitle_html = f"<div class='mantis-section-caption'>{subtitle}</div>" if subtitle else ""
    st.html(
        f"""
        <div class="mantis-section-header">
            <div>
                <div class="mantis-section-title">{title}</div>
                {subtitle_html}
            </div>
        </div>
        """,
    )


def render_metric(label: str, value: str) -> None:
    st.html(
        f"""
        <div class="mantis-kpi-card">
            <div class="mantis-kpi-label">{label}</div>
            <div class="mantis-kpi-value">{value}</div>
        </div>
        """,
    )


def render_card(title: str, content: Callable[[], None], subtitle: Optional[str] = None) -> None:
    with st.container(border=True):
        st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
        content()
