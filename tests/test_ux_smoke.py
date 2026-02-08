"""Comprehensive UX smoke tests for MANTIS Studio.

These tests validate every page and critical function from the user's
standpoint without requiring a running Streamlit server.  They exercise
imports, data-layer operations, navigation config, utility functions,
and the auth stub so that regressions in any module are caught early.
"""
from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---------------------------------------------------------------------------
# 1) Critical imports – every module that the UI depends on must import
# ---------------------------------------------------------------------------

class TestCriticalImports:
    """Verify that all modules the app needs can be imported without error."""

    def test_import_main(self):
        mod = importlib.import_module("app.main")
        assert hasattr(mod, "AppConfig")
        assert hasattr(mod, "Project")
        assert hasattr(mod, "run_selftest")

    def test_import_difflib(self):
        """difflib is required for the editor diff view."""
        import difflib  # noqa: F401
        # Also verify it is imported in app.main
        mod = importlib.import_module("app.main")
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "import difflib" in source

    def test_import_auth_module(self):
        """app.utils.auth must exist and provide stub functions."""
        auth = importlib.import_module("app.utils.auth")
        assert callable(auth.get_current_user)
        assert callable(auth.is_authenticated)
        assert auth.is_authenticated() is False
        assert auth.get_current_user() is None

    def test_import_navigation(self):
        nav = importlib.import_module("app.utils.navigation")
        labels, page_map = nav.get_nav_config(True)
        assert "Dashboard" in labels
        assert page_map.get("Dashboard") == "home"

    def test_import_ui_components(self):
        ui = importlib.import_module("app.components.ui")
        required = ("card", "section_header", "primary_button", "stat_tile", "action_card")
        missing = [name for name in required if not hasattr(ui, name)]
        assert not missing, f"Missing UI helpers: {', '.join(missing)}"

    def test_import_keys(self):
        keys = importlib.import_module("app.utils.keys")
        assert callable(keys.ui_key)
        assert callable(keys.scoped_key)

    def test_import_versioning(self):
        ver = importlib.import_module("app.utils.versioning")
        assert hasattr(ver, "get_app_version")

    def test_import_ui_theme(self):
        importlib.import_module("app.ui.theme")

    def test_import_ui_layout(self):
        importlib.import_module("app.ui.layout")

    def test_import_ui_components_file(self):
        importlib.import_module("app.ui.components")

    def test_import_services_projects(self):
        importlib.import_module("app.services.projects")

    def test_import_services_storage(self):
        importlib.import_module("app.services.storage")

    def test_import_services_export(self):
        importlib.import_module("app.services.export")


# ---------------------------------------------------------------------------
# 2) Project CRUD – the core data model that all pages rely on
# ---------------------------------------------------------------------------

class TestProjectCRUD:
    """Verify create / save / load / delete lifecycle."""

    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.storage = str(tmp_path / "projects")
        os.makedirs(self.storage, exist_ok=True)

    def _make_project(self, title="Test", **kw):
        from app.main import Project
        return Project.create(title, storage_dir=self.storage, **kw)

    def test_create_project(self):
        p = self._make_project("My Story", author="Author", genre="Fantasy")
        assert p.title == "My Story"
        assert p.author == "Author"
        assert p.genre == "Fantasy"
        assert p.id  # non-empty UUID

    def test_save_and_load_project(self):
        from app.main import Project
        p = self._make_project("Save Test")
        p.outline = "Chapter 1: The Beginning"
        path = p.save()
        assert os.path.exists(path)

        loaded = Project.load(path)
        assert loaded.title == "Save Test"
        assert loaded.outline == "Chapter 1: The Beginning"

    def test_add_chapter(self):
        p = self._make_project()
        ch = p.add_chapter("First Chapter", "Hello world")
        assert ch.word_count == 2
        assert ch.title == "First Chapter"
        assert len(p.chapters) == 1

    def test_chapter_ordering(self):
        p = self._make_project()
        p.add_chapter("One", "a")
        p.add_chapter("Two", "b")
        p.add_chapter("Three", "c")
        ordered = p.get_ordered_chapters()
        assert [c.index for c in ordered] == [1, 2, 3]

    def test_total_word_count(self):
        p = self._make_project()
        p.add_chapter("A", "one two three")
        p.add_chapter("B", "four five")
        assert p.get_total_word_count() == 5

    def test_add_entity(self):
        p = self._make_project()
        ent = p.add_entity("Alice", "Character", "Protagonist")
        assert ent is not None
        assert ent.name == "Alice"
        assert ent.category == "Character"

    def test_delete_entity(self):
        p = self._make_project()
        ent = p.add_entity("Bob", "Character", "Sidekick")
        assert ent.id in p.world_db
        p.delete_entity(ent.id)
        assert ent.id not in p.world_db

    def test_upsert_entity_merge(self):
        p = self._make_project()
        p.upsert_entity("Alice", "Character", "Hero", allow_merge=True)
        p.upsert_entity("Alice", "Character", "Also brave", allow_merge=True)
        # Should not create a duplicate
        chars = [e for e in p.world_db.values() if e.name == "Alice"]
        assert len(chars) == 1

    def test_import_text_file(self):
        p = self._make_project()
        text = "Chapter 1: Intro\nSome content\n\nChapter 2: Middle\nMore content"
        count = p.import_text_file(text)
        assert count >= 1

    def test_delete_file(self):
        from app.main import Project
        p = self._make_project()
        path = p.save()
        assert os.path.exists(path)
        Project.delete_file(path)
        assert not os.path.exists(path)

    def test_to_dict_roundtrip(self):
        from app.main import Project
        p = self._make_project("Roundtrip")
        p.add_chapter("Ch1", "content here")
        p.add_entity("Ent1", "Location", "A place")
        d = p.to_dict()
        assert d["title"] == "Roundtrip"
        assert "chapters" in d
        assert "world_db" in d


