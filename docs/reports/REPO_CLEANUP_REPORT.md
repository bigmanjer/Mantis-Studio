# REPO CLEANUP REPORT

Date: 2026-03-31
Repository: Mantis-Studio
Working copy: `C:\Users\BIGMANJER\Documents\Playground\mantis testing`

## 1) Audit Findings

### Runtime Entry Points
- Canonical runtime is `app/main.py`.
- `streamlit_app.py` is a minimal deployment shim that imports and calls `app.main._run_ui`.

### UI/View Files
- Active routing uses wrappers in `app/views/` (dashboard/projects/outline/editor/world_bible/export/ai_tools/legal).
- Found duplicate wrappers and route maps with overlapping purpose.

### Services / Business Logic
- Core domain logic is in `app/services/`.
- `world_bible.py`, `world_bible_db.py`, and `world_bible_merge.py` are all used and not duplicates.

### Config / State / Routing
- Canonical configuration module exists at `app/config/settings.py`.
- State init is in `app/session_init.py` with compatibility bridge in `app/state.py`.
- Navigation config was duplicated between `app/router.py` and `app/utils/navigation.py`.

### Utilities / Components / Layout
- `app/components/editors.py` and `app/components/forms.py` were placeholder-only.
- `app/layout/sidebar.py` was placeholder/stub and not used in runtime.

### Runtime/Generated Data
- Generated caches and runtime output existed in tracked tree:
  - `__pycache__/` directories
  - `.pytest_cache/`
  - `logs/*`
  - `artifacts/*`
- `projects/` contains local runtime project data and backups.

### Docs
- `app/README.md` was stale and included outdated structure references.
- Root `README.md` did not have a concise current cleanup status section.

## 2) Duplicate / Redundant Items Found

- Duplicate nav mapping logic:
  - `app/router.py:get_nav_config`
  - `app/utils/navigation.py:get_nav_config`
- Duplicate/unused wrapper files:
  - `app/views/home.py`
  - `app/views/world.py`
  - `app/views/routes.py`
- Placeholder modules with no implementation:
  - `app/components/editors.py`
  - `app/components/forms.py`
  - `app/layout/sidebar.py`

## 3) Cleanup Actions and Reasoning

### Kept
- `streamlit_app.py`: retained as deployment compatibility shim.
- `app/app_context.py`: retained because tests still import it.

### Merged / Consolidated
- `app/router.py:get_nav_config` now delegates directly to `app.utils.navigation.get_nav_config`.
- Reason: one canonical nav source; removes duplicated mapping construction.

### Deleted
- `app/views/home.py`: redundant wrapper not used by router.
- `app/views/world.py`: redundant wrapper not used by router.
- `app/views/routes.py`: duplicate route table not used by runtime router.
- `app/components/editors.py`: placeholder-only file.
- `app/components/forms.py`: placeholder-only file.
- `app/layout/sidebar.py`: placeholder-only stub; no runtime references.

### Generated Clutter Removed
- Removed `__pycache__/` folders under `app/` and `tests/`.
- Removed `.pytest_cache/` content.
- Removed `logs/` and `artifacts/` contents from working tree.

## 4) Files Updated

- `.gitignore`
  - Expanded ignores for generated/runtime folders and caches.
- `app/router.py`
  - Removed duplicate nav construction; now delegates to canonical nav module.
- `app/README.md`
  - Rewritten to reflect actual active architecture and runtime policy.
- `README.md`
  - Added “Repository Cleanup Status (2026-03-31)” section.

## 5) Final Architecture Tree

```text
/
+-- app/
¦   +-- main.py
¦   +-- router.py
¦   +-- state.py
¦   +-- session_init.py
¦   +-- config/
¦   +-- models/
¦   +-- services/
¦   +-- views/
¦   +-- components/
¦   +-- layout/
¦   +-- utils/
+-- assets/
+-- docs/
+-- legal/
+-- scripts/
+-- tests/
+-- .github/
+-- .devcontainer/
+-- streamlit_app.py
+-- pyproject.toml
+-- requirements.txt
+-- README.md
+-- VERSION.txt
+-- Mantis_Launcher.bat
```

## 6) Follow-up Recommendations

1. Gradually extract render logic from `app/main.py` into `app/views/*` and keep services UI-free.
2. Retire `app/app_context.py` only after removing test/runtime imports.
3. Add a small architecture CI check that fails on tracked cache/runtime artifacts.
4. Consider moving historical QA screenshots to an external artifact store if long-term retention is needed.

## 2026-03-31 Additional Organization Pass

- Removed duplicate app-level metadata files:
  - `app/requirements.txt`
  - `app/CHANGELOG.md`
- Cleared runtime-generated clutter directories in the working repo:
  - `.pytest_cache/`
  - `logs/`
  - `artifacts/`
- Preserved canonical source/runtime structure (`app/`, `scripts/`, `tests/`, `assets/`, `legal/`, `docs/`).

## 2026-03-31 App + Legal Deep Verification

- Verified active `app/` modules referenced by runtime/tests were retained.
- Normalized legal filename casing for consistency:
  - `legal/Brand_ip_Clarity.md` -> `legal/brand_ip_clarity.md`
  - `legal/Trademark_Path.md` -> `legal/trademark_path.md`
- Updated all known references in:
  - `app/main.py`
  - `legal/README.md`
  - `README.md`
- Re-ran compile check after rename to confirm runtime safety.

## 2026-03-31 Encoding Hardening

- Added UTF-8 with fallback decode handling (`cp1252`, `latin-1`) when loading project JSON files in:
  - `app/main.py` (`Project.load`)
  - `app/services/projects.py` (`Project.load`)
- Added fallback text reader in `app/main.py` for legal/policy markdown rendering paths.
- Purpose: prevent runtime crashes from legacy Windows-encoded files (`UnicodeDecodeError` like byte `0x96`).
