from typing import Dict, List, Tuple


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    nav_labels = [
        "Dashboard",
        "Projects",
        "Outline",
        "Editor",
        "World Bible",
        "Memory",
        "Insights",
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
