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


def render_metric_card(label: str, value: str) -> None:
    """Render a metric card with consistent styling for the dashboard.
    
    This is a semantic alias for render_metric() that provides clearer intent
    when used in dashboard contexts. The function name explicitly indicates
    it renders a "card" component, improving code readability.
    
    Args:
        label: The metric label (e.g., "Total Projects")
        value: The metric value (e.g., "5")
    """
    render_metric(label, value)


def render_empty_state(icon: str, title: str, message: str) -> None:
    """Render an empty state with icon and message.
    
    Args:
        icon: Emoji icon
        title: Empty state title
        message: Descriptive message
    """
    st.html(
        f"""
        <div class="mantis-empty-state">
            <div class="mantis-empty-state-icon">{icon}</div>
            <div class="mantis-empty-state-title">{title}</div>
            <div class="mantis-empty-state-message">{message}</div>
        </div>
        """
    )
