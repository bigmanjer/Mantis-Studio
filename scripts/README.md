# MANTIS Scripts

Developer scripts live here when they are safe to run from the repository root
and are not imported by the Streamlit app as runtime services.

## Script Groups

- `toolbox.py` - command dispatcher for health, smoke, tests, visual QA, and version bump helpers.
- `healthcheck.py`, `smoke_test.py`, `visual_regression_pass.py`, `full_repo_audit.py` - QA and audit commands.
- `bump_version.py` - version file updater used by the toolbox.
- `mantis_launcher_chat.py`, `mantis_banner.py`, `mantis_progress.py`, `mantis_simulator_drills.json` - local launcher support files.
- `list_sidebar_buttons.py` - small inspection utility for sidebar debugging.

## Placement Rules

- App business logic belongs in `app/services/`, not here.
- Streamlit page rendering belongs in `app/views/` or `app/main.py` while migration is in progress.
- Reusable app helpers belong in `app/utils/`, `app/ui/`, or `app/layout/`.
- One-off generated output belongs in `artifacts/`, which is ignored by git.
- Local user data belongs in `projects/`, which is ignored except for placeholder files.
