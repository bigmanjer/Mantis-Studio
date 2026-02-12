from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from app.views.ai_tools import render_ai_settings
from app.views.editor import render_chapters
from app.views.export import render_export
from app.views.dashboard import render_home
from app.views.legal import render_legal_redirect
from app.views.outline import render_outline
from app.views.projects import render_projects
from app.views.world_bible import render_world


PageRenderer = Callable[[object], None]


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    # Delegate to the centralized navigation configuration so that
    # sidebar, footer, and router all stay in sync automatically.
    # To add or remove nav items edit NAV_ITEMS in app/utils/navigation.py.
    from app.utils.navigation import NAV_ITEMS, EXTENDED_MAP

    nav_labels = [label for label, _, _ in NAV_ITEMS]
    pmap = {label: key for label, key, _ in NAV_ITEMS}
    pmap.update(EXTENDED_MAP)
    return nav_labels, pmap


def get_routes() -> Dict[str, PageRenderer]:
    # Legal sub-pages (terms, privacy, etc.) are rendered by dedicated
    # functions inside app/main.py.  The router maps them to the Legal
    # Center as a fallback so resolve_route() always returns a valid
    # renderer.
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
    routes = get_routes()
    return routes.get(page_key, render_home)
