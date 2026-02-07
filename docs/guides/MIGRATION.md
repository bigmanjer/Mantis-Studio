# Migration Guide: Recommended Directory Structure

This document describes the migration from the old `mantis/` based structure to the new recommended `app/` structure as outlined in README Section 9A.

## Overview

The repository has been reorganized to follow a cleaner, more maintainable architecture:

**Old Structure (mantis/)** → **New Structure (app/)**

## What Changed

### Directory Mapping

| Old Location | New Location | Status |
|-------------|--------------|--------|
| `mantis/router.py` | `app/router.py` | ✅ Migrated |
| `mantis/state/session.py` | `app/state.py` | ✅ Migrated |
| `mantis/ui/pages/home.py` | `app/views/dashboard.py` | ✅ Migrated |
| `mantis/ui/pages/chapters.py` | `app/views/editor.py` | ✅ Migrated |
| `mantis/ui/pages/world.py` | `app/views/world_bible.py` | ✅ Migrated |
| `mantis/ui/pages/*.py` | `app/views/*.py` | ✅ Migrated |
| `mantis/ui/layout.py` | `app/layout/styles.py` | ✅ Migrated |
| `mantis/ui/components/ui.py` | `app/components/buttons.py` | ✅ Migrated |
| `mantis/services/auth.py` | `app/services/auth.py` | ✅ Copied |
| `mantis/services/llm.py` | `app/services/ai.py` | ✅ Copied |
| `mantis/core/storage.py` | `app/services/storage.py` | ✅ Copied |
| `mantis/core/export.py` | `app/services/export.py` | ✅ Copied |
| `mantis/core/models.py` | `app/services/projects.py` | ✅ Copied |
| - | `app/layout/sidebar.py` | 📝 Placeholder |
| - | `app/layout/header.py` | 📝 Placeholder |
| - | `app/components/forms.py` | 📝 Placeholder |
| - | `app/components/editors.py` | 📝 Placeholder |

### Import Changes

#### Before (Old)
```python
from mantis.router import get_routes, resolve_route
from mantis.ui.pages.home import render_home
from mantis.services.llm import AIEngine
```

#### After (New)
```python
from app.router import get_routes, resolve_route
from app.views.dashboard import render_home
from app.services.ai import AIEngine
```

## Backward Compatibility

The new structure **maintains backward compatibility** with existing code:

1. **mantis/ directory still exists** - All existing imports continue to work
2. **app/components/ui.py** - Provides fallback to mantis/ui/components/ui.py if needed
3. **Dual structure** - Both mantis/ and app/ directories coexist temporarily

## Migration Strategy

### Phase 1: Structure Creation (✅ Complete)
- Created `app/` directory with recommended structure
- Copied/moved files to new locations
- Updated internal imports within app/
- Maintained backward compatibility

### Phase 2: Future Extraction (Planned)
- Extract render functions from `app/main.py` to view files
- Extract sidebar/header logic to layout files
- Move business logic to service files
- Update all imports to use `app/` instead of `mantis/`

### Phase 3: Deprecation (Future)
- Mark `mantis/` imports as deprecated
- Provide migration warnings
- Update all code to use new structure

### Phase 4: Removal (Future)
- Remove `mantis/` directory entirely
- Clean up backward compatibility shims

## Current State

✅ **Working and Tested**
- New directory structure created
- Files organized per specification
- Smoke tests passing
- Backward compatibility maintained

📝 **Placeholder/Future Work**
- Sidebar and header extraction
- Complete render function extraction
- Full migration of business logic
- Removal of mantis/ directory

## For Developers

### Using the New Structure

When adding new features, prefer the new structure:

```python
# ✅ Good: Use new structure
from app.views.dashboard import render_home
from app.services.ai import AIEngine
from app.components.buttons import card, primary_button

# ⚠️ Avoid: Old structure (still works but deprecated)
from mantis.ui.pages.home import render_home
from mantis.services.llm import AIEngine
```

### Adding New Views

1. Create view file in `app/views/`
2. Add route in `app/router.py`
3. Follow the pattern from existing views

### Adding New Services

1. Create service file in `app/services/`
2. Keep UI-independent business logic
3. Export public API in `app/services/__init__.py`

## Benefits

✅ **Improved Organization**: Clear separation of concerns  
✅ **Better Maintainability**: Easy to find and update code  
✅ **Scalability**: Structure supports future growth  
✅ **Developer Experience**: Faster onboarding for new contributors  
✅ **Testing**: Easier to test isolated components  

## Questions?

See `app/README.md` for detailed directory structure documentation.
