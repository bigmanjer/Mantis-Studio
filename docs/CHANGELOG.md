## [91.3] - 2026-03-30

### Fixed
- Eliminated remaining mojibake separators in World Bible UI labels (`Open details | Name`, review labels use `|` separators).
- Removed raw UUIDs from World Bible detail expander labels so entity cards read cleanly for users.
- Synced Outline `Project Title` and `Genre` inputs with persisted project metadata on every rerun/project change.
- Improved chapter title auto-detection from outlines by supporting both `Chapter X:` lines and numbered markdown lists (for example `1. **Title** - ...`).

### Changed
- Added compact entity metadata caption in World Bible detail panels (`Aliases` and `Created`), replacing noisy ID display.

---
# Changelog

All notable changes to Mantis Studio are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Stability
- Dashboard workflow progress UI polish: added stage completion progress bar, explicit done/pending stage labels, and a "Current target" hint for the next incomplete step.
- Dashboard workflow progress style: set the dashboard completion bar to a green fill for clearer visual status.
- Encoding hardening: project JSON and legal text readers now fall back from UTF-8 to CP1252/Latin-1 to avoid decode crashes on legacy Windows-encoded files.
- Repository hygiene: completed deep app/legal verification, normalized legal filenames to lowercase (`brand_ip_clarity.md`, `trademark_path.md`), and updated all in-repo references.
- Workspace cleanup: removed older duplicate local repo copies from `C:\Users\BIGMANJER\Documents\Playground` and cleaned stale `__pycache__` plus temporary Streamlit log artifacts from the active repo.
- Sidebar control cleanup: removed the duplicate top-left collapse control and standardized the visible action label to `Hide Sidebar`.
- Crash fix: replaced invalid Streamlit `icon="!"` values with valid emoji characters so settings and World Bible pages render normally again.
- Light mode button readability: hardened disabled button styles so inactive actions use readable light surfaces instead of dark blocks.
- Navigation IA: removed separate `Export` item from primary sidebar; import/export remains in `Projects`.
- Sidebar information architecture: restored `Memory` and `Insights` to their own `Intelligence` section in the sidebar.
- Routing hardening: added query-parameter page navigation guard to prevent rerun redirect loops.
- Navigation UX: page changes now auto-scroll to top for consistent landing behavior.
- Footer UX: "Back to top" now targets all Streamlit scroll containers instead of a single element.
- Canon defaults: World Bible auto-apply confidence default increased to `0.83` (83%).
- Theme consistency: removed hardcoded dark forcing in shell styles so Light mode can apply correctly.
- Light mode hardening: added explicit Streamlit metric selectors (`stMetricLabel`, `stMetricValue`, `stMetricDelta`) so metric text remains readable in Light mode.
- QA evidence: reran screenshot regression with `scripts/toolbox.py visual --base-url http://localhost:8501`; artifacts updated under `artifacts/visual_regression/`.
- Navigation landing fix: sidebar page transitions now trigger a scroll nonce and a repeated, multi-container top-scroll script (main section + app container + document/body) to prevent landing at footer.
- Dashboard light-theme cleanup: replaced remaining hardcoded dark utility card/status colors with theme tokens for consistent Light-mode rendering.
- Light-mode permanence pass: added a final, theme-scoped CSS enforcement layer (loaded after shared button CSS) so disabled actions, alerts, and sidebar cards stay readable in Light mode across all pages.
- Sidebar control wording: standardized collapsed-state control to `Show Sidebar` (open-state remains `Hide Sidebar`) for one consistent toggle flow.
- Theme duplication cleanup: converted legacy `app/ui/theme.py` into a compatibility shim that forwards to `app/ui/enhanced_theme.py`, preventing parallel theme systems from diverging.
- Dashboard cleanup: removed corrupted/garbled dashboard labels, switched KPI label from `System health` to `Workflow readiness`, and normalized CTA text to plain readable labels.
- Onboarding UX: reordered dashboard checklist so `AI connected` appears first, then project/outline/chapter steps.
- Light mode hardening (phase 2): added high-priority button text/background overrides (including sidebar buttons and primary/disabled variants) plus explicit sidebar project-chip text color enforcement for reliable readability.

