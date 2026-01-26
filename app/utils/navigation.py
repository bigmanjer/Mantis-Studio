from typing import Dict, List, Tuple


def get_nav_config(has_project: bool) -> Tuple[List[str], Dict[str, str]]:
    if has_project:
        nav_labels = [
            "Dashboard",
            "Projects",
            "Editor",
            "Outline",
            "World Bible",
            "AI Tools",
        ]
        pmap = {
            "Dashboard": "home",
            "Projects": "projects",
            "Editor": "chapters",
            "Outline": "outline",
            "World Bible": "world",
            "AI Tools": "ai",
        }
    else:
        nav_labels = ["Dashboard", "Projects", "AI Tools"]
        pmap = {
            "Dashboard": "home",
            "Projects": "projects",
            "AI Tools": "ai",
        }
    return nav_labels, pmap
