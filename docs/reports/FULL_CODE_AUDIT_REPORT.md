# Full Code Audit Report

Date: 2026-06-02

## Scope

This report covers the entire workspace under `mantis testing`: app code,
tests, scripts, docs/legal files, root config files, CSS, and branding assets.

The repo now has a single full-check entry point:

```bash
python scripts/full_repo_audit.py
```

That program inventories every file, records line counts and hashes, compiles
Python files, parses Python AST, scans source-policy risks, runs the built-in
selftest, runs `scripts/healthcheck.py`, and runs the full pytest suite when
pytest is installed.

Outputs:

- `artifacts/full_repo_audit/full_repo_audit.md`
- `artifacts/full_repo_audit/full_repo_audit.json`

The existing toolbox command also delegates to the same runner:

```bash
python scripts/toolbox.py qa
```

## Workspace Inventory

Source inventory from `rg --files`:

| Area | Files | Lines |
| --- | ---: | ---: |
| App Python | 57 | 20,639 |
| Tests | 9 | 3,305 |
| Scripts | 7 | 1,044 |
| Docs and legal | 21 | 1,371 |
| Assets | 7 | 371 text lines |
| Root config/docs | 4 | 273 |
| GitHub/other docs | 12 | 981 |

Total inventory: 118 files.

## Test Organization

Existing test coverage is spread across:

- `tests/test_all.py`: canonical smoke/service subset.
- `tests/test_ux_smoke.py`: broad UX/import/source-policy smoke coverage.
- `tests/test_workflows.py`: project lifecycle, chapters, world bible, export,
  import workflows.
- `tests/test_services.py`: config parsing, file locks, JSON extraction.
- `tests/test_integration_ai.py`: AI integration behavior with mocked HTTP.
- `tests/test_enhanced_sidebar_stability.py`: sidebar rendering and navigation.
- `tests/conftest.py`: fixtures and test data factories.

The new full audit runner executes all tests with:

```bash
python -m pytest tests -q
```

`scripts/toolbox.py test` now uses the same full `tests` target by default.

### Tests vs Scripts

- `tests/` contains pytest assertions for behavior and source contracts.
- `scripts/` contains command-line tools for repo/app operations such as
  healthcheck, smoke runs, visual captures, version bumps, and audit reports.
- Prefer extending `scripts/toolbox.py` or `scripts/full_repo_audit.py` instead
  of adding another standalone maintenance script.

### Export Consolidation

The separate Export page was reviewed against the Projects workflow. Projects
already owns project selection and has the richer export panel, so export remains
a project action rather than a top-level navigation item. The export service
stays in `app/services/export.py`; the redundant `app/views/export.py` wrapper
was removed.

## Fixes Applied During Audit

1. Selftest cleanup is now isolated.
   `app/main.py` creates `projects/selftest_<uuid>` and only removes that
   directory. It no longer removes the whole real `projects` folder.

2. Remaining `unsafe_allow_html=True` app usage was removed.
   Streamlit HTML snippets now use `st.html()`.

3. Legacy `app/app_context.py` canon gating now matches `app/main.py`.
   Canon statuses are `OK`, `WARN`, and `RISK`; Auto-Write only blocks on
   `RISK`.

4. `tests/test_enhanced_sidebar_stability.py` was updated for the current
   sidebar API and routing behavior.

5. `scripts/full_repo_audit.py` was added as the single comprehensive audit
   program.

6. `scripts/toolbox.py qa` now delegates to the full audit runner.

## Executed Checks

Python was located at:

```text
C:\Users\BIGMANJER\AppData\Local\Python\bin\python.exe
```

Executed successfully:

- `python -m pytest tests -q` -> `245 passed`
- `python scripts/full_repo_audit.py` -> selftest PASS, healthcheck PASS, pytest PASS
- Generated audit output under `artifacts/full_repo_audit/`

Confirmed by audit/source search:

- No `unsafe_allow_html` remains in runtime `app/` modules.
- `app/main.py` selftest cleanup targets `selftest_dir`, not the projects root.
- `app/app_context.py` blocks Auto-Write only on `RISK`.
- The full audit runner is present and wired into `scripts/toolbox.py qa`.

## Current Static Risks To Watch

These are not necessarily bugs, but they should stay visible in the generated
audit output:

- `app/main.py` is very large and still contains most runtime behavior. Future
  work should continue moving stable logic into `app/services`, `app/views`, and
  `app/ui_context.py`.
- Broad `except Exception` handlers exist in UI fallback paths and service
  helpers. Most are intentional defensive UI guards, but they should keep
  logging enough context.
- `app/ui/dashboard_components.py` still uses a generated UUID instance value
  for dashboard component keys. Verify this is only for non-persistent layout
  keys and does not reset user inputs unexpectedly.

## How To Run The Full Program

Install requirements first:

```bash
pip install -r requirements.txt
pip install pytest
```

Run the complete audit:

```bash
python scripts/full_repo_audit.py
```

Run without pytest execution, useful for quick source inventory:

```bash
python scripts/full_repo_audit.py --skip-tests
```

Run through the toolbox:

```bash
python scripts/toolbox.py qa
```

Optional browser regression remains separate because it requires a running
Streamlit server and Playwright:

```bash
streamlit run app/main.py --server.port 8510
python scripts/toolbox.py qa --with-visual --base-url http://localhost:8510
```

## Next Execution Gate

For the current complete gate, run:

```bash
python scripts/full_repo_audit.py
```

Treat the generated Markdown and JSON files as the authoritative full-line
audit artifact for the repo.
