# MANTIS Test Suite

Canonical test entry:

```bash
python -m pytest tests -q
```

Unified toolbox commands:

```bash
python scripts/full_repo_audit.py
python scripts/toolbox.py health
python scripts/toolbox.py smoke
python scripts/toolbox.py test --target tests
python scripts/toolbox.py qa
```

The full audit runner also compiles/parses Python files, runs selftest, runs
healthcheck, and writes Markdown/JSON output under `artifacts/full_repo_audit/`.
