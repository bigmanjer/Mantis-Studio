# App Directory Structure

This directory contains the reorganized codebase following the recommended architecture from README Section 9A.

## Directory Layout

```
app/
├── state.py              # Session state schema + defaults
├── router.py             # Central navigation logic
│
├── layout/               # Layout components
│   ├── sidebar.py        # Sidebar UI
│   ├── header.py         # App header + version
│   └── styles.py         # CSS / theme helpers
│
├── views/                # Each UI screen (one file each)
│   ├── dashboard.py      # Main dashboard (formerly home.py)
│   ├── projects.py       # Project management
│   ├── outline.py        # Story outline
│   ├── editor.py         # Chapter editor (formerly chapters.py)
│   ├── world_bible.py    # World Bible (formerly world.py)
│   ├── ai_tools.py       # AI configuration
│   ├── export.py         # Export functionality
│   ├── account.py        # Account management
│   └── legal.py          # Legal pages
│
├── components/           # Reusable UI blocks
│   ├── buttons.py        # Button components and UI helpers
│   ├── forms.py          # Form components
│   └── editors.py        # Editor components
│
├── services/             # Business logic (no UI)
│   ├── projects.py       # Project management logic
│   ├── storage.py        # Storage and persistence
│   ├── auth.py           # Authentication
│   ├── ai.py             # AI/LLM services
│   └── export.py         # Export logic
│
└── utils/
    ├── versioning.py     # Version management
    ├── helpers.py        # Common utilities
    └── navigation.py     # Navigation helpers
```

## Design Principles

1. **Single Entry Point**: `app/app_context.py` is the only entry point
2. **State-Driven Navigation**: Uses `st.session_state.page` for routing
3. **Separation of Concerns**: UI (views) separate from logic (services)
4. **Reusability**: Common components in `components/` directory
5. **Maintainability**: Clear structure makes the codebase easy to understand

## Migration Status

The directory structure has been created and organized. The following components are in place:

- ✅ Router with view mappings
- ✅ State management module
- ✅ View files (currently thin wrappers)
- ✅ Service modules (copied from mantis/)
- ✅ Component modules
- ✅ Layout modules (theme/styles)
- ✅ Utility modules

## Current Implementation

Currently, the actual render logic still resides in `app/app_context.py` for backward compatibility. 
The view files in `app/views/` are thin wrappers that delegate to the main file's render functions.

This allows the new structure to coexist with the existing implementation while providing a clear 
path for future refactoring.

## Future Enhancements

1. Extract render functions from `app/app_context.py` into respective view files
2. Move business logic from `app/app_context.py` to service modules
3. Extract layout components (sidebar, header) into layout modules
4. Deprecate and remove the `mantis/` directory once migration is complete
