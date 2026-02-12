"""UI component exports for backward compatibility.

This module provides backward compatibility by re-exporting components
from the new location in buttons.py.
"""
try:
    from app.components.buttons import *  # noqa: F403
    import app.components.buttons as _buttons
    __all__ = [name for name in dir(_buttons) if not name.startswith("_")]
except ImportError:
    # Fallback to old location for compatibility
    try:
        from mantis.ui.components.ui import *  # noqa: F403
        import mantis.ui.components.ui as _ui
        __all__ = [name for name in dir(_ui) if not name.startswith("_")]
    except ImportError:
        __all__ = []

