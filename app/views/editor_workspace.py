from __future__ import annotations

from typing import Any, Callable, Dict, List

import streamlit as st


def render_editor_utility_bar(
    *,
    project: Any,
    current_chapter: Any,
    chapters: List[Dict[str, Any]],
    on_select: Callable[[str], None],
    on_previous: Callable[[], None],
    on_next: Callable[[], None],
    previous_disabled: bool,
    next_disabled: bool,
    on_create_next: Callable[[], None],
    on_delete_current: Callable[[], None],
    delete_pending: bool,
    current_title: str,
    on_cancel_delete: Callable[[], None],
) -> None:
    with st.container(border=True):
        st.markdown("### Chapter Flow")
        chapter_ids = [chapter.get("id") for chapter in chapters if chapter.get("id")]
        current_index = chapter_ids.index(current_chapter.id) if current_chapter.id in chapter_ids else 0
        chapter_lookup = {chapter.get("id"): chapter for chapter in chapters if chapter.get("id")}

        def _chapter_label(chapter_id: str) -> str:
            chapter = chapter_lookup.get(chapter_id, {})
            index = chapter.get("index", 0)
            title = chapter.get("title") or "Untitled"
            words = int(chapter.get("word_count") or 0)
            return f"{index}. {title} ({words:,} words)"

        flow_cols = st.columns([0.85, 0.85, 3.4, 1.0, 1.0])
        with flow_cols[0]:
            if st.button(
                "Previous",
                use_container_width=True,
                disabled=previous_disabled,
                key=f"editor_flow_prev_{current_chapter.id}",
            ):
                on_previous()
        with flow_cols[1]:
            if st.button(
                "Next",
                use_container_width=True,
                disabled=next_disabled,
                key=f"editor_flow_next_{current_chapter.id}",
            ):
                on_next()
        with flow_cols[2]:
            selected_chapter_id = st.selectbox(
                "Chapter",
                chapter_ids,
                index=current_index,
                format_func=_chapter_label,
                key=f"editor_chapter_flow_select_{project.id}_{current_chapter.id}",
            )
            if selected_chapter_id != current_chapter.id:
                on_select(selected_chapter_id)
        with flow_cols[3]:
            if st.button(
                "New",
                use_container_width=True,
                key="editor_flow_new_chapter",
                help="Create a new chapter in this project.",
            ):
                on_create_next()
        with flow_cols[4]:
            if st.button(
                "Delete",
                use_container_width=True,
                key=f"editor_flow_delete_{current_chapter.id}",
            ):
                st.session_state.delete_chapter_id = current_chapter.id
                st.session_state.delete_chapter_title = current_title
                st.rerun()
        if delete_pending:
            st.warning(f"Delete **{current_title}**?")
            confirm_cols = st.columns([1, 1, 5])
            with confirm_cols[0]:
                if st.button(
                    "Yes",
                    type="primary",
                    use_container_width=True,
                    key="editor_flow_del_confirm",
                ):
                    on_delete_current()
            with confirm_cols[1]:
                if st.button(
                    "No",
                    use_container_width=True,
                    key="editor_flow_del_cancel",
                ):
                    on_cancel_delete()