# ---------------------------------------------------------------------------
# 3) Export – verify markdown generation (Export page logic)
# ---------------------------------------------------------------------------

class TestExport:
    """Test the export-to-markdown function used by the Export page."""

    def test_project_to_markdown(self):
        from app.main import Project, project_to_markdown
        p = Project.create("Export Test", storage_dir=tempfile.mkdtemp())
        p.genre = "Sci-Fi"
        p.outline = "Plot outline here"
        p.add_chapter("Ch 1", "Story content")
        p.add_entity("Ship", "Location", "A spaceship")

        md = project_to_markdown(p)
        assert "# Export Test" in md
        assert "Sci-Fi" in md
        assert "Plot outline here" in md
        assert "Story content" in md
        assert "Ship" in md

    def test_empty_project_export(self):
        from app.main import Project, project_to_markdown
        p = Project.create("Empty", storage_dir=tempfile.mkdtemp())
        md = project_to_markdown(p)
        assert "# Empty" in md


# ---------------------------------------------------------------------------
# 4) Navigation – sidebar routing config
# ---------------------------------------------------------------------------

class TestNavigation:
    """Verify navigation config used by the sidebar."""

    def test_nav_config_returns_expected_pages(self):
        from app.utils.navigation import get_nav_config
        labels, page_map = get_nav_config(True)
        expected_labels = {"Dashboard", "Projects"}
        assert expected_labels.issubset(set(labels))

    def test_nav_page_map_has_home(self):
        from app.utils.navigation import get_nav_config
        _, page_map = get_nav_config(True)
        assert page_map.get("Dashboard") == "home"


# ---------------------------------------------------------------------------
# 5) Auth stub – must not crash the app
# ---------------------------------------------------------------------------

class TestAuth:
    """Verify the auth stub module provides the expected interface."""

    def test_get_current_user_returns_none(self):
        from app.utils.auth import get_current_user
        assert get_current_user() is None

    def test_is_authenticated_returns_false(self):
        from app.utils.auth import is_authenticated
        assert is_authenticated() is False


# ---------------------------------------------------------------------------
# 6) Utility functions
# ---------------------------------------------------------------------------

class TestUtilities:
    def test_sanitize_chapter_title(self):
        from app.main import sanitize_chapter_title
        assert sanitize_chapter_title("  Hello World  ") == "Hello World"
        assert sanitize_chapter_title("") == ""
        assert sanitize_chapter_title("**Bold**") == "Bold"
        assert sanitize_chapter_title('"Quoted"') == "Quoted"

    def test_rewrite_prompt(self):
        from app.main import rewrite_prompt
        result = rewrite_prompt("Sample text", "Fix Grammar")
        assert "Fix Grammar" in result
        assert "Sample text" in result

    def test_rewrite_prompt_custom(self):
        from app.main import rewrite_prompt
        result = rewrite_prompt("Text", "Custom", "Make it funny")
        assert "Make it funny" in result

    def test_app_version(self):
        from app.main import get_app_version
        version = get_app_version()
        assert version  # non-empty string

    def test_truncate_prompt(self):
        from app.main import _truncate_prompt
        long_text = "a" * 100
        result = _truncate_prompt(long_text, 50)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# 7) Rewrite presets – used by the Editor page
