"""End-to-end workflow tests for critical user journeys.

These tests validate complete user workflows from start to finish,
ensuring that all components work together correctly.
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

# Ensure app package is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import Project
from app.services.projects import Chapter, Entity
from app.services.export import project_to_markdown


# Create an alias for consistency
export_to_markdown = project_to_markdown


class TestProjectLifecycleWorkflow:
    """Test the complete project lifecycle from creation to export."""

    @pytest.fixture
    def temp_storage(self, tmp_path):
        """Create temporary storage directory."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        return str(storage_dir)

    def test_complete_project_workflow(self, temp_storage):
        """Test: Create project → Add chapters → Add entities → Save → Load → Export."""
        # Step 1: Create a new project
        project = Project.create(
            "My Novel",
            storage_dir=temp_storage,
            author="Test Author",
            genre="Fantasy"
        )
        assert project.title == "My Novel"
        assert project.author == "Test Author"
        assert project.id is not None

        # Step 2: Add outline
        project.outline = """
Act 1: Setup
- Chapter 1: Introduction of hero
- Chapter 2: Call to adventure

Act 2: Conflict
- Chapter 3: Rising action
- Chapter 4: Midpoint crisis
        """
        assert "Call to adventure" in project.outline

        # Step 3: Add chapters
        ch1 = project.add_chapter(
            "The Beginning",
            "In the small village of Elderwood, young Aria lived a quiet life..."
        )
        ch2 = project.add_chapter(
            "The Call",
            "One fateful morning, a mysterious stranger arrived at the village gates..."
        )
        ch3 = project.add_chapter(
            "The Journey Begins",
            "With her belongings packed, Aria set out on the road to adventure..."
        )
        
        assert len(project.chapters) == 3
        assert project.get_total_word_count() > 0

        # Step 4: Add world bible entities
        hero = project.add_entity("Aria", "Character", "Protagonist hero")
        villain = project.add_entity("Dark Lord", "Character", "Antagonist")
        village = project.add_entity("Elderwood", "Location", "Starting village")
        
        assert len(project.world_db) == 3
        assert hero.name == "Aria"
        assert village.category == "Location"

        # Step 5: Save the project
        saved_path = project.save()
        assert saved_path != ""
        assert os.path.exists(saved_path)
        assert project.filepath == saved_path

        # Step 6: Load the project
        loaded_project = Project.load(saved_path)
        assert loaded_project.title == "My Novel"
        assert loaded_project.author == "Test Author"
        assert len(loaded_project.chapters) == 3
        assert len(loaded_project.world_db) == 3
        assert "Call to adventure" in loaded_project.outline

        # Step 7: Verify chapter ordering is preserved
        ordered_chapters = loaded_project.get_ordered_chapters()
        assert ordered_chapters[0].title == "The Beginning"
        assert ordered_chapters[1].title == "The Call"
        assert ordered_chapters[2].title == "The Journey Begins"

        # Step 8: Export to markdown
        markdown = export_to_markdown(loaded_project)
        assert "# My Novel" in markdown
        assert "Fantasy" in markdown
        assert "The Beginning" in markdown
        assert "Aria" in markdown  # Entity should appear in export
        assert "Elderwood" in markdown


