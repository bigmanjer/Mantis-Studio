"""Enhanced Sidebar Component for Mantis Studio."""
from __future__ import annotations

import html
from contextlib import contextmanager, nullcontext
from pathlib import Path
from typing import Any, Callable, Optional

import streamlit as st

from app.utils.branding_assets import resolve_asset_path


def render_sidebar_brand(version: str) -> None:
    safe_version = html.escape(str(version))
    st.html('<div class="mantis-sidebar-brand mantis-sidebar-brand--modern">')
    assets_dir = Path(__file__).resolve().parents[2] / "assets"

    lockup_path = (
        resolve_asset_path(assets_dir, "branding/mantis_lockup.png")
        or resolve_asset_path(assets_dir, "mantis_lockup.png")
    )
    wordmark_path = (
        resolve_asset_path(assets_dir, "branding/mantis_wordmark.png")
        or resolve_asset_path(assets_dir, "mantis_wordmark.png")
        or resolve_asset_path(assets_dir, "mantis_banner_dark.png")
    )
    emblem_path = (
        resolve_asset_path(assets_dir, "branding/mantis_emblem.png")
        or resolve_asset_path(assets_dir, "mantis_emblem.png")
    )

    if wordmark_path:
        st.image(str(wordmark_path), use_container_width=True)
    elif lockup_path:
        st.image(str(lockup_path), use_container_width=True)
    elif emblem_path:
        st.image(str(emblem_path), width=96)
    else:
        st.markdown("**MANTIS**")

    st.html(
        f'<div class="mantis-sidebar-meta"><span class="mantis-sidebar-version">MANTIS Studio - v{safe_version}</span></div><div class="mantis-sidebar-divider"></div></div>'
    )


def render_theme_selector(
    key_scope: Callable[[str], Any],
    sidebar_key: Callable[[str], str] = lambda name: name,
    on_theme_change: Optional[Callable[[str], None]] = None,
) -> None:
    st.html("<div class='mantis-nav-section'>Appearance</div>")
    current_theme = "Light" if str(st.session_state.get("ui_theme", "Dark")).strip().lower() == "light" else "Dark"

    def apply_theme(theme_name: str) -> None:
        existing_theme = "Light" if str(st.session_state.get("ui_theme", "Dark")).strip().lower() == "light" else "Dark"
        if existing_theme == theme_name:
            return
        st.session_state.ui_theme = theme_name
        if callable(on_theme_change):
            on_theme_change(theme_name)
        st.rerun()

    with key_scope("theme_toggle_buttons"):
        dark_col, light_col = st.columns(2)
        with dark_col:
            if st.button(
                "Dark",
                key=sidebar_key("sidebar_theme_dark"),
                type="primary" if current_theme == "Dark" else "secondary",
                use_container_width=True,
            ):
                apply_theme("Dark")
        with light_col:
            if st.button(
                "Light",
                key=sidebar_key("sidebar_theme_light"),
                type="primary" if current_theme == "Light" else "secondary",
                use_container_width=True,
            ):
                apply_theme("Light")
    st.caption("Theme applies instantly across the studio.")


def render_sidebar_controls(key_scope: Callable[[str], Any], sidebar_key: Callable[[str], str] = lambda name: name) -> None:
    st.html("<div class='mantis-nav-section'>View</div>")
    with key_scope("sidebar_controls"):
        if st.button(
            "Hide Sidebar",
            key=sidebar_key("sidebar_collapse"),
            type="secondary",
            use_container_width=True,
            help="Hide the sidebar to maximize workspace width",
        ):
            st.session_state["sidebar_collapsed"] = True
            st.rerun()


def render_project_info(project: Optional[Any]) -> None:
    st.html("<div class='mantis-nav-section'>Workspace</div>")
    if not project:
        st.html('<div class="mantis-project-chip"><div class="mantis-project-chip__title">No project loaded</div><div class="mantis-project-chip__meta">Create or open a workspace</div></div>')
        return
    safe_title = html.escape(str(project.title))
    safe_words = html.escape(f"{project.get_total_word_count():,}")
    st.html(
        f'<div class="mantis-project-chip"><div class="mantis-project-chip__title">{safe_title}</div><div class="mantis-project-chip__meta">Words: {safe_words}</div></div>'
    )


def render_navigation_section(
    section_name: str,
    nav_items: list,
    current_page: str,
    world_focus: str,
    expanded: bool,
    slugify: Callable,
    key_scope: Callable[[str], Any],
    sidebar_key: Callable[[str], str] = lambda name: name,
    on_navigate: Optional[Callable[[str], None]] = None,
) -> None:
    del world_focus
    section_slug = slugify(section_name) if callable(slugify) else str(section_name).lower().replace(" ", "_")
    with st.expander(section_name, expanded=expanded):
        for label, target, icon in nav_items:
            if target == "legal":
                is_active = current_page in {"legal", "terms", "privacy", "copyright", "cookie", "help"}
            else:
                is_active = current_page == target

            button_label = f"{icon} {label}"
            label_slug = slugify(label) if callable(slugify) else str(label).lower().replace(" ", "_")
            button_key = sidebar_key(f"nav_{section_slug}_{target}_{label_slug}")

            scope = key_scope if callable(key_scope) else (lambda _name: nullcontext())
            with scope(button_key):
                if st.button(
                    button_label,
                    key=button_key,
                    use_container_width=True,
                    disabled=is_active,
                    type="primary" if is_active else "secondary",
                ):
                    if callable(on_navigate):
                        on_navigate(target)
                    else:
                        st.session_state.page = target
                        st.session_state["_scroll_top_nonce"] = int(st.session_state.get("_scroll_top_nonce", 0)) + 1
                        st.session_state["_scroll_top_pending"] = True
                        st.rerun()


