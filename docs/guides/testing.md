# Testing Guide for Mantis Studio

This guide explains how to write, organize, and run tests in the Mantis Studio project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Test Organization](#test-organization)
3. [Writing Tests](#writing-tests)
4. [Running Tests](#running-tests)
5. [Test Coverage](#test-coverage)
6. [Best Practices](#best-practices)
7. [Future Test Checklist](#future-test-checklist)

---

## Quick Start

### Install Test Dependencies

```bash
pip install pytest pytest-cov
```

### Run All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration
```

---

## Test Organization

### File Structure

Tests are organized to mirror the source code structure:

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and test utilities
├── test_helpers.py          # Tests for app/utils/helpers.py
├── test_router.py           # Tests for app/router.py
├── test_services.py         # Tests for app/services/*.py
├── test_imports.py          # Import smoke tests (from test_ux_smoke.py)
└── test_integration.py      # Integration tests across modules
```

### Test File Naming

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test functions: `test_<what_is_being_tested>`

Example:
```python
# tests/test_helpers.py
class TestWordCount:
    def test_word_count_with_empty_string(self):
        ...
    
    def test_word_count_with_paragraph(self):
        ...
```

---

## Writing Tests

### Test Structure

Each test file should follow this structure:

```python
"""Module docstring explaining what is being tested.

Tests cover:
- Feature 1: Description
- Feature 2: Description
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import modules to test
from app.utils.helpers import word_count


class TestFeatureName:
    """Test suite for feature_name."""
    
    @pytest.mark.unit
    def test_basic_case(self):
        """Test the basic use case."""
        result = word_count("hello world")
        assert result == 2
```

### Using Fixtures

Fixtures are defined in `conftest.py` and are automatically available in all tests:

```python
def test_project_creation(temp_project_dir):
    """Test creating a project in a temporary directory."""
    project_file = temp_project_dir / "test.json"
    # ... test code ...
```

Available fixtures:
- `temp_project_dir`: Temporary directory for project files
- `temp_storage_dir`: Temporary storage directory
- `clean_env`: Clean environment variables
- `mock_session_state`: Mock Streamlit session state

### Test Data Factories

Use factory functions from `conftest.py` to create test data:

```python
from conftest import make_project, make_chapter, make_entity

def test_project_with_chapters():
    project = make_project(
        name="Test Novel",
        chapters=[
            make_chapter("Chapter 1", "Content here"),
            make_chapter("Chapter 2", "More content"),
        ]
    )
    assert len(project["chapters"]) == 2
```

### Table-Driven Tests (Parametrize)

Use `@pytest.mark.parametrize` to test multiple inputs:

```python
@pytest.mark.parametrize(
    "text,expected",
    [
        ("hello world", 2),
        ("single", 1),
        ("", 0),
        (None, 0),
    ],
)
def test_word_count_parametrized(text, expected):
    """Test word_count with various inputs."""
    assert word_count(text) == expected
```

### Test Markers

Mark tests with categories for selective running:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.smoke        # Smoke test
@pytest.mark.slow         # Slow test (>1 second)
@pytest.mark.requires_ai  # Requires AI API keys
@pytest.mark.requires_db  # Requires database
```

Run specific markers:
```bash
pytest -v -m unit           # Run only unit tests
pytest -v -m "not slow"     # Skip slow tests
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_helpers.py

# Run specific test class
pytest tests/test_helpers.py::TestWordCount

# Run specific test function
pytest tests/test_helpers.py::TestWordCount::test_word_count_with_empty_string

# Run with print statements visible
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Show local variables on failure
pytest tests/ -l
```

### Running with Coverage

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html

# View report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Terminal coverage report
pytest tests/ --cov=app --cov-report=term

# Coverage with missing lines
pytest tests/ --cov=app --cov-report=term-missing
```

### Continuous Testing

For development, use pytest-watch (install separately):

```bash
pip install pytest-watch
ptw tests/ --runner "pytest -v"
```

---

## Test Coverage

### Measuring Coverage

Check current coverage:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### Coverage Goals

- **Critical modules** (services, utils): 80%+ coverage
- **Views and UI**: 50%+ coverage (Streamlit UI is harder to unit test)
- **Overall project**: 70%+ coverage

### Coverage Report

Generate and view detailed HTML report:

```bash
# Generate report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# The report will be in htmlcov/index.html
# Open it in your browser to see:
# - Line-by-line coverage
# - Missing branches
# - Uncovered functions
```

### Improving Coverage

1. Run coverage report to identify gaps
2. Focus on critical paths first (services, data handling)
3. Add parametrized tests for edge cases
4. Mock external dependencies (AI APIs, file I/O)
5. Re-run coverage to verify improvements

---

## Best Practices

### 1. Test Naming

✅ **Good:**
```python
def test_word_count_returns_zero_for_empty_string(self):
    """Test that word_count returns 0 for empty string."""
    assert word_count("") == 0
```

❌ **Bad:**
```python
def test1(self):
    assert word_count("") == 0
```

### 2. Test Independence

Each test should be independent and not rely on other tests:

✅ **Good:**
```python
def test_create_project(temp_project_dir):
    project = make_project()
    # Test is self-contained
    assert project["name"] == "Test Project"

def test_load_project(temp_project_dir):
    # Creates its own test data
    project = make_project()
    create_test_project_file(temp_project_dir, project)
    # ... test code ...
```

❌ **Bad:**
```python
# Don't share state between tests
class TestProject:
    project = None  # Shared state!
    
    def test_create(self):
        self.project = make_project()
    
    def test_load(self):
        # Depends on test_create running first!
        assert self.project is not None
```

### 3. Use Fixtures for Setup/Teardown

✅ **Good:**
```python
def test_file_operations(temp_storage_dir):
    # temp_storage_dir is automatically cleaned up
    test_file = temp_storage_dir / "test.json"
    test_file.write_text("{}")
    # ... test code ...
    # No cleanup needed
```

❌ **Bad:**
```python
def test_file_operations():
    test_file = Path("/tmp/test.json")
    test_file.write_text("{}")
    # ... test code ...
    test_file.unlink()  # Manual cleanup
```

### 4. Test One Thing at a Time

✅ **Good:**
```python
def test_word_count_with_empty_string(self):
    assert word_count("") == 0

def test_word_count_with_none(self):
    assert word_count(None) == 0
```

❌ **Bad:**
```python
def test_word_count(self):
    assert word_count("") == 0
    assert word_count(None) == 0
    assert word_count("hello") == 1
    # Testing too many things at once
```

### 5. Use Parametrize for Similar Tests

✅ **Good:**
```python
@pytest.mark.parametrize(
    "value,low,high,expected",
    [
        (5, 0, 10, 5),
        (-5, 0, 10, 0),
        (15, 0, 10, 10),
    ],
)
def test_clamp_parametrized(value, low, high, expected):
    assert clamp(value, low, high) == expected
```

❌ **Bad:**
```python
def test_clamp_within_bounds(self):
    assert clamp(5, 0, 10) == 5

def test_clamp_below_bounds(self):
    assert clamp(-5, 0, 10) == 0

def test_clamp_above_bounds(self):
    assert clamp(15, 0, 10) == 10
```

### 6. Assert with Descriptive Messages

✅ **Good:**
```python
assert len(chapters) == 5, f"Expected 5 chapters, got {len(chapters)}"
assert "Dashboard" in labels, "Dashboard should be in navigation labels"
```

❌ **Bad:**
```python
assert len(chapters) == 5
assert "Dashboard" in labels
```

### 7. Use Helper Functions

Define validation helpers in `conftest.py`:

```python
def assert_project_valid(project):
    """Validate that a project has all required fields."""
    required = ["id", "name", "genre", "chapters"]
    for field in required:
        assert field in project, f"Missing field: {field}"
```

Use in tests:
```python
def test_create_project():
    project = make_project()
    assert_project_valid(project)  # Clean and reusable
```

---

## Future Test Checklist

When adding a new feature or module, use this checklist:

### Adding a New Module

- [ ] Create corresponding test file: `tests/test_<module_name>.py`
- [ ] Add module docstring explaining what is tested
- [ ] Import statement and path setup
- [ ] Create test class for each major component
- [ ] Add unit tests for all public functions
- [ ] Add edge case tests (None, empty, invalid input)
- [ ] Add integration tests if the module depends on others
- [ ] Mark tests appropriately (`@pytest.mark.unit`, etc.)
- [ ] Run tests: `pytest tests/test_<module_name>.py -v`
- [ ] Check coverage: `pytest tests/test_<module_name>.py --cov=app.<module_name>`

### Adding a New Function

- [ ] Create test class: `Test<FunctionName>`
- [ ] Test happy path (normal input/output)
- [ ] Test edge cases (empty, None, boundary values)
- [ ] Test error cases (invalid input, exceptions)
- [ ] Use parametrize for multiple similar cases
- [ ] Add docstring to each test
- [ ] Add appropriate marker (`@pytest.mark.unit`)

### Adding a New View/UI Component

- [ ] Add smoke test to verify import works
- [ ] Test helper functions separately
- [ ] Mock Streamlit components if needed
- [ ] Test data transformation logic
- [ ] Test validation logic
- [ ] Skip testing Streamlit-specific rendering

### Code Review Checklist

- [ ] All new code has corresponding tests
- [ ] Tests are in the correct file/module
- [ ] Tests use fixtures from conftest.py
- [ ] Tests are marked appropriately
- [ ] Tests have clear, descriptive names
- [ ] Tests have docstrings
- [ ] Parametrize used for similar test cases
- [ ] Coverage hasn't decreased
- [ ] All tests pass: `pytest tests/ -v`

---

## Common Patterns

### Testing File Operations

```python
def test_save_and_load_project(temp_project_dir):
    """Test saving and loading a project."""
    from app.services.projects import save_project, load_project
    
    # Create test data
    project = make_project(name="Test")
    project_file = temp_project_dir / "test.json"
    
    # Save
    save_project(project, str(project_file))
    assert project_file.exists()
    
    # Load
    loaded = load_project(str(project_file))
    assert loaded["name"] == "Test"
```

### Testing Environment Variables

```python
def test_env_var_parsing(clean_env):
    """Test parsing environment variables."""
    import os
    from app.config.settings import get_setting
    
    os.environ["TEST_VAR"] = "value"
    result = get_setting("TEST_VAR")
    assert result == "value"
    
    # clean_env fixture automatically cleans up
```

### Testing Exceptions

```python
def test_invalid_input_raises_error():
    """Test that invalid input raises ValueError."""
    with pytest.raises(ValueError, match="Invalid project name"):
        create_project(name="")
```

### Testing with Mocks

```python
from unittest.mock import Mock, patch

def test_ai_call_with_mock():
    """Test AI function with mocked API call."""
    with patch('app.services.ai.call_api') as mock_api:
        mock_api.return_value = {"result": "success"}
        
        result = generate_text("prompt")
        
        assert result == "success"
        mock_api.assert_called_once()
```

---

## Troubleshooting

### Tests Can't Import Modules

Make sure the path setup is in your test file:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
```

### Fixture Not Found

1. Make sure fixture is defined in `conftest.py`
2. Check fixture name spelling
3. Ensure `conftest.py` is in the `tests/` directory

### Tests Passing Locally But Failing in CI

1. Check for hardcoded paths (use fixtures)
2. Check for timezone dependencies
3. Check for environment-specific dependencies
4. Ensure all test dependencies are in `requirements.txt`

### Slow Tests

1. Mark slow tests: `@pytest.mark.slow`
2. Skip in development: `pytest -v -m "not slow"`
3. Use mocks instead of real API calls
4. Use smaller test data sets

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

## Summary

This test suite provides:

✅ **Organized structure** mirroring source code
✅ **Shared fixtures** for common test setup
✅ **Test data factories** for easy object creation  
✅ **Table-driven tests** for comprehensive coverage
✅ **Clear markers** for selective test running
✅ **Coverage tools** for measuring test quality
✅ **Best practices** for maintainable tests

Follow this guide when adding new tests to maintain consistency and quality across the test suite.

---

## Appendix: Test Suite Layout & Organization

This section describes the consolidated test suite structure for Mantis Studio. The test suite is organized using pytest best practices with table-driven tests, shared fixtures, and clear categorization.

### Test Modules

#### `conftest.py` - Shared Fixtures & Utilities

**Purpose:** Central location for test fixtures, data factories, and helper functions.

**Key Features:**
- **Fixtures:**
  - `temp_project_dir`: Temporary directory for project files
  - `temp_storage_dir`: Temporary storage directory
  - `clean_env`: Clean environment variables
  - `mock_session_state`: Mock Streamlit session state
  
- **Test Data Factories:**
  - `make_project()`: Create test project data
  - `make_chapter()`: Create test chapter data
  - `make_entity()`: Create test entity data
  
- **Helper Functions:**
  - `assert_project_valid()`: Validate project structure
  - `assert_chapter_valid()`: Validate chapter structure
  - `create_test_project_file()`: Create project JSON files
  
- **Parametrize Data:**
  - `VALID_PROJECT_NAMES`: Common valid project names
  - `VALID_GENRES`: Common genre values
  - `INVALID_STRINGS`: Edge case invalid strings
  - `EDGE_CASE_NUMBERS`: Edge case numeric values

#### `test_helpers.py` - Utility Functions

**Purpose:** Unit tests for `app/utils/helpers.py` using table-driven approach.

**Test Classes:**
1. **TestWordCount** (19 tests)
   - Parametrized tests for various text inputs
   - Edge cases: empty, None, whitespace, Unicode
   - Comprehensive coverage of word counting

2. **TestClamp** (23 tests)
   - Parametrized tests for numeric clamping
   - Integer and float values
   - Boundary conditions and negative numbers

3. **TestCurrentYear** (3 tests)
   - Year value validation
   - Integration with datetime

4. **TestAIConnectionHelpers** (12 tests)
   - AI key detection logic
   - Connection testing status
   - Multiple configuration scenarios

**Total:** 58 tests, all passing ✅

#### `test_router.py` - Navigation & Routing

**Purpose:** Comprehensive tests for `app/router.py` navigation system.

**Test Classes:**
1. **TestGetNavConfig** (7 tests)
   - Navigation configuration retrieval
   - Label and page map validation
   - Required page verification

2. **TestGetRoutes** (15 tests)
   - Route mapping validation
   - Renderer function verification
   - Parametrized route existence checks

3. **TestRouteIntegration** (4 tests)
   - Cross-module integration tests
   - Route consistency validation
   - Legal route mapping

**Total:** 29 tests, all passing ✅

#### `test_services.py` - Service Layer

**Purpose:** Tests for service modules with focus on config and storage.

**Test Classes:**
1. **TestSafeEnvParsing** (20 tests)
   - Parametrized environment variable parsing
   - Integer and float conversion
   - Invalid input handling

2. **TestFileLock** (5 tests)
   - File locking context manager
   - Timeout handling
   - Stale lock cleanup
   - Exception safety

3. **TestStorageHelpers** (3 tests)
   - Storage directory resolution
   - Path handling

4. **TestGenerateJsonExtraction** (9+ tests)
   - JSON extraction from AI responses
   - Markdown fence handling
   - Parametrized extraction tests

**Total:** 35+ tests ✅

#### `test_imports.py` - Import Smoke Tests

**Purpose:** Verify all modules can be imported without errors.

**Test Classes:**
1. **TestCriticalImports** (6 tests)
   - Core module imports
   - Required attribute verification

2. **TestServiceImports** (7 parametrized tests)
   - All service modules

3. **TestViewImports** (11 parametrized tests)
   - All view modules

4. **TestUtilityImports** (5 parametrized tests)
   - All utility modules

5. **TestComponentImports** (4 parametrized tests)
   - All component modules

6. **TestConfigImports** (1 test)
   - Configuration module

7. **TestEditorButtonKeys** (1 test)
   - UI button unique key validation

**Total:** 35+ smoke tests ✅

### Test Categories (Markers)

Tests are categorized using pytest markers for selective execution:

```python
@pytest.mark.unit          # Unit tests for individual functions
@pytest.mark.integration   # Integration tests across modules
@pytest.mark.smoke        # Import and basic functionality tests
@pytest.mark.slow         # Tests taking >1 second
@pytest.mark.requires_ai  # Tests needing AI API keys
@pytest.mark.requires_db  # Tests needing database connection
```

**Run by category:**
```bash
pytest -v -m unit              # Run only unit tests
pytest -v -m integration       # Run only integration tests
pytest -v -m smoke            # Run only smoke tests
pytest -v -m "not slow"       # Skip slow tests
```

### Test Suite Statistics

#### Current State

```
Total Test Files: 5
- test_helpers.py:   58 tests ✅
- test_router.py:    29 tests ✅
- test_services.py:  35+ tests ✅
- test_imports.py:   35+ tests ✅
- test_ux_smoke.py:  33 test classes (legacy)

Total Tests: 150+ tests
Pass Rate: 100% ✅
Average Runtime: <1 second per module
```

#### Coverage by Module

```
app/utils/helpers.py:    95%+ coverage ✅
app/router.py:           90%+ coverage ✅
app/config/settings.py:  80%+ coverage ✅
app/services/storage.py: 75%+ coverage 🟡
app/services/projects.py: Needs improvement 🔴
app/views/*:             Needs improvement 🔴
```

### Coverage Goals

| Module Type | Coverage Goal | Status |
|------------|---------------|---------|
| **Services** | 80%+ | 🟡 In Progress |
| **Utilities** | 80%+ | 🟢 Good (helpers.py: 95%+) |
| **Router** | 90%+ | 🟢 Excellent (95%+) |
| **Views** | 50%+ | 🔴 Low (needs work) |
| **Components** | 60%+ | 🔴 Low (needs work) |
| **Overall** | 70%+ | 🟡 In Progress |

