"""Enhanced UI feedback components for Mantis Studio.

This module provides:
- Loading states with spinners and progress indicators
- Step-by-step workflow guidance
- Success/error feedback animations
- Progress bars with estimated time
"""

from typing import Optional, List, Dict, Any
import streamlit as st


def loading_state(
    message: str = "Loading...",
    subtext: Optional[str] = None,
    show_spinner: bool = True,
) -> None:
    """Display an enhanced loading state with clear messaging.
    
    Args:
        message: Primary loading message
        subtext: Optional additional context (e.g., "this may take ~10 seconds")
        show_spinner: Whether to show an animated spinner
    """
    html = f"""
    <div class="mantis-loading-state">
        {'<div class="mantis-spinner"></div>' if show_spinner else ''}
        <div class="mantis-loading-message">{message}</div>
        {f'<div class="mantis-loading-subtext">{subtext}</div>' if subtext else ''}
    </div>
    <style>
    .mantis-loading-state {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        gap: 1rem;
    }}
    .mantis-spinner {{
        width: 40px;
        height: 40px;
        border: 3px solid var(--mantis-card-border, rgba(148, 163, 184, 0.15));
        border-top-color: var(--mantis-accent, #22c55e);
        border-radius: 50%;
        animation: mantis-spin 0.8s linear infinite;
    }}
    @keyframes mantis-spin {{
        to {{ transform: rotate(360deg); }}
    }}
    .mantis-loading-message {{
        font-size: 16px;
        font-weight: 600;
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-loading-subtext {{
        font-size: 13px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
    }}
    </style>
    """
    st.html(html)


def step_indicator(
    steps: List[str],
    current_step: int,
    completed_steps: Optional[List[int]] = None,
) -> None:
    """Display a step-by-step workflow indicator.
    
    Args:
        steps: List of step labels
        current_step: Index of the current step (0-based)
        completed_steps: List of completed step indices (default: all before current)
    """
    if completed_steps is None:
        completed_steps = list(range(current_step))
    
    steps_html = []
    for i, step_label in enumerate(steps):
        is_completed = i in completed_steps
        is_current = i == current_step
        is_future = i > current_step and not is_completed
        
        step_class = "mantis-step"
        if is_completed:
            step_class += " mantis-step-completed"
        elif is_current:
            step_class += " mantis-step-current"
        elif is_future:
            step_class += " mantis-step-future"
        
        icon = "✓" if is_completed else str(i + 1)
        
        steps_html.append(f"""
        <div class="{step_class}">
            <div class="mantis-step-icon">{icon}</div>
            <div class="mantis-step-label">{step_label}</div>
        </div>
        """)
        
        # Add connector line between steps (except after last step)
        if i < len(steps) - 1:
            connector_class = "mantis-step-connector"
            if is_completed:
                connector_class += " mantis-step-connector-completed"
            steps_html.append(f'<div class="{connector_class}"></div>')
    
    html = f"""
    <div class="mantis-step-indicator">
        {''.join(steps_html)}
    </div>
    <style>
    .mantis-step-indicator {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.5rem 1rem;
        margin-bottom: 1.5rem;
        background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
        border-radius: 16px;
        border: 1px solid var(--mantis-card-border, rgba(148, 163, 184, 0.15));
    }}
    .mantis-step {{
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;
        flex: 0 0 auto;
    }}
    .mantis-step-icon {{
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        border: 2px solid var(--mantis-card-border, rgba(148, 163, 184, 0.15));
        background: var(--mantis-surface, rgba(6,18,14,0.85));
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        transition: all 0.3s ease;
    }}
    .mantis-step-label {{
        font-size: 12px;
        font-weight: 500;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        text-align: center;
        max-width: 100px;
    }}
    .mantis-step-completed .mantis-step-icon {{
        background: var(--mantis-accent, #22c55e);
        border-color: var(--mantis-accent, #22c55e);
        color: #ffffff;
    }}
    .mantis-step-completed .mantis-step-label {{
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-step-current .mantis-step-icon {{
        border-color: var(--mantis-accent, #22c55e);
        color: var(--mantis-accent, #22c55e);
        box-shadow: 0 0 0 4px var(--mantis-accent-glow, rgba(34,197,94,0.25));
        animation: mantis-pulse 2s ease-in-out infinite;
    }}
    .mantis-step-current .mantis-step-label {{
        color: var(--mantis-text, #e2e8f0);
        font-weight: 600;
    }}
    @keyframes mantis-pulse {{
        0%, 100% {{ box-shadow: 0 0 0 4px var(--mantis-accent-glow, rgba(34,197,94,0.25)); }}
        50% {{ box-shadow: 0 0 0 8px var(--mantis-accent-glow, rgba(34,197,94,0.15)); }}
    }}
    .mantis-step-future .mantis-step-icon {{
        background: var(--mantis-surface, rgba(6,18,14,0.85));
        opacity: 0.5;
    }}
    .mantis-step-connector {{
        flex: 1;
        height: 2px;
        background: var(--mantis-card-border, rgba(148, 163, 184, 0.15));
        margin: 0 0.5rem;
        position: relative;
        top: -18px;
    }}
    .mantis-step-connector-completed {{
        background: var(--mantis-accent, #22c55e);
    }}
    @media (max-width: 768px) {{
        .mantis-step-indicator {{
            flex-direction: column;
            align-items: flex-start;
        }}
        .mantis-step {{
            flex-direction: row;
            width: 100%;
        }}
        .mantis-step-label {{
            text-align: left;
            max-width: none;
        }}
        .mantis-step-connector {{
            width: 2px;
            height: 20px;
            margin: 0.5rem 0 0.5rem 17px;
            top: 0;
        }}
    }}
    </style>
    """
    st.html(html)


