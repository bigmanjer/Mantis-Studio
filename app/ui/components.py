from __future__ import annotations

from typing import Any, Iterable, Optional

import streamlit as st


def section_title(title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f"<div class='mantis-muted'>{subtitle}</div>", unsafe_allow_html=True)


def card_start(title: Optional[str] = None, subtitle: Optional[str] = None) -> None:
    st.markdown("<div class='mantis-card'>", unsafe_allow_html=True)
    if title:
        st.markdown(f"### {title}")
    if subtitle:
        st.caption(subtitle)


def card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def cta_tile(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="mantis-cta-tile">
            <div style="font-weight:600;">{title}</div>
            <div class="mantis-muted" style="margin-top:6px;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
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
    st.markdown(
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
        unsafe_allow_html=True,
    )


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="mantis-card-soft">
            <div style="font-weight:600;">{title}</div>
            <div class="mantis-muted" style="margin-top:6px;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tag_list(tags: Iterable[str]) -> None:
    pills = "".join(f"<span class='mantis-pill'>{tag}</span>" for tag in tags if tag)
    if pills:
        st.markdown(f"<div style='display:flex; gap:6px; flex-wrap:wrap;'>{pills}</div>", unsafe_allow_html=True)
