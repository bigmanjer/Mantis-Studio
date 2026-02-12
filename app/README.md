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
│   └── layout.py         # Theme tokens and footer
│
├── views/                # Each UI screen (one file each)
│   ├── dashboard.py      # Main dashboard / home
│   ├── projects.py       # Project management
│   ├── outline.py        # Story outline
│   ├── editor.py         # Chapter editor
│   ├── world_bible.py    # World Bible
│   ├── ai_tools.py       # AI configuration
│   ├── export.py         # Export functionality
│   └── legal.py          # Legal pages
│
├── components/           # Reusable UI blocks
│   ├── buttons.py        # Button components and UI helpers
│   ├── forms.py          # Form components
│   ├── editors.py        # Editor components
│   └── ui.py             # Shared UI helpers
│
├── services/             # Business logic (no UI)
│   ├── projects.py       # Project management logic
│   ├── storage.py        # Storage and persistence
│   ├── ai.py             # AI/LLM services
│   ├── export.py         # Export logic
│   ├── world_bible.py    # World bible logic
│   ├── world_bible_db.py # World bible database layer
│   └── world_bible_merge.py # World bible merge utilities
│
├── ui/                   # Additional UI utilities
│   ├── components.py     # Re-export wrapper
│   ├── layout.py         # Footer rendering
│   └── theme.py          # Theme injection
│
├── config/
│   └── settings.py       # App configuration
│
└── utils/
    ├── versioning.py     # Version management
    ├── helpers.py        # Common utilities
    ├── auth.py           # Authentication helpers
    ├── keys.py           # Widget key helpers
    └── navigation.py     # Navigation helpers
```

## Design Principles

1. **Single Entry Point**: `app/main.py` is the only entry point
2. **State-Driven Navigation**: Uses `st.session_state.page` for routing
3. **Separation of Concerns**: UI (views) separate from logic (services)
4. **Reusability**: Common components in `components/` directory
5. **Maintainability**: Clear structure makes the codebase easy to understand

## Migration Status

The directory structure is in place. The following components are active:

- ✅ Router with view mappings
- ✅ State management module
- ✅ View files (thin wrappers)
- ✅ Service modules
- ✅ Component modules
- ✅ Layout modules (theme/styles)
- ✅ Utility modules

## Current Implementation

Currently, the actual render logic resides in `app/main.py` for backward compatibility. 
The view files in `app/views/` are thin wrappers that delegate to the main file's render functions.

This allows the structure to provide a clear path for future refactoring while maintaining stability.

## Future Enhancements

1. Extract render functions from `app/main.py` into respective view files
2. Move business logic from `app/main.py` to service modules
3. Extract layout components (sidebar, header) into layout modules
