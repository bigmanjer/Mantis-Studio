from __future__ import annotations

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Centralized navigation configuration — single source of truth.
#
# To add, remove, or reorder a navigation item, edit only NAV_ITEMS below.
# Both the sidebar and the footer are generated from this list, so changes
# here automatically propagate everywhere.
#
# Each entry is a tuple of (label, page_key, icon):
#   label    – display name shown in sidebar buttons and footer links
#   page_key – the value stored in st.session_state.page for routing
#   icon     – emoji shown in the sidebar button
# ---------------------------------------------------------------------------
NAV_ITEMS: List[Tuple[str, str, str]] = [
    ("Dashboard", "home", "🏠"),
    ("Projects", "projects", "📁"),
    ("Write", "outline", "✍️"),
    ("Editor", "chapters", "🧩"),
    ("World Bible", "world", "🌍"),
    ("Export", "export", "⬇️"),
    ("AI Settings", "ai", "🤖"),
]

# Extended map includes entries that don't appear in the main nav bar
# (e.g. Memory and Insights route to the World Bible page with a focus tab).
_EXTENDED_MAP: Dict[str, str] = {
    "Memory": "memory",
    "Insights": "insights",
}

# ---------------------------------------------------------------------------
# Derived helpers – keep in sync automatically with NAV_ITEMS.
# ---------------------------------------------------------------------------

_DEFAULT_NAV_LABELS: List[str] = [label for label, _, _ in NAV_ITEMS]

_DEFAULT_MAP: Dict[str, str] = {label: key for label, key, _ in NAV_ITEMS}
_DEFAULT_MAP.update(_EXTENDED_MAP)


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    try:
        from app.router import get_nav_config as _get_nav_config

        return _get_nav_config(has_project)
    except Exception:
        return list(_DEFAULT_NAV_LABELS), dict(_DEFAULT_MAP)


def get_nav_items() -> List[Tuple[str, str, str]]:
    """Return the canonical ordered list of (label, page_key, icon) tuples.

    Use this to build both sidebar buttons and footer navigation links so
    they always stay in sync.
    """
    return list(NAV_ITEMS)


__all__ = ["NAV_ITEMS", "get_nav_config", "get_nav_items"]
