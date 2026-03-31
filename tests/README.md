# MANTIS Test Suite

Canonical test entry:

```bash
pytest tests/test_all.py -v
```

Unified toolbox commands:

```bash
python scripts/toolbox.py health
python scripts/toolbox.py smoke
python scripts/toolbox.py test
python scripts/toolbox.py qa --with-visual
```

Archived legacy test modules live in `tests/archive/`.
