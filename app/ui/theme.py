"""Legacy theme compatibility shim.

Single source of truth for runtime theming is now:
    app.ui.enhanced_theme.inject_enhanced_theme

This module is intentionally kept as a thin wrapper so any older imports
continue to work without loading a second styling system.
"""

from __future__ import annotations

from typing import Literal

from app.ui.enhanced_theme import inject_enhanced_theme


def inject_theme(theme: Literal["Dark", "Light"] = "Dark") -> None:
    """Compatibility wrapper around the unified enhanced theme injector."""
    resolved = "Light" if str(theme).strip().lower() == "light" else "Dark"
    inject_enhanced_theme(resolved)


__all__ = ["inject_theme"]

