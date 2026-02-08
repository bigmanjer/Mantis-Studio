# 🐜 Mantis Studio

> **MANTIS** — **M**odular **A**I **N**arrative **T**ext **I**ntelligence **S**ystem

**Mantis Studio** is an all‑in‑one AI‑assisted writing and story‑development environment built with **Streamlit**. It is designed to take a project from *idea → outline → chapters → world‑building → export*, while maintaining persistent memory and structured data across sessions.


---

## 🚀 Quick Start (For First-Time Users)

**New to Mantis Studio?** Start here!

1. **[📖 Getting Started Guide](docs/guides/GETTING_STARTED.md)** ← Complete step-by-step installation and setup
2. **Prerequisites**: Python 3.10+, basic command line knowledge
3. **Installation**: `pip install -r requirements.txt` then `streamlit run app/main.py`
4. **First Project**: Use the sidebar to create a new project, build your outline, and start writing!

💡 **Just want to try it?** The app works locally without any external setup.

---

## 📚 What This Document Covers

This README explains **what the app does, how it is structured, what every major button/section is supposed to do, and how the UI flows from a user’s point of view**.

---

## 1. High‑Level Purpose

Mantis Studio is meant to replace scattered tools (notes apps, docs, AI chats, spreadsheets) with **one guided creative workspace**:

* Centralized project management
* AI‑assisted outlining and drafting
* Structured world‑building (characters, locations, lore)
* Persistent memory and insights
* Clean export for manuscripts or planning docs

The app is **state‑driven**, not page‑driven. All navigation feeds a single app shell (`app/main.py`).

---

## 2. Technology Stack

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

## 3. Application Entry & Architecture

### Entrypoint

```
app/main.py
```

This file:

* Initializes global session state
* Handles authentication gating
* Renders the global layout (sidebar + main panel)
* Routes all navigation internally (NOT Streamlit multipage routing)

---

## 4. UI Layout Overview

### A. Global Layout

**Left Sidebar**

* App branding + version
* Primary navigation buttons
* Project selector / creator

**Main Content Area**

* Changes dynamically based on selected section
* Contains all forms, editors, and AI tools

---

### B. Sidebar Navigation (Expected Behavior)

| Button                | Purpose                                           |
| --------------------- | ------------------------------------------------- |
| 🏠 **Dashboard**      | Overview of the current project status             |
| 📁 **Projects**       | Create, load, rename, or delete projects           |
| ✍️ **Write**          | High‑level story outlining and beat planning       |
| 🧩 **Editor**         | Scene‑level writing & chapter drafting             |
| 🌍 **World Bible**    | Structured lore & entities (characters, locations) |
| ⬇️ **Export**         | Generate files (DOCX / PDF / TXT)                  |
| 🤖 **AI Settings**    | Configure AI provider, model, and preferences      |

---

## 5. Section‑by‑Section Breakdown

### 5.1 Dashboard

**Intent:**
A quick snapshot of the project.

**Should Display:**

* Project name
* Completion indicators (outline %, chapters written)
* Recent activity

**Common Issues Identified:**

* Buttons not wired to state updates
* Duplicate UI components

---

### 5.2 Projects

**Purpose:** Manage creative projects.

**Core Actions:**

* ➕ Create new project
* 📂 Load existing project
* ✏️ Rename project
* 🗑️ Delete project

**Data Stored Per Project:**

* Outline
* Chapters
* World Bible entities
* AI memory / insights

---

### 5.3 Outline

**Purpose:** Define the story structure.

**Features:**

* Act / section breakdown
* Beat‑level planning
* AI‑assisted expansion

**Buttons:**

* Generate outline
* Expand section
* Save outline

---

### 5.4 Chapters / Editor

**Purpose:** Actual writing environment.

**Expected UI:**

* Chapter selector
* Rich text editor
* AI assist buttons (rewrite, expand, summarize)

**Data Flow:**

```
Outline → Chapter → Saved Draft → Export
```

---

### 5.5 World Bible

**Purpose:** Canon‑safe world building.

**Entity Types:**

* Characters
* Locations
* Organizations
* Lore / Rules

**Each Entity Stores:**

* Name
* Description
* Attributes
* Notes

This section is critical for **consistency across chapters**.

---

### 5.6 AI Settings

**Purpose:** Configure AI integration for the workspace.

**Features:**

* Select AI provider and model
* Adjust generation parameters (temperature, length)
* Manage API keys and connection settings
* Access AI utilities: rewrite, summarize, brainstorm, tone adjustment

These tools operate on **selected text or context**, not blindly.

---

### 5.7 Export

**Purpose:** Produce usable outputs.

**Formats:**

* TXT
* DOCX
* PDF (planned)

**Export Scope:**

* Single chapter
* Full manuscript
* Outline only

---

### 5.8 Legal

The All Policies page provides access to all policy documents stored in the `legal/` directory:

| Document | File |
| -------- | ---- |
| Terms of Service | `legal/terms.md` |
| Privacy Policy | `legal/privacy.md` |
| Copyright | `legal/copyright.md` |
| Cookie Policy | `legal/cookie.md` |
| Brand & IP Clarity | `legal/Brand_ip_Clarity.md` |
| Trademark Path | `legal/Trademark_Path.md` |
| Help | `legal/help.md` |
| Contact | `legal/contact.md` |

Accessible via footer links or the All Policies page.

---

## 6. Recent Improvements (Version 87.0)

### ✅ User Experience Enhancements

**New Documentation:**
- ✨ Comprehensive [Getting Started Guide](docs/guides/GETTING_STARTED.md) added
  - Step-by-step installation for all platforms (Windows/Mac/Linux)
  - First project walkthrough
  - AI setup instructions with screenshots
  - Troubleshooting section for common issues
  - FAQ for new users

