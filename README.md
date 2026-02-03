# 🐜 Mantis Studio

**Mantis Studio** is an all‑in‑one AI‑assisted writing and story‑development environment built with **Streamlit**. It is designed to take a project from *idea → outline → chapters → world‑building → export*, while maintaining persistent memory and structured data across sessions.

This README explains **what the app does, how it is structured, what every major button/section is supposed to do, and how the UI flows from a user’s point of view**.

---

## 1. High‑Level Purpose

Mantis Studio is meant to replace scattered tools (notes apps, docs, AI chats, spreadsheets) with **one guided creative workspace**:

* Centralized project management
* AI‑assisted outlining and drafting
* Structured world‑building (characters, locations, lore)
* Persistent memory and insights
* Clean export for manuscripts or planning docs

The app is **state‑driven**, not page‑driven. All navigation feeds a single app shell (`Mantis_Studio.py`).

---

## 2. Technology Stack

* **Python 3.10+**
* **Streamlit** (UI + state)
* **Session State** for routing and persistence
* **Local JSON / serialized storage** (project data)
* **OIDC Auth (optional)**: Google / Microsoft / Apple
* **GitHub Actions** for version bumping

---

## 3. Application Entry & Architecture

### Entrypoint

```
Mantis_Studio.py
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
| **Account**           | Authentication & profile settings             |
| **Legal**             | Terms, privacy, licensing                     |

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

### 5.8 Account

**Purpose:** Authentication & identity.

**Current State:**

* Google / Microsoft OIDC supported
* Email‑only auth missing

**Required Improvement:**

* Manual email/password option
* Clear login feedback (success/failure)

---

### 5.9 Legal

Static informational pages:

* License
* Terms
* Privacy

Should **not** clutter main navigation for most users.

---

## 6. Known Issues (High Impact)

* Buttons triggering no action (missing callbacks)
* Duplicate UI logic across files
* Legacy `/pages` causing confusion
* Inconsistent state keys
* Account flow lacks fallback auth

---

## 7. Versioning System

* Version stored in `VERSION.txt`
* GitHub Action: `.github/workflows/version-bump.yml`
* Automatically increments version on merge

Displayed in UI header for transparency.

---

## 8. Who This App Is For

* Novelists
* Screenwriters
* Game writers
* World‑builders
* AI‑assisted creative workflows

---

## 9. Recommended Next Steps

1. Remove legacy Streamlit multipage routing (`/pages`)
2. Centralize all navigation and callbacks
3. Normalize session state schema
4. Finish Account authentication flow
5. Polish UI spacing, hierarchy, and feedback states

---

## 9A. Repository Organization Recommendation (Critical)

To ensure long-term maintainability, eliminate dead UI, and prevent state bugs, the repository should be restructured into a **single-entry, state-driven architecture**.

### ✅ Recommended Directory Structure

```
Mantis-Studio/
│
├── Mantis_Studio.py          # Single entrypoint (routing + layout only)
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
