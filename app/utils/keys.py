from __future__ import annotations

import re
from typing import Optional


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_]+", "_", (value or "").lower()).strip("_")
    return cleaned or "key"


def ui_key(*parts: Optional[str]) -> str:
    """
    Build a stable Streamlit widget key from multiple parts.

    Uses a consistent slugification strategy so keys remain predictable
    across reruns and modules.
    """
    cleaned_parts = [_slugify(str(part)) for part in parts if part]
    return "__".join(cleaned_parts) or "key"


def scoped_key(scope: str, *parts: Optional[str]) -> str:
    return ui_key(scope, *parts)