# ---------------------------------------------------------------------------

class TestRewritePresets:
    """Verify the rewrite presets are complete and usable."""

    def test_presets_not_empty(self):
        from app.main import REWRITE_PRESETS
        assert len(REWRITE_PRESETS) > 0

    def test_custom_preset_exists(self):
        from app.main import REWRITE_PRESETS
        assert "Custom" in REWRITE_PRESETS

    def test_all_presets_have_descriptions(self):
        from app.main import REWRITE_PRESETS
        for name, desc in REWRITE_PRESETS.items():
            assert desc.strip(), f"Preset '{name}' has empty description"


# ---------------------------------------------------------------------------
# 8) Entity matching – World Bible fuzzy matching
# ---------------------------------------------------------------------------

class TestEntityMatching:
    """Verify entity fuzzy matching used by the World Bible page."""

    def test_normalize_category(self):
        from app.main import Project
        assert Project._normalize_category("character") == "Character"
        assert Project._normalize_category("LOCATION") == "Location"
        assert Project._normalize_category("faction") == "Faction"
        assert Project._normalize_category("lore") == "Lore"

    def test_normalize_entity_name(self):
        from app.main import Project
        assert Project._normalize_entity_name("  Alice  ") == "alice"

    def test_names_match_exact(self):
        from app.main import Project
        assert Project._names_match("Alice", "Alice")

    def test_names_match_case_insensitive(self):
        from app.main import Project
        assert Project._names_match("alice", "Alice")

    def test_names_no_match(self):
        from app.main import Project
        assert not Project._names_match("Alice", "Bob")


# ---------------------------------------------------------------------------
# 9) Chapter operations – Editor page logic
# ---------------------------------------------------------------------------

class TestChapterOperations:
    """Test chapter content and revision operations used by the Editor."""

    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.storage = str(tmp_path / "projects")
        os.makedirs(self.storage, exist_ok=True)

    def test_chapter_update_content(self):
        from app.main import Project
        p = Project.create("Test", storage_dir=self.storage)
        ch = p.add_chapter("Ch1", "original")
        ch.update_content("updated text", "manual")
        assert ch.content == "updated text"
        assert ch.word_count == 2

    def test_chapter_revision_history(self):
        from app.main import Project
        p = Project.create("Test", storage_dir=self.storage)
        ch = p.add_chapter("Ch1", "v1")
        ch.update_content("v2 text", "manual")
        assert len(ch.history) >= 1

    def test_chapter_restore_revision(self):
        from app.main import Project
        p = Project.create("Test", storage_dir=self.storage)
        ch = p.add_chapter("Ch1", "original text")
        ch.update_content("modified text", "manual")
        ch.restore_revision("original text")
        assert ch.content == "original text"


# ---------------------------------------------------------------------------
# 10) AppConfig – configuration sanity
# ---------------------------------------------------------------------------

class TestAppConfig:
    """Verify application configuration defaults."""

    def test_app_name(self):
        from app.main import AppConfig
        assert AppConfig.APP_NAME == "MANTIS Studio"

    def test_projects_dir_set(self):
        from app.main import AppConfig
        assert AppConfig.PROJECTS_DIR

    def test_max_upload_positive(self):
        from app.main import AppConfig
        assert AppConfig.MAX_UPLOAD_MB > 0

    def test_max_prompt_chars_positive(self):
        from app.main import AppConfig
        assert AppConfig.MAX_PROMPT_CHARS > 0

    def test_getting_started_url(self):
        from app.main import AppConfig
        assert "github.com" in AppConfig.GETTING_STARTED_URL


# ---------------------------------------------------------------------------
# 11) Selftest – verify the built-in selftest still works
# ---------------------------------------------------------------------------

class TestSelftest:
    """The built-in selftest exercises save/load/chapter/entity/export."""

    def test_selftest_passes(self):
        from app.main import run_selftest
        assert run_selftest() == 0


# ---------------------------------------------------------------------------
# 12) update_locked_chapters – must be defined (previously missing)
# ---------------------------------------------------------------------------