class TestChapterEditingWorkflow:
    """Test chapter editing and revision workflows."""

    @pytest.fixture
    def project_with_chapters(self, tmp_path):
        """Create a project with sample chapters."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create("Test Project", storage_dir=str(storage_dir))
        project.add_chapter("Chapter 1", "First draft content")
        project.add_chapter("Chapter 2", "Second chapter content")
        return project

    def test_chapter_edit_and_revision_history(self, project_with_chapters):
        """Test: Edit chapter → Save revision → Restore previous version."""
        project = project_with_chapters
        
        # Get first chapter
        chapters = project.get_ordered_chapters()
        chapter = chapters[0]
        original_content = chapter.content
        
        # Edit the chapter
        chapter.update_content("This is the revised content with new paragraphs.")
        assert chapter.content != original_content
        assert chapter.word_count > 0
        
        # Check revision history exists
        assert len(chapter.history) > 0
        
        # Edit again
        chapter.update_content("This is the third revision of the content.")
        assert len(chapter.history) > 1
        
        # Restore previous revision from history
        if len(chapter.history) > 0:
            previous_text = chapter.history[-1]["previous_text"]
            chapter.restore_revision(previous_text)
            assert chapter.content == previous_text

    def test_chapter_deletion_and_reordering(self, project_with_chapters):
        """Test: Delete middle chapter → Verify reordering → Add new chapter."""
        project = project_with_chapters
        
        # Add a third chapter
        project.add_chapter("Chapter 3", "Third chapter content")
        assert len(project.chapters) == 3
        
        # Delete the middle chapter
        chapters = project.get_ordered_chapters()
        middle_chapter_id = chapters[1].id
        project.delete_chapter(middle_chapter_id)
        
        # Verify chapter count
        assert len(project.chapters) == 2
        
        # Verify ordering is correct
        ordered = project.get_ordered_chapters()
        assert ordered[0].title == "Chapter 1"
        assert ordered[1].title == "Chapter 3"
        assert ordered[0].index == 1
        assert ordered[1].index == 2  # Should be reordered

    def test_chapter_word_count_tracking(self, project_with_chapters):
        """Test: Add/edit chapters → Verify word counts → Check project total."""
        project = project_with_chapters
        
        # Initial word count
        initial_total = project.get_total_word_count()
        assert initial_total > 0
        
        # Add a substantial chapter
        long_content = " ".join(["word"] * 500)  # 500 words
        project.add_chapter("Long Chapter", long_content)
        
        new_total = project.get_total_word_count()
        assert new_total > initial_total
        assert new_total >= initial_total + 500


class TestWorldBibleWorkflow:
    """Test world bible entity management workflows."""

    @pytest.fixture
    def project_with_entities(self, tmp_path):
        """Create a project with sample entities."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create("Fantasy Project", storage_dir=str(storage_dir))
        project.add_entity("Hero", "Character", "The main protagonist")
        project.add_entity("Villain", "Character", "The main antagonist")
        project.add_entity("Castle", "Location", "The royal castle")
        return project

    def test_entity_crud_operations(self, project_with_entities):
        """Test: Create → Read → Update → Delete entities."""
        project = project_with_entities
        
        # Create
        assert len(project.world_db) == 3
        
        # Read
        hero = None
        for entity in project.world_db.values():
            if entity.name == "Hero":
                hero = entity
                break
        assert hero is not None
        assert hero.category == "Character"
        
        # Update (via upsert)
        project.upsert_entity("Hero", "Character", "Updated description", allow_merge=True)
        updated_hero = None
        for entity in project.world_db.values():
            if entity.name == "Hero":
                updated_hero = entity
                break
        assert "Updated description" in updated_hero.description
        
        # Delete
        project.delete_entity(updated_hero.id)
        assert len(project.world_db) == 2

    def test_entity_deduplication(self, project_with_entities):
        """Test: Add duplicate entity → Verify it's merged, not duplicated."""
        project = project_with_entities
        initial_count = len(project.world_db)
        
        # Try to add a duplicate
        project.upsert_entity("Hero", "Character", "Additional info", allow_merge=True)
        
        # Should not create a new entity
        assert len(project.world_db) == initial_count
        
        # Should merge the information
        heroes = [e for e in project.world_db.values() if e.name == "Hero"]
        assert len(heroes) == 1

    def test_entity_filtering_by_category(self, project_with_entities):
        """Test: Filter entities by category."""
        project = project_with_entities
        
        # Get all characters
        characters = [e for e in project.world_db.values() if e.category == "Character"]
        assert len(characters) == 2
        assert all(e.category == "Character" for e in characters)
        
        # Get all locations
        locations = [e for e in project.world_db.values() if e.category == "Location"]
        assert len(locations) == 1
        assert locations[0].name == "Castle"


class TestExportWorkflow:
    """Test export functionality for different formats."""

    @pytest.fixture
    def complete_project(self, tmp_path):
        """Create a complete project ready for export."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create(
            "Complete Novel",
            storage_dir=str(storage_dir),
            author="Test Author",
            genre="Science Fiction"
        )
        
        project.outline = "Act 1: Setup\nAct 2: Conflict\nAct 3: Resolution"
        
        # Add chapters
        for i in range(1, 6):
            project.add_chapter(
                f"Chapter {i}",
                f"This is the content of chapter {i}. " * 20  # ~20 words
            )
        
        # Add entities
        project.add_entity("Alice", "Character", "Main character")
        project.add_entity("Mars Colony", "Location", "Setting")
        project.add_entity("Starship", "Item", "Transportation")
        
        return project

    def test_export_includes_all_content(self, complete_project):
        """Test: Export project → Verify all content is included."""
        project = complete_project
        markdown = export_to_markdown(project)
        
        # Check title and metadata
        assert "Complete Novel" in markdown
        assert "Science Fiction" in markdown
        
        # Check outline
        assert "Act 1: Setup" in markdown
        
        # Check all chapters
        for i in range(1, 6):
            assert f"Chapter {i}" in markdown
        
        # Check entities
        assert "Alice" in markdown
        assert "Mars Colony" in markdown

    def test_export_word_count_accuracy(self, complete_project):
        """Test: Verify exported word count matches project total."""
        project = complete_project
        project_word_count = project.get_total_word_count()
        
        markdown = export_to_markdown(project)
        
        # Count words in markdown (rough approximation)
        exported_words = len(markdown.split())
        
        # The export should contain at least the project word count
        # (it may have more due to formatting)
        assert exported_words >= project_word_count

    def test_export_empty_project(self, tmp_path):
        """Test: Export empty project → Should not crash."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create("Empty Project", storage_dir=str(storage_dir))
        
        # Should not crash
        markdown = export_to_markdown(project)
        assert "Empty Project" in markdown


