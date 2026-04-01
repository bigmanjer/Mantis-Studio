from __future__ import annotations

from typing import Any, Callable, Dict, List

import streamlit as st


def render_editor_utility_bar(
    *,
    project: Any,
    current_chapter: Any,
    on_open_outline: Callable[[], None],
    on_open_world: Callable[[], None],
    on_word_target_change: Callable[[int], None],
) -> None:
    with st.container(border=True):
        utility_cols = st.columns([1.15, 1.0, 0.95])
        with utility_cols[0]:
            st.caption("Draft metrics")
            st.caption(f"Current chapter: {current_chapter.word_count} words")
            st.caption(f"Project total: {project.get_total_word_count()} words")
            save_state = (
                "Autosave enabled"
                if st.session_state.get("auto_save", True)
                else "Manual save mode"
            )
            st.caption(save_state)
        with utility_cols[1]:
            st.caption("Quick jump")
            jump_cols = st.columns(2)
            with jump_cols[0]:
                if st.button(
                    "Outline",
                    use_container_width=True,
                    key=f"editor_jump_outline_{current_chapter.id}",
                ):
                    on_open_outline()
            with jump_cols[1]:
                if st.button(
                    "World",
                    use_container_width=True,
                    key=f"editor_jump_world_{current_chapter.id}",
                ):
                    on_open_world()
        with utility_cols[2]:
            avg_target = st.number_input(
                "AI avg/chapter",
                min_value=200,
                max_value=6000,
                step=50,
                value=int(project.default_word_count or 1000),
                key=f"editor_default_word_avg_{project.id}",
                help="Fallback length target for AI chapter generation.",
            )
            if int(avg_target) != int(project.default_word_count or 1000):
                on_word_target_change(int(avg_target))
            st.caption("Fallback target")


def render_chapter_sidebar(
    *,
    chapters: List[Dict[str, Any]],
    current_chapter_id: str,
    on_select: Callable[[str], None],
    on_create_next: Callable[[], None],
    on_delete_current: Callable[[], None],
    delete_pending: bool,
    current_title: str,
    on_cancel_delete: Callable[[], None],
) -> None:
    with st.container(border=True):
        st.markdown("### Chapters")
        for chapter in chapters:
            chapter_id = chapter.get("id")
            chapter_words = int(chapter.get("word_count") or 0)
            raw_title = chapter.get("title") or "Untitled"
            short_title = raw_title if len(raw_title) <= 22 else f"{raw_title[:19]}..."
            label = f"{chapter.get('index', 0)}. {short_title} ({chapter_words})"
            if st.button(
                label,
                key=f"n_{chapter_id}",
                type="primary" if chapter_id == current_chapter_id else "secondary",
                use_container_width=True,
            ):
                on_select(chapter_id)

        st.divider()
        if st.button(
            "New Chapter",
            use_container_width=True,
            help="Create a new chapter in this project.",
            key="editor_new_chapter",
        ):
            on_create_next()

        if delete_pending:
            st.warning(f"Delete **{current_title}**?")
            cdel1, cdel2 = st.columns(2)
            with cdel1:
                if st.button(
                    "Yes",
                    type="primary",
                    use_container_width=True,
                    key="editor_del_ch_confirm",
                ):
                    on_delete_current()
            with cdel2:
                if st.button(
                    "No",
                    use_container_width=True,
                    key="editor_del_ch_cancel",
                ):
                    on_cancel_delete()
        elif st.button(
            "Delete Chapter",
            use_container_width=True,
            key=f"editor_del_{current_chapter_id}",
        ):
            st.session_state.delete_chapter_id = current_chapter_id
            st.session_state.delete_chapter_title = current_title
            st.rerun()

