# IA + Navigation Spec

## Primary Navigation (Sidebar)
- **Dashboard** → `page="home"`
- **Projects** → `page="projects"`
- **Write (Outline)** → `page="outline"`
- **Editor** → `page="chapters"`
- **World Bible** → `page="world"`
- **Export** → `page="export"` (gated for guests)
- **AI Settings** → `page="ai"`

> Account is removed from primary nav and is accessible via the header menu.

## Secondary Navigation (Header)
- **App title + logo** (left)
- **Current project selector** (center)
  - Loads selected project and routes to `chapters`.
- **Quick actions** (contextual – optional per page)
- **Account menu** (right)
  - Profile & settings → `open_account_settings()`
  - Log out → `auth.logout_button()`

## Page Rendering Map
- `home` → Dashboard / Home
- `projects` → Projects
- `outline` → Outline (Write)
- `chapters` → Editor (Write)
- `world` → World Bible (Entities + Memory + Insights)
- `export` → Export
- `ai` → AI Settings
- `account` → Account Access
- `legal` → Legal hub redirect

## Header Actions by Page
- **Dashboard:** Resume project, New project
- **Projects:** Create project, Import
- **Outline:** Save outline, Generate outline, Scan entities
- **Editor:** Save chapter, Update summary
- **World Bible:** Add entity, Run coherence check
- **Export:** Export current project
- **AI Settings:** Save settings, Refresh models
- **Account:** Back to Studio, Log out
