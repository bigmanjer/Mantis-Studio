# Documentation Consolidation Report

Date: 2026-06-02

## Goal

Reduce documentation clutter while keeping the repo understandable and legally
safe. Root docs should be concise. Active operating instructions should live in
`docs/HANDBOOK.md`. Historical one-off audit evidence should live in
`docs/reports/` or generated `artifacts/`, not mixed into the root README.

## Active Source Of Truth

Keep these files as active docs:

- `README.md` - concise project landing page.
- `docs/README.md` - documentation index and doc policy.
- `docs/HANDBOOK.md` - setup, workflow, testing, maintenance, and current app conventions.
- `docs/CHANGELOG.md` - user-visible and maintenance changes.
- `app/README.md` - app architecture and runtime entry policy.
- `CONTRIBUTING.md` - contributor workflow.
- `tests/README.md` - test-suite entry points.
- `legal/README.md` - legal index.

## Legal Files

Keep separate unless counsel says otherwise:

- `legal/terms.md`
- `legal/privacy.md`
- `legal/cookie.md`
- `legal/copyright.md`
- `legal/brand_ip_clarity.md`
- `legal/trademark_path.md`

Reason: legal/policy docs are easier to render in-app and review separately.

Potential consolidation:

- `legal/contact.md` can remain separate because it is a simple footer/support target.
- `legal/help.md` overlaps with `docs/HANDBOOK.md`, but it is used as an in-app Help page. Keep it short and user-facing; do not turn it into another handbook.

## Reports And Evidence

Keep as historical reports:

- `docs/reports/REPO_CLEANUP_REPORT.md`
- `docs/reports/FULL_CODE_AUDIT_REPORT.md`
- `docs/reports/DOCS_CONSOLIDATION_REPORT.md`
- `docs/qa/LIGHT_MODE_QA_REPORT.md`

Generated outputs should stay ignored and should not become source docs:

- `artifacts/full_repo_audit/full_repo_audit.md`
- `artifacts/full_repo_audit/full_repo_audit.json`
- `artifacts/visual_regression/*`

## Consolidation Completed

- Replaced the oversized root `README.md` with a concise landing page.
- Removed stale historical audit content from root docs by pointing to `docs/reports/`.
- Updated `docs/README.md` to include the current report index and doc policy.
- Updated `docs/HANDBOOK.md` and `tests/README.md` so testing guidance uses:
  - `python scripts/full_repo_audit.py`
  - `python -m pytest tests -q`
- Updated `legal/help.md` to use current navigation labels.
- Cleaned `docs/CHANGELOG.md` so it starts with the real changelog heading and reflects the full-audit/docs consolidation work.
- Updated `docs/reports/FULL_CODE_AUDIT_REPORT.md` now that Python/pytest were found and executed successfully.

## Redundant Or Stale Items Found

| File | Issue | Decision |
| --- | --- | --- |
| `README.md` | Contained duplicated handbook, architecture, audit, cleanup, and corrupted path text. | Replaced with concise landing page. |
| `docs/HANDBOOK.md` | Testing and Export navigation guidance was stale. | Updated. |
| `tests/README.md` | Pointed to `tests/test_all.py` as canonical. | Updated to full suite and audit runner. |
| `docs/CHANGELOG.md` | Had a duplicate release section before `# Changelog`; stale Export nav note. | Cleaned and updated. |
| `legal/help.md` | Used stale label `AI Tools`. | Updated to `AI Settings`. |
| `docs/reports/FULL_CODE_AUDIT_REPORT.md` | Said executable Python tests could not run. | Updated after real Python/pytest execution. |

## Files That Should Not Be Added Back

- Root-level historical audit sections.
- Duplicate test guides outside `docs/HANDBOOK.md` and `tests/README.md`.
- Runtime-generated audit reports in source-controlled docs.
- Cache docs such as `.pytest_cache/README.md`.

## Recommended Future Cleanup

1. Keep `README.md` under roughly 100 lines.
2. Keep `docs/HANDBOOK.md` as the only operational guide.
3. Keep one report per completed audit under `docs/reports/`.
4. Do not duplicate legal text into root docs; link to `legal/README.md`.
5. Add a small audit check that warns when root README grows too large or when `artifacts/` docs are accidentally copied into `docs/`.

## Tests vs Scripts Decision

`tests/` and `scripts/` should stay separate because they serve different
purposes:

- `tests/`: pytest modules that assert app behavior and source contracts.
- `scripts/`: executable maintenance tools for humans/CI.

Current script consolidation decision:

| Script | Role | Consolidation Decision |
| --- | --- | --- |
| `scripts/full_repo_audit.py` | Canonical all-in-one audit/test/report runner. | Keep as primary. |
| `scripts/toolbox.py` | Human-friendly command wrapper. | Keep as primary wrapper. |
| `scripts/healthcheck.py` | Minimal compile/import check. | Keep as compatibility helper; full audit calls it. |
| `scripts/smoke_test.py` | Direct smoke/selftest wrapper. | Keep as compatibility helper; toolbox/full audit cover it. |
| `scripts/visual_regression_pass.py` | Specialized Playwright screenshot pass. | Keep specialized; expose through toolbox visual command. |
| `scripts/bump_version.py` | Version bump direct entry. | Keep for workflow compatibility; toolbox bump covers it. |
| `scripts/list_sidebar_buttons.py` | Temporary/debug browser helper. | Candidate for archive/removal after visual tooling covers sidebar inventory. |

Future rule: do not add a new standalone script unless it cannot reasonably be
a `toolbox.py` subcommand or a `full_repo_audit.py` check.
