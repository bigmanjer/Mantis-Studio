# IA + Navigation Spec

## Primary Navigation (Sidebar)
- **Dashboard** → `page="home"`
- **Projects** → `page="projects"`
- **Write (Outline)** → `page="outline"`
- **Editor** → `page="chapters"`
- **World Bible** → `page="world"`
- **Export** → `page="export"`
- **AI Settings** → `page="ai"`

> Navigation is focused on core writing workflows.

## Secondary Navigation (Header)
- **App title + logo** (left)
- **Current project selector** (center)
  - Loads selected project and routes to `chapters`.
- **Quick actions** (contextual – optional per page)
- **Quick actions** (right)

## Page Rendering Map
- `home` → Dashboard / Home
- `projects` → Projects
- `outline` → Outline (Write)
- `chapters` → Editor (Write)
- `world` → World Bible (Entities + Memory + Insights)
- `export` → Export
- `ai` → AI Settings
- `legal` → Legal hub redirect

## Header Actions by Page
- **Dashboard:** Resume project, New project
- **Projects:** Create project, Import
- **Outline:** Save outline, Generate outline, Scan entities
- **Editor:** Save chapter, Update summary
- **World Bible:** Add entity, Run coherence check
- **Export:** Export current project
- **AI Settings:** Save settings, Refresh models
