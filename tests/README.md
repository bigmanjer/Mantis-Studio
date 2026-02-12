# Mantis Studio Test Suite

Comprehensive, well-organized test suite for the Mantis Studio project.

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
python scripts/measure_coverage.py --html

# Run specific test categories
pytest -v -m unit              # Unit tests only
pytest -v -m integration       # Integration tests only
pytest -v -m smoke            # Smoke tests only
```

## 📊 Test Statistics

- **Total Tests:** 160+ tests
- **Pass Rate:** 100% ✅
- **Execution Time:** < 1 second
- **Coverage:** 23% baseline (focused on critical modules)

### Module Coverage

| Module | Coverage | Status |
|--------|----------|--------|
| `app/utils/helpers.py` | 93% | 🟢 Excellent |
| `app/router.py` | 91% | 🟢 Excellent |
| `app/services/storage.py` | 88% | 🟢 Good |
| `app/utils/auth.py` | 100% | 🟢 Perfect |
| `app/config/settings.py` | 80%+ | 🟢 Good |

## 📁 File Structure

```
tests/
├── README.md                 # This file
├── __init__.py
├── conftest.py              # Shared fixtures and test utilities
│
├── test_helpers.py          # Tests for app/utils/helpers.py (58 tests)
├── test_router.py           # Tests for app/router.py (29 tests)
├── test_services.py         # Tests for app/services/*.py (38 tests)
├── test_imports.py          # Import smoke tests (35 tests)
│
└── test_ux_smoke.py         # Legacy comprehensive tests (to be refactored)
```

## 🧪 Test Organization

### By Module

- **test_helpers.py** - Utility function tests
  - `word_count()` - 19 parametrized tests
  - `clamp()` - 23 parametrized tests
  - `current_year()` - 3 tests
  - AI connection helpers - 12 tests

- **test_router.py** - Navigation and routing
  - Navigation config - 7 tests
  - Route mapping - 15 tests
  - Integration tests - 4 tests

- **test_services.py** - Service layer
  - Environment parsing - 20 parametrized tests
  - File locking - 5 tests
  - Storage helpers - 3 tests
  - JSON extraction - 11 tests

- **test_imports.py** - Smoke tests
  - Critical imports - 6 tests
  - Service imports - 7 tests
  - View imports - 11 tests
  - Component imports - 9 tests

### By Category (Markers)

```bash
# Unit tests - Test individual functions
pytest -v -m unit

# Integration tests - Test module interactions
pytest -v -m integration

# Smoke tests - Import and basic functionality
pytest -v -m smoke

# Skip slow tests during development
pytest -v -m "not slow"
```

## 🔧 Key Features

### 1. Shared Fixtures (conftest.py)

```python
def test_project_creation(temp_project_dir):
    """Automatic cleanup after test."""
    project = make_project(name="Test")
    # ... test code ...
```

Available fixtures:
- `temp_project_dir` - Temporary project directory
- `temp_storage_dir` - Temporary storage directory
- `clean_env` - Clean environment variables
- `mock_session_state` - Mock Streamlit session state

### 2. Test Data Factories

```python
from conftest import make_project, make_chapter, make_entity

project = make_project(
    name="My Novel",
    chapters=[make_chapter("Chapter 1", "Content")]
)
```

### 3. Table-Driven Tests

```python
@pytest.mark.parametrize(
    "text,expected",
    [
        ("hello world", 2),
        ("", 0),
        (None, 0),
    ],
)
def test_word_count(text, expected):
    assert word_count(text) == expected
```

### 4. Test Markers

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.smoke        # Smoke test
```

## 📖 Documentation

- **[Testing Guide](../docs/guides/testing.md)** - Comprehensive testing guide
  - How to write tests
  - Best practices
  - Running tests
  - Coverage measurement
  - Troubleshooting

- **Test Suite Layout** - Merged into testing guide
  - File structure details
  - Module documentation
  - Test patterns
  - Coverage goals
  - Future improvements

## 🚀 Running Tests

### Basic Commands

