from contextlib import contextmanager
from collections.abc import Generator
from typing import Optional

import streamlit as st


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
    st.markdown(
        f"""
        <div class="mantis-section-header">
            <div>
                <div class="mantis-section-title">{title}</div>
                {caption_html}
            </div>
            {tag_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def primary_button(label: str, key: Optional[str] = None, **kwargs) -> bool:
    if "use_container_width" not in kwargs:
        kwargs["use_container_width"] = True
    return st.button(label, key=key, type="primary", **kwargs)


def stat_tile(label: str, value: str, helper: Optional[str] = None, icon: Optional[str] = None) -> None:
    icon_html = f"<div class='mantis-stat-icon'>{icon}</div>" if icon else ""
    helper_html = f"<div class='mantis-stat-help'>{helper}</div>" if helper else ""
    st.markdown(
        f"""
        <div class="mantis-stat-tile">
            {icon_html}
            <div class="mantis-stat-label">{label}</div>
            <div class="mantis-stat-value">{value}</div>
            {helper_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def action_card(
    title: str,
    caption: str,
    button_label: str = "Open",
    key: Optional[str] = None,
    help_text: Optional[str] = None,
) -> bool:
    with st.container(border=True):
        st.markdown(f"### {title}")
        st.caption(caption)
        return st.button(button_label, key=key, use_container_width=True, help=help_text)
