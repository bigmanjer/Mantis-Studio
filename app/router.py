from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Tuple

from app.views.ai_tools import render_ai_settings
from app.views.editor import render_chapters
from app.views.export import render_export
from app.views.dashboard import render_home
from app.views.legal import render_legal_redirect
from app.views.outline import render_outline
from app.views.projects import render_projects
from app.views.world_bible import render_world

logger = logging.getLogger("MANTIS")

PageRenderer = Callable[[object], None]


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    """Get navigation configuration from centralized module."""
    from app.utils.navigation import NAV_ITEMS, EXTENDED_MAP

    nav_labels = [label for label, _, _ in NAV_ITEMS]
    pmap = {label: key for label, key, _ in NAV_ITEMS}
    pmap.update(EXTENDED_MAP)
    return nav_labels, pmap


def get_routes() -> Dict[str, PageRenderer]:
    """Get all registered page routes."""
    return {
        "home": render_home,
        "projects": render_projects,
        "outline": render_outline,
        "chapters": render_chapters,
        "world": render_world,
        "export": render_export,
        "ai": render_ai_settings,
        "legal": render_legal_redirect,
        "terms": render_legal_redirect,
        "privacy": render_legal_redirect,
        "copyright": render_legal_redirect,
        "cookie": render_legal_redirect,
        "help": render_legal_redirect,
    }


def resolve_route(page_key: str) -> PageRenderer:
    """Resolve page key to renderer function with fallback to home."""
    routes = get_routes()
    return routes.get(page_key, render_home)


def render_current_page(st, ctx: Any) -> None:
    """Render the current page based on session state with error handling and fallback UI.
    
    Args:
        st: Streamlit module instance
        ctx: UI context object with utilities
    """
    try:
        # Get current page
        current_page = st.session_state.get("page", "home")
        
        # Validate page key
        if not current_page or not isinstance(current_page, str):
            logger.warning(f"Invalid page key: {current_page}, defaulting to home")
            st.session_state.page = "home"
            current_page = "home"
        
        logger.info(f"Rendering page: {current_page}")
        
        # Resolve route
        renderer = resolve_route(current_page)
        
        # Render with key scope
        with ctx.key_scope(current_page):
            try:
                renderer(ctx)
                logger.debug(f"Successfully rendered page: {current_page}")
            except Exception as render_exc:
                logger.error(f"Error rendering page {current_page}", exc_info=True)
                raise  # Re-raise to outer handler
        
        # Render footer if page loaded successfully
        try:
            from app.layout.layout import render_footer
            render_footer()
        except Exception as footer_exc:
            logger.warning(f"Failed to render footer: {footer_exc}")
            # Non-critical, continue
        
    except Exception as exc:
        # Comprehensive error handling with fallback UI
        error_msg = f"{type(exc).__name__}: {exc}"
        st.session_state["last_exception"] = error_msg
        
        logger.error("=" * 60)
        logger.error("UNHANDLED PAGE RENDERING EXCEPTION")
        logger.error("=" * 60)
        logger.error(f"Page: {st.session_state.get('page', 'unknown')}")
        logger.error(f"Error: {error_msg}")
        logger.exception("Full exception details:", exc_info=True)
        logger.error("=" * 60)
        
        # Render fallback error UI
        render_error_fallback(st, ctx, error_msg, exc)


def render_error_fallback(st, ctx: Any, error_msg: str, exc: Exception) -> None:
    """Render a comprehensive error fallback UI when page rendering fails.
    
    This ensures the app never shows a blank page.
    """
    try:
        st.error("⚠️ **Something went wrong while rendering this page.**")
        
        st.markdown("""
        ### Troubleshooting Steps:
        1. Try reloading the app (F5 or Ctrl+R)
        2. Return to the dashboard using the button below
        3. Check the terminal/logs for detailed error messages
        4. If the issue persists, please report it on GitHub with the error details
        """)
        
        # Show error details in expander
        with st.expander("🔍 Error Details (Click to expand)", expanded=False):
            st.code(error_msg, language="text")
            
            if ctx.debug_enabled():
                st.write("**Debug Mode Active - Full Stack Trace:**")
                st.exception(exc)
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 Return to Dashboard", use_container_width=True, type="primary"):
                st.session_state.page = "home"
                st.rerun()
        with col2:
            if st.button("🔄 Reload App", use_container_width=True):
                st.rerun()
                
    except Exception as fallback_exc:
        # Last resort: even the error UI failed
        logger.critical(f"Error fallback UI failed: {fallback_exc}", exc_info=True)
        try:
            # Absolute minimum UI
            st.text("Critical error - please refresh the page")
            if st.button("Refresh"):
                st.rerun()
        except Exception:
            # Nothing we can do at this point
            pass

