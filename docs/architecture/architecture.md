# Architecture Documentation

This document provides an overview of the Mantis Studio architecture and links to detailed technical documentation.

---

## Overview

Mantis Studio follows a **single-entry, state-driven architecture** built on Streamlit. The application is designed to be:

- **Modular** - Clear separation of concerns
- **Maintainable** - Predictable structure and patterns
- **Scalable** - Easy to add new features
- **Testable** - Comprehensive test coverage

---

## Technology Stack

| Layer | Technology |
| ----- | ---------- |
| **Language** | Python 3.10+ |
| **UI Framework** | Streamlit ≥ 1.30.0 |
| **State Management** | Streamlit Session State for routing and persistence |
| **Data & Visualization** | Pandas, Plotly, Pillow |
| **HTTP** | Requests |
| **Backend (optional)** | Supabase ≥ 2.5.0 |
| **Configuration** | python‑dotenv |
| **Storage** | Local JSON / serialized storage (project data) |
| **Auth (optional)** | OIDC — Google / Microsoft / Apple (if configured) |
| **CI/CD** | GitHub Actions for version bumping |

---

## High-Level Architecture

### Single Entry Point

```
app/main.py
```

This file:
- Initializes global session state
- Handles authentication gating
- Renders the global layout (sidebar + main panel)
- Routes all navigation internally (NOT Streamlit multipage routing)

### State-Driven Navigation

The app uses `st.session_state.page` for routing rather than Streamlit's built-in multipage system. This provides:
- Centralized routing logic
- Consistent state management
- Predictable navigation flow
- Easy debugging

---

## Directory Structure

```
Mantis-Studio/
│
├── app/main.py              # Single entrypoint (routing + layout)
│
├── app/
│   ├── state.py             # Session state schema + defaults
│   ├── router.py            # Central navigation logic
│   ├── app_context.py       # App context reference
│   │
│   ├── layout/
│   │   ├── sidebar.py       # Sidebar UI
│   │   ├── header.py        # App header + version
│   │   └── layout.py        # Layout utilities
│   │
│   ├── views/               # UI screens (one file each)
│   │   ├── dashboard.py
│   │   ├── projects.py
│   │   ├── outline.py
│   │   ├── editor.py
│   │   ├── world_bible.py
│   │   ├── ai_tools.py
│   │   ├── export.py
│   │   └── legal.py
│   │
│   ├── components/          # Reusable UI blocks
│   │   ├── buttons.py
│   │   ├── forms.py
│   │   ├── editors.py
│   │   └── ui.py
│   │
│   ├── services/            # Business logic (no UI)
│   │   ├── projects.py
│   │   ├── storage.py
│   │   ├── ai.py
│   │   ├── export.py
│   │   ├── world_bible.py
│   │   ├── world_bible_db.py
│   │   └── world_bible_merge.py
│   │
│   ├── ui/                  # Additional UI utilities
│   │   ├── components.py
│   │   ├── layout.py
│   │   └── theme.py
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   └── utils/
│       ├── versioning.py
│       ├── helpers.py
│       ├── auth.py
│       ├── keys.py
│       └── navigation.py    # Centralized NAV_ITEMS config
│
├── docs/                    # Documentation
├── legal/                   # Policy documents
├── scripts/                 # Utility scripts
├── tests/                   # Automated tests
├── assets/                  # Brand assets & CSS
│
├── VERSION.txt
├── requirements.txt
├── LICENSE.md
└── Mantis_Launcher.bat      # Windows launcher
```

---

## Design Principles

1. **Single Responsibility** - Each module has one clear purpose
2. **Separation of Concerns** - UI, business logic, and data are separated
3. **State-Driven** - Session state is the source of truth
4. **No Duplicate Logic** - Shared functionality lives in services
5. **Testable** - Business logic can be tested independently of UI

---

## Detailed Documentation

For in-depth technical documentation, see:

### Guides for Developers

- **[Contributing Guide](../guides/CONTRIBUTING.md)** - Development setup, code style, and workflow

### Design & UX

- **[Design System](../design/DESIGN_SYSTEM.md)** - Design tokens, colors, typography, navigation spec, footer design, and UX audit

### Testing

- **[Testing Guide](../guides/testing.md)** - Comprehensive testing documentation
- **[Smoke Test Runbook](../runbooks/SMOKE_TEST.md)** - QA checklist

---

## Key Architectural Patterns

### 1. View Layer Pattern

Views are responsible for rendering UI components:

```python
# app/views/dashboard.py
def render_dashboard():
    """Render the dashboard view."""
    st.title("Dashboard")
    # Render UI components
```

### 2. Service Layer Pattern

Services contain business logic with no UI dependencies:

```python
# app/services/projects.py
class Project:
    """Project data model and operations."""
    
    def save(self, path: str) -> None:
        """Save project to file."""
        # Business logic here
```

### 3. Component Pattern

Reusable UI components that can be used across views:

```python
# app/components/buttons.py
def action_button(label: str, key: str) -> bool:
    """Render a styled action button."""
    return st.button(label, key=key, type="primary")
```

### 4. Router Pattern

Centralized navigation logic:

```python
# app/router.py
def route_to_page(page_name: str) -> None:
    """Navigate to a specific page."""
    st.session_state.page = page_name
    st.rerun()
```

---

## State Management

### Session State Schema

The application uses Streamlit's session state with a defined schema:

```python
# Core state
st.session_state.page          # Current page/route
st.session_state.user          # Current user (if authenticated)
st.session_state.current_project  # Active project

# Project data
st.session_state.projects      # List of available projects
st.session_state.chapters      # Current project chapters
st.session_state.entities      # World Bible entities

# AI configuration
st.session_state.ai_provider   # Selected AI provider
st.session_state.ai_model      # Selected AI model
st.session_state.api_keys      # API keys for AI services
```

---

## Data Flow

```
User Input
    ↓
View Layer (app/views/)
    ↓
Service Layer (app/services/)
    ↓
Data Storage (JSON files / Database)
    ↓
Service Layer
    ↓
View Layer
    ↓
UI Update
```

---

## Extension Points

The architecture supports extension through:

1. **New Views** - Add files to `app/views/` and register in router
2. **New Services** - Add files to `app/services/` for business logic
3. **New Components** - Add reusable UI to `app/components/`
4. **Plugins** (planned) - Dynamic loading from `plugins/` directory

---

## Performance Considerations

- **Caching** - Use `@st.cache_data` for expensive operations
- **Lazy Loading** - Load data only when needed
- **Batch Updates** - Minimize session state writes
- **Efficient Rendering** - Conditional rendering to reduce reruns

---

## Security

- **API Key Storage** - Keys stored in session state and config file
- **Input Validation** - All user inputs are validated
- **File Access** - Restricted to project directories
- **Authentication** (optional) - OIDC integration available

---

## Future Architecture Plans

### Short Term (0-2 months)
- Complete view extraction from `app/main.py`
- Standardize error handling
- Add first-run onboarding wizard

### Mid Term (2-6 months)
- Introduce snapshot-based version history
- Add pipeline automation
- Begin plugin/extension system design

### Long Term (6-12 months)
- Collaboration + cloud sync layer
- Marketplace-ready plugin ecosystem
- Deep integrations (Notion, Google Docs, Obsidian)

---

## Resources

- **[README](../../README.md)** - Project overview
- **[Contributing](../guides/CONTRIBUTING.md)** - How to contribute
- **[Testing](../guides/testing.md)** - Testing guide
- **[Documentation Index](../guides/index.md)** - Complete documentation

---

*For more detailed architectural documentation, see the [architecture docs](.) directory.*
