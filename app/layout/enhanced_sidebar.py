"""
Enhanced Sidebar Component for Mantis Studio

This module provides a redesigned sidebar with:
- Improved visual hierarchy
- Better navigation grouping
- Enhanced active states
- Smooth animations
- Better spacing and alignment
"""

from __future__ import annotations
from typing import Any, Callable, Optional
import streamlit as st


def render_sidebar_brand(version: str) -> None:
    """Render the sidebar brand section with app name and version.
    
    Args:
        version: Application version string
    """
    st.html('<div class="mantis-sidebar-brand mantis-sidebar-brand--modern">')
    st.image("assets/mantis_logo_trans.png", use_container_width=True)
    st.html(
        f"""
        <div class="mantis-sidebar-meta">
            <span class="mantis-sidebar-version">Version {version}</span>
        </div>
        <div class="mantis-sidebar-divider"></div>
        </div>
        """
    )


def render_theme_selector(key_scope: Callable) -> None:
    """Render theme selection dropdown with improved styling.
    
    Args:
        key_scope: Key scope context manager for unique keys
    """
    st.html("<div class='mantis-nav-section'>Appearance</div>")
    with key_scope("theme_selector"):
        st.selectbox(
            "Theme",
            ["Dark", "Light"],
            key="ui_theme",
            label_visibility="collapsed",
        )


def render_project_info(project: Optional[Any]) -> None:
    """Render current project information card.
    
    Args:
        project: Current project object or None
    """
    st.html("<div class='mantis-nav-section'>Current Project</div>")
    
    if project:
        word_count = project.get_total_word_count()
        word_count_str = f"{word_count:,}" if word_count else "0"
        
        st.html(
            f"""
            <div style="
                background: var(--mantis-surface-alt);
                border: 1px solid var(--mantis-border);
                border-radius: var(--mantis-radius-lg);
                padding: 12px 14px;
                margin-bottom: 8px;
            ">
                <div style="
                    font-weight: 600;
                    font-size: 14px;
                    color: var(--mantis-text);
                    margin-bottom: 6px;
                ">
                    {project.title}
                </div>
                <div style="
                    font-size: 12px;
                    color: var(--mantis-text-muted);
                    display: flex;
                    align-items: center;
                    gap: 6px;
                ">
                    <span>📚</span>
                    <span>{word_count_str} words</span>
                </div>
            </div>
            """
        )
    else:
        st.html(
            """
            <div style="
                background: var(--mantis-surface-sunken);
                border: 1px solid var(--mantis-border-light);
                border-radius: var(--mantis-radius-md);
                padding: 10px 12px;
                margin-bottom: 8px;
                text-align: center;
            ">
                <div style="
                    font-size: 13px;
                    color: var(--mantis-text-muted);
                ">
                    No project loaded
                </div>
            </div>
            """
        )


def render_navigation_section(
    section_name: str,
    nav_items: list,
    current_page: str,
    world_focus: str,
    expanded: bool,
    key_scope: Callable,
    slugify: Callable,
) -> None:
    """Render a navigation section with improved styling.
    
    Args:
        section_name: Section title
        nav_items: List of (label, target, icon) tuples
        current_page: Current active page key
        world_focus: Current world bible focus tab
        expanded: Whether section should be expanded by default
        key_scope: Key scope context manager
        slugify: Function to slugify strings for keys
    """
    with st.expander(section_name, expanded=expanded):
        for label, target, icon in nav_items:
            # Determine active state
            if target == "memory":
                is_active = current_page == "world" and world_focus == "Memory"
            elif target == "insights":
                is_active = current_page == "world" and world_focus == "Insights"
            elif target == "legal":
                is_active = current_page in {
                    "legal", "terms", "privacy", "copyright", "cookie", "help"
                }
            else:
                is_active = current_page == target
            
            # Navigation button
            button_label = f"{icon} {label}"
            button_key = f"nav_{target}_{slugify(label)}"
            
            with key_scope(button_key):
                if st.button(
                    button_label,
                    key=button_key,
                    use_container_width=True,
                    disabled=is_active,
                    type="primary" if is_active else "secondary",
                ):
                    # Handle routing
                    if target == "memory":
                        st.session_state.world_focus_tab = "Memory"
                        st.session_state.page = "world"
                    elif target == "insights":
                        st.session_state.world_focus_tab = "Insights"
                        st.session_state.page = "world"
                    else:
                        st.session_state.page = target
                    st.rerun()


def render_project_actions(
    project: Optional[Any],
    key_scope: Callable,
    save_callback: Callable,
    close_callback: Callable,
) -> None:
    """Render project save/close action buttons.
    
    Args:
        project: Current project or None
        key_scope: Key scope context manager
        save_callback: Function to call when saving
        close_callback: Function to call when closing
    """
    if not project:
        return
    
    st.divider()
    
    st.html("<div class='mantis-nav-section'>Project Actions</div>")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with key_scope("sidebar_save_btn"):
            if st.button(
                "💾 Save",
                key="sidebar_save_project",
                type="primary",
                use_container_width=True,
                help="Save all changes to this project"
            ):
                try:
                    save_callback()
                    st.toast("✓ Project saved successfully", icon="✅")
                except Exception as e:
                    st.toast(f"⚠ Save failed: {str(e)}", icon="⚠")
    
    with col2:
        with key_scope("sidebar_close_btn"):
            if st.button(
                "✖ Close",
                key="sidebar_close_project",
                use_container_width=True,
                help="Save and close the current project"
            ):
                close_callback()


