from __future__ import annotations

from typing import Dict, List, Tuple

_DEFAULT_NAV_LABELS: List[str] = [
    "Dashboard",
    "Projects",
    "Outline",
    "Editor",
    "World Bible",
    "Export",
    "AI Tools",
]

_DEFAULT_MAP: Dict[str, str] = {
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


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    try:
        from app.router import get_nav_config as _get_nav_config

        return _get_nav_config(has_project)
    except Exception:
        return list(_DEFAULT_NAV_LABELS), dict(_DEFAULT_MAP)

__all__ = ["get_nav_config"]
