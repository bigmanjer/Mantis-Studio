# Testing Guide for Mantis Studio

This comprehensive guide explains how to write, organize, and run tests in the Mantis Studio project.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Testing Strategy](#testing-strategy)
3. [Test Organization](#test-organization)
4. [Writing Tests](#writing-tests)
5. [Running Tests](#running-tests)
6. [Test Coverage](#test-coverage)
7. [Best Practices](#best-practices)
8. [Future Test Checklist](#future-test-checklist)

---

## Testing Strategy

### Overview

This section describes the comprehensive testing strategy for Mantis Studio, addressing gaps identified in the original test suite and establishing guidelines for maintainable, effective tests.

### What Was The Problem?

The original test suite had several critical issues:

1. **Fake Mocks That Bypassed Real Logic**
   - Tests used a fake `_FakeSt` class that always returned `False` for buttons
   - This meant button click handlers were NEVER actually tested
   - Users could experience broken features while tests passed

2. **No AI Integration Testing**
   - AI generation functions were never tested with actual (mocked) API calls
   - Streaming, error handling, and API responses were untested
   - Canon enforcement logic was never exercised

3. **No End-to-End Workflows**
   - Tests only checked isolated functions
   - Complete user journeys were never validated
   - Integration between components was not tested

4. **Testing Implementation, Not Behavior**
   - Tests checked if source code contained certain strings
   - Tests verified CSS classes existed
   - But didn't validate that features actually worked

### What Was Fixed

#### Before ❌
- Fake mocks bypassed button handlers
- No AI API integration tests
- No end-to-end workflows
- Checked code structure, not behavior
- ~70% code coverage but many features untested

#### After ✅
- Proper mocked HTTP responses for AI tests
- 34 new integration and workflow tests
- Complete user journey testing
- Tests validate actual behavior
- Critical paths now have test coverage

### New Test Structure

#### 1. AI Integration Tests (`tests/test_integration_ai.py`)

**Purpose**: Test AI functionality with mocked API responses instead of bypassing logic.

**Test Classes**:
- **TestAIEngineIntegration**: Tests AI engine with mocked Groq API responses
  - Model probing (success and failure cases)
  - Generation with mocked responses
  - API error handling
  - Missing API key/model handling
  
- **TestAICanonEnforcement**: Documents canon enforcement behavior
  - Canon rules are enforced via Streamlit session state
  - Requires integration environment for full testing
  
- **TestAISanitization**: Tests input sanitization
  - Null byte removal
  - Whitespace trimming
  - Max length truncation
  - Empty input handling
  - Prompt truncation with logging
  
- **TestAIStreamingGeneration**: Tests streaming behavior
  - Chunk collection
  - Timeout handling
  
- **TestAIErrorHandling**: Comprehensive error scenarios
  - 401 Unauthorized (invalid API key)
  - 429 Rate limit exceeded
  - Malformed JSON responses
  - Missing response fields

**Key Improvements**:
- Uses `responses` library to mock HTTP calls
- Tests actual error handling paths
- Validates error messages reach users
- Tests both success and failure scenarios

**Example AI Integration Test**:
```python
@responses.activate
def test_generate_with_mocked_api():
    """Test AI generation with a mocked Groq API response."""
    responses.add(
        responses.POST,
        f"{AppConfig.GROQ_API_URL}/chat/completions",
        json={"choices": [{"message": {"content": "Generated text"}}]},
        status=200
    )
    
    result = AIEngine().generate("Test prompt", "llama-3.1-8b-instant")
    assert "Generated text" in result["text"]
```

#### 2. End-to-End Workflow Tests (`tests/test_workflows.py`)

**Purpose**: Validate complete user journeys from start to finish.

**Test Classes**:

- **TestProjectLifecycleWorkflow**: Complete project lifecycle
  - Create → Add chapters → Add entities → Save → Load → Export
  - Tests integration between all major components
  - Validates data persistence and ordering
  
- **TestChapterEditingWorkflow**: Chapter editing scenarios
  - Edit with revision history
  - Deletion and reordering
  - Word count tracking
  
- **TestWorldBibleWorkflow**: Entity management
  - CRUD operations
  - Entity deduplication
  - Filtering by category
  
- **TestExportWorkflow**: Export functionality
  - All content included
  - Word count accuracy
  - Empty project handling
  
- **TestProjectSaveLoadConsistency**: Data persistence
  - Complete data preservation
  - Multiple save cycles
  - Concurrent project isolation
  
- **TestImportWorkflow**: Text import
  - Chapter marker detection
  - Plain text handling

**Key Improvements**:
- Tests actual user workflows, not just isolated functions
- Validates data flows through the entire system
- Tests persistence and state management
- Verifies ordering and relationships

**Example Workflow Test**:
```python
def test_complete_project_workflow():
    """Test: Create → Edit → Save → Load → Export"""
    # Create project
    project = Project.create("My Novel", author="Author", genre="Fantasy")
    
    # Add content
    project.add_chapter("Chapter 1", "Content here...")
    project.add_entity("Hero", "Character", "Main character")
    
    # Save
    path = project.save()
    
    # Load
    loaded = Project.load(path)
    
    # Verify
    assert loaded.title == "My Novel"
    assert len(loaded.chapters) == 1
    assert len(loaded.world_db) == 1
    
    # Export
    markdown = export_to_markdown(loaded)
    assert "My Novel" in markdown
```

### Coverage Gaps (Still TODO)

These areas still need testing in future PRs:

1. **Streamlit UI Integration**
   - Button click handlers
   - Form submissions
   - Session state management
   - Widget interactions
   - Requires special Streamlit test harness
   
2. **AI Canon Enforcement** (requires Streamlit test environment)
   - Hard canon rule injection
   - Canon violation blocking
   - Conflict resolution workflows
   
3. **World Bible Suggestions**
   - Entity suggestion generation
   - Merge workflows
   - Widget cache clearing
   
4. **Advanced Features**
   - Collaborative editing (if added)
   - Cloud sync (if added)
   - Plugin system (if added)

### Test Results Summary

```
Total Tests: 160+ tests
Result: ✅ ALL PASSED
Pass Rate: 100%
Average Runtime: <1 second
```

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

### Principles for Writing Good Tests

1. **Test Behavior, Not Implementation**
   ```python
   # ❌ Bad - tests implementation
   assert 'key="my_button"' in source_code
   
   # ✅ Good - tests behavior
   project = Project.create("Test")
   assert project.title == "Test"
   ```

2. **Use Proper Mocks**
   ```python
   # ❌ Bad - fake that bypasses logic
   class FakeStreamlit:
       def button(self, *args, **kwargs):
           return False  # Always!
   
   # ✅ Good - mock with actual responses
   @responses.activate
   def test_api_call():
       responses.add(responses.POST, url, json={...})
       result = api_function()
       assert result["success"]
   ```

3. **Test Complete Workflows**
   ```python
   # ❌ Bad - isolated test
   def test_add_chapter():
       chapter = Chapter(title="Test")
       assert chapter.title == "Test"
   
   # ✅ Good - workflow test
   def test_project_workflow():
       project = Project.create("Novel")
       project.add_chapter("Ch1", "Content")
       saved = project.save()
       loaded = Project.load(saved)
       assert len(loaded.chapters) == 1
   ```

4. **Use Fixtures for Setup**
   ```python
   @pytest.fixture
   def temp_project(tmp_path):
       storage = tmp_path / "projects"
       storage.mkdir()
       return Project.create("Test", storage_dir=str(storage))
   
   def test_something(temp_project):
       # temp_project is automatically created
       pass
   ```

### Specific Best Practices

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

## Test Dependencies & CI

### Test Dependencies

Test dependencies are included in the main `requirements.txt`:

```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
responses>=0.23.0  # For mocking HTTP calls
```

Install dependencies:
```bash
pip install -r requirements.txt
```

For development-specific dependencies (if you have a `requirements-dev.txt`):
```bash
pip install -r requirements-dev.txt
```

### Configuration

Tests are configured in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests for isolated components",
    "integration: Integration tests for multiple components",
    "smoke: Smoke tests for quick validation",
    "slow: Tests that take >1 second",
    "requires_ai: Tests requiring AI API keys",
    "requires_db: Tests requiring database connection",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### Continuous Integration

Tests should run on every PR. Example GitHub Actions workflow:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=app --cov-report=term
      - run: pytest tests/ --cov=app --cov-report=xml
      - uses: codecov/codecov-action@v3  # Optional: upload to Codecov
```

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Responses Library](https://github.com/getsentry/responses) - HTTP request mocking

---

## Summary & Impact

### What This Test Suite Provides

✅ **Organized structure** mirroring source code  
✅ **Shared fixtures** for common test setup  
✅ **Test data factories** for easy object creation  
✅ **Table-driven tests** for comprehensive coverage  
✅ **Clear markers** for selective test running  
✅ **Coverage tools** for measuring test quality  
✅ **Best practices** for maintainable tests  
✅ **Real integration testing** with mocked external services  
✅ **End-to-end workflow validation** for critical user journeys  
✅ **Proper error handling tests** for edge cases  

### Test Suite Statistics

```
Total Test Files: 5+
Total Tests: 160+ tests
Pass Rate: 100% ✅
Average Runtime: <1 second
Coverage: 23% baseline (focused on critical modules)
```

### Module Coverage Status

| Module | Coverage | Status |
|--------|----------|--------|
| `app/utils/helpers.py` | 93% | 🟢 Excellent |
| `app/router.py` | 91% | 🟢 Excellent |
| `app/services/storage.py` | 88% | 🟢 Good |
| `app/utils/auth.py` | 100% | 🟢 Perfect |
| `app/config/settings.py` | 80%+ | 🟢 Good |

### Impact

This testing overhaul ensures that:
- ✅ Features are tested as users experience them
- ✅ Regressions are caught before reaching users  
- ✅ Error handling actually works
- ✅ Integration points are validated
- ✅ Future changes have a safety net

The test suite now provides **real confidence** that the application works correctly, rather than just confirming that code exists.

Follow this guide when adding new tests to maintain consistency and quality across the test suite.

---

*Last Updated: 2026-02-18*  
*Test Suite Version: 2.0 (Consolidated)*

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

