"""Shared pytest fixtures and test utilities for Mantis Studio.

This module provides common fixtures, test data factories, and helper
functions used across the test suite.

Fixtures:
    temp_project_dir: Temporary directory for test project files
    sample_project_data: Factory for creating test project data
    clean_env: Clean environment variables for testing
    mock_session_state: Mock Streamlit session state

Test Data Factories:
    make_project: Create a test project with customizable fields
    make_chapter: Create a test chapter
    make_entity: Create a test entity (character, location, etc.)
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest

# Ensure the app package is importable
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================================
# Directory and File Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for project files.
    
    Yields:
        Path to temporary directory that is cleaned up after test.
    
    Example:
        def test_save_project(temp_project_dir):
            project_file = temp_project_dir / "project.json"
            # ... test code ...
    """
    project_dir = tmp_path / "projects"
    project_dir.mkdir(parents=True, exist_ok=True)
    yield project_dir
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary storage directory for test files.
    
    Yields:
        Path to temporary storage directory.
    """
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    yield storage_dir


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def clean_env() -> Generator[Dict[str, str], None, None]:
    """Provide a clean environment for testing.
    
    Saves current environment, yields an empty dict, and restores
    original environment after the test.
    
    Example:
        def test_env_var(clean_env):
            os.environ["TEST_VAR"] = "value"
            # ... test code ...
            # Environment is automatically restored
    """
    original_env = os.environ.copy()
    # Clear test-related vars
    test_vars = [k for k in os.environ if k.startswith("_TEST_")]
    for var in test_vars:
        del os.environ[var]
    
    yield {}
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_session_state() -> Dict[str, Any]:
    """Create a mock Streamlit session state for testing.
    
    Returns:
        Dictionary mimicking st.session_state
    
    Example:
        def test_navigation(mock_session_state):
            mock_session_state["page"] = "home"
            # ... test code ...
    """
    return {
        "page": "home",
        "current_project": None,
        "ai_keys": {},
        "ai_session_keys": {},
        "user": None,
        "authenticated": False,
    }


# ============================================================================
# Test Data Factories
# ============================================================================

def make_project(
    name: str = "Test Project",
    genre: str = "Fantasy",
    target_words: int = 50000,
    **kwargs: Any
) -> Dict[str, Any]:
    """Factory function to create test project data.
    
    Args:
        name: Project name
        genre: Project genre
        target_words: Target word count
        **kwargs: Additional fields to override
    
    Returns:
        Dictionary representing a project
    
    Example:
        project = make_project(name="My Novel", genre="Sci-Fi")
        project = make_project(chapters=[make_chapter("Chapter 1")])
    """
    project = {
        "id": kwargs.get("id", "test-project-001"),
        "name": name,
        "genre": genre,
        "target_words": target_words,
        "tagline": kwargs.get("tagline", "A test project"),
        "synopsis": kwargs.get("synopsis", "This is a test project for unit testing."),
        "chapters": kwargs.get("chapters", []),
        "entities": kwargs.get("entities", {}),
        "outline": kwargs.get("outline", []),
        "metadata": kwargs.get("metadata", {}),
    }
    return project


def make_chapter(
    title: str = "Chapter 1",
    content: str = "This is test content.",
    order: int = 1,
    **kwargs: Any
) -> Dict[str, Any]:
    """Factory function to create test chapter data.
    
    Args:
        title: Chapter title
        content: Chapter content
        order: Chapter order/number
        **kwargs: Additional fields to override
    
    Returns:
        Dictionary representing a chapter
    
    Example:
        chapter = make_chapter("The Beginning", "Once upon a time...")
    """
    return {
        "id": kwargs.get("id", f"chapter-{order}"),
        "title": title,
        "content": content,
        "order": order,
        "word_count": kwargs.get("word_count", len(content.split())),
        "status": kwargs.get("status", "draft"),
        "notes": kwargs.get("notes", ""),
    }


def make_entity(
    name: str = "Test Character",
    entity_type: str = "character",
    **kwargs: Any
) -> Dict[str, Any]:
    """Factory function to create test entity data.
    
    Args:
        name: Entity name
        entity_type: Type of entity (character, location, item, etc.)
        **kwargs: Additional fields to override
    
    Returns:
        Dictionary representing an entity
    
    Example:
        character = make_entity("John Doe", "character", role="protagonist")
        location = make_entity("Castle", "location", description="Ancient castle")
    """
    return {
        "id": kwargs.get("id", f"{entity_type}-{name.lower().replace(' ', '-')}"),
        "name": name,
        "type": entity_type,
        "description": kwargs.get("description", f"A test {entity_type}"),
        "attributes": kwargs.get("attributes", {}),
        "notes": kwargs.get("notes", ""),
    }


# ============================================================================
# Test Helper Functions
# ============================================================================

def assert_project_valid(project: Dict[str, Any]) -> None:
    """Assert that a project dict has required fields.
    
    Args:
        project: Project dictionary to validate
    
    Raises:
        AssertionError: If project is missing required fields
    
    Example:
        project = load_project("test.json")
        assert_project_valid(project)
    """
    required_fields = ["id", "name", "genre", "chapters"]
    for field in required_fields:
        assert field in project, f"Project missing required field: {field}"
    
    assert isinstance(project["chapters"], list), "Chapters must be a list"
    assert isinstance(project.get("entities", {}), dict), "Entities must be a dict"


def assert_chapter_valid(chapter: Dict[str, Any]) -> None:
    """Assert that a chapter dict has required fields.
    
    Args:
        chapter: Chapter dictionary to validate
    
    Raises:
        AssertionError: If chapter is missing required fields
    """
    required_fields = ["id", "title", "content", "order"]
    for field in required_fields:
        assert field in chapter, f"Chapter missing required field: {field}"
    
    assert isinstance(chapter["order"], int), "Order must be an integer"
    assert chapter["order"] >= 0, "Order must be non-negative"


def create_test_project_file(
    project_dir: Path,
    project_data: Optional[Dict[str, Any]] = None
) -> Path:
    """Create a test project JSON file.
    
    Args:
        project_dir: Directory to create project file in
        project_data: Project data (uses make_project() if None)
    
    Returns:
        Path to created project file
    
    Example:
        project_file = create_test_project_file(temp_dir)
    """
    if project_data is None:
        project_data = make_project()
    
    project_file = project_dir / f"{project_data['id']}.json"
    with open(project_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, indent=2)
    
    return project_file


# ============================================================================
# Parametrize Helpers
# ============================================================================

# Common test data sets for parametrized tests
VALID_PROJECT_NAMES = [
    "My Novel",
    "Test Project",
    "A Very Long Project Name That Should Still Work",
    "Project-With-Hyphens",
    "Project_With_Underscores",
]

VALID_GENRES = [
    "Fantasy",
    "Science Fiction",
    "Mystery",
    "Romance",
    "Thriller",
    "Horror",
]

INVALID_STRINGS = [
    "",
    "   ",
    None,
]

EDGE_CASE_NUMBERS = [
    0,
    -1,
    1,
    1000000,
    -1000000,
]
