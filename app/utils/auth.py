"""Authentication stubs for Mantis Studio.

Mantis Studio uses a local-first, single-user architecture.
These functions provide safe no-op defaults so the rest of the
application can import and call them without errors.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the current user, or ``None`` (local-first: no user accounts)."""
    return None


def is_authenticated() -> bool:
    """Return ``True`` if the user is logged in.  Always ``False`` in
    local-first mode (no user accounts)."""
    return False
