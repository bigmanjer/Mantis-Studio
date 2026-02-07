# Repository Structure

## Overview

MANTIS Studio follows a single-entry, state-driven architecture with clear separation of concerns.

## Top-Level Directory Layout

```
Mantis-Studio/
├── app/                           # Streamlit UI + services
│   ├── main.py                    # Single Streamlit entrypoint
│   ├── state.py                   # Session state schema + defaults
│   ├── router.py                  # Central navigation logic
│   ├── layout/                    # Layout components (sidebar, header, styles)
│   ├── views/                     # UI screens (one file per feature)
│   ├── components/                # Reusable UI blocks
│   ├── services/                  # Business logic (no UI)
│   ├── ui/                        # Theme + footer rendering
│   └── utils/                     # Utilities (versioning, helpers, navigation)
├── assets/                        # Static images + CSS
├── docs/                          # All documentation (organized by domain)
│   ├── architecture/              # Repository structure docs
│   ├── design/                    # Design system + UX specs
│   ├── guides/                    # User-facing guides
│   └── runbooks/                  # Operational runbooks
├── legal/                         # Legal policy documents
├── scripts/                       # Maintenance utilities
├── requirements.txt               # Python dependencies
├── VERSION.txt                    # Current app version
├── LICENSE.md                     # License
└── README.md                      # Main project documentation
```

## Purpose of Each Directory

| Directory | Purpose |
|-----------|---------|
| `app/` | Active Streamlit codebase: views, services, layout, components |
| `assets/` | Logos, UI images, and shared CSS |
| `docs/` | Technical and user documentation grouped by topic |
| `legal/` | Terms, privacy, copyright, and IP documentation |
| `scripts/` | Developer utilities (healthcheck, smoke test, version bump) |

## App Directory Detail

```
app/
├── main.py                 # Single entrypoint (routing + layout)
├── state.py                # Session state schema + defaults
├── router.py               # Central navigation logic
├── layout/
│   ├── sidebar.py          # Sidebar UI
│   ├── header.py           # App header + version
│   └── styles.py           # CSS / theme helpers
├── views/
│   ├── dashboard.py        # Main dashboard
│   ├── projects.py         # Project management
│   ├── outline.py          # Story outline
│   ├── editor.py           # Chapter editor
│   ├── world_bible.py      # World Bible
│   ├── ai_tools.py         # AI configuration
│   ├── export.py           # Export functionality
│   ├── account.py          # Account management
│   └── legal.py            # Legal pages
├── components/
│   ├── buttons.py          # Button components and UI helpers
│   ├── forms.py            # Form components
│   └── editors.py          # Editor components
├── services/
│   ├── projects.py         # Project management logic
│   ├── storage.py          # Storage and persistence
│   ├── auth.py             # Authentication
│   ├── ai.py               # AI/LLM services
│   └── export.py           # Export logic
├── ui/
│   ├── layout.py           # Footer rendering
│   ├── theme.py            # Theme injection
│   └── components.py       # UI component helpers
└── utils/
    ├── versioning.py       # Version management
    ├── helpers.py           # Common utilities
    └── navigation.py       # Navigation helpers
```

## Design Principles

1. **Single Entry Point**: `app/main.py` is the only Streamlit entrypoint
2. **State-Driven Navigation**: Uses `st.session_state.page` for routing
3. **Separation of Concerns**: UI (views) separate from logic (services)
4. **Reusability**: Common components in `components/` directory

## Current Implementation Notes

The actual render logic resides in `app/main.py`. The view files in `app/views/` are thin wrappers that delegate to the main file's render functions. This allows the structure to provide a clear path for future refactoring while maintaining stability.

## Future Improvements

1. Extract render functions from `app/main.py` into respective view files
2. Extract sidebar/header logic to `app/layout/` modules
3. Migrate business logic from `app/main.py` to `app/services/`
4. Add a `tests/` directory with automated testing
5. Adopt `pyproject.toml` for dependency and tooling configuration
