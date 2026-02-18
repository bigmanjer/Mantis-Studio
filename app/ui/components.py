from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator
from typing import Iterable, Optional

import streamlit as st


def page_header(
    title: str,
    subtitle: Optional[str] = None,
    *,
    pill: Optional[str] = None,
    actions: Optional[str] = None,
) -> None:
    """Render a standardized page header with title, subtitle, and optional elements.
    
    Args:
        title: Main page title
        subtitle: Optional subtitle/description
        pill: Optional status pill text (e.g., "Beta", "New")
        actions: Optional HTML for action buttons in the header
    """
    pill_html = f"<span class='mantis-pill'>{pill}</span>" if pill else ""
    actions_html = f"<div style='display:flex; gap:8px; align-items:center;'>{actions}</div>" if actions else ""
    
    st.html(
        f"""
        <div class="mantis-page-header">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:16px;">
                <div style="flex:1;">
                    <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
                        <h1 class="mantis-page-title" style="margin:0;">{title}</h1>
                        {pill_html}
                    </div>
                    {f'<div class="mantis-page-subtitle">{subtitle}</div>' if subtitle else ''}
                </div>
                {actions_html}
            </div>
        </div>
        """
    )


def section_header(
    title: str,
    *,
    caption: Optional[str] = None,
    tag: Optional[str] = None,
    actions: Optional[str] = None,
) -> None:
    """Render a section header with optional caption, tag, and actions.
    
    Args:
        title: Section title
        caption: Optional caption/description below title
        tag: Optional tag/badge text
        actions: Optional HTML for action buttons
    """
    tag_html = f"<span class='mantis-pill'>{tag}</span>" if tag else ""
    actions_html = actions if actions else ""
    
    st.html(
        f"""
        <div class="mantis-section-header">
            <div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <h3 class="mantis-section-title">{title}</h3>
                    {tag_html}
                </div>
                {f'<div class="mantis-section-caption">{caption}</div>' if caption else ''}
            </div>
            {f'<div>{actions_html}</div>' if actions_html else ''}
        </div>
        """
    )


def section_title(title: str, subtitle: Optional[str] = None) -> None:
    """Simple section title - use section_header() for more features"""
    st.markdown(f"## {title}")
    if subtitle:
        st.html(f"<div class='mantis-muted'>{subtitle}</div>")


@contextmanager
def card_block(title: Optional[str] = None, subtitle: Optional[str] = None) -> Generator[None, None, None]:
    """Render a styled card using Streamlit's native container.

    Replaces the old card_start/card_end pattern which broke rendering
    because Streamlit sanitizes each st.markdown call independently,
    preventing split open/close ``<div>`` tags from working.
    """
    with st.container(border=True):
        if title:
            st.markdown(f"### {title}")
        if subtitle:
            st.caption(subtitle)
        yield


def card_start(title: Optional[str] = None, subtitle: Optional[str] = None) -> None:
    """Deprecated — kept for backward compatibility.

    Prefer :func:`card_block` context manager instead.  This now
    delegates to ``st.container(border=True)`` so the opening markup
    is no longer an orphaned ``<div>`` tag.
    """
    st.html("<div class='mantis-card'>")
    if title:
        st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def card_end() -> None:
    """Deprecated — kept for backward compatibility."""
    st.html("</div>")


def cta_tile(title: str, body: str, *, icon: Optional[str] = None, subtitle: Optional[str] = None) -> None:
    """Render a card-style CTA tile (Quick Actions style).

    Uses CSS classes from the unified button system (assets/styles.css).
    Supports optional icon and subtitle for enhanced card layouts.

    Args:
        title: Primary label, may include an emoji prefix (e.g. "✍️ Editor").
        body: Short description shown below the title.
        icon: Optional standalone icon rendered above the title.
        subtitle: Optional secondary text below *body*.
    """
    icon_html = f'<div class="mantis-cta-icon">{icon}</div>' if icon else ""
    subtitle_html = (
        f'<div class="mantis-cta-subtitle">{subtitle}</div>'
        if subtitle
        else ""
    )
    st.html(
        f"""
        <div class="mantis-cta-tile">
            {icon_html}
            <div class="mantis-cta-title">{title}</div>
            <div class="mantis-cta-body">{body}</div>
            {subtitle_html}
        </div>
        """,
    )


