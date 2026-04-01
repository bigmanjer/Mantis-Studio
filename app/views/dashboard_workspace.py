from __future__ import annotations

from typing import Any, Callable, Dict, List

import streamlit as st


def render_dashboard_workspace(
    *,
    recent_projects: List[Dict[str, Any]],
    project_title: str,
    latest_chapter_label: str,
    has_outline: bool,
    has_chapter: bool,
    canon_icon: str,
    canon_label: str,
    system_mode: str,
    ai_ops_today: int,
    weekly_count: int,
    weekly_goal: int,
    project_entity_count: int,
    world_recent_names: List[str],
    total_words: int,
    project_health_percent: int,
    ai_connected: bool,
    on_resume_writing: Callable[[], None],
    on_open_outline: Callable[[], None],
    on_new_project: Callable[[], None],
    on_open_world: Callable[[], None],
    on_open_memory: Callable[[], None],
    on_open_insights: Callable[[], None],
    on_open_project: Callable[[str, str], None],
) -> None:
    with st.container(border=True):
        st.markdown("#### Top metrics")
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.metric("Active projects", str(len(recent_projects)))
        with kpi_cols[1]:
            st.metric("Words generated", f"{total_words:,}")
        with kpi_cols[2]:
            ai_modules = "2" if ai_connected else "0"
            st.metric("AI modules active", ai_modules)
        with kpi_cols[3]:
            st.metric("Workflow readiness", f"{project_health_percent}%")

    with st.container(border=True):
        st.markdown("#### Workflow progress")
        steps = [
            ("Idea", bool(recent_projects)),
            ("Outline", bool(has_outline)),
            ("Chapters", bool(has_chapter)),
            ("World Bible", project_entity_count > 0),
            ("Revision", False),
            ("Export", False),
        ]
        completed_steps = sum(1 for _, done in steps if done)
        total_steps = len(steps)
        workflow_percent = int((completed_steps / total_steps) * 100) if total_steps else 0
        next_step = next((label for label, done in steps if not done), "Complete")

        st.markdown(
            f"""
            <div style="width:100%;height:12px;background:#d9e3db;border-radius:999px;overflow:hidden;">
                <div style="width:{workflow_percent}%;height:100%;background:#2e7d32;"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption(
            f"{completed_steps}/{total_steps} stages complete ({workflow_percent}%). Current target: {next_step}."
        )

        step_cols = st.columns(total_steps)
        for idx, (label, done) in enumerate(steps):
            with step_cols[idx]:
                st.markdown(f"**{label}**")
                st.caption("Done" if done else "Pending")

    st.html("<div style='height: 16px;'></div>")

    main_cols = st.columns([2.2, 1])
    with main_cols[0]:
        with st.container(border=True):
            st.markdown("#### Current focus")
            st.markdown(f"### {project_title}")
            st.caption(latest_chapter_label)
            action_row = st.columns(3)
            with action_row[0]:
                if st.button(
                    "Continue writing",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="dashboard_resume_writing",
                ):
                    on_resume_writing()
            with action_row[1]:
                if st.button(
                    "Open outline",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="dashboard_open_outline",
                ):
                    on_open_outline()
            with action_row[2]:
                if st.button(
                    "New project",
                    use_container_width=True,
                    key="dashboard_new_project_focus",
                ):
                    on_new_project()
            st.caption("Pick up where you left off without leaving the dashboard.")

        with st.container(border=True):
            st.markdown("### Quick jump")
            st.caption("Open key workflow modules.")
            qa_row_1 = st.columns(3)
            with qa_row_1[0]:
                if st.button(
                    "Outline",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="qa_outline",
                ):
                    on_open_outline()
            with qa_row_1[1]:
                if st.button(
                    "Chapters",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="qa_chapters",
                ):
                    on_resume_writing()
            with qa_row_1[2]:
                if st.button(
                    "World Bible",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="qa_world",
                ):
                    on_open_world()
            qa_row_2 = st.columns(2)
            with qa_row_2[0]:
                if st.button(
                    "Memory",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="qa_memory",
                ):
                    on_open_memory()
            with qa_row_2[1]:
                if st.button(
                    "Insights",
                    use_container_width=True,
                    disabled=not recent_projects,
                    key="qa_insights",
                ):
                    on_open_insights()

        st.html("<div style='height: 8px;'></div>")
        st.markdown("### My projects")
        with st.container(border=True):
            if not recent_projects:
                st.info("No projects yet. Create one to get started.")
                if st.button(
                    "Create a project",
                    use_container_width=True,
                    type="primary",
                    key="dashboard_empty_create_project",
                ):
                    on_new_project()
            else:
                header = st.columns([2.4, 1, 1])
                with header[0]:
                    st.markdown("**Project**")
                with header[1]:
                    st.markdown("**Genre**")
                with header[2]:
                    st.markdown("**Open**")

                for project_entry in recent_projects[:5]:
                    meta = project_entry.get("meta", {})
                    title = meta.get("title") or "Untitled"
                    genre = meta.get("genre") or "-"
                    chapters = meta.get("chapters") or {}
                    word_sum = sum((c.get("word_count") or 0) for c in chapters.values())
                    row = st.columns([2.4, 1, 1])
                    with row[0]:
                        if st.button(
                            f"Open {title}",
                            use_container_width=True,
                            key=f"dash_proj_{project_entry.get('path', '')}",
                        ):
                            on_open_project(project_entry["path"], "chapters")
                        st.caption(f"{len(chapters)} chapters - {word_sum:,} words")
                    with row[1]:
                        st.caption(genre)
                    with row[2]:
                        if st.button(
                            "Open",
                            use_container_width=True,
                            key=f"dash_open_{project_entry.get('path', '')}",
                        ):
                            on_open_project(project_entry["path"], "chapters")

    with main_cols[1]:
        with st.container(border=True):
            st.markdown("#### Studio snapshot")
            st.caption("At-a-glance health for your workspace.")
            st.markdown(f"**Canon health:** {canon_icon} {canon_label}")
            st.caption(f"System mode: {system_mode} - AI ops today: {ai_ops_today}")
            st.divider()
            st.markdown("**Weekly momentum**")
            st.caption(f"{weekly_count}/{weekly_goal} sessions logged")
            st.markdown("**Onboarding checklist**")
            st.checkbox(
                "AI connected",
                value=ai_connected,
                disabled=True,
                key="home_check_ai",
            )
            st.checkbox(
                "Project created",
                value=bool(recent_projects),
                disabled=True,
                key="home_check_project",
            )
            st.checkbox(
                "Outline drafted",
                value=bool(has_outline),
                disabled=True,
                key="home_check_outline",
            )
            st.checkbox(
                "Chapter drafted",
                value=bool(has_chapter),
                disabled=True,
                key="home_check_chapter",
            )

        with st.container(border=True):
            st.markdown("#### World Bible pulse")
            st.caption("Recent canon activity from the active project.")
            st.markdown(f"**Entities tracked:** {project_entity_count}")
            if world_recent_names:
                st.caption("Recently updated")
                for name in world_recent_names:
                    st.markdown(f"- {name}")
            if st.button(
                "Open World Bible",
                use_container_width=True,
                key="dashboard_open_world_pulse",
                disabled=not recent_projects,
            ):
                on_open_world()


