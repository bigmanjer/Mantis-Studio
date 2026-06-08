# MANTIS Studio

**MANTIS** means **Modular AI Narrative Text Intelligence System**.

MANTIS Studio is a local-first Streamlit workspace for planning, drafting,
tracking canon, using AI assistance, and exporting long-form fiction projects.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

The app opens on the Dashboard in guest mode. You can create a local account
from the sidebar when you want user-specific project folders and admin controls.

## Core Workflow

1. **Dashboard**: view project health, workflow progress, and quick jumps.
2. **Projects**: create, open, import, delete, and manage project files.
3. **Outline**: plan story structure and chapter beats.
4. **Editor**: draft, revise, summarize, and improve chapters.
5. **World Bible**: track characters, locations, items, factions, and lore.
6. **Projects export panel**: generate manuscript/planning outputs from the selected project.
7. **AI Settings**: configure Groq/OpenAI-compatible providers and models.

## Architecture

Canonical runtime:

```bash
streamlit run app/main.py
```

Deployment shim:

```text
streamlit_app.py
```

High-level layout:

```text
app/        Streamlit runtime, routing, UI, services, state, utilities
assets/     Branding images and shared CSS
docs/       Active handbook, changelog, QA, and maintenance reports
legal/      Terms, privacy, copyright, cookie, brand, and support policies
scripts/    Developer, audit, smoke, health, visual, and version tools
tests/      Automated pytest suite
```

`app/main.py` remains the canonical shell. Some render logic still lives there
while the project gradually migrates stable behavior into `app/views/`,
`app/services/`, and shared UI modules.

## Documentation

Start here:

- [Documentation index](docs/README.md)
- [Handbook](docs/HANDBOOK.md)
- [Changelog](docs/CHANGELOG.md)
- [Repo structure guide](docs/REPO_STRUCTURE.md)
- [OAuth setup](docs/OAUTH_SETUP.md)
- [App architecture notes](app/README.md)
- [Legal index](legal/README.md)

## Streamlit Secrets

Hosted recovery emails use Resend through Streamlit secrets. In Streamlit Cloud,
open **App settings > Secrets** and paste TOML like this:

```toml
MANTIS_EMAIL_PROVIDER = "resend"
RESEND_API_KEY = "replace-with-a-new-resend-key"
MANTIS_EMAIL_FROM = "MANTIS Studio <rebusinessmatters@gmail.com>"
MANTIS_APP_URL = "https://mantis-studio.streamlit.app"
```

Rotate any API key that was pasted into chat or screenshots before using it in
production. Resend may require the sender/domain to be verified before delivery.

Current audit/cleanup reports:

- [Full code audit report](docs/reports/FULL_CODE_AUDIT_REPORT.md)
- [Documentation consolidation report](docs/reports/DOCS_CONSOLIDATION_REPORT.md)
- [Repository cleanup report](docs/reports/REPO_CLEANUP_REPORT.md)

## Testing And Audit

Run the full repository audit:

```bash
python scripts/full_repo_audit.py
```

Run the full pytest suite directly:

```bash
python -m pytest tests -q
```

Useful toolbox commands:

```bash
python scripts/toolbox.py health
python scripts/toolbox.py smoke
python scripts/toolbox.py test --target tests
python scripts/toolbox.py qa
```

The audit runner writes:

- `artifacts/full_repo_audit/full_repo_audit.md`
- `artifacts/full_repo_audit/full_repo_audit.json`

## Versioning

Current version: `136.6`.

Current version is stored in [VERSION.txt](VERSION.txt).

To bump locally:

```bash
python scripts/toolbox.py bump
```

Document user-visible changes in [docs/CHANGELOG.md](docs/CHANGELOG.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

Before handing off changes, run:

```bash
python scripts/full_repo_audit.py
```

## Support

- Help: [legal/help.md](legal/help.md)
- Contact: [legal/contact.md](legal/contact.md)
- Issues: [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues)
