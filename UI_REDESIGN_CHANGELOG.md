# UI Redesign Changelog

## Summary
- Introduced a centralized dark theme and card system to align the UI with a modern SaaS aesthetic.
- Consolidated navigation into a single sidebar with a consistent header and account access in the header area.
- Refreshed Dashboard, AI Settings, and Account Access with card-based layouts and clear action hierarchy.

## Key Changes
- Added `app/ui/theme.py` for design tokens and CSS injection.
- Added `app/ui/components.py` for reusable header/cards/tiles.
- Updated dashboard layout to emphasize current project, quick actions, and recent projects.
- Updated AI Settings with provider cards and a unified action strip.
- Updated Account Access (in-shell + multipage) with consistent header and back-to-studio action.
