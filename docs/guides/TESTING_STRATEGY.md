# Testing Strategy for Mantis Studio

## Overview

This document describes the comprehensive testing strategy for Mantis Studio, addressing the gaps identified in the original test suite.

## Problem Statement

The original tests were bypassing real functionality by:
1. Using fake Streamlit mocks that always returned `False` for button clicks
2. Not testing AI integration with actual (mocked) API calls
3. Missing end-to-end workflow tests
4. Testing implementation details instead of user behavior
5. No integration tests for critical user journeys

## New Test Structure

### 1. AI Integration Tests (`tests/test_integration_ai.py`)

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

### 2. End-to-End Workflow Tests (`tests/test_workflows.py`)

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

## Running Tests

### Run All Tests
```bash
python3 -m pytest tests/ -v
```

### Run Only New Tests
```bash
python3 -m pytest tests/test_integration_ai.py tests/test_workflows.py -v
```

### Run with Coverage
```bash
python3 -m pytest tests/ --cov=app --cov-report=html
```

### Run Specific Test Classes
```bash
# AI tests only
python3 -m pytest tests/test_integration_ai.py -v

# Workflow tests only
python3 -m pytest tests/test_workflows.py -v

# Specific test
python3 -m pytest tests/test_workflows.py::TestProjectLifecycleWorkflow::test_complete_project_workflow -v
```

## Test Marks

Tests use pytest marks for categorization:
- `@pytest.mark.unit` - Unit tests for isolated components
- `@pytest.mark.integration` - Integration tests for multiple components
- `@pytest.mark.smoke` - Smoke tests for quick validation

Configure in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "smoke: Smoke tests",
]
```

## What Was Fixed

### Before
- ❌ Fake Streamlit mocks that never executed button handlers
- ❌ No AI API integration tests
- ❌ No end-to-end workflows
- ❌ Tests checked source code structure, not behavior
- ❌ ~70% code coverage, but many features untested

### After
- ✅ Proper mocked HTTP responses for AI tests
- ✅ 34 new integration and workflow tests
- ✅ Complete user journey testing
- ✅ Tests validate actual behavior
- ✅ Critical paths now have test coverage

## Coverage Gaps (Still TODO)

These areas still need testing in future PRs:

1. **Streamlit UI Integration**
   - Button click handlers
   - Form submissions
   - Session state management
   - Widget interactions
   
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

## Best Practices

### For New Tests

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

## Dependencies

Test dependencies are in `requirements-dev.txt`:
```
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
pytest-asyncio>=0.21.0
responses>=0.23.0
```

Install with:
```bash
pip install -r requirements-dev.txt
```

## Continuous Integration

Tests should run on every PR:
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
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v --cov=app
```

## Conclusion

The new test suite provides:
- **Real integration testing** with mocked external services
- **End-to-end workflow validation** for critical user journeys
- **Proper error handling tests** for edge cases
- **Foundation for future testing** of UI and advanced features

This ensures that tests actually validate user-facing functionality rather than just checking that code exists.
