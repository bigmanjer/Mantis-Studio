"""Dashboard-specific UI components for MANTIS Studio enterprise console."""
from __future__ import annotations

from collections.abc import Callable
from typing import Optional

import streamlit as st
import uuid

SPACING_UNIT = 8


def spacing(multiplier: int) -> str:
    return f"{SPACING_UNIT * multiplier}px"


def render_hero_header(
    *,
    status_label: str = "AI Ready",
    status_caption: str = "System healthy",
    primary_action: Optional[Callable[[], None]] = None,
    secondary_action: Optional[Callable[[], None]] = None,
    tertiary_action: Optional[Callable[[], None]] = None,
    key_prefix: str = "home",
) -> None:
    st.html(
        """
        <div class="mantis-enterprise-hero">
            <div>
                <h1>MANTIS Control Center</h1>
                <p>Enterprise narrative intelligence platform for teams, creators, and operators.</p>
            </div>
            <div class="mantis-status-pill"><span></span>"""
        + status_label
        + """</div>
        </div>
        """
    )
    if status_caption:
        st.caption(status_caption)

    action_cols = st.columns(4)
    instance = uuid.uuid4().hex
    actions = [
        ("✨ New Project", "new_project", primary_action, "primary"),
        ("📝 Continue Writing", "continue", secondary_action, "secondary"),
        ("🧠 Analyze Text", "analyze", tertiary_action, "secondary"),
        ("⬇️ Export", "export", None, "secondary"),
    ]
    for idx, (label, slug, callback, btn_type) in enumerate(actions):
        with action_cols[idx]:
            if st.button(
                label,
                key=f"{key_prefix}_hero_{slug}_{instance}",
                use_container_width=True,
                type=btn_type,
            ):
                if callback:
                    callback()


def render_metrics_row(metrics: list[tuple[str, str]]) -> None:
    cols = st.columns(len(metrics))
    for idx, (label, value) in enumerate(metrics):
        with cols[idx]:
            st.html(
                f"""
                <div class="mantis-metric-card">
                    <div class="mantis-metric-label">{label}</div>
                    <div class="mantis-metric-value">{value}</div>
                </div>
                """
            )


def render_workspace_hub_section(title: str, content_fn: Callable[[], None]) -> None:
    with st.container(border=True):
        st.markdown(f"### {title}")
        content_fn()


def render_feature_group(
    group_name: str,
    features: list[tuple[str, str, Callable[[], None]]],
    expanded: bool = False,
    key_prefix: str = "",
) -> None:
    with st.expander(group_name, expanded=expanded):
        for idx, (feature_name, feature_desc, action) in enumerate(features):
            feature_cols = st.columns([3, 1])
            with feature_cols[0]:
                st.markdown(f"**{feature_name}**")
                st.caption(feature_desc)
            with feature_cols[1]:
                if st.button("Open", key=f"{key_prefix}_{group_name}_{idx}", use_container_width=True):
                    with st.spinner(f"Loading {feature_name.lower()}..."):
                        action()


def render_dashboard_section_header(title: str, description: Optional[str] = None) -> None:
    st.html(
        f"""
        <div style="margin-top:{spacing(3)};margin-bottom:{spacing(2)};">
            <h2 style="margin:0;">{title}</h2>
            <p style="margin:4px 0 0 0;color:var(--mantis-muted);">{description or ''}</p>
        </div>
        """
    )


def render_activity_feed(events: list[tuple[str, str, str]]) -> None:
    st.markdown("### Activity & Intelligence Feed")
    if not events:
        st.caption("No recent activity yet.")
        return
    for ts, status, message in events:
        st.html(
            f"""
            <div class="mantis-activity-item">
                <div class="mantis-activity-time">{ts}</div>
                <div class="mantis-activity-status">{status}</div>
                <div class="mantis-activity-text">{message}</div>
            </div>
            """
        )


def add_vertical_space(multiplier: int = 2) -> None:
    st.html(f"<div style='height: {spacing(multiplier)};'></div>")


def add_divider_with_spacing(top: int = 3, bottom: int = 3) -> None:
    add_vertical_space(top)
    st.divider()
    add_vertical_space(bottom)