def header_bar(
    title: str,
    subtitle: str,
    *,
    pill: Optional[str] = None,
    right_slot: Optional[str] = None,
) -> None:
    pill_html = f"<span class='mantis-pill'>{pill}</span>" if pill else ""
    right_html = f"<div>{right_slot}</div>" if right_slot else ""
    st.html(
        f"""
        <div class="mantis-header">
            <div>
                <div style="font-size:24px; font-weight:700;">{title}</div>
                <div class="mantis-muted" style="margin-top:4px;">{subtitle}</div>
            </div>
            <div style="display:flex; gap:12px; align-items:center;">
                {pill_html}
                {right_html}
            </div>
        </div>
        """,
    )


def empty_state(title: str, body: str) -> None:
    st.html(
        f"""
        <div class="mantis-card-soft">
            <div style="font-weight:600;">{title}</div>
            <div class="mantis-muted" style="margin-top:6px;">{body}</div>
        </div>
        """,
    )


def render_tag_list(tags: Iterable[str]) -> None:
    pills = "".join(f"<span class='mantis-pill'>{tag}</span>" for tag in tags if tag)
    if pills:
        st.html(f"<div style='display:flex; gap:6px; flex-wrap:wrap;'>{pills}</div>")


def stat_card(label: str, value: str, *, icon: Optional[str] = None, help_text: Optional[str] = None) -> None:
    """Render a stat/KPI card with optional icon and help text.
    
    Args:
        label: Stat label (e.g., "Total Words")
        value: Stat value (e.g., "12,450")
        icon: Optional emoji icon
        help_text: Optional help/description text
    """
    icon_html = f"<div class='mantis-stat-icon'>{icon}</div>" if icon else ""
    help_html = f"<div class='mantis-stat-help'>{help_text}</div>" if help_text else ""
    
    st.html(
        f"""
        <div class="mantis-stat-tile">
            {icon_html}
            <div class="mantis-stat-label">{label}</div>
            <div class="mantis-stat-value">{value}</div>
            {help_html}
        </div>
        """
    )


def divider(*, spacing: str = "24px") -> None:
    """Render a horizontal divider with custom spacing.
    
    Args:
        spacing: Vertical spacing around divider (default: 24px)
    """
    st.html(f"<div class='mantis-divider' style='margin: {spacing} 0;'></div>")


def loading_indicator(message: str = "Loading...") -> None:
    """Show a styled loading indicator.
    
    Args:
        message: Loading message to display
    """
    st.html(
        f"""
        <div style="text-align:center; padding:40px 20px;">
            <div class="mantis-muted" style="font-size:14px;">⏳ {message}</div>
        </div>
        """
    )


def success_message(message: str) -> None:
    """Display a success message with styling.
    
    Args:
        message: Success message text
    """
    st.html(
        f"""
        <div style="
            background: var(--mantis-accent-soft);
            border: 1px solid var(--mantis-accent-glow);
            border-radius: var(--mantis-radius-md);
            padding: 12px 16px;
            color: var(--mantis-text);
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 12px 0;
        ">
            <span style="font-size:20px;">✓</span>
            <span>{message}</span>
        </div>
        """
    )


def error_message(message: str) -> None:
    """Display an error message with styling.
    
    Args:
        message: Error message text
    """
    st.html(
        f"""
        <div style="
            background: rgba(239,68,68,0.12);
            border: 1px solid rgba(239,68,68,0.3);
            border-radius: var(--mantis-radius-md);
            padding: 12px 16px;
            color: var(--mantis-text);
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 12px 0;
        ">
            <span style="font-size:20px;">⚠</span>
            <span>{message}</span>
        </div>
        """
    )


def info_message(message: str) -> None:
    """Display an info message with styling.
    
    Args:
        message: Info message text
    """
    st.html(
        f"""
        <div style="
            background: rgba(56,189,248,0.12);
            border: 1px solid rgba(56,189,248,0.3);
            border-radius: var(--mantis-radius-md);
            padding: 12px 16px;
            color: var(--mantis-text);
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 12px 0;
        ">
            <span style="font-size:20px;">ℹ</span>
            <span>{message}</span>
        </div>
        """
    )
