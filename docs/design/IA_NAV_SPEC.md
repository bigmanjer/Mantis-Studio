# IA + Navigation Spec

## Primary Navigation (Sidebar)
- **Dashboard** → `page="home"`
- **Projects** → `page="projects"`
- **Write (Outline)** → `page="outline"`
- **Editor** → `page="chapters"`
- **World Bible** → `page="world"`
- **Export** → `page="export"`
- **AI Settings** → `page="ai"`

## Secondary Navigation (Header)
- **App title + logo** (left)
- **Current project selector** (center)
  - Loads selected project and routes to `chapters`.
- **Quick actions** (contextual per page)

## Footer Navigation
- **Terms** → `page="terms"` (renders `legal/terms.md`)
- **Privacy** → `page="privacy"` (renders `legal/privacy.md`)
- **Legal** → `page="legal"` (All Policies)
- **Support** → external link to GitHub Issues
- **Contact** → mailto link
- **Version** → displays current app version

## Page Rendering Map
- `home` → Dashboard / Home
- `projects` → Projects
- `outline` → Outline (Write)
- `chapters` → Editor (Write)
- `world` → World Bible
- `export` → Export
- `ai` → AI Settings
- `legal` → All Policies
- `terms` → Terms of Service
- `privacy` → Privacy Policy
- `copyright` → Copyright Notice
- `cookie` → Cookie Policy

## Header Actions by Page
- **Dashboard:** Resume project, New project
- **Projects:** Create project, Import
- **Outline:** Save outline, Generate outline, Scan entities
- **Editor:** Save chapter, Update summary
- **World Bible:** Add entity, Run coherence check
- **Export:** Export current project
- **AI Settings:** Save settings, Refresh models