class TestUpdateLockedChapters:
    """Verify the update_locked_chapters function exists in source.

    This function was previously missing, causing NameError when
    canon violations were detected or resolved.
    """

    def test_function_referenced_in_source(self):
        """Verify that update_locked_chapters is both called and defined."""
        source = Path(ROOT / "app" / "main.py").read_text(encoding="utf-8")
        # It should be called in multiple places
        assert source.count("update_locked_chapters()") >= 5
        # It should be defined
        assert "def update_locked_chapters" in source


# ---------------------------------------------------------------------------
# 13) difflib availability check
# ---------------------------------------------------------------------------

class TestDifflibAvailability:
    """Verify that difflib is properly imported for the diff view."""

    def test_difflib_imported_in_main(self):
        source = Path(ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "import difflib" in source

    def test_difflib_unified_diff_works(self):
        import difflib
        a = ["line1", "line2", "line3"]
        b = ["line1", "line2 modified", "line3"]
        diff = list(difflib.unified_diff(a, b, fromfile="a", tofile="b"))
        assert len(diff) > 0


# ---------------------------------------------------------------------------
# 14) Auto-write scoping fix validation
# ---------------------------------------------------------------------------

class TestAutoWriteScoping:
    """Verify the auto-write variable scoping bug is fixed.

    Previously, `full` was defined inside `if st.button(...)` but
    referenced outside it, causing a NameError on every editor render.
    """

    def test_full_variable_properly_scoped(self):
        source = Path(ROOT / "app" / "main.py").read_text(encoding="utf-8")
        # Find the auto-write section and verify `full` is not used outside
        # the button block. The fix moved the post-generation code inside
        # the if-block. We verify by checking that `if full.strip():` does
        # NOT appear at a lower indent level than `if st.button(`.
        lines = source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            if stripped.startswith("if full.strip():"):
                # This line should be indented MORE than the auto_write button block
                # (i.e., it must be inside the button's if-block)
                indent = len(line) - len(stripped)
                # Look back to find the enclosing st.button
                for j in range(i - 1, max(i - 20, 0), -1):
                    prev_stripped = lines[j].lstrip()
                    if "auto_label" in prev_stripped and "st.button" in prev_stripped:
                        button_indent = len(lines[j]) - len(prev_stripped)
                        assert indent > button_indent, (
                            f"'if full.strip():' at line {i+1} is not properly "
                            f"scoped inside the st.button block at line {j+1}"
                        )
                        break


# ---------------------------------------------------------------------------
# 16) Helpers module
# ---------------------------------------------------------------------------


class TestHelpers:
    """Tests for app.utils.helpers utility functions."""

    def test_word_count_basic(self):
        from app.utils.helpers import word_count
        assert word_count("hello world") == 2

    def test_word_count_empty(self):
        from app.utils.helpers import word_count
        assert word_count("") == 0

    def test_word_count_none(self):
        from app.utils.helpers import word_count
        assert word_count(None) == 0

    def test_clamp_in_range(self):
        from app.utils.helpers import clamp
        assert clamp(5, 0, 10) == 5

    def test_clamp_below(self):
        from app.utils.helpers import clamp
        assert clamp(-1, 0, 10) == 0

    def test_clamp_above(self):
        from app.utils.helpers import clamp
        assert clamp(15, 0, 10) == 10

    def test_current_year(self):
        from app.utils.helpers import current_year
        assert current_year() >= 2026


# ---------------------------------------------------------------------------
# 17) Layout duplicate removal – styles.py must no longer exist
# ---------------------------------------------------------------------------


class TestLayoutConsolidation:
    """Verify that the duplicate styles.py was removed."""

    def test_styles_py_removed(self):
        styles_path = ROOT / "app" / "layout" / "styles.py"
        assert not styles_path.exists(), "app/layout/styles.py should be removed"

    def test_layout_module_still_importable(self):
        mod = importlib.import_module("app.layout.layout")
        assert hasattr(mod, "get_theme_tokens")
        assert hasattr(mod, "apply_theme")

    def test_footer_year_is_dynamic(self):
        from app.layout.layout import _CURRENT_YEAR
        assert _CURRENT_YEAR >= 2026

    def test_ui_footer_year_is_dynamic(self):
        from app.ui.layout import _CURRENT_YEAR
        assert _CURRENT_YEAR >= 2026