```bash
# All tests with verbose output
pytest tests/ -v

# Specific test file
pytest tests/test_helpers.py -v

# Specific test class
pytest tests/test_helpers.py::TestWordCount -v

# Specific test function
pytest tests/test_helpers.py::TestWordCount::test_word_count_parametrized -v

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l

# Run tests in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```

### Coverage Commands

```bash
# Using coverage script (recommended)
python scripts/measure_coverage.py              # Terminal report
python scripts/measure_coverage.py --html       # HTML report
python scripts/measure_coverage.py --all        # All reports

# Manual pytest coverage
pytest tests/ --cov=app --cov-report=term-missing
pytest tests/ --cov=app --cov-report=html
```

### Continuous Testing

```bash
# Install pytest-watch
pip install pytest-watch

# Watch mode
ptw tests/ --runner "pytest -v"
```

## ✅ Best Practices

### 1. Test Naming
- Files: `test_<module_name>.py`
- Classes: `Test<FeatureName>`
- Functions: `test_<what>_<condition>_<result>`

### 2. Test Independence
- Each test should be independent
- Use fixtures for setup/teardown
- Don't share state between tests

### 3. One Assertion Per Test
- Test one thing at a time
- Use parametrize for multiple similar cases
- Makes failures easier to debug

### 4. Use Fixtures
- Avoid manual setup/teardown
- Leverage conftest.py fixtures
- Create new fixtures for common patterns

### 5. Descriptive Names
```python
# Good
def test_word_count_returns_zero_for_empty_string(self):
    assert word_count("") == 0

# Bad
def test1(self):
    assert word_count("") == 0
```

## 🎯 Adding New Tests

### Checklist for New Tests

- [ ] Create test file: `tests/test_<module_name>.py`
- [ ] Add module docstring
- [ ] Create test class: `Test<FeatureName>`
- [ ] Add test functions with descriptive names
- [ ] Use parametrize for similar test cases
- [ ] Add appropriate markers
- [ ] Add docstrings to test functions
- [ ] Use shared fixtures from conftest.py
- [ ] Run tests: `pytest tests/test_<module_name>.py -v`
- [ ] Check coverage: `pytest --cov=app.<module_name>`
- [ ] Update this README if needed

### Example New Test

```python
"""Tests for app/services/new_feature.py

Tests cover:
- Feature 1: Description
- Feature 2: Description
"""
from __future__ import annotations

import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.new_feature import my_function


class TestMyFunction:
    """Test suite for my_function."""
    
    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("test", "expected"),
            ("", "default"),
        ],
    )
    @pytest.mark.unit
    def test_my_function_parametrized(self, input_val, expected):
        """Test my_function with various inputs."""
        assert my_function(input_val) == expected
```

## 🐛 Troubleshooting

### Import Errors

Make sure the path setup is in your test file:
```python
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

### Fixture Not Found

1. Check fixture is defined in `conftest.py`
2. Verify fixture name spelling
3. Ensure `conftest.py` is in `tests/` directory

### Tests Fail in CI But Pass Locally

1. Check for hardcoded paths (use fixtures)
2. Check for environment-specific code
3. Ensure dependencies are in `requirements.txt`
4. Use `pytest -v --tb=long` for detailed output

## 📈 Coverage Goals

| Module Type | Goal | Current |
|------------|------|---------|
| Services | 80%+ | Varies |
| Utilities | 80%+ | 93% (helpers) |
| Router | 90%+ | 91% ✅ |
| Views | 50%+ | Low |
| Components | 60%+ | Low |
| **Overall** | **70%+** | **23%** |

## 🔮 Future Enhancements

- [ ] Split `test_ux_smoke.py` into focused modules
- [ ] Add `test_state.py` for session state
- [ ] Add integration test suite
- [ ] Add performance benchmarks (pytest-benchmark)
- [ ] Add property-based tests (Hypothesis)
- [ ] Add mutation testing (mutmut)
- [ ] Add test data generation (Faker)

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Testing Guide](../docs/guides/testing.md) - Full testing guide
- [Coverage.py](https://coverage.readthedocs.io/)

---

**Test Suite Version:** 1.0.0  
**Last Updated:** 2026-02-12  
**Status:** ✅ Stable - All 160+ tests passing
