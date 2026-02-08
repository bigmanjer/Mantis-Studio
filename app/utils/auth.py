"""Authentication stubs for Mantis Studio.

User accounts are temporarily disabled. These functions provide safe
no-op defaults so the rest of the application can import and call them
without errors.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def get_current_user() -> Optional[Dict[str, Any]]:
    """Return the current user, or ``None`` when auth is disabled."""
    return None


def is_authenticated() -> bool:
    """Return ``True`` if the user is logged in.  Always ``False`` while
    user accounts are disabled."""
    return False
