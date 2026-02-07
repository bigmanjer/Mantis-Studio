# Repository Structure Review

## Summary of issues
- **Documentation is split across root and `docs/`**, making onboarding and navigation harder.
- **Two parallel code trees (`app/` and `mantis/`)** make it unclear which modules are canonical.
- **UI concerns are duplicated** (`app/components/`, `app/ui/`, `app/layout/`) and overlap with `mantis/ui/`.
- **Mixed responsibility in the root** (scripts, docs, assets, and runtime artifacts like logs) increases clutter.
- **Data/runtime folders (`projects/`, `logs/`)** sit beside source, making it unclear what is source vs. output.

## BEFORE → AFTER (top-level tree)

**Before**
```
Mantis-Studio/
├── DESIGN_SYSTEM.md
├── GETTING_STARTED.md
├── IA_NAV_SPEC.md
├── IMPLEMENTATION_SUMMARY.md
├── MIGRATION.md
├── Mantis_Studio.py
├── README.md
├── app/
├── mantis/
├── assets/
├── docs/                # mixed docs
├── legal/
├── logs/
├── scripts/
└── requirements.txt
```

**After (this change)**
```
Mantis-Studio/
├── Mantis_Studio.py
├── README.md
├── app/
├── mantis/
├── assets/
├── docs/
│   ├── architecture/
│   ├── design/
│   ├── guides/
│   └── runbooks/
├── legal/
├── logs/
├── scripts/
└── requirements.txt
```

## Proposed folder structure (target)

```
Mantis-Studio/
├── Mantis_Studio.py              # Streamlit entrypoint (keep at root)
├── app/                           # Canonical Streamlit UI + services (current target)
│   ├── components/
│   ├── layout/
│   ├── services/
│   ├── state.py
│   ├── views/
│   └── utils/
├── mantis/                        # Legacy package (deprecate once migration finishes)
├── assets/                        # Static images + CSS
├── docs/                          # All documentation (organized by domain)
├── legal/                         # Legal policy docs
├── scripts/                       # Maintenance utilities
├── requirements.txt
└── VERSION.txt
```

## Purpose of each top-level folder
- **app/**: Active, reorganized Streamlit codebase (views, services, layout, components).
- **mantis/**: Legacy implementation; currently required by `app/` imports.
- **assets/**: Logos, UI images, and shared CSS.
- **docs/**: All technical and user documentation (now grouped by topic).
- **legal/**: Terms, privacy, and IP documentation.
- **logs/**: Runtime output logs (should remain gitignored).
- **scripts/**: Developer utilities (healthcheck, smoke test, version bump).

## Suggested renames / moves (recommendations)
- **`app/auth_supabase.py` → `app/services/auth_supabase.py`** to keep auth in services.
- **`app/ui/`** should be merged into `app/components/` or `app/layout/` (avoid 3 UI layers).
- **`mantis/` → `legacy/`** once imports are fully removed to signal deprecation.
- **`logs/launcher_*.log`** should be removed from git history and left ignored.

## Files to merge, split, move, or remove
- **Merge**: `app/ui/` and `app/components/` once component boundaries are clarified.
- **Move**: documentation files into `docs/` subfolders (completed in this change).
- **Split**: large monolithic `Mantis_Studio.py` into view/service modules after migration.
- **Remove**: tracked log artifacts (keep runtime logs ignored).

## Breaking changes + mitigation
- **Breaking**: Documentation paths changed (root docs moved into `docs/`).
  - **Mitigation**: Updated README and internal links; external links should be updated to new paths.
- **Breaking (future)**: Consolidating `app/` + `mantis/` would require import updates.
  - **Mitigation**: Provide compatibility shims and perform migration in phases.

## Migration steps (ordered and safe)
1. Create documentation subfolders under `docs/`.
2. Move root and legacy docs into the new folders using `git mv`.
3. Update all intra-doc references and README links.
4. Add this repository-structure summary as a single reference point.

## Optional improvements for future growth
- Consolidate into a single codebase (`app/` or `src/`) and retire `mantis/`.
- Introduce a dedicated `data/` directory for runtime artifacts (`projects/`, logs, backups).
- Add a standard `tests/` folder and automate `scripts/healthcheck.py` in CI.
- Adopt `pyproject.toml` for clearer dependency and tooling configuration.
