from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

from app.services.projects import Project
from app.services.world_bible_merge import classify_suggestion


def queue_world_bible_suggestion(
    item: Dict[str, Any],
    project: Optional[Project] = None,
) -> None:
    """Add an AI suggestion to the review queue.

    When *project* is provided the suggestion is first classified by the
    merge engine so that the review UI can show whether the entry will
    update an existing entity, add aliases only, or create something new.
    Duplicate suggestions (where all information is already present) are
    silently dropped.
    """
    queue = st.session_state.setdefault("world_bible_review", [])

    # --- Classify against the live project when available ---
    if project is not None:
        item = classify_suggestion(project, item)
        # Drop suggestions that contribute nothing new
        if item.get("type") == "duplicate":
            return

    # --- Build dedup key ---
    aliases = item.get("novel_aliases") or item.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = [str(aliases)]
    normalized_aliases = []
    for alias in aliases:
        clean = str(alias).strip()
        if not clean:
            continue
        normalized_aliases.append(Project._normalize_entity_name(clean))
    alias_key = ",".join(sorted({a for a in normalized_aliases if a}))
    key = (
        f"{Project._normalize_category(item.get('category'))}|"
        f"{Project._normalize_entity_name(item.get('name'))}|"
        f"{alias_key}|"
        f"{(item.get('description') or '').strip().lower()}|"
        f"{item.get('type', 'new')}"
    )
    existing_keys = {q.get("_key") for q in queue}
    if key in existing_keys:
        return
    item["_key"] = key
    queue.append(item)