**README Improvements:**
- 🚀 Added Quick Start section at the top for impatient users
- 📖 Clear prerequisites and installation steps
- 🔗 Prominent links to detailed guides

**In-App Improvements:**
- 👋 First-time welcome screen on Dashboard
  - Clear getting started instructions
  - Quick tips for navigation
  - Direct link to create first project
- 💡 Context-aware help tooltips throughout the app
- 📝 Better descriptions for confusing features (World Bible, etc.)

### 🎯 What Changed

**For First-Time Users:**
1. **Before**: Confusing empty dashboard with no guidance
2. **After**: Friendly welcome message with clear next steps

**Documentation:**
1. **Before**: README was technical and developer-focused
2. **After**: Quick Start section + dedicated Getting Started guide for writers

**Navigation:**
1. **Before**: No explanation of what "World Bible" or other features do
2. **After**: Improved descriptions and contextual help

---

## 7. Known Issues & Planned Improvements

### Current Limitations

* Some AI features are experimental
* View files in `app/views/` are thin wrappers; render logic still lives in `app/main.py` (see `app/README.md` for migration status)

### Recommended Next Steps for Contributors

1. Add in-app tutorial/walkthrough mode
2. Create sample projects for users to explore
3. Add keyboard shortcuts reference
4. Improve error messages to be more helpful
5. Add video tutorials for key workflows

---

## 8. Versioning System

* **Current Version**: 87.0 (stored in `VERSION.txt`)
* **Version Format**: `MAJOR.MINOR` (e.g., 87.0, 87.1, 88.0)

### Versioning Rules

The version increments with each merge following these rules:

1. **Minor version** increments by 1 on each merged pull request to `main`
   - Example: 87.0 → 87.1 → 87.2
   - Rolls over at 10: 87.9 → 88.0

2. **Major bumps** are handled via the Version Bump workflow dispatch inputs

3. **Manual updates** to VERSION.txt are reflected immediately in the UI

### How It Works

* Version is read from `VERSION.txt` at startup
* Can be overridden with `MANTIS_APP_VERSION` environment variable
* Displayed in UI header for transparency
* The Version Bump GitHub Action bumps patch versions on merge
* Use `python scripts/bump_version.py` to increment the patch version locally

### Manual Version Bump

To bump the patch version for the next release:

```bash
python scripts/bump_version.py
```

For minor or major bumps, use the Version Bump workflow dispatch inputs.

---

## 9. Who This App Is For

* Novelists
* Screenwriters
* Game writers
* World‑builders
* AI‑assisted creative workflows

---

## 9A. Repository Organization (Current Architecture)

The codebase follows a **single-entry, state-driven architecture** as outlined below. See `app/README.md` for migration status and future enhancements.

### ✅ Directory Structure

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
├── docs/                    # Documentation (see Section 11)
├── legal/                   # Policy documents (see Section 5.8)
├── scripts/                 # Utility scripts (see Section 12)
├── tests/                   # Automated tests
├── assets/                  # Brand assets & CSS
│
├── VERSION.txt
├── requirements.txt
├── LICENSE.md
└── Mantis_Launcher.bat      # Windows launcher
```

### Design Principles

* Eliminates duplicate logic
* Prevents buttons from silently failing
* Makes debugging predictable
* Allows contributors to understand the app quickly
* Scales cleanly as features grow

---

## 10. Getting Started & Next Steps

### 👋 New Users
**First time here?** Check out the **[Getting Started Guide](docs/guides/GETTING_STARTED.md)** for:
- Step-by-step installation
- Your first project walkthrough  
- AI setup instructions
- Troubleshooting help

### 🔧 For Developers
Recommended technical improvements:

1. Extract render logic from `app/main.py` into respective view files
2. Move business logic from `app/main.py` to service modules
3. Normalize session state schema
4. Polish UI spacing, hierarchy, and feedback states

---

## 11. Documentation

Additional documentation lives in the `docs/` directory:

| Document | Path |
| -------- | ---- |
| Getting Started Guide | [`docs/guides/GETTING_STARTED.md`](docs/guides/GETTING_STARTED.md) |
| Migration Guide | [`docs/guides/MIGRATION.md`](docs/guides/MIGRATION.md) |
| Repository Structure | [`docs/architecture/REPOSITORY_STRUCTURE.md`](docs/architecture/REPOSITORY_STRUCTURE.md) |
| Design System | [`docs/design/DESIGN_SYSTEM.md`](docs/design/DESIGN_SYSTEM.md) |
| Navigation & IA Spec | [`docs/design/IA_NAV_SPEC.md`](docs/design/IA_NAV_SPEC.md) |
| UX Audit | [`docs/design/ux-audit.md`](docs/design/ux-audit.md) |
| Footer Design Spec | [`docs/footer-design-spec.md`](docs/footer-design-spec.md) |
| Smoke Test Runbook | [`docs/runbooks/SMOKE_TEST.md`](docs/runbooks/SMOKE_TEST.md) |
| App Architecture | [`app/README.md`](app/README.md) |

---

## 12. Utility Scripts

Helper scripts are located in the `scripts/` directory:

| Script | Purpose |
| ------ | ------- |
| `scripts/bump_version.py` | Increment the patch version in `VERSION.txt` |
| `scripts/healthcheck.py` | Run a basic health check on the application |
| `scripts/smoke_test.py` | Execute smoke tests to verify core functionality |

**Windows users** can also launch the app with `Mantis_Launcher.bat`, which handles dependency checks, Ollama AI detection, and starts Streamlit automatically.

---

## 13. Project Vision

Mantis Studio aims to be a **professional‑grade creative OS**, not just another AI chat wrapper.

The foundation is solid — the next step is tightening execution.

---

*Maintained by the Mantis Studio project.*
