# Development Workflow Guide

This guide explains the production-grade development workflow for Mantis Studio.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Making Changes](#making-changes)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Common Tasks](#common-tasks)

---

## Initial Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/bigmanjer/Mantis-Studio.git
cd Mantis-Studio

# Initialize development environment
make init-dev

# Or manually:
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Add API keys for AI providers you want to use
```

### 3. Verify Installation

```bash
# Run health check
make health

# Run comprehensive diagnostics
make diagnose

# Run tests
make test
```

---

## Development Workflow

### Standard Workflow

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# Edit files in app/, tests/, docs/, etc.

# 3. Format your code
make format

# 4. Run linters
make lint

# 5. Run tests
make test

# 6. Commit your changes
git add .
git commit -m "feat: add your feature description"

# 7. Push and create PR
git push origin feature/your-feature-name
```

### Using Make Commands

The `Makefile` provides shortcuts for common tasks:

```bash
make help          # Show all available commands
make install-dev   # Install all dependencies
make test          # Run test suite
make test-coverage # Run tests with coverage report
make lint          # Run linters (flake8, mypy)
make format        # Auto-format code (black, isort)
make format-check  # Check formatting without changes
make run           # Start the application
make clean         # Remove build artifacts
make diagnose      # Run comprehensive diagnostics
```

---

## Code Quality

### Formatting

We use **Black** for code formatting and **isort** for import sorting:

```bash
# Auto-format all code
make format

# Check formatting without making changes
make format-check

# Format specific files
black app/services/ai.py
isort app/services/ai.py
```

### Linting

We use **flake8** for linting and **mypy** for type checking:

```bash
# Run all linters
make lint

# Run individual linters
flake8 app/
mypy app/ --ignore-missing-imports
```

### Code Style Guidelines

- **Line length**: 100 characters (configured in `pyproject.toml`)
- **Imports**: Organized with isort (black profile)
- **Type hints**: Use where appropriate
- **Docstrings**: Required for public functions and classes
- **Comments**: Use sparingly, prefer self-documenting code

---

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test file
pytest tests/test_services.py -v

# Run specific test
pytest tests/test_services.py::TestAIEngine::test_generate -v

# Run tests matching a pattern
pytest -k "test_import" -v
```

### Test Organization

Tests are organized by module:

```
tests/
├── conftest.py              # Test configuration and fixtures
├── test_imports.py          # Import tests
├── test_services.py         # Service layer tests
├── test_router.py           # Router tests
├── test_helpers.py          # Helper function tests
└── test_ux_smoke.py         # Smoke tests
```

### Writing Tests

```python
# tests/test_myfeature.py
import pytest
from app.services import myfeature

class TestMyFeature:
    def test_basic_functionality(self):
        result = myfeature.do_something()
        assert result is not None
        
    def test_edge_case(self):
        with pytest.raises(ValueError):
            myfeature.do_something(invalid=True)
```

---

## Making Changes

### Adding a New Feature

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Add code** in appropriate module:
   - UI code → `app/views/`
   - Business logic → `app/services/`
   - Reusable components → `app/components/`
   - Utilities → `app/utils/`

3. **Add tests** in `tests/`:
   ```python
   # tests/test_your_feature.py
   def test_your_feature():
       # Test implementation
       pass
   ```

4. **Update documentation**:
   - Update README if user-facing
   - Add to CHANGELOG.md
   - Update relevant docs in `docs/`

5. **Format and lint**:
   ```bash
   make format
   make lint
   ```

6. **Run tests**:
   ```bash
   make test
   ```

7. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: add your feature"
   git push origin feature/your-feature
   ```

### Fixing a Bug

1. **Create a bugfix branch**:
   ```bash
   git checkout -b fix/bug-description
   ```

2. **Write a failing test** that reproduces the bug

3. **Fix the bug**

4. **Verify the test passes**:
   ```bash
   make test
   ```

5. **Format and lint**:
   ```bash
   make format
   make lint
   ```

6. **Commit and push**:
   ```bash
   git commit -m "fix: description of bug fix"
   git push origin fix/bug-description
   ```

---

## Pre-commit Hooks

Pre-commit hooks automatically run before each commit to ensure code quality.

### Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

### Configured Hooks

- **Trailing whitespace removal**
- **End-of-file fixer**
- **YAML/JSON/TOML validation**
- **Large file check**
- **Black formatting**
- **isort import sorting**
- **flake8 linting**
- **Bandit security scanning**
- **Markdown linting**

### Bypassing Hooks (Use Sparingly)

```bash
# Skip hooks for a single commit (not recommended)
git commit --no-verify -m "message"
```

---

## Common Tasks

### Update Dependencies

```bash
# Update production dependencies
pip install -r requirements.txt --upgrade
pip freeze > requirements.txt

# Update development dependencies
pip install -r requirements-dev.txt --upgrade
```

### Bump Version

```bash
# Bump patch version (e.g., 89.2 → 89.3)
make bump-version

# Or manually
python scripts/bump_version.py
```

### Clean Build Artifacts

```bash
# Remove all build artifacts, caches, etc.
make clean
```

### Run Application Locally

```bash
# Using Makefile
make run

# Or directly
streamlit run app/main.py

# Windows users
Mantis_Launcher.bat
```

### Generate Documentation

```bash
# Install mkdocs if needed
pip install mkdocs mkdocs-material

# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

---

## Troubleshooting

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.10+
```

### Test Failures

```bash
# Run tests with verbose output
pytest -vv

# Run specific failing test
pytest tests/test_file.py::test_name -vv

# Run diagnostics
make diagnose
```

### Pre-commit Hook Failures

```bash
# Run hooks manually to see errors
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Application Won't Start

```bash
# Run health check
make health

# Run diagnostics
make diagnose

# Check logs
tail -f logs/*.log
```

---

## Best Practices

1. **Always create a branch** for changes
2. **Write tests** for new features and bug fixes
3. **Format code** before committing
4. **Run tests** before pushing
5. **Write clear commit messages** (see `docs/COMMIT_MESSAGES.md`)
6. **Update documentation** when needed
7. **Keep PRs focused** - one feature/fix per PR
8. **Review your changes** before creating a PR

---

## Additional Resources

- **[CONTRIBUTING.md](../../CONTRIBUTING.md)** - Contribution guidelines
- **[Testing Guide](testing.md)** - Detailed testing documentation
- **[Debugging Guide](DEBUGGING_GUIDE.md)** - Troubleshooting help
- **[Architecture](../architecture/APP_STRUCTURE.md)** - Codebase structure

---

**Last Updated**: 2026-02-12  
**Maintained by**: Mantis Studio Team