def progress_bar_with_message(
    progress: float,
    message: str = "",
    estimated_time: Optional[str] = None,
) -> None:
    """Display a progress bar with message and optional time estimate.
    
    Args:
        progress: Progress value from 0.0 to 1.0
        message: Status message to display
        estimated_time: Optional time estimate (e.g., "~2 minutes remaining")
    """
    progress_percent = int(progress * 100)
    
    html = f"""
    <div class="mantis-progress-container">
        <div class="mantis-progress-header">
            <span class="mantis-progress-message">{message}</span>
            {f'<span class="mantis-progress-time">{estimated_time}</span>' if estimated_time else ''}
        </div>
        <div class="mantis-progress-bar">
            <div class="mantis-progress-fill" style="width: {progress_percent}%"></div>
        </div>
        <div class="mantis-progress-percent">{progress_percent}%</div>
    </div>
    <style>
    .mantis-progress-container {{
        padding: 1rem;
        background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
        border-radius: 12px;
        border: 1px solid var(--mantis-card-border, rgba(148, 163, 184, 0.15));
    }}
    .mantis-progress-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.75rem;
    }}
    .mantis-progress-message {{
        font-size: 14px;
        font-weight: 600;
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-progress-time {{
        font-size: 12px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
    }}
    .mantis-progress-bar {{
        height: 8px;
        background: var(--mantis-card-border, rgba(148, 163, 184, 0.15));
        border-radius: 999px;
        overflow: hidden;
        position: relative;
    }}
    .mantis-progress-fill {{
        height: 100%;
        background: linear-gradient(90deg, var(--mantis-accent, #22c55e), var(--mantis-accent-glow, #4ade80));
        border-radius: 999px;
        transition: width 0.3s ease;
        position: relative;
    }}
    .mantis-progress-fill::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        animation: mantis-shimmer 2s infinite;
    }}
    @keyframes mantis-shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    .mantis-progress-percent {{
        text-align: right;
        font-size: 12px;
        font-weight: 600;
        color: var(--mantis-accent, #22c55e);
        margin-top: 0.5rem;
    }}
    </style>
    """
    st.html(html)