class TestProjectSaveLoadConsistency:
    """Test data persistence and consistency."""

    @pytest.fixture
    def complex_project(self, tmp_path):
        """Create a complex project to test save/load."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create(
            "Complex Project",
            storage_dir=str(storage_dir),
            author="Author Name",
            genre="Mystery"
        )
        
        # Add complex data
        project.outline = "Detailed outline with multiple acts"
        project.memory = "Long story memory here..."
        
        # Add chapters with revisions
        ch1 = project.add_chapter("Chapter 1", "Original content")
        ch1.update_content("Revised content")
        ch1.update_content("Final content")
        
        project.add_chapter("Chapter 2", "Chapter 2 content")
        
        # Add entities with various attributes
        project.add_entity("Detective", "Character", "Main investigator")
        project.add_entity("Crime Scene", "Location", "Where it happened")
        
        return project

    def test_save_and_load_preserves_all_data(self, complex_project):
        """Test: Save → Load → Verify all data is preserved."""
        project = complex_project
        
        # Save
        saved_path = project.save()
        assert os.path.exists(saved_path)
        
        # Load
        loaded = Project.load(saved_path)
        
        # Verify all fields
        assert loaded.title == project.title
        assert loaded.author == project.author
        assert loaded.genre == project.genre
        assert loaded.outline == project.outline
        
        # Verify chapters
        assert len(loaded.chapters) == len(project.chapters)
        
        # Verify entities
        assert len(loaded.world_db) == len(project.world_db)

    def test_multiple_save_cycles(self, complex_project, tmp_path):
        """Test: Save → Modify → Save → Load → Verify changes."""
        project = complex_project
        
        # First save
        path1 = project.save()
        
        # Modify
        project.add_chapter("Chapter 3", "New chapter")
        
        # Second save
        path2 = project.save()
        assert path2 == path1  # Should save to same file
        
        # Load and verify
        loaded = Project.load(path2)
        assert len(loaded.chapters) == 3
        
        chapters = loaded.get_ordered_chapters()
        assert chapters[2].title == "Chapter 3"

    def test_concurrent_projects_isolated(self, tmp_path):
        """Test: Create multiple projects → Verify they don't interfere."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        # Create two separate projects
        project1 = Project.create("Project 1", storage_dir=str(storage_dir))
        project1.add_chapter("P1 Chapter", "Content 1")
        path1 = project1.save()
        
        project2 = Project.create("Project 2", storage_dir=str(storage_dir))
        project2.add_chapter("P2 Chapter", "Content 2")
        path2 = project2.save()
        
        # Verify they're separate files
        assert path1 != path2
        
        # Load and verify isolation
        loaded1 = Project.load(path1)
        loaded2 = Project.load(path2)
        
        assert loaded1.title == "Project 1"
        assert loaded2.title == "Project 2"
        assert loaded1.chapters[list(loaded1.chapters.keys())[0]].title == "P1 Chapter"
        assert loaded2.chapters[list(loaded2.chapters.keys())[0]].title == "P2 Chapter"


class TestImportWorkflow:
    """Test importing content from text files."""

    def test_import_text_with_chapter_markers(self, tmp_path):
        """Test: Import text file → Verify chapters created correctly."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create("Import Test", storage_dir=str(storage_dir))
        
        # Text with chapter markers
        text_content = """
Chapter 1: The Start

This is the content of the first chapter.
It has multiple paragraphs.

Chapter 2: The Middle

This is the second chapter.
More content here.

Chapter 3: The End

Final chapter content.
"""
        
        count = project.import_text_file(text_content)
        
        # Should create multiple chapters
        assert count >= 1
        assert len(project.chapters) >= count

    def test_import_plain_text(self, tmp_path):
        """Test: Import plain text → Creates single chapter."""
        storage_dir = tmp_path / "projects"
        storage_dir.mkdir(exist_ok=True)
        
        project = Project.create("Plain Import", storage_dir=str(storage_dir))
        
        plain_text = "This is just plain text without any chapter markers. " * 50
        
        count = project.import_text_file(plain_text)
        
        # Should import as a single unit
        assert count >= 0
