from contextlib import contextmanager
from collections.abc import Generator
from typing import Optional

try:
    import streamlit as st
    _STREAMLIT_AVAILABLE = True
except ImportError:
    _STREAMLIT_AVAILABLE = False
    # Create a mock streamlit module for type checking
    class _MockStreamlit:
        @staticmethod
        @contextmanager
        def container(*args, **kwargs):
            yield
        @staticmethod
        def markdown(*args, **kwargs):
            pass
        @staticmethod
        def html(*args, **kwargs):
            pass
        @staticmethod
        def caption(*args, **kwargs):
            pass
        @staticmethod
        def button(*args, **kwargs):
            return False
    st = _MockStreamlit()


@contextmanager
def card(title: Optional[str] = None, caption: Optional[str] = None) -> Generator[None, None, None]:
    with st.container(border=True):
        if title:
            st.markdown(f"### {title}")
        if caption:
            st.caption(caption)
        yield


def section_header(title: str, caption: Optional[str] = None, tag: Optional[str] = None) -> None:
    caption_html = f"<div class='mantis-section-caption'>{caption}</div>" if caption else ""
    tag_html = f"<span class='mantis-tag'>{tag}</span>" if tag else ""
    st.html(
        f"""
        <div class="mantis-section-header">
            <div>
                <div class="mantis-section-title">{title}</div>
                {caption_html}
            </div>
            {tag_html}
        </div>
        """,
    )


def primary_button(label: str, key: Optional[str] = None, **kwargs) -> bool:
    if "use_container_width" not in kwargs:
        kwargs["use_container_width"] = True
    return st.button(label, key=key, type="primary", **kwargs)


def stat_tile(label: str, value: str, helper: Optional[str] = None, icon: Optional[str] = None) -> None:
    icon_html = f"<div class='mantis-stat-icon'>{icon}</div>" if icon else ""
    helper_html = f"<div class='mantis-stat-help'>{helper}</div>" if helper else ""
    st.html(
        f"""
        <div class="mantis-stat-tile">
            {icon_html}
            <div class="mantis-stat-label">{label}</div>
            <div class="mantis-stat-value">{value}</div>
            {helper_html}
        </div>
        """,
    )


def action_card(
    title: str,
    caption: str,
    button_label: str = "Open",
    button_type: str = "primary",
    key: Optional[str] = None,
    help_text: Optional[str] = None,
    *,
    icon: Optional[str] = None,
) -> bool:
    """Render a card with title, description, and an action button.

    Uses the unified button system classes (assets/styles.css).

    Args:
        title: Card heading.
        caption: Short description below the heading.
        button_label: Text on the action button.
        button_type: Streamlit button type ("primary" or "secondary").
        key: Streamlit widget key.
        help_text: Tooltip for the button.
        icon: Optional emoji/icon prepended to *title*.
    """
    display_title = f"{icon} {title}" if icon else title
    st.html(
        f"""
        <div class="mantis-action-card">
            <div class="mantis-action-card-title">{display_title}</div>
            <div class="mantis-action-card-desc">{caption}</div>
        </div>
        """,
    )
    return st.button(
        button_label,
        key=key,
        use_container_width=True,
        type=button_type,
        help=help_text,
    )
