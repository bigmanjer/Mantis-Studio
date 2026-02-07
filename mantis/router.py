from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from mantis.ui.pages.ai_tools import render_ai_settings
from mantis.ui.pages.chapters import render_chapters
from mantis.ui.pages.export import render_export
from mantis.ui.pages.home import render_home
from mantis.ui.pages.legal import render_legal_redirect
from mantis.ui.pages.outline import render_outline
from mantis.ui.pages.projects import render_projects
from mantis.ui.pages.world import render_world


PageRenderer = Callable[[object], None]


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    nav_labels = [
        "Dashboard",
        "Projects",
        "Outline",
        "Editor",
        "World Bible",
        "Export",
        "AI Tools",
    ]
    pmap = {
        "Dashboard": "home",
        "Projects": "projects",
        "Outline": "outline",
        "Editor": "chapters",
        "World Bible": "world",
        "Memory": "memory",
        "Insights": "insights",
        "Export": "export",
        "AI Tools": "ai",
    }
    return nav_labels, pmap


def get_routes() -> Dict[str, PageRenderer]:
    return {
        "home": render_home,
        "projects": render_projects,
        "outline": render_outline,
        "chapters": render_chapters,
        "world": render_world,
        "export": render_export,
        "ai": render_ai_settings,
        "legal": render_legal_redirect,
    }


def resolve_route(page_key: str) -> PageRenderer:
    routes = get_routes()
    return routes.get(page_key, render_home)