def render_project_actions(
    project: Optional[Any],
    save_callback: Callable,
    close_callback: Callable,
    key_scope: Callable[[str], Any],
    sidebar_key: Callable[[str], str] = lambda name: name,
) -> None:
    if not project:
        return

    st.divider()
    st.html("<div class='mantis-nav-section'>Project Actions</div>")

    col1, col2 = st.columns(2)

    with col1:
        with key_scope("sidebar_save_btn"):
            if st.button(
                "Save",
                key=sidebar_key("sidebar_save_project"),
                type="primary",
                use_container_width=True,
                help="Save all changes to this project",
            ):
                try:
                    save_callback()
                    st.toast("Project saved", icon="")
                except Exception as exc:
                    st.toast(f"Save failed: {str(exc)}", icon="")

    with col2:
        with key_scope("sidebar_close_btn"):
            if st.button(
                "Close",
                key=sidebar_key("sidebar_close_project"),
                use_container_width=True,
                help="Save and close the current project",
            ):
                close_callback()


def render_account_panel(
    *,
    current_username: Optional[str],
    is_guest: bool,
    on_open_auth: Optional[Callable[[], None]],
    on_logout: Optional[Callable[[], None]],
    on_open_user_settings: Optional[Callable[[], None]] = None,
    key_scope: Callable[[str], Any] = lambda _name: nullcontext(),
    sidebar_key: Callable[[str], str] = lambda name: name,
) -> None:
    if not current_username:
        return
    st.divider()
    st.html("<div class='mantis-nav-section'>Account</div>")
    if is_guest:
        st.caption("Guest session")
    else:
        st.caption(f"Signed in as {current_username}")
    if is_guest:
        with key_scope("sidebar_auth_btn"):
            if st.button(
                "Sign in / Create account",
                key=sidebar_key("sidebar_open_auth"),
                use_container_width=True,
            ):
                if callable(on_open_auth):
                    on_open_auth()
    elif callable(on_open_user_settings):
        with key_scope("sidebar_user_settings_btn"):
            if st.button(
                "User settings",
                key=sidebar_key("sidebar_user_settings"),
                use_container_width=True,
            ):
                on_open_user_settings()
    with key_scope("sidebar_logout_btn"):
        if st.button(
            "End session" if is_guest else "Sign out",
            key=sidebar_key("sidebar_sign_out"),
            use_container_width=True,
        ):
            if callable(on_logout):
                on_logout()


def render_enhanced_sidebar(
    version: str,
    project: Optional[Any],
    current_page: str,
    world_focus: str,
    debug_enabled: bool = False,
    key_scope: Callable[[str], Any] = None,
    slugify: Callable = None,
    save_project_callback: Callable = None,
    close_project_callback: Callable = None,
    on_theme_change: Optional[Callable[[str], None]] = None,
    current_username: Optional[str] = None,
    is_guest: bool = False,
    on_open_auth: Optional[Callable[[], None]] = None,
    on_logout: Optional[Callable[[], None]] = None,
    on_open_user_settings: Optional[Callable[[], None]] = None,
    on_navigate: Optional[Callable[[str], None]] = None,
) -> None:
    del debug_enabled
    from app.utils.navigation import get_nav_sections

    @contextmanager
    def scoped(scope_name: str, scope_manager: Optional[Callable[[str], Any]] = None):
        manager = scope_manager if scope_manager is not None else key_scope
        if callable(manager):
            with manager(scope_name):
                yield
            return
        with nullcontext():
            yield

    def safe_scope(scope_name: str):
        return scoped(scope_name, key_scope)

    def sidebar_key(name: str) -> str:
        return name

    with st.sidebar:
        with safe_scope("sidebar"):
            render_sidebar_brand(version)
            render_theme_selector(safe_scope, sidebar_key, on_theme_change=on_theme_change)
            render_sidebar_controls(safe_scope, sidebar_key)

            st.divider()
            render_project_info(project)
            st.divider()

            st.html("<div class='mantis-nav-section'>Navigation</div>")
            for idx, (section_name, nav_items) in enumerate(get_nav_sections()):
                render_navigation_section(
                    section_name,
                    nav_items,
                    current_page,
                    world_focus,
                    idx < 2,
                    slugify,
                    safe_scope,
                    sidebar_key,
                    on_navigate=on_navigate,
                )
            render_project_actions(project, save_project_callback, close_project_callback, key_scope, sidebar_key)
            render_account_panel(
                current_username=current_username,
                is_guest=is_guest,
                on_open_auth=on_open_auth,
                on_logout=on_logout,
                on_open_user_settings=on_open_user_settings,
                key_scope=safe_scope,
                sidebar_key=sidebar_key,
            )


__all__ = ["render_enhanced_sidebar"]
