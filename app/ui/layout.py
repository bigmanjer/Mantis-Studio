"""Compatibility footer exports.

The active app shell uses ``app.layout.layout``.  This module remains for older
imports, but delegates to the single footer implementation so navigation and
scroll behavior cannot drift.
"""

from app.layout.layout import _CURRENT_YEAR, _build_footer_nav_links, render_footer

__all__ = ["_CURRENT_YEAR", "_build_footer_nav_links", "render_footer"]
