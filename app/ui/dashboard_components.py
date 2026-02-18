"""Dashboard-specific UI components for MANTIS Studio Command Center.

This module provides reusable components for the dashboard redesign,
implementing a consistent design system with proper spacing and hierarchy.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Optional

import streamlit as st


# =============================================================================
# DESIGN SYSTEM CONSTANTS
# =============================================================================

SPACING_UNIT = 8  # Base spacing unit in pixels (8px system)


def spacing(multiplier: int) -> str:
    """Generate spacing value based on 8px system."""
    return f"{SPACING_UNIT * multiplier}px"


# =============================================================================
# HERO HEADER COMPONENT
# =============================================================================

def render_hero_header(
    *,
    status_label: str = "🟢 Operational",
    status_caption: str = "",
    primary_action: Optional[Callable[[], None]] = None,
    secondary_action: Optional[Callable[[], None]] = None,
    tertiary_action: Optional[Callable[[], None]] = None,
) -> None:
    """Render the hero header section at the top of the dashboard.
    
    This creates a visually distinct top section with:
    - Large MANTIS title
    - Subtitle
    - System status indicator
    - 3 Primary action buttons
    
    Args:
        status_label: Status indicator text (default: "🟢 Operational")
        status_caption: Additional status caption
        primary_action: Callback for "New Project" button
        secondary_action: Callback for "Open Workspace" button
        tertiary_action: Callback for "Run Analysis" button
    """
    with st.container(border=True):
        # Title and subtitle
        st.html(
            f"""
            <div style="margin-bottom: {spacing(2)};">
                <h1 style="margin: 0 0 {spacing(1)} 0; font-size: 44px; font-weight: 700; letter-spacing: -0.03em;">
                    MANTIS
                </h1>
                <div style="font-size: 18px; color: var(--mantis-muted); font-weight: 500;">
                    Modular AI Narrative Text Intelligence System
                </div>
            </div>
            """
        )
        
        # Status row
        status_cols = st.columns([1, 1])
        with status_cols[0]:
            st.markdown(f"**{status_label}**")
        with status_cols[1]:
            if status_caption:
                st.caption(status_caption)
        
        st.html(f"<div style='height: {spacing(2)};'></div>")
        
        # Action buttons
        action_cols = st.columns(3)
        with action_cols[0]:
            if st.button(
                "🚀 New Project",
                type="primary",
                use_container_width=True,
                key="hero_new_project",
            ):
                if primary_action:
                    primary_action()
        
        with action_cols[1]:
            if st.button(
                "📂 Open Workspace",
                use_container_width=True,
                key="hero_open_workspace",
            ):
                if secondary_action:
                    secondary_action()
        
        with action_cols[2]:
            if st.button(
                "🔍 Run Analysis",
                use_container_width=True,
                key="hero_run_analysis",
            ):
                if tertiary_action:
                    tertiary_action()


# =============================================================================
# METRICS COMPONENT
# =============================================================================

def render_metrics_row(metrics: list[tuple[str, str]]) -> None:
    """Render a row of metric cards with consistent styling.
    
    Args:
        metrics: List of (label, value) tuples for each metric card
    """
    st.html(
        f"""
        <style>
        .mantis-dashboard-metric {{
            padding: {spacing(2)} {spacing(2)};
            border-radius: 16px;
            background: var(--mantis-surface-alt);
            border: 1px solid var(--mantis-card-border);
            text-align: center;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        .mantis-dashboard-metric:hover {{
            transform: translateY(-2px);
            border-color: var(--mantis-accent-glow);
        }}
        .mantis-dashboard-metric-label {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--mantis-muted);
            font-weight: 600;
            margin-bottom: {spacing(1)};
        }}
        .mantis-dashboard-metric-value {{
            font-size: 28px;
            font-weight: 700;
            color: var(--mantis-text);
            line-height: 1.2;
        }}
        </style>
        """
    )
    
    cols = st.columns(len(metrics))
    for idx, (label, value) in enumerate(metrics):
        with cols[idx]:
            st.html(
                f"""
                <div class="mantis-dashboard-metric">
                    <div class="mantis-dashboard-metric-label">{label}</div>
                    <div class="mantis-dashboard-metric-value">{value}</div>
                </div>
                """
            )


# =============================================================================
# WORKSPACE HUB COMPONENT
# =============================================================================

def render_workspace_hub_section(
    title: str,
    content_fn: Callable[[], None],
) -> None:
    """Render a section within the workspace hub.
    
    Args:
        title: Section title
        content_fn: Function to render section content
    """
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.html(f"<div style='height: {spacing(1)};'></div>")
        content_fn()


# =============================================================================
# FEATURE GROUP COMPONENT
# =============================================================================

def render_feature_group(
    group_name: str,
    features: list[tuple[str, str, Callable[[], None]]],
    expanded: bool = False,
    key_prefix: str = "",
) -> None:
    """Render a collapsible group of features with consistent styling.
    
    Args:
        group_name: Name of the feature group (e.g., "🧠 Intelligence")
        features: List of (feature_name, description, action) tuples
        expanded: Whether the group should be expanded by default
        key_prefix: Prefix for button keys to avoid collisions
    """
    with st.expander(group_name, expanded=expanded):
        for idx, (feature_name, feature_desc, action) in enumerate(features):
            # Create a clean layout for each feature
            feature_cols = st.columns([3, 1])
            
            with feature_cols[0]:
                st.markdown(f"**{feature_name}**")
                st.caption(feature_desc)
            
            with feature_cols[1]:
                # Generate safe key
                safe_group = group_name.replace(" ", "_").replace("🧠", "intel").replace("✍", "write").replace("📊", "insight").replace("⚙", "sys")
                safe_feature = feature_name.replace(" ", "_").lower()
                button_key = f"{key_prefix}_feature_{safe_group}_{safe_feature}_{idx}"
                
                if st.button("Open", key=button_key, use_container_width=True):
                    with st.spinner(f"Loading {feature_name.lower()}..."):
                        action()
            
            # Add spacing between features (except after last one)
            if idx < len(features) - 1:
                st.html(f"<div style='height: {spacing(1)};'></div>")


# =============================================================================
# SECTION HEADER COMPONENT (Enhanced)
# =============================================================================

def render_dashboard_section_header(title: str, description: Optional[str] = None) -> None:
    """Render a section header with consistent styling for dashboard sections.
    
    Args:
        title: Section title
        description: Optional description text
    """
    desc_html = f"<div style='color: var(--mantis-muted); font-size: 14px; margin-top: {spacing(1)};'>{description}</div>" if description else ""
    
    st.html(
        f"""
        <div style="margin-top: {spacing(3)}; margin-bottom: {spacing(2)};">
            <h2 style="margin: 0; font-size: 24px; font-weight: 600;">
                {title}
            </h2>
            {desc_html}
        </div>
        """
    )


# =============================================================================
# SPACING UTILITIES
# =============================================================================

def add_vertical_space(multiplier: int = 2) -> None:
    """Add vertical spacing using the 8px system.
    
    Args:
        multiplier: Number of spacing units (default: 2 = 16px)
    """
    st.html(f"<div style='height: {spacing(multiplier)};'></div>")


def add_divider_with_spacing(top: int = 3, bottom: int = 3) -> None:
    """Add a divider with spacing above and below.
    
    Args:
        top: Spacing units above divider
        bottom: Spacing units below divider
    """
    add_vertical_space(top)
    st.divider()
    add_vertical_space(bottom)
