from __future__ import annotations

from typing import Any, Dict

import streamlit as st

from mantis.core.models import Project


def queue_world_bible_suggestion(item: Dict[str, Any]) -> None:
    queue = st.session_state.setdefault("world_bible_review", [])
    key = (
        f"{Project._normalize_category(item.get('category'))}|"
        f"{Project._normalize_entity_name(item.get('name'))}|"
        f"{(item.get('description') or '').strip().lower()}|"
        f"{item.get('type', 'new')}"
    )
    existing_keys = {q.get("_key") for q in queue}
    if key in existing_keys:
        return
    item["_key"] = key
    queue.append(item)
