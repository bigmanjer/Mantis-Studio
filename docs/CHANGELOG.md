# Changelog

All notable changes to Mantis Studio are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Stability
- Google OAuth secret detection: Streamlit Secrets now accepts both uppercase deployment keys and lowercase Streamlit keys, and the auth screen points users to Secrets instead of a removed super-admin OAuth menu.
- Google OAuth redirect default: hosted Google sign-in now defaults to the active `https://mantis-studio.streamlit.app/?oauth_provider=google` callback URL.
- Version bump: updated app metadata and docs to `136.1`.
- Auth page professional redesign: rebuilt the sign-in screen into a cleaner product-access page with research-informed hierarchy, fewer default choices, stronger guest/account/subscription comparison, and clearer provider/recovery positioning.
- Version bump: updated app metadata and docs to `136.0`.
- Email password recovery: added Resend-backed one-time reset links using Streamlit secrets, hashed expiring reset tokens, and a token landing flow on the auth page.
- Recovery UX: the Recover tab now prefers email reset links, keeps recovery-code reset as a fallback, and reports whether email secrets are configured.
- Version bump: updated app metadata and docs to `135.9`.
- Auth page redesign: replaced the earlier command-center hero with a focused access screen emphasizing guest drafting, account recovery, provider sign-in, and canon continuity.
- Canon auto-apply correction: Canon Scanner now uses classified/boosted confidence for Workspace threshold decisions and Insights auto-promotes already-queued suggestions that meet the current threshold.
- Canon review clarity: queued suggestions now show the matched World Bible entry so users can confirm whether proposed details are already present before applying.
- Workspace Settings expansion: added workspace overview metrics, storage/config/backup visibility, current-project save/export/refresh actions, and clearer writing/canon automation controls.
- Workspace settings persistence fix: startup now restores saved autosave, word-goal, session-goal, focus-timer, and confidence settings with safe bool/int/float coercion.
- Auth access redesign: rebuilt the sign-in/sign-up page into a focused account workflow with clearer provider sign-in, form-based Sign in/Create/Recover tabs, a better guest path, and local-first/subscription-ready positioning.
- Navigation landing fix: page changes now reset to the `#mantis-top` anchor once, and footer navigation links target that anchor, so Streamlit reruns no longer leave users staring at the footer after navigation.
- Outline action layout: moved `Undo last outline apply` into Revision Tools and placed `Save Outline` at the bottom of the Blueprint panel to match the Editor action flow.
- Auth page polish: rebuilt the account entry screen around the MANTIS brand lockup, a clearer Plan/Draft/Review value flow, an integrated guest path, and a compact account-access panel that fits laptop-height viewports.
- Editor action layout: Chapter Flow now only handles Previous, Next, chapter selection, New, and Delete; Save Chapter sits below the editor dropdown tools, and Update Summary moved into Assistant > Summary.
- Scroll stability: removed the automatic page-transition scroll script and theme-level scroll injection that could cause pages to land at the footer or jump unexpectedly.
- Insights consolidation: moved the relationship graph into Insights so canon health, graph review, scanner results, and coherence checks live in one review page.
- World Bible cleanup: World Bible cards now keep entity names clean and show status as metadata instead of prefixing names with `Unused`.
- Memory cleanup: scanned canon facts now belong in World Bible; Memory's soft area is labeled Writing Guidance and no longer receives automatic soft-memory additions.
- Settings order: Settings navigation now lists Workspace Settings, AI Settings, then User Settings in both sidebar and footer.
- Project discovery hardening: hidden config JSON files are excluded from project discovery and repair passes so saving AI settings cannot appear as a random project.
- Welcome onboarding: replaced the jumbled welcome tips with a Start, Write, Review flow plus links to the Getting Started guide and changelog.
- Release notes UX: replaced stale self-referential update messaging with real current highlights and added a compact latest-update summary plus changelog link to the welcome card.
- Compatibility shim cleanup: removed obsolete `app/components/ui.py`, `app/ui/theme.py`, `app/ui/layout.py`, and `app/ui/footer_shared.py` wrappers after moving imports to the canonical modules; removed unused split-card helpers from `app/ui/components.py`.
- Runtime consolidation: removed the legacy `app/app_context.py` duplicate Streamlit implementation so the enhanced sidebar and `app/main.py` are the only live app path.
- Editor find/replace safety: renamed the action to Apply replacement, defaulted replacement scope to the first exact match, added optional all-match scope, and surfaced an in-panel undo only after a replacement is applied.
- Editor Chapter Flow: replaced the top stats strip and long left chapter list with a compact dropdown-driven Chapter Flow bar containing Previous, Next, chapter select, New, Delete, Outline, and World Bible actions.
- Editor workspace restructure: removed the redundant top jump bar, moved chapter movement into the chapter rail, widened the writing surface, compacted draft stats, and changed Assistant to Write/Summary/Tools modes.
- Memory IA cleanup: removed Coherence Check from Memory now that Insights owns coherence review.
- Insights IA cleanup: moved Canon Scanner and queued World Bible suggestion review into Insights so canon review work happens in one place.
- Intelligence navigation order: Insights now appears before Memory in sidebar, footer, and dashboard quick actions so users check risk and project health before editing AI instructions.
- Insights workflow: added the full Coherence Check panel to Insights with explicit target text, suggested replacement, and smart replacement behavior that blocks instead of appending when it cannot locate the passage.
- Canon scanner fix: high-confidence World Bible suggestions now auto-apply once they meet the configured threshold, while lower-confidence suggestions stay queued for review.
- Canon intelligence foundation: added deterministic chapter analysis for extracted facts, relationships, timeline events, memory suggestions, and canon conflicts, then surfaced latest-chapter signals in Insights.
- Settings IA cleanup: moved super-admin OAuth and user administration controls from Workspace Settings into User Settings.
- Repository replacement: published the local `mantis testing` workspace to the existing `bigmanjer/Mantis-Studio` GitHub repository, updated contributor clone guidance for the `mantis testing` checkout folder, and bumped the app version to `134.0`.
- Full repository audit: added `scripts/full_repo_audit.py` as the canonical compile/selftest/healthcheck/pytest/static-report runner.
- Test gate restored: full suite now passes with `245 passed` using the real Python 3.14 install.
- Documentation consolidation: replaced the oversized root README with a concise landing page and moved audit/cleanup detail into `docs/reports/`.
- Navigation cleanup: removed the separate `Export` navigation/page as redundant with the richer Projects export panel.
- Auth screen visual redesign: upgraded onboarding to a centered two-panel experience with a branded hero card, clearer messaging hierarchy, and improved desktop/mobile composition.
- Dashboard-first onboarding: app now opens directly into Dashboard as guest by default, with sign-in/sign-up available on demand from the sidebar.
- Logout UX: signing out now returns users to guest dashboard instead of forcing the auth gate first.
- Auth compatibility fix: login now accepts legacy PBKDF2 account hashes and auto-migrates them to SHA-256 on successful sign-in.
- Auth UX upgrade: redesigned onboarding screen with a consumer-style split layout and a `Continue as guest` path so users can enter the app before signing in.
- Guest conversion flow: guests can now open `Sign in / Create account` from the sidebar and upgrade sessions without feeling blocked.
- Account creation UX: added clearer signup requirements on the auth screen and an admin-side "Create account" panel in User Settings.
- Account role management: admins can now promote/demote users between `member` and `admin`, with safeguards to prevent removing the last admin.
- Account admin controls: added admin-only user management in User Settings (user list, enable/disable account, and password reset).
- Account roles: first created account is now seeded as `admin`; later accounts default to `member`.
- Account system: added local user sign-in/sign-up flow with secure password hashing, per-user workspace directories under `projects/users/<user_id>`, and sidebar sign-out control.
- Editor layout cleanup: tightened chapter navigation into a single-row control cluster, cleaned sidebar chapter labels/buttons, and reduced visual clutter in editor controls.
- Editor warning fix: removed Streamlit `text_area` value/session-state conflict that caused "widget ... default value but also had its value set via Session State API" warnings.
- Editor cleanup: removed chapter export controls from the Editor utility bar to keep export actions centralized outside drafting.
- Navigation naming alignment: standardized workflow navigation and top header labels to use `Editor` consistently (removed `Draft` vs `Editor` mismatch).
- Outline workflow upgrade: added outline diagnostics (word count, planned chapters, last-updated), quick links to Editor/World Bible, and structure checks.
- Editor workflow upgrade: added previous/next navigation, chapter jump selector with explicit confirm action, and in-page find/replace for current chapter.
- Dashboard workflow progress UI polish: added stage completion progress bar, explicit done/pending stage labels, and a "Current target" hint for the next incomplete step.
- Dashboard workflow progress style: set the dashboard completion bar to a green fill for clearer visual status.
- Encoding hardening: project JSON and legal text readers now fall back from UTF-8 to CP1252/Latin-1 to avoid decode crashes on legacy Windows-encoded files.
- Repository hygiene: completed deep app/legal verification, normalized legal filenames to lowercase (`brand_ip_clarity.md`, `trademark_path.md`), and updated all in-repo references.
- Workspace cleanup: removed older duplicate local repo copies from `C:\Users\BIGMANJER\Documents\Playground` and cleaned stale `__pycache__` plus temporary Streamlit log artifacts from the active repo.
- Sidebar control cleanup: removed the duplicate top-left collapse control and standardized the visible action label to `Hide Sidebar`.
- Crash fix: replaced invalid Streamlit `icon="!"` values with valid emoji characters so settings and World Bible pages render normally again.
- Light mode button readability: hardened disabled button styles so inactive actions use readable light surfaces instead of dark blocks.
- Navigation IA: `Export` is available as a primary workflow item while project workflows still expose export actions where useful.
- Sidebar information architecture: restored `Insights` and `Memory` to their own `Intelligence` section in the sidebar.
- Routing hardening: added query-parameter page navigation guard to prevent rerun redirect loops.
- Navigation UX: removed automatic scroll forcing from page changes after it caused inconsistent landing positions in Streamlit.
- Footer UX: removed the Back to top control and its scroll handler while app-shell scroll behavior is being reworked.
- Canon defaults: World Bible auto-apply confidence default increased to `0.83` (83%).
- Theme consistency: removed hardcoded dark forcing in shell styles so Light mode can apply correctly.
- Light mode hardening: added explicit Streamlit metric selectors (`stMetricLabel`, `stMetricValue`, `stMetricDelta`) so metric text remains readable in Light mode.
- QA evidence: reran screenshot regression with `scripts/toolbox.py visual --base-url http://localhost:8501`; artifacts updated under `artifacts/visual_regression/`.
- Navigation landing rollback: removed the earlier scroll nonce and repeated multi-container top-scroll script because it introduced viewport jumps.
- Dashboard light-theme cleanup: replaced remaining hardcoded dark utility card/status colors with theme tokens for consistent Light-mode rendering.
- Light-mode permanence pass: added a final, theme-scoped CSS enforcement layer (loaded after shared button CSS) so disabled actions, alerts, and sidebar cards stay readable in Light mode across all pages.
- Sidebar control wording: standardized collapsed-state control to `Show Sidebar` (open-state remains `Hide Sidebar`) for one consistent toggle flow.
- Theme duplication cleanup: consolidated theme injection on `app/ui/enhanced_theme.py`, preventing parallel theme systems from diverging.
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
- `assets/branding/mantis_wordmark.png`  header logo
- `assets/branding/mantis_lockup.png`  `main.py` top brand header
- `assets/branding/mantis_emblem.png`  sidebar brand + compact header icon

### Changelog output
- Images sliced at runtime: 8 outputs (`mantis_emblem`, `mantis_wordmark`, `mantis_lockup`, `mantis_favicon`, each with 1x and 2x variants).
- Code files updated: `app/main.py`, `app/layout/enhanced_sidebar.py`, `app/utils/branding_assets.py`.

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