def render_debug_panel(key_scope: Callable) -> None:
    """Render debug panel for troubleshooting.
    
    Args:
        key_scope: Key scope context manager
    """
    import time
    import sys
    
    st.divider()
    st.html("<div class='mantis-nav-section'>Debug Tools</div>")
    
    with st.expander("📊 Session State", expanded=False):
        st.caption(f"**Current Page:** {st.session_state.get('page', 'unknown')}")
        st.caption(f"**Initialized:** {st.session_state.get('initialized', False)}")
        st.caption(f"**Project Loaded:** {st.session_state.project is not None}")
        
        if st.session_state.project:
            st.caption(f"  - Title: {st.session_state.project.title}")
            st.caption(f"  - Path: {st.session_state.project.filepath}")
        
        last_action = st.session_state.get("last_action") or "—"
        last_action_ts = st.session_state.get("last_action_ts")
        if last_action_ts:
            st.caption(f"**Last Action:** {last_action} ({time.strftime('%H:%M:%S', time.localtime(last_action_ts))})")
        else:
            st.caption(f"**Last Action:** {last_action}")
        
        last_exception = st.session_state.get("last_exception") or "—"
        st.caption(f"**Last Exception:** {last_exception}")
    
    with st.expander("🔧 System Info", expanded=False):
        st.caption(f"**Python:** {sys.version.split()[0]}")
        st.caption(f"**Streamlit:** {st.__version__}")
        
        from app.config.settings import AppConfig
        st.caption(f"**App Version:** {AppConfig.VERSION}")
        st.caption(f"**Projects Dir:** {AppConfig.PROJECTS_DIR}")
        st.caption(f"**Config Path:** {AppConfig.CONFIG_PATH}")
    
    with st.expander("📝 Session Keys", expanded=False):
        keys = sorted([k for k in st.session_state.keys() if not k.startswith("_")])
        st.caption(f"Total: {len(keys)} keys")
        for key in keys[:15]:  # Show first 15 keys
            value = st.session_state.get(key)
            value_str = str(value)[:40] if value is not None else "None"
            st.caption(f"- {key}: {value_str}")
        if len(keys) > 15:
            st.caption(f"... and {len(keys) - 15} more")
    
    # Debug actions
    col1, col2 = st.columns(2)
    with col1:
        with key_scope("debug_rerun"):
            if st.button("🔄 Rerun", use_container_width=True):
                st.rerun()
    
    with col2:
        with key_scope("debug_clear"):
            if st.button("🗑️ Clear State", use_container_width=True):
                # Clear only user-defined keys
                keys_to_clear = [k for k in st.session_state.keys() if not k.startswith("_")]
                for key in keys_to_clear:
                    del st.session_state[key]
                st.toast(f"Cleared {len(keys_to_clear)} keys")
                st.rerun()


def render_enhanced_sidebar(
    version: str,
    project: Optional[Any],
    current_page: str,
    world_focus: str,
    debug_enabled: bool,
    key_scope: Callable,
    slugify: Callable,
    save_project_callback: Callable,
    close_project_callback: Callable,
) -> None:
    """Render the complete enhanced sidebar.
    
    Args:
        version: App version string
        project: Current project or None
        current_page: Current active page key
        world_focus: World bible focus tab
        debug_enabled: Whether debug mode is enabled
        key_scope: Key scope context manager
        slugify: String slugify function
        save_project_callback: Callback for saving project
        close_project_callback: Callback for closing project
    """
    from app.utils.navigation import get_nav_sections
    
    with st.sidebar:
        with key_scope("sidebar"):
            # Brand section
            render_sidebar_brand(version)
            
            # Theme selector
            render_theme_selector(key_scope)
            
            # Debug mode toggle
            with st.expander("🔧 Advanced", expanded=False):
                with key_scope("debug_toggle"):
                    st.checkbox(
                        "Enable Debug Mode",
                        key="debug",
                        help="Show detailed debugging information and logs"
                    )
                    if st.session_state.debug:
                        st.caption("✓ Debug mode active")
                        st.caption("Check terminal for detailed logs")
            
            st.divider()
            
            # Current project info
            render_project_info(project)
            
            st.divider()
            
            # Navigation sections
            st.html("<div class='mantis-nav-section'>Navigation</div>")
            
            nav_sections = get_nav_sections()
            for section_idx, (section_name, nav_items) in enumerate(nav_sections):
                render_navigation_section(
                    section_name=section_name,
                    nav_items=nav_items,
                    current_page=current_page,
                    world_focus=world_focus,
                    expanded=section_idx < 2,  # Expand first two sections by default
                    key_scope=key_scope,
                    slugify=slugify,
                )
            
            # Project actions
            render_project_actions(
                project=project,
                key_scope=key_scope,
                save_callback=save_project_callback,
                close_callback=close_project_callback,
            )
            
            # Debug panel
            if debug_enabled:
                render_debug_panel(key_scope)


__all__ = [
    "render_enhanced_sidebar",
    "render_sidebar_brand",
    "render_theme_selector",
    "render_project_info",
    "render_navigation_section",
    "render_project_actions",
    "render_debug_panel",
]
