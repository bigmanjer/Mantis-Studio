# MANTIS Documentation Index

This project keeps only active, non-duplicative docs.

## Core Docs
- [HANDBOOK.md](HANDBOOK.md)
- [CHANGELOG.md](CHANGELOG.md)
- [REPO_STRUCTURE.md](REPO_STRUCTURE.md)
- [../scripts/README.md](../scripts/README.md)

## QA
- [qa/LIGHT_MODE_QA_REPORT.md](qa/LIGHT_MODE_QA_REPORT.md)

## Maintenance Reports
- [reports/DOCS_CONSOLIDATION_REPORT.md](reports/DOCS_CONSOLIDATION_REPORT.md)
- [reports/FULL_CODE_AUDIT_REPORT.md](reports/FULL_CODE_AUDIT_REPORT.md)
- [reports/REPO_CLEANUP_REPORT.md](reports/REPO_CLEANUP_REPORT.md)

## Policy
- Keep root `README.md` concise; put operational instructions in `HANDBOOK.md`.
- Keep historical one-off reports in `docs/reports/`, not in root docs.
- Generated audit output belongs under `artifacts/` and is ignored by git.
- If behavior changes in routing/state/theme/footer/testing, update `HANDBOOK.md` and `CHANGELOG.md` in the same change set.
