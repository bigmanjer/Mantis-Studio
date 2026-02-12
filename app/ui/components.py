from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator
from typing import Any, Iterable, Optional

import streamlit as st


def section_title(title: str, subtitle: Optional[str] = None) -> None:
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
