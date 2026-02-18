"""Enhanced Sidebar Component for Mantis Studio."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional
import uuid
import streamlit as st

from app.utils.branding_assets import resolve_asset_path


def render_sidebar_brand(version: str) -> None:
    st.html('<div class="mantis-sidebar-brand mantis-sidebar-brand--modern">')
    assets_dir = Path(__file__).resolve().parents[2] / "assets"
    emblem_path = resolve_asset_path(assets_dir, "branding/mantis_emblem.png")
    if emblem_path:
        st.image(str(emblem_path), width=128)
    else:
        st.markdown("**MANTIS**")
    st.html(f'<div class="mantis-sidebar-meta"><span class="mantis-sidebar-version">Enterprise Console · v{version}</span></div><div class="mantis-sidebar-divider"></div></div>')


def render_theme_selector(instance_id: str) -> None:
    st.html("<div class='mantis-nav-section'>Appearance</div>")
    current_theme = st.session_state.get("ui_theme", "Dark")
    selected_theme = st.selectbox(
        "Theme",
        ["Dark", "Light"],
        index=0 if current_theme == "Dark" else 1,
        key=f"sidebar_theme_selector_{instance_id}",
        label_visibility="collapsed",
    )
    st.session_state.ui_theme = selected_theme


def render_project_info(project: Optional[Any]) -> None:
    st.html("<div class='mantis-nav-section'>Workspace</div>")
    if not project:
        st.html('<div class="mantis-project-chip"><div class="mantis-project-chip__title">No project loaded</div><div class="mantis-project-chip__meta">Create or open a workspace</div></div>')
        return
    st.html(f'<div class="mantis-project-chip"><div class="mantis-project-chip__title">{project.title}</div><div class="mantis-project-chip__meta">📚 {project.get_total_word_count():,} words</div></div>')


def render_navigation_section(section_name: str, nav_items: list, current_page: str, world_focus: str, expanded: bool, slugify: Callable, instance_id: str) -> None:
    with st.expander(section_name, expanded=expanded):
        section_slug = slugify(section_name)
        for label, target, icon in nav_items:
            if target == "memory":
                is_active = current_page == "world" and world_focus == "Memory"
            elif target == "insights":
                is_active = current_page == "world" and world_focus == "Insights"
            elif target == "legal":
                is_active = current_page in {"legal", "terms", "privacy", "copyright", "cookie", "help"}
            else:
                is_active = current_page == target

            key = f"nav_{instance_id}_{section_slug}_{target}_{slugify(label)}"
            if st.button(f"{icon} {label}", key=key, use_container_width=True, disabled=is_active, type="primary" if is_active else "secondary"):
                if target == "memory":
                    st.session_state.world_focus_tab = "Memory"
                    st.session_state.page = "world"
                elif target == "insights":
                    st.session_state.world_focus_tab = "Insights"
                    st.session_state.page = "world"
                else:
                    st.session_state.page = target
                st.rerun()


def render_project_actions(project: Optional[Any], save_callback: Callable, close_callback: Callable, instance_id: str) -> None:
    if not project:
        return
    st.divider()
    st.html("<div class='mantis-nav-section'>Project Actions</div>")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save", key=f"sidebar_save_project_{instance_id}", type="primary", use_container_width=True):
            try:
                save_callback()
                st.toast("Project saved", icon="✅")
            except Exception as e:
                st.toast(f"Save failed: {e}", icon="⚠️")
    with c2:
        if st.button("✖ Close", key=f"sidebar_close_project_{instance_id}", use_container_width=True):
            close_callback()


def render_debug_panel(instance_id: str) -> None:
    st.divider()
    st.html("<div class='mantis-nav-section'>Diagnostics</div>")
    st.session_state.debug = st.checkbox("Enable Debug Mode", value=bool(st.session_state.get("debug", False)), key=f"sidebar_debug_{instance_id}")


def render_enhanced_sidebar(version: str, project: Optional[Any], current_page: str, world_focus: str, debug_enabled: bool, key_scope: Callable, slugify: Callable, save_project_callback: Callable, close_project_callback: Callable) -> None:
    del debug_enabled, key_scope
    from app.utils.navigation import get_nav_sections

    instance_id = uuid.uuid4().hex
    with st.sidebar:
        render_sidebar_brand(version)
        render_theme_selector(instance_id)
        st.divider()
        render_project_info(project)
        st.divider()
        st.html("<div class='mantis-nav-section'>Navigation</div>")
        for idx, (section_name, nav_items) in enumerate(get_nav_sections()):
            render_navigation_section(section_name, nav_items, current_page, world_focus, idx < 2, slugify, instance_id)
        render_project_actions(project, save_project_callback, close_project_callback, instance_id)
        render_debug_panel(instance_id)


__all__ = ["render_enhanced_sidebar"]
