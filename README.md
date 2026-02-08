# 🐜 Mantis Studio

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

* **Python 3.10+**
* **Streamlit** (UI + state)
* **Session State** for routing and persistence
* **Local JSON / serialized storage** (project data)
* **OIDC Auth (optional)**: Google / Microsoft / Apple (if configured)
* **GitHub Actions** for version bumping

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

> Files under `/pages` are legacy or transitional and should not be relied on for core state.

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

| Button                | Purpose                                       |
| --------------------- | --------------------------------------------- |
| **Dashboard**         | Overview of the current project status        |
| **Projects**          | Create, load, rename, or delete projects      |
| **Outline**           | High‑level story structure                    |
| **Chapters / Editor** | Scene‑level writing & drafting                |
| **World Bible**       | Structured lore & entities                    |
| **AI Tools**          | Utilities like rewrite, summarize, brainstorm |
| **Export**            | Generate files (DOCX / PDF / TXT)             |
| **Legal**             | Terms, privacy, copyright (via footer)        |

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

### 5.6 AI Tools

**Purpose:** Utility layer, not the core workflow.

**Examples:**

* Rewrite text
* Tone adjustment
* Brainstorm ideas
* Summaries

These tools should operate on **selected text or context**, not blindly.

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

### 5.9 Legal

The Legal Center provides access to all policy documents:

* Terms of Service
* Privacy Policy
* Copyright
* Cookie Policy
* Brand & IP Clarity
* Trademark Path
* Contact

Accessible via footer links or the Legal Center page.

---

## 6. Recent Improvements (Version 84.7)

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
* Legacy `/pages` directory exists but is not used (can be safely ignored)

### Recommended Next Steps for Contributors

1. Add in-app tutorial/walkthrough mode
2. Create sample projects for users to explore
3. Add keyboard shortcuts reference
4. Improve error messages to be more helpful
5. Add video tutorials for key workflows

---

## 8. Versioning System

* **Current Version**: 84.7.1 (stored in `VERSION.txt`)
* **Version Format**: `MAJOR.MINOR.PATCH` (e.g., 84.7.1, 84.7.2, 84.8.0)

### Versioning Rules

The version increments with each merge following these rules:

1. **Patch version** increments by 1 on each merged pull request to `main`
   - Example: 84.7.1 → 84.7.2 → 84.7.3

2. **Minor/major bumps** are handled via the Version Bump workflow dispatch inputs

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

## 10. Getting Started & Next Steps

### 👋 New Users
**First time here?** Check out the **[Getting Started Guide](docs/guides/GETTING_STARTED.md)** for:
- Step-by-step installation
- Your first project walkthrough  
- AI setup instructions
- Troubleshooting help

### 🔧 For Developers
Recommended technical improvements:

1. Remove legacy Streamlit multipage routing (`/pages`)
2. Centralize all navigation and callbacks
3. Normalize session state schema
4. Polish UI spacing, hierarchy, and feedback states

---

## 9A. Repository Organization Recommendation (Critical)

To ensure long-term maintainability, eliminate dead UI, and prevent state bugs, the repository should be restructured into a **single-entry, state-driven architecture**.

### ✅ Recommended Directory Structure

```
Mantis-Studio/
│
├── app/main.py          # Single entrypoint (routing + layout only)
│
├── app/
│   ├── state.py              # Session state schema + defaults
│   ├── router.py             # Central navigation logic
│   │
│   ├── layout/
│   │   ├── sidebar.py        # Sidebar UI
│   │   ├── header.py         # App header + version
│   │   └── styles.py         # CSS / theme helpers
│   │
│   ├── views/                # Each UI screen (one file each)
│   │   ├── dashboard.py
│   │   ├── projects.py
│   │   ├── outline.py
│   │   ├── editor.py
│   │   ├── world_bible.py
│   │   ├── ai_tools.py
│   │   ├── export.py
│   │   ├── account.py
│   │   └── legal.py
│   │
│   ├── components/           # Reusable UI blocks
│   │   ├── buttons.py
│   │   ├── forms.py
│   │   └── editors.py
│   │
│   ├── services/             # Business logic (no UI)
│   │   ├── projects.py
│   │   ├── storage.py
│   │   ├── auth.py
│   │   ├── ai.py
│   │   └── export.py
│   │
│   └── utils/
│       ├── versioning.py
│       └── helpers.py
│
├── data/
│   └── projects/
│
├── assets/
│   └── styles.css
│
├── .github/workflows/
│   └── version-bump.yml
│
├── VERSION.txt
├── README.md
└── requirements.txt
```

### Why This Matters

* Eliminates duplicate logic
* Prevents buttons from silently failing
* Makes debugging predictable
* Allows contributors to understand the app quickly
* Scales cleanly as features grow

This refactor is **strongly recommended before adding new features**.

---

## 10. Project Vision

Mantis Studio aims to be a **professional‑grade creative OS**, not just another AI chat wrapper.

The foundation is solid — the next step is tightening execution.

---

*Maintained by the Mantis Studio project.*
