# MANTIS Studio Repo Structure

This project should stay organized around runtime responsibility, not feature
age. New code should land in the narrowest folder that owns the behavior.

## Top Level

- `app/` - application code.
- `assets/` - static images, branding, and app media.
- `docs/` - human documentation, audits, and architecture notes.
- `legal/` - policy markdown rendered by the app.
- `projects/` - local runtime data only. Ignored by git except placeholders.
- `scripts/` - developer maintenance scripts and local launcher helpers.
- `tests/` - automated tests.
- `streamlit_app.py` - Streamlit Cloud deployment shim.
- `Mantis_Launcher.bat` - Windows local launcher.
- `VERSION.txt` - source of truth for the displayed app version.

## Application Code

- `app/config/` - app constants, environment config, and config file I/O.
- `app/data/` - bundled source-controlled data such as built-in Knowledge Base documents.
- `app/security/` - encryption, protected storage, signing, and secret handling.
- `app/services/` - business logic and provider clients.
- `app/utils/` - small reusable helpers with minimal app knowledge.
- `app/layout/` - app shell components such as sidebar, header, and footer.
- `app/ui/` - low-level UI styling and helper components.
- `app/views/` - page-level UI modules.
- `app/components/` - reusable Streamlit components.
- `app/models/` - shared data models when they are split out of legacy modules.

## Placement Rules

- OAuth, AI providers, exports, project storage, and World Bible merge logic go in `app/services/`.
- Passwords, OAuth client secrets, encryption, tokens, and signing helpers go in `app/security/`.
- Page rendering belongs in `app/views/`; avoid adding new large pages to `app/main.py`.
- Shared styling belongs in `app/layout/` or `app/ui/`, not inside service modules.
- Runtime data must stay under `projects/`, `logs/`, or `artifacts/`, all ignored by git.
- Script output must go under `artifacts/`; do not write generated reports into the root.
- Local secrets stay in `.streamlit/secrets.toml`, which is ignored by git.
- Keep new top-level files rare. Prefer `docs/`, `scripts/`, `tests/`, `assets/`, or the narrowest `app/` package.

## Runtime Data Layout

Runtime data is intentionally present locally but mostly absent from git:

```text
projects/
+-- .gitkeep                 # tracked placeholder
+-- .backups/.gitkeep        # tracked placeholder for local save backups
+-- .mantis_config.json      # local app config, ignored
+-- .mantis_users.json       # local users, ignored
+-- .knowledge_base/         # local imported learning docs, ignored
+-- guests/                  # guest workspaces, ignored
+-- users/                   # account workspaces, ignored
logs/                        # local launcher and Streamlit logs, ignored
artifacts/                   # generated QA/audit/screenshots, ignored
```

The app may create these folders at runtime. Do not commit user projects,
launcher memory, account files, secrets, logs, screenshots, or generated audit
artifacts.

## Scripts Layout

Use `scripts/README.md` as the index for maintenance tools. Scripts that are
part of the local launcher can stay beside the launcher support files there.
If a script grows into application behavior, move it into `app/services/` or
`app/utils/` and keep `scripts/` as the CLI wrapper only.

## Current Migration Note

`app/main.py` still contains legacy page code and duplicated model logic. New features should avoid growing it further unless they are temporary wiring. As pages are touched, move stable page sections into `app/views/` and business logic into `app/services/`.