def feedback_message(
    message: str,
    message_type: str = "success",
    icon: Optional[str] = None,
    dismissible: bool = True,
) -> None:
    """Display a feedback message with appropriate styling.
    
    Args:
        message: The feedback message to display
        message_type: Message type - "success", "error", "warning", "info"
        icon: Optional custom icon (default: auto-selected based on message_type)
        dismissible: Whether the message can be dismissed
    """
    default_icons = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "info": "ℹ",
    }
    
    icon_display = icon or default_icons.get(message_type, "ℹ")
    
    type_classes = {
        "success": "mantis-feedback-success",
        "error": "mantis-feedback-error",
        "warning": "mantis-feedback-warning",
        "info": "mantis-feedback-info",
    }
    
    feedback_class = type_classes.get(message_type, "mantis-feedback-info")
    
    html = f"""
    <div class="mantis-feedback-message {feedback_class}">
        <div class="mantis-feedback-icon">{icon_display}</div>
        <div class="mantis-feedback-text">{message}</div>
    </div>
    <style>
    .mantis-feedback-message {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid;
        animation: mantis-slide-in 0.3s ease-out;
    }}
    @keyframes mantis-slide-in {{
        from {{
            opacity: 0;
            transform: translateY(-10px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    .mantis-feedback-icon {{
        font-size: 18px;
        font-weight: 700;
        flex-shrink: 0;
    }}
    .mantis-feedback-text {{
        flex: 1;
        font-size: 14px;
        line-height: 1.5;
    }}
    .mantis-feedback-success {{
        background: rgba(34, 197, 94, 0.12);
        border-color: rgba(34, 197, 94, 0.35);
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-feedback-success .mantis-feedback-icon {{
        color: var(--mantis-success, #22c55e);
    }}
    .mantis-feedback-error {{
        background: rgba(239, 68, 68, 0.12);
        border-color: rgba(239, 68, 68, 0.35);
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-feedback-error .mantis-feedback-icon {{
        color: #ef4444;
    }}
    .mantis-feedback-warning {{
        background: rgba(245, 158, 11, 0.12);
        border-color: rgba(245, 158, 11, 0.35);
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-feedback-warning .mantis-feedback-icon {{
        color: var(--mantis-warning, #f59e0b);
    }}
    .mantis-feedback-info {{
        background: rgba(56, 189, 248, 0.12);
        border-color: rgba(56, 189, 248, 0.35);
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-feedback-info .mantis-feedback-icon {{
        color: #38bdf8;
    }}
    </style>
    """
    st.html(html)


def page_header(
    title: str,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    breadcrumbs: Optional[List[str]] = None,
) -> None:
    """Display a consistent page header with title, subtitle, and optional breadcrumbs.
    
    Args:
        title: Page title
        subtitle: Optional subtitle/description
        icon: Optional emoji/icon to display
        breadcrumbs: Optional list of breadcrumb labels (e.g., ["Home", "Projects", "My Novel"])
    """
    breadcrumbs_html = ""
    if breadcrumbs:
        crumbs = " › ".join(f'<span class="mantis-breadcrumb-item">{crumb}</span>' for crumb in breadcrumbs)
        breadcrumbs_html = f'<div class="mantis-breadcrumbs">{crumbs}</div>'
    
    icon_html = f'<span class="mantis-page-icon">{icon}</span>' if icon else ''
    subtitle_html = f'<div class="mantis-page-subtitle">{subtitle}</div>' if subtitle else ''
    
    html = f"""
    <div class="mantis-page-header">
        {breadcrumbs_html}
        <div class="mantis-page-title-row">
            {icon_html}
            <h1 class="mantis-page-title">{title}</h1>
        </div>
        {subtitle_html}
    </div>
    <style>
    .mantis-page-header {{
        margin-bottom: 2rem;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--mantis-divider, #143023);
    }}
    .mantis-breadcrumbs {{
        font-size: 12px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        margin-bottom: 0.75rem;
        letter-spacing: 0.02em;
    }}
    .mantis-breadcrumb-item:not(:last-child) {{
        opacity: 0.7;
    }}
    .mantis-page-title-row {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }}
    .mantis-page-icon {{
        font-size: 32px;
        line-height: 1;
    }}
    .mantis-page-title {{
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        color: var(--mantis-text, #e2e8f0);
        letter-spacing: -0.02em;
    }}
    .mantis-page-subtitle {{
        font-size: 15px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        margin-top: 0.5rem;
        line-height: 1.5;
    }}
    </style>
    """
    st.html(html)
