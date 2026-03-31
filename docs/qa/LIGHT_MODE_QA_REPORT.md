# Light Mode QA Report

Date: 2026-03-30

## Audit Scope
Full light-mode QA pass across these routes/pages:
- Dashboard (`?page=home`)
- Projects (`?page=projects`)
- Outline (`?page=outline`)
- Draft/Editor (`?page=chapters`)
- World Bible (`?page=world`)
- Export (`?page=export`)
- AI Settings (`?page=ai`)
- Memory (`?page=memory`)
- Insights (`?page=insights`)
- Legal pages (`?page=legal`, `terms`, `privacy`, `copyright`, `cookie`, `help`)
- Sidebar, header/banner, forms, alerts, tabs, expanders, and button states

## Method
1. Ran automated visual crawl via `scripts/toolbox.py visual --base-url http://localhost:8501`.
2. Ran deep interaction audits with Playwright that:
   - switched to Light mode
   - opened each route
   - clicked visible non-destructive buttons
   - toggled tabs/expanders where present
   - captured full-page screenshots
   - generated JSON matrices under `artifacts/light_mode_deep_audit*`
3. Applied centralized theme fixes in shared style layer (`app/ui/enhanced_theme.py`).
4. Re-ran visual checks and captured post-fix screenshots.

## Readability Issues Found
- Sidebar selected theme toggle (`Light`) could become low-contrast in disabled/active state.
- Disabled button labels on light backgrounds were too faint in some states.
- Non-primary/global button selectors were too broad and could override primary contrast.
- Light-mode muted text (helper/meta/caption) was too washed out in some sections.
- Alert readability needed stronger warning/info contrast.
- Expander/tab/dataframe text color consistency needed explicit reinforcement in light mode.

## Fixes Applied
Centralized in `app/ui/enhanced_theme.py`:
- Hardened disabled button palette (text/border/background) for readable light-mode states.
- Scoped non-primary `baseButton` selectors to secondary/tertiary only (stopped accidental primary override).
- Added explicit sidebar primary button rules for enabled-only states.
- Added explicit sidebar disabled-button text/icon contrast rules.
- Strengthened warning/info alert color pairings.
- Darkened light-mode secondary/muted token aliases for helper/caption clarity.
- Added explicit light-mode styles for expander headers/icons, tabs (selected/unselected), and dataframe text.

## Page-by-Page Summary
- Dashboard: button states and cards readable; no blocking contrast failures after shared fixes.
- Projects: project controls and metadata rows readable; primary/disabled states corrected via shared button rules.
- Outline: bottom action row (Save/Revision/Undo) remains readable in light mode; expander header contrast reinforced.
- Draft/Editor: CTA and inactive states readable with updated disabled/button token enforcement.
- World Bible: form labels, chips, and action buttons stay legible; helper text improved by muted-token hardening.
- Export: no readability regressions; shared button and caption contrast improvements apply.
- AI Settings: provider cards, helper copy, tabs, and save/apply controls improved via token + tab/alert overrides.
- Memory: section buttons and body text remain readable; no new contrast regressions.
- Insights: sidebar + content card readability remains stable in light mode.
- Legal pages: headings/body and sidebar controls are readable; active Light toggle now remains legible.

## Evidence Artifacts
- Visual regression summary:
  - `artifacts/visual_regression/summary.json`
- Deep audit matrices/screenshots:
  - `artifacts/light_mode_deep_audit/light_mode_matrix.json`
  - `artifacts/light_mode_deep_audit_postfix/light_mode_matrix.json`
  - `artifacts/light_mode_deep_audit_final/light_mode_matrix.json`
  - `artifacts/light_mode_deep_audit_final/terms_after_disabled_fix2.png`

## Remaining Edge Cases
- Automated contrast scripts can over-report around emoji/icon-prefixed labels because of mixed glyph rendering.
- Some routes (`export`, `ai`) may redirect or render limited state when no project/API key is configured; light-mode styling still applies, but full functional content depends on runtime data.

## Result
Light mode has been comprehensively audited and hardened with centralized styling fixes. Primary/secondary/disabled button readability, sidebar theme controls, alerts, helper text, and structural UI elements (tabs/expanders/tables/cards) are now consistent and legible without dark-mode regressions.

## Additional user-reported screenshot fixes (2026-03-30 follow-up)
- Fixed unreadable dark expander headers in Light mode by adding high-priority Light selectors for expander summary/header foreground/background/border.
- Fixed AI provider radio option readability (labels no longer fade/vanish on Light backgrounds).
- Normalized chapter status captions to plain separators (`|`) to remove mojibake artifacts like `•` in Draft/Outline stats.
- Re-captured verification screenshots:
  - `artifacts/light_mode_deep_audit_final/outline_after_refactor.png`
  - `artifacts/light_mode_deep_audit_final/draft_after_refactor.png`
  - `artifacts/light_mode_deep_audit_final/ai_after_refactor.png`


## World Bible follow-up fixes
- Removed mojibake separators and action labels in AI suggestion review cards.
- Corrected high-confidence behavior so matched suggestions auto-apply at/above configured threshold.
- Improved entity extraction prompt quality to include relationship and objective context for stronger narrative canon details.