### Changed
-  Replaced in-app branding assets with slices generated from `assets/NEW MANTIS BRANDING.png`, including a new emblem, wordmark, full lockup, and favicon set (1x + 2x) generated at runtime from the source board.
-  Updated Streamlit branding references for page icon, header logo, sidebar logo, and home-header emblem to use generated `branding/*` assets.
-  Tuned header logo sizing for the wider lockup image so branding renders cleanly at default viewport widths.
-  Refined header/sidebar brand containers and logo treatment (transparent extraction + themed glow frames) so the new brand system feels native to the product UI instead of pasted-in artboards.

### Branding asset map
- `assets/branding/mantis_favicon.png`  Streamlit `page_icon` metadata
- `assets/branding/mantis_wordmark.png`  `app_context` header logo
- `assets/branding/mantis_lockup.png`  `main.py` top brand header
- `assets/branding/mantis_emblem.png`  sidebar brand + compact header icon

### Changelog output
- Images sliced at runtime: 8 outputs (`mantis_emblem`, `mantis_wordmark`, `mantis_lockup`, `mantis_favicon`, each with 1x and 2x variants).
- Code files updated: `app/app_context.py`, `app/main.py`, `app/layout/enhanced_sidebar.py`, `app/utils/branding_assets.py`.

### Fixed
-  Eliminated binary image slices from git history moving forward by generating derived branding assets on demand, which avoids PR tooling failures on binary diffs.

---

## [91.6] - 2026-02-18

### Added
-  **In-app "What's New" notification system**: Users now see a friendly notification banner when the app version updates
  - Shows key changes and improvements in each version
  - Includes direct link to full changelog
  - Dismissible with persistent memory of last seen version
  - Helps users understand what changed between updates
-  Version tracking in user config to detect when app has been updated

### Changed
-  Updated CHANGELOG.md to document all versions from 90.7 to 91.6
-  Updated README.md to reflect current version (91.6) throughout documentation
-  Improved transparency about version changes and updates

### Fixed
-  **Major UX Issue**: Users can now see what changed between versions
  - Previously, users reported "merged 4 times now with no changed from users point of view"
  - Version number was incrementing but changes were invisible to users
  - Now users get a clear notification when version changes
-  Documentation version inconsistencies corrected

### Impact
This release directly addresses user feedback about version changes being invisible. Users will now be informed whenever the app updates, creating better awareness and transparency about ongoing improvements.

---

## [91.5] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [91.4] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [91.3] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [91.2] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [91.1] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [91.0] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [90.9] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [90.8] - 2026-02-18

### Note
- Version auto-incremented by CI/CD workflow
- Specific changes not documented in this retroactive update

---

## [90.7] - 2026-02-18

### Changed
- Refreshed documentation links and guidance so all referenced files and commands match the current repository layout.
- Updated contributor and testing docs to use direct `pip`/`pytest` workflows (no Makefile assumptions).

### Fixed
- Corrected stale internal links in docs.
- Corrected changelog historical notes that referenced removed files.

---

## [89.2] - 2026-02-12

### Added
- Production-grade repository structure.
- Modern Python packaging and test configuration via `pyproject.toml`.
- Consolidated documentation under `docs/`.

### Changed
- Simplified dependency management to a single `requirements.txt`.
- Improved project organization and documentation.

### Fixed
- Removed duplicate dependency files from legacy structure.

---

## [89.1] - 2026-02-11

### Changed
- Foundation release in the 89.x stabilization cycle.

---

## Version History Reference

- **90.x** - Documentation and maintenance improvements.
- **89.x** - Production infrastructure improvements.
- **88.x** - Debugging and troubleshooting framework.
- **87.x** - User experience enhancements.
- See [`../VERSION.txt`](../VERSION.txt) for the current version.






