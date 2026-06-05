# MANTIS Studio Repo Structure

This project should stay organized around runtime responsibility, not feature
age. New code should land in the narrowest folder that owns the behavior.

## Top Level

- `app/` - application code.
- `assets/` - static images, branding, and app media.
- `docs/` - human documentation, audits, and architecture notes.
- `legal/` - policy markdown rendered by the app.
- `projects/` - local runtime data only. Ignored by git except placeholders.
- `scripts/` - developer maintenance scripts.
- `tests/` - automated tests.

## Application Code

- `app/config/` - app constants, environment config, and config file I/O.
- `app/security/` - encryption, protected storage, signing, and secret handling.
- `app/services/` - business logic and provider clients.
- `app/utils/` - small reusable helpers with minimal app knowledge.
- `app/layout/` - app shell components such as sidebar, header, and footer.
- `app/ui/` - low-level UI styling/helpers and compatibility shims.
- `app/views/` - page-level UI modules.
- `app/components/` - reusable Streamlit components.
- `app/models/` - shared data models when they are split out of legacy modules.

## Placement Rules

- OAuth, AI providers, exports, project storage, and World Bible merge logic go in `app/services/`.
- Passwords, OAuth client secrets, encryption, tokens, and signing helpers go in `app/security/`.
- Page rendering belongs in `app/views/`; avoid adding new large pages to `app/main.py`.
- Shared styling belongs in `app/layout/` or `app/ui/`, not inside service modules.
- Runtime data must stay under `projects/`, `logs/`, or `artifacts/`, all ignored by git.

## Current Migration Note

`app/main.py` still contains legacy page code and duplicated model logic. New features should avoid growing it further unless they are temporary wiring. As pages are touched, move stable page sections into `app/views/` and business logic into `app/services/`.

