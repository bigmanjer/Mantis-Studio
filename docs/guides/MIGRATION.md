# Migration Guide: App Directory Structure

This document describes the `app/` directory structure used by MANTIS Studio.

## Overview

The repository uses a modular `app/` structure with clear separation between views, services, components, and utilities.

## Directory Layout

| Directory | Purpose |
|-----------|---------|
| `app/state.py` | Session state schema + defaults |
| `app/router.py` | Central navigation logic |
| `app/views/` | UI screens (dashboard, projects, outline, editor, etc.) |
| `app/components/` | Reusable UI blocks (buttons, forms, editors) |
| `app/services/` | Business logic (projects, storage, auth, AI, export) |
| `app/layout/` | Layout components (sidebar, header, styles) |
| `app/ui/` | Theme injection + footer rendering |
| `app/utils/` | Utilities (versioning, helpers, navigation) |

## Import Conventions

```python
from app.router import get_routes, resolve_route
from app.views.dashboard import render_home
from app.services.ai import AIEngine
from app.components.buttons import card, primary_button
```

## Adding New Features

### Adding a New View

1. Create a view file in `app/views/`
2. Add the route in `app/router.py`
3. Add the page rendering branch in `app/main.py`'s `_render_current_page()`

### Adding a New Service

1. Create a service file in `app/services/`
2. Keep it UI-independent (no Streamlit imports in service logic)
3. Import from views as needed

## Current State

The actual render logic resides in `app/main.py` for stability. View files in `app/views/` are thin wrappers that delegate to the main file's render functions. This provides a clear path for future extraction without breaking existing functionality.

## For More Details

See [REPOSITORY_STRUCTURE.md](../architecture/REPOSITORY_STRUCTURE.md) for the full directory tree and design principles.
