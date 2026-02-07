# MANTIS Studio Architecture Tree Plan

## Goals
- Preserve **Mantis_Studio.py** as the Streamlit Cloud entrypoint (thin shim only).
- Keep behavior, features, and on-disk project JSON formats intact.
- Introduce a scalable, modular package layout under `mantis/`.
- Provide backward-compatibility shims for legacy import paths.

## Current Tree → New Tree Mapping

| Current Location | New Location | Why |
| --- | --- | --- |
| `Mantis_Studio.py` | `Mantis_Studio.py` (thin shim) + `mantis/app.py` | Preserve Streamlit entrypoint while moving orchestration to a package module. |
| `Mantis_Studio.py` config section | `mantis/config/settings.py` | Centralize settings and defaults. |
| `Mantis_Studio.py` dataclasses/models | `mantis/core/models.py` | Separate core domain models. |
| `Mantis_Studio.py` persistence + IO helpers | `mantis/core/storage.py` | Isolate file IO, project paths, and locking. |
| `Mantis_Studio.py` world bible/entity logic | `mantis/core/world_bible.py` | Group world bible + entity scanning/canon logic. |
| `Mantis_Studio.py` export helpers | `mantis/core/export.py` | Encapsulate export formatting and file generation. |
| `Mantis_Studio.py` AI/LLM helpers | `mantis/services/llm.py` | Separate LLM adapters and prompts. |
| `app/utils/auth.py` | `mantis/services/auth.py` + `app/utils/auth.py` shim | Keep auth abstraction in services; preserve legacy import path. |
| UI layout + styling in `Mantis_Studio.py` | `mantis/ui/layout.py` | Extract layout/theming + header/footer components. |
| Page renderers in `Mantis_Studio.py` | `mantis/ui/pages/*.py` | One module per page to scale. |
| Navigation logic in `Mantis_Studio.py` | `mantis/router.py` | Central routing + navigation model. |
| Session/state init in `Mantis_Studio.py` | `mantis/state/session.py` | Explicit session initialization + widget key helper. |
| `app/utils/navigation.py` | `mantis/router.py` + `app/utils/navigation.py` shim | Preserve old imports while moving routing. |

## Modules That Must Remain for Streamlit Cloud
- **`Mantis_Studio.py`** must stay at repo root and remain executable by Streamlit Cloud.
- Any Streamlit multipage files under `pages/` remain in place (account/legal pages).

## Backward Compatibility Strategy
- **Legacy imports** (`app.utils.auth`, `app.utils.navigation`) become thin wrappers that re-export from `mantis.*`.
- **Project JSON format** stays unchanged: `Project.save()` and `Project.load()` preserve the same schema and file paths.
- **On-disk paths** remain unchanged by default (`projects/`, backups, config file). No migrations needed.
- **Widget keys** remain stable. Introduce a single `ui_key()` helper that returns the exact key string used today.

## Migration Steps (Incremental)
1. **Plan + scaffolding**: document the tree mapping and create the new `mantis/` package skeleton.
2. **Core extraction**: move settings, models, storage, and LLM services into `mantis/` modules; add shims.
3. **UI extraction**: move layout/theming and page renderers into `mantis/ui` with a router in `mantis/router.py`.
4. **Entrypoint shim**: reduce `Mantis_Studio.py` to import and run `mantis.app.run_app()`.
5. **Docs + smoke test**: add `docs/runbooks/SMOKE_TEST.md` with manual verification steps.

## Risks + Mitigations
- **Widget keys changing** → `ui_key()` returns unchanged key names and is used consistently.
- **Auth/Supabase usage** → keep `app/utils/auth.py` as compatibility wrapper.
- **Project IO changes** → retain `Project.save/load` logic and storage paths; no migrations.
