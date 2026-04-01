from __future__ import annotations

from typing import Dict, List, Tuple

NAV_ITEMS: List[Tuple[str, str, str]] = [
    ("Dashboard", "home", ""),
    ("Projects", "projects", ""),
    ("Outline", "outline", ""),
    ("Editor", "chapters", ""),
    ("World Bible", "world", ""),
    ("AI Settings", "ai", ""),
]

NAV_SECTIONS: List[Tuple[str, List[Tuple[str, str, str]]]] = [
    ("Workflow", [
        ("Dashboard", "home", ""),
        ("Projects", "projects", ""),
        ("Outline", "outline", ""),
        ("Editor", "chapters", ""),
        ("World Bible", "world", ""),
    ]),
    ("Intelligence", [
        ("Memory", "memory", ""),
        ("Insights", "insights", ""),
    ]),
    ("Settings", [
        ("AI Settings", "ai", ""),
        ("Workspace Settings", "workspace", ""),
    ]),
]

EXTENDED_MAP: Dict[str, str] = {
    "Memory": "memory",
    "Insights": "insights",
}

_DEFAULT_NAV_LABELS: List[str] = [label for label, _, _ in NAV_ITEMS]

_DEFAULT_MAP: Dict[str, str] = {label: key for label, key, _ in NAV_ITEMS}
_DEFAULT_MAP.update(EXTENDED_MAP)


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    del has_project
    return list(_DEFAULT_NAV_LABELS), dict(_DEFAULT_MAP)


def get_nav_items() -> List[Tuple[str, str, str]]:
    return list(NAV_ITEMS)


def get_nav_sections() -> List[Tuple[str, List[Tuple[str, str, str]]]]:
    return [(section, list(items)) for section, items in NAV_SECTIONS]


__all__ = [
    "NAV_ITEMS",
    "NAV_SECTIONS",
    "EXTENDED_MAP",
    "get_nav_config",
    "get_nav_items",
    "get_nav_sections",
]

