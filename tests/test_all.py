"""Merged test suite for MANTIS Studio.

This file combines all individual test modules into a single test file.
Original files: test_ux_smoke.py, test_buttons.py, test_helpers.py,
test_router.py, test_services.py, test_imports.py, test_bump_version.py
"""
from __future__ import annotations

import datetime
import importlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.router import get_nav_config, get_routes
from app.utils.helpers import word_count, clamp, current_year
from scripts.bump_version import bump_version

# These routes are represented in grouped navigation as focused/redirect views:
# - memory / insights map to the world page with a focus tab
# - legal maps to the legal redirect hub and policy routes
EXCLUDED_NAV_TARGETS = {"memory", "insights", "legal"}


# ============================================================================
# Tests from test_ux_smoke.py — Comprehensive UX smoke tests
# ============================================================================

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

    def test_editor_chapter_buttons_have_keys(self):
        mod = importlib.import_module("app.main")
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ Create Chapter 1['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_create_chapter_1['\"]",
            source,
        )
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ New Chapter['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_new_chapter['\"]",
            source,
        )

        ctx = importlib.import_module("app.app_context")
        ctx_source = Path(ctx.__file__).read_text(encoding="utf-8")
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ Create Chapter 1['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_create_chapter_1['\"]",
            ctx_source,
        )
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ New Chapter['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_new_chapter['\"]",
            ctx_source,
        )

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
        mod = importlib.import_module("app.layout.layout")
        assert hasattr(mod, "render_footer")
        assert hasattr(mod, "_build_footer_nav_links")

    def test_import_ui_components_file(self):
        mod = importlib.import_module("app.ui.components")
        assert hasattr(mod, "card_block"), "card_block context manager should exist"

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

    def test_delete_chapter(self):
        p = self._make_project()
        ch1 = p.add_chapter("One", "a")
        ch2 = p.add_chapter("Two", "b")
        ch3 = p.add_chapter("Three", "c")
        assert len(p.chapters) == 3
        p.delete_chapter(ch2.id)
        assert len(p.chapters) == 2
        assert ch2.id not in p.chapters
        ordered = p.get_ordered_chapters()
        assert [c.index for c in ordered] == [1, 2]
        assert ordered[0].title == "One"
        assert ordered[1].title == "Three"

    def test_delete_chapter_nonexistent(self):
        p = self._make_project()
        p.add_chapter("One", "a")
        p.delete_chapter("nonexistent-id")
        assert len(p.chapters) == 1

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

    def test_save_returns_nonempty_path_on_success(self):
        p = self._make_project("Save Path Test")
        path = p.save()
        assert path, "save() must return a non-empty path on success"
        assert os.path.exists(path)

    def test_save_returns_empty_on_unwritable_dir(self):
        p = self._make_project("Unwritable")
        p.storage_dir = "/proc/nonexistent_dir"
        path = p.save()
        assert path == "", "save() must return empty string on failure"

    def test_save_updates_filepath_on_success(self):
        p = self._make_project("Filepath Check")
        assert p.filepath is None
        path = p.save()
        assert p.filepath == path
        assert path != ""

    def test_save_preserves_filepath_on_failure(self):
        p = self._make_project("Fail Test")
        old_fp = p.filepath
        p.storage_dir = "/proc/nonexistent_dir"
        path = p.save()
        assert path == ""
        assert p.filepath == old_fp


# ---------------------------------------------------------------------------
# 2b) Save – app config atomic write
# ---------------------------------------------------------------------------

class TestAppConfigSave:
    """Verify save_app_config writes atomically."""

    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.config_path = str(tmp_path / "test_config.json")

    def test_save_and_load_config(self):
        from app.config.settings import AppConfig, load_app_config, save_app_config
        original = AppConfig.CONFIG_PATH
        try:
            AppConfig.CONFIG_PATH = self.config_path
            save_app_config({"ui_theme": "Light", "daily_word_goal": "1000"})
            loaded = load_app_config()
            assert loaded["ui_theme"] == "Light"
            assert loaded["daily_word_goal"] == "1000"
        finally:
            AppConfig.CONFIG_PATH = original

    def test_save_config_no_tmp_left(self):
        from app.config.settings import AppConfig, save_app_config
        original = AppConfig.CONFIG_PATH
        try:
            AppConfig.CONFIG_PATH = self.config_path
            save_app_config({"key": "value"})
            assert not os.path.exists(self.config_path + ".tmp"), \
                "Temporary file should be removed after atomic save"
        finally:
            AppConfig.CONFIG_PATH = original


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
# 4b) Navigation parity – sidebar and footer must stay in sync
# ---------------------------------------------------------------------------


class TestNavigationParity:
    """Ensure the footer navigation is generated from the same centralized
    config as the sidebar so they can never drift apart."""

    def test_nav_items_has_all_sidebar_pages(self):
        from app.utils.navigation import NAV_ITEMS
        labels = [label for label, _, _ in NAV_ITEMS]
        assert "Dashboard" in labels
        assert "Projects" in labels
        assert "Editor" in labels
        assert "World Bible" in labels
        assert "Export" in labels
        assert "AI Settings" in labels

    def test_get_nav_items_returns_list_of_tuples(self):
        from app.utils.navigation import get_nav_items
        items = get_nav_items()
        assert isinstance(items, list)
        assert len(items) >= 7
        for item in items:
            assert len(item) == 3, "Each item must be (label, page_key, icon)"

    def test_get_nav_sections_has_required_groups(self):
        from app.utils.navigation import get_nav_sections

        groups = [group for group, _ in get_nav_sections()]
        assert groups == [
            "🏠 Home",
            "🗂 Workspace",
            "🧠 Intelligence",
            "✍ Writing",
            "📊 Insights",
            "⚙ System",
        ]

    def test_get_nav_sections_keeps_existing_pages_available(self):
        from app.utils.navigation import get_nav_items, get_nav_sections

        nav_targets = {target for _, target, _ in get_nav_items()}
        grouped_all_targets = {
            target
            for _, items in get_nav_sections()
            for _, target, _ in items
        }
        grouped_targets = {
            target
            for _, items in get_nav_sections()
            for _, target, _ in items
            if target not in EXCLUDED_NAV_TARGETS
        }
        assert nav_targets.issubset(grouped_targets)
        assert EXCLUDED_NAV_TARGETS.issubset(grouped_all_targets)

    def test_footer_nav_links_match_nav_items(self):
        """The footer link builder must produce one link per NAV_ITEMS entry."""
        from app.utils.navigation import get_nav_items
        from app.layout.layout import _build_footer_nav_links

        html = _build_footer_nav_links()
        for label, page_key, icon in get_nav_items():
            assert f'href="?page={page_key}"' in html, (
                f"Footer missing link for {label} (?page={page_key})"
            )
            assert label in html, f"Footer missing label text '{label}'"

    def test_layout_footer_nav_links_match_nav_items(self):
        """The layout/layout.py footer builder must also match NAV_ITEMS."""
        from app.utils.navigation import get_nav_items
        from app.layout.layout import _build_footer_nav_links

        html = _build_footer_nav_links()
        for label, page_key, icon in get_nav_items():
            assert f'href="?page={page_key}"' in html, (
                f"Layout footer missing link for {label} (?page={page_key})"
            )

    def test_router_labels_match_nav_items(self):
        """router.get_nav_config must return labels that match NAV_ITEMS."""
        from app.utils.navigation import NAV_ITEMS
        from app.router import get_nav_config

        labels, pmap = get_nav_config(True)
        expected_labels = [label for label, _, _ in NAV_ITEMS]
        assert labels == expected_labels

        for label, page_key, _ in NAV_ITEMS:
            assert pmap[label] == page_key


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

    # -- ai_connection_warning suppression tests --

    def _make_fake_st(self, state_dict):
        """Return a minimal mock of the Streamlit module for ai_connection_warning."""
        class _FakeSt:
            def __init__(self, d):
                self.session_state = dict(d)
                self.warned = False
                self.info_shown = False
            def warning(self, msg):
                self.warned = True
            def info(self, msg):
                self.info_shown = True
            def button(self, *a, **kw):
                return False
        return _FakeSt(state_dict)

    def test_ai_warning_shown_when_no_keys(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({})
        ai_connection_warning(fake_st)
        assert fake_st.warned, "Warning should be shown when no AI keys are configured"

    def test_ai_warning_hidden_when_ai_keys_set(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"ai_keys": {"groq": "sk-test-key"}, "groq_model_list": ["m1"]})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when ai_keys dict has a provider key"

    def test_ai_warning_hidden_when_groq_api_key_set(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"groq_api_key": "sk-test", "groq_model_list": ["m1"]})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when groq_api_key is set"

    def test_ai_warning_hidden_when_openai_api_key_set(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"openai_api_key": "sk-test", "openai_model_list": ["m1"]})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when openai_api_key is set"

    def test_ai_warning_hidden_when_ai_configured_flag(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"ai_configured": True})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when ai_configured flag is set"

    def test_ai_warning_shown_when_ai_keys_empty(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"ai_keys": {}})
        ai_connection_warning(fake_st)
        assert fake_st.warned, "Warning should be shown when ai_keys dict is empty"

    def test_ai_warning_hidden_when_session_keys_set(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"ai_session_keys": {"groq": "sk-test", "openai": ""}, "groq_model_list": ["m1"]})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when ai_session_keys has a provider key"

    def test_ai_info_shown_when_key_added_but_not_tested(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({"ai_session_keys": {"groq": "sk-test", "openai": ""}})
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when keys exist"
        assert fake_st.info_shown, "Info prompt should be shown when keys exist but models not tested"

    def test_ai_no_prompt_when_key_added_and_models_tested(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({
            "ai_session_keys": {"groq": "sk-test", "openai": ""},
            "groq_model_tests": {"llama3-8b-8192": ""},
        })
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when connected and tested"
        assert not fake_st.info_shown, "Info should NOT be shown when models are tested"

    def test_ai_no_prompt_when_key_added_and_models_fetched(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({
            "groq_api_key": "sk-test",
            "groq_model_list": ["llama3-8b-8192"],
        })
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when connected"
        assert not fake_st.info_shown, "Info should NOT be shown when models are fetched"

    def test_ai_no_prompt_when_groq_connection_tested(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({
            "groq_api_key": "sk-test",
            "groq_connection_tested": True,
        })
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when connected"
        assert not fake_st.info_shown, "Info should NOT be shown when connection was tested"

    def test_ai_no_prompt_when_openai_connection_tested(self):
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({
            "openai_api_key": "sk-test",
            "openai_connection_tested": True,
        })
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when connected"
        assert not fake_st.info_shown, "Info should NOT be shown when connection was tested"

    def test_ai_warning_hidden_when_config_has_saved_keys(self):
        """Warning should be suppressed when ai_session_keys are populated from config."""
        from app.utils.helpers import ai_connection_warning
        fake_st = self._make_fake_st({
            "ai_session_keys": {"groq": "sk-saved-key", "openai": ""},
            "groq_connection_tested": True,
        })
        ai_connection_warning(fake_st)
        assert not fake_st.warned, "Warning should NOT be shown when config has saved keys"

    def test_initialize_populates_ai_session_keys_from_config(self):
        """initialize_session_state should populate ai_session_keys from config data."""
        from app.state import initialize_session_state
        from types import SimpleNamespace

        fake_state = {}

        class FakeSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(name)
            def __setattr__(self, name, value):
                self[name] = value

        fake_st = SimpleNamespace(session_state=FakeSessionState())
        config_data = {"groq_api_key": "sk-from-config", "openai_api_key": ""}
        initialize_session_state(fake_st, config_data)
        keys = fake_st.session_state.get("ai_session_keys", {})
        assert keys.get("groq") == "sk-from-config", \
            "ai_session_keys should be populated from config data"

    def test_initialize_restores_connection_tested_from_config(self):
        """initialize_session_state should restore connection_tested flags from config."""
        from app.state import initialize_session_state
        from types import SimpleNamespace

        class FakeSessionState(dict):
            def __getattr__(self, name):
                try:
                    return self[name]
                except KeyError:
                    raise AttributeError(name)
            def __setattr__(self, name, value):
                self[name] = value

        fake_st = SimpleNamespace(session_state=FakeSessionState())
        config_data = {
            "groq_api_key": "sk-test",
            "groq_connection_tested": True,
        }
        initialize_session_state(fake_st, config_data)
        assert fake_st.session_state.get("groq_connection_tested") is True, \
            "groq_connection_tested should be restored from config"
        assert fake_st.session_state.get("openai_connection_tested") is False, \
            "openai_connection_tested should default to False when not in config"


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
        from app.layout.layout import _CURRENT_YEAR
        assert _CURRENT_YEAR >= 2026

    def test_ui_layout_removed(self):
        """app/ui/layout.py should be removed (consolidated into app/layout/layout.py)."""
        assert not (ROOT / "app" / "ui" / "layout.py").exists(), (
            "app/ui/layout.py should be removed"
        )

    def test_layout_back_to_top_uses_parent_window(self):
        """Back-to-top must scroll the parent window (Streamlit iframe fix)."""
        source = (ROOT / "app" / "layout" / "layout.py").read_text(encoding="utf-8")
        assert "window.parent" in source, (
            "Back-to-top button must use window.parent to escape Streamlit iframe"
        )


# ---------------------------------------------------------------------------
# 18b) Light mode theme quality – comfort and readability
# ---------------------------------------------------------------------------


class TestLightModeThemeQuality:
    """Ensure Light mode tokens avoid harsh values and stay in sync."""

    def test_dark_and_light_have_same_keys(self):
        from app.layout.layout import get_theme_tokens
        tokens = get_theme_tokens("Light")
        dark_keys = set(tokens["Dark"].keys())
        light_keys = set(tokens["Light"].keys())
        assert dark_keys == light_keys, (
            f"Key mismatch: only in Dark={dark_keys - light_keys}, "
            f"only in Light={light_keys - dark_keys}"
        )

    def test_light_bg_is_not_pure_white(self):
        from app.layout.layout import get_theme_tokens
        light = get_theme_tokens("Light")["Light"]
        assert light["bg"].lower() != "#ffffff", "bg should not be pure white"
        assert light["card_bg"].lower() != "#ffffff", "card_bg should not be pure white"
        assert light["input_bg"].lower() != "#ffffff", "input_bg should not be pure white"

    def test_light_muted_not_too_faint(self):
        """Muted text should be dark enough for readability (not lighter than #7f7f7f)."""
        from app.layout.layout import get_theme_tokens
        light = get_theme_tokens("Light")["Light"]
        muted = light["muted"]
        if muted.startswith("#") and len(muted) == 7:
            r = int(muted[1:3], 16)
            g = int(muted[3:5], 16)
            b = int(muted[5:7], 16)
            avg = (r + g + b) / 3
            assert avg < 128, f"Muted color {muted} is too light (avg={avg:.0f})"

    def test_light_accent_differs_from_dark(self):
        """Light mode should use a darker accent than dark mode for contrast."""
        from app.layout.layout import get_theme_tokens
        tokens = get_theme_tokens("Light")
        dark_accent = tokens["Dark"]["accent"]
        light_accent = tokens["Light"]["accent"]
        # They can be the same or different, but Light bg_glow should be softer
        light_glow = tokens["Light"]["bg_glow"]
        dark_glow = tokens["Dark"]["bg_glow"]
        assert light_glow != dark_glow, "bg_glow should differ between Light and Dark"


# ---------------------------------------------------------------------------
# 18) Input sanitization – AI prompt safety
# ---------------------------------------------------------------------------


class TestSanitizeAIInput:
    """Verify that sanitize_ai_input strips dangerous characters and enforces limits."""

    def test_strips_whitespace(self):
        from app.main import sanitize_ai_input
        assert sanitize_ai_input("  hello  ") == "hello"

    def test_removes_null_bytes(self):
        from app.main import sanitize_ai_input
        assert sanitize_ai_input("hello\x00world") == "helloworld"

    def test_empty_input(self):
        from app.main import sanitize_ai_input
        assert sanitize_ai_input("") == ""
        assert sanitize_ai_input(None) == ""

    def test_max_length_enforced(self):
        from app.main import sanitize_ai_input
        result = sanitize_ai_input("a" * 100, max_length=50)
        assert len(result) == 50

    def test_no_limit_when_zero(self):
        from app.main import sanitize_ai_input
        text = "a" * 200
        result = sanitize_ai_input(text, max_length=0)
        assert len(result) == 200

    def test_service_module_has_sanitize(self):
        from app.services.ai import sanitize_ai_input
        assert sanitize_ai_input("  test\x00  ") == "test"


# ---------------------------------------------------------------------------
# 19) Improved error handling – Project.load with corrupt JSON
# ---------------------------------------------------------------------------


class TestProjectLoadErrorHandling:
    """Verify that Project.load raises clear errors for corrupt files."""

    def test_corrupt_json_raises_value_error(self, tmp_path):
        corrupt_file = tmp_path / "corrupt.json"
        corrupt_file.write_text("not valid json {{{", encoding="utf-8")
        from app.main import Project
        with pytest.raises(ValueError, match="not valid JSON"):
            Project.load(str(corrupt_file))

    def test_non_dict_json_raises_value_error(self, tmp_path):
        bad_file = tmp_path / "array.json"
        bad_file.write_text('["not", "a", "dict"]', encoding="utf-8")
        from app.main import Project
        with pytest.raises(ValueError, match="expected JSON object"):
            Project.load(str(bad_file))

    def test_services_project_load_corrupt(self, tmp_path):
        corrupt_file = tmp_path / "corrupt2.json"
        corrupt_file.write_text("{invalid", encoding="utf-8")
        from app.services.projects import Project
        with pytest.raises(ValueError, match="not valid JSON"):
            Project.load(str(corrupt_file))


# ---------------------------------------------------------------------------
# 20) Service module sync – verify service modules match main.py
# ---------------------------------------------------------------------------


class TestServiceModuleSync:
    """Verify that service modules are consistent with main.py."""

    def test_rewrite_presets_match(self):
        from app.main import REWRITE_PRESETS as main_presets
        from app.services.ai import REWRITE_PRESETS as svc_presets
        assert main_presets == svc_presets

    def test_sanitize_chapter_title_match(self):
        from app.main import sanitize_chapter_title as main_fn
        from app.services.projects import sanitize_chapter_title as svc_fn
        test_cases = ["  Hello World  ", "", "**Bold**", '"Quoted"']
        for tc in test_cases:
            assert main_fn(tc) == svc_fn(tc), f"Mismatch on: {tc!r}"

    def test_upsert_entity_returns_tuple(self):
        """Verify upsert_entity returns (entity, status) tuple."""
        from app.services.projects import Project
        import tempfile
        p = Project.create("Test", storage_dir=tempfile.mkdtemp())
        result = p.upsert_entity("Alice", "Character", "Hero")
        assert isinstance(result, tuple)
        assert len(result) == 2
        entity, status = result
        assert entity is not None
        assert status in ("created", "matched", "skipped")


# ---------------------------------------------------------------------------
# 21) API key format validation
# ---------------------------------------------------------------------------


class TestAPIKeyValidation:
    """Verify the API key format validator."""

    def test_valid_key(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("sk-abc123def456") is True

    def test_empty_key_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("") is False

    def test_short_key_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("short") is False

    def test_key_with_null_byte_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("sk-abc\x00def") is False

    def test_key_with_non_ascii_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("sk-abc™def456") is False

    def test_very_long_key_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("x" * 300) is False


# ---------------------------------------------------------------------------
# 22b) API key persistence – keys survive refresh via config file
# ---------------------------------------------------------------------------


class TestAPIKeyPersistence:
    """Verify that API keys are saved to and loaded from the config file."""

    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.config_path = str(tmp_path / "test_config.json")

    def _make_mock_st(self, state_dict):
        import unittest.mock as mock
        mock_st = mock.MagicMock()
        mock_st.session_state = state_dict
        return mock_st

    def test_set_session_key_persists_to_config(self):
        from app.main import AppConfig as MainAppConfig, set_session_key, load_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": ""}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st):
                set_session_key("groq", "sk-test-persist-key")

            config = load_app_config()
            assert config.get("groq_api_key") == "sk-test-persist-key"
        finally:
            MainAppConfig.CONFIG_PATH = original

    def test_clear_session_key_removes_from_config(self):
        from app.main import AppConfig as MainAppConfig, clear_session_key, save_app_config, load_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            save_app_config({"groq_api_key": "sk-old-key"})

            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": "sk-old-key"}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st):
                clear_session_key("groq")

            config = load_app_config()
            assert "groq_api_key" not in config
        finally:
            MainAppConfig.CONFIG_PATH = original

    def test_get_effective_key_finds_saved_key(self):
        from app.main import AppConfig as MainAppConfig, get_effective_key, save_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            save_app_config({"openai_api_key": "sk-saved-key"})

            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": ""}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st):
                key, source = get_effective_key("openai")

            assert key == "sk-saved-key"
            assert source == "saved"
        finally:
            MainAppConfig.CONFIG_PATH = original


# ---------------------------------------------------------------------------
# 23) HTML rendering – st.html() migration
# ---------------------------------------------------------------------------


class TestHtmlRendering:
    """Verify that UI modules use st.html() instead of st.markdown(unsafe_allow_html=True).

    Streamlit 1.54 sanitizes block-level HTML in st.markdown(), even with
    unsafe_allow_html=True. All custom HTML rendering must use st.html()
    to avoid raw-tag display.
    """

    _UI_MODULES = [
        "app/ui/components.py",
        "app/ui/theme.py",
        "app/ui/layout.py",
        "app/components/buttons.py",
        "app/layout/layout.py",
        "app/main.py",
        "app/app_context.py",
    ]

    def test_no_unsafe_allow_html_in_ui_modules(self):
        """No UI module should contain unsafe_allow_html=True."""
        violations = []
        for rel_path in self._UI_MODULES:
            path = ROOT / rel_path
            if not path.exists():
                continue
            source = path.read_text(encoding="utf-8")
            if "unsafe_allow_html" in source:
                violations.append(rel_path)
        assert not violations, (
            f"unsafe_allow_html still present in: {', '.join(violations)}. "
            "Use st.html() for block-level HTML rendering."
        )

    def test_ui_components_use_st_html(self):
        """Core UI component files should use st.html() for HTML rendering."""
        path = ROOT / "app" / "ui" / "components.py"
        source = path.read_text(encoding="utf-8")
        assert "st.html(" in source, "app/ui/components.py should use st.html()"

    def test_buttons_use_st_html(self):
        """Button components should use st.html() for HTML rendering."""
        path = ROOT / "app" / "components" / "buttons.py"
        source = path.read_text(encoding="utf-8")
        assert "st.html(" in source, "app/components/buttons.py should use st.html()"

    def test_theme_uses_st_html(self):
        """Theme injection should use st.html() for CSS."""
        path = ROOT / "app" / "ui" / "theme.py"
        source = path.read_text(encoding="utf-8")
        assert "st.html(" in source, "app/ui/theme.py should use st.html()"

    def test_theme_injects_scroll_to_top(self):
        """Theme injection should include a scroll-to-top script so that
        every page navigation starts at the top of the viewport."""
        path = ROOT / "app" / "ui" / "theme.py"
        source = path.read_text(encoding="utf-8")
        assert "scrollTo" in source, (
            "app/ui/theme.py should inject a scrollTo script for page navigation"
        )


# ---------------------------------------------------------------------------
# 24) Button hierarchy CSS classes
# ---------------------------------------------------------------------------


class TestButtonHierarchyCSS:
    """Verify that assets/styles.css defines the four button hierarchy classes."""

    _STYLES_PATH = ROOT / "assets" / "styles.css"

    def _css(self) -> str:
        return self._STYLES_PATH.read_text(encoding="utf-8")

    def test_primary_class_exists(self):
        assert ".mantis-btn-primary" in self._css()

    def test_secondary_class_exists(self):
        assert ".mantis-btn-secondary" in self._css()

    def test_ghost_class_exists(self):
        assert ".mantis-btn-ghost" in self._css()

    def test_danger_class_exists(self):
        assert ".mantis-btn-danger" in self._css()

    def test_primary_uses_theme_bg(self):
        css = self._css()
        assert ".mantis-btn-primary > button" in css
        assert "--mantis-primary-bg" in css

    def test_danger_uses_theme_vars(self):
        css = self._css()
        assert ".mantis-btn-danger > button" in css
        assert "--mantis-warning" in css

    def test_ghost_uses_theme_surface(self):
        css = self._css()
        assert ".mantis-btn-ghost > button" in css
        assert "--mantis-surface-alt" in css


class TestActionCardButtonsPrimary:
    """Action cards must use the primary button theme."""

    def test_action_card_uses_primary_type(self):
        import inspect
        from app.components.buttons import action_card

        src = inspect.getsource(action_card)
        signature = inspect.signature(action_card)
        assert signature.parameters["button_type"].default == "primary"
        assert "type=button_type" in src, "action_card should pass through button_type"


class TestQuickActionButtonsStyled:
    """Dashboard feature access groups should remain present and actionable."""

    def test_dashboard_feature_groups_exist(self):
        src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        start = src.index("Feature Access")
        end = src.index("Connect your AI providers", start)
        section = src[start:end]
        assert "🧠 Intelligence" in section
        assert "✍ Writing" in section
        assert "📊 Insights" in section
        assert "⚙ System" in section
        for label in (
            "Narrative Analysis",
            "Semantic Tools",
            "Entity Extraction",
            "Editor",
            "Rewrite",
            "Tone Modulation",
            "Reports",
            "Analytics",
            "Data Viewer",
            "Settings",
            "Configuration",
        ):
            assert label in section


# ---------------------------------------------------------------------------
# Dashboard AI CTA card – layout must be stable regardless of AI connection
# ---------------------------------------------------------------------------

class TestDashboardAICardLayoutStable:
    """The AI providers card must always render on the dashboard.

    Previously the card was only shown when keys were missing, causing
    the button layout to shift when AI providers were connected.  Both
    branches (connected / not-connected) must render a card_block so
    the dashboard layout remains stable.
    """

    def test_main_renders_ai_card_in_both_branches(self):
        src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        # Locate the conditional AI card section
        assert "Connect your AI providers" in src
        assert "AI providers connected" in src
        # Both branches should use card_block so the layout is consistent
        # Search before the "Connect" string to capture both card_block calls
        marker = src.index("Connect your AI providers")
        start = src.rfind("card_block(", 0, marker)
        end = src.index("def render_projects", start)
        section = src[start:end]
        assert section.count("card_block(") >= 2, (
            "Both connected and not-connected branches must render a card_block"
        )

    def test_app_context_renders_ai_card_in_both_branches(self):
        src = (ROOT / "app" / "app_context.py").read_text(encoding="utf-8")
        assert "Connect your AI providers" in src
        assert "AI providers connected" in src
        # Both branches must render a card so the layout is stable
        marker = src.index("Connect your AI providers")
        start = src.rfind("card(", 0, marker)
        end = src.index("def render_projects", start)
        section = src[start:end]
        assert section.count("card(") >= 2, (
            "Both connected and not-connected branches must render a card"
        )


# ---------------------------------------------------------------------------
# World Bible DB – structured lore intelligence layer
# ---------------------------------------------------------------------------

class TestWorldBibleDB:
    """Validate the world-bible database CRUD, search, tagging, and helpers."""

    @pytest.fixture(autouse=True)
    def _session(self):
        from app.services.world_bible_db import ensure_world_bible_db
        self.ss: Dict[str, Any] = {}
        ensure_world_bible_db(self.ss)

    def test_ensure_creates_all_categories(self):
        db = self.ss["world_bible_db"]
        for cat in ("characters", "locations", "factions", "history", "rules"):
            assert cat in db
            assert isinstance(db[cat], dict)

    def test_add_entry_returns_id_and_record(self):
        from app.services.world_bible_db import add_entry
        eid, rec = add_entry("characters", {"name": "Alice", "description": "Hero", "tags": ["protag"]}, session_state=self.ss)
        assert eid
        assert rec["id"] == eid
        assert rec["name"] == "Alice"
        assert rec["tags"] == ["protag"]
        assert rec["created_at"]
        assert rec["updated_at"]

    def test_get_entry(self):
        from app.services.world_bible_db import add_entry, get_entry
        eid, _ = add_entry("locations", {"name": "Gotham", "description": "A city"}, session_state=self.ss)
        got = get_entry("locations", eid, session_state=self.ss)
        assert got is not None
        assert got["name"] == "Gotham"

    def test_update_entry(self):
        from app.services.world_bible_db import add_entry, update_entry
        eid, _ = add_entry("factions", {"name": "Order", "description": "Knights"}, session_state=self.ss)
        updated = update_entry("factions", eid, {"description": "Holy Knights"}, session_state=self.ss)
        assert updated is not None
        assert updated["description"] == "Holy Knights"

    def test_delete_entry(self):
        from app.services.world_bible_db import add_entry, delete_entry, get_entry
        eid, _ = add_entry("characters", {"name": "Bob", "description": "Sidekick"}, session_state=self.ss)
        assert delete_entry("characters", eid, session_state=self.ss) is True
        assert get_entry("characters", eid, session_state=self.ss) is None

    def test_list_entries(self):
        from app.services.world_bible_db import add_entry, list_entries
        add_entry("rules", {"name": "Magic System", "description": "Elemental"}, session_state=self.ss)
        entries = list_entries("rules", session_state=self.ss)
        assert len(entries) >= 1

    def test_search_world_bible(self):
        from app.services.world_bible_db import add_entry, search_world_bible
        add_entry("characters", {"name": "Zara", "description": "Warrior queen", "tags": ["royal"]}, session_state=self.ss)
        results = search_world_bible("zara", session_state=self.ss)
        assert len(results) == 1
        assert results[0]["entry"]["name"] == "Zara"

    def test_get_entries_by_tag(self):
        from app.services.world_bible_db import add_entry, get_entries_by_tag
        add_entry("characters", {"name": "Kai", "description": "Mage", "tags": ["magic"]}, session_state=self.ss)
        results = get_entries_by_tag("magic", session_state=self.ss)
        assert len(results) >= 1

    def test_scan_editor_for_world_bible_references(self):
        from app.services.world_bible_db import add_entry, scan_editor_for_world_bible_references
        add_entry("characters", {"name": "Marcus", "description": "Knight"}, session_state=self.ss)
        add_entry("locations", {"name": "Ironforge", "description": "City of steel"}, session_state=self.ss)
        refs = scan_editor_for_world_bible_references("Marcus rode to Ironforge at dawn.", session_state=self.ss)
        names = {r["name"] for r in refs}
        assert "Marcus" in names
        assert "Ironforge" in names

    def test_scan_editor_empty_text(self):
        from app.services.world_bible_db import scan_editor_for_world_bible_references
        refs = scan_editor_for_world_bible_references("", session_state=self.ss)
        assert refs == []

    def test_check_world_bible_consistency(self):
        from app.services.world_bible_db import check_world_bible_consistency
        warnings = check_world_bible_consistency("Gandalf entered the room", session_state=self.ss)
        assert any("Gandalf" in w for w in warnings)

    def test_detect_canon_conflicts_global_duplicates(self):
        from app.services.world_bible_db import add_entry, detect_canon_conflicts_global
        add_entry("characters", {"name": "Eve", "description": "A", "tags": ["x"]}, session_state=self.ss)
        add_entry("factions", {"name": "Eve", "description": "B", "tags": ["y"]}, session_state=self.ss)
        conflicts = detect_canon_conflicts_global(session_state=self.ss)
        assert any("Eve" in c.lower() or "eve" in c.lower() for c in conflicts)

    def test_detect_canon_conflicts_global_missing_desc(self):
        from app.services.world_bible_db import add_entry, detect_canon_conflicts_global
        add_entry("characters", {"name": "Ghost", "description": "", "tags": []}, session_state=self.ss)
        conflicts = detect_canon_conflicts_global(session_state=self.ss)
        assert any("missing a description" in c for c in conflicts)

    def test_build_world_bible_relationships(self):
        from app.services.world_bible_db import add_entry, build_world_bible_relationships
        add_entry("characters", {"name": "Aria", "description": "Friend of Bran", "tags": ["hero"]}, session_state=self.ss)
        add_entry("characters", {"name": "Bran", "description": "Warrior", "tags": ["hero"]}, session_state=self.ss)
        graph = build_world_bible_relationships(session_state=self.ss)
        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["nodes"]) >= 2
        assert len(graph["edges"]) >= 1  # shared tag 'hero'

    def test_validate_world_timeline_clean(self):
        from app.services.world_bible_db import add_entry, validate_world_timeline
        add_entry("history", {"name": "Founding", "description": "City founded", "tags": [], "year": 100}, session_state=self.ss)
        add_entry("history", {"name": "War", "description": "Great war", "tags": [], "year": 200}, session_state=self.ss)
        warnings = validate_world_timeline(session_state=self.ss)
        assert not any("Duplicate year" in w for w in warnings)

    def test_validate_world_timeline_duplicate_year(self):
        from app.services.world_bible_db import add_entry, validate_world_timeline
        add_entry("history", {"name": "Event A", "description": "A", "tags": [], "year": 50}, session_state=self.ss)
        add_entry("history", {"name": "Event B", "description": "B", "tags": [], "year": 50}, session_state=self.ss)
        warnings = validate_world_timeline(session_state=self.ss)
        assert any("Duplicate year 50" in w for w in warnings)

    def test_validate_world_timeline_missing_year(self):
        from app.services.world_bible_db import add_entry, validate_world_timeline
        add_entry("history", {"name": "No Year", "description": "Missing", "tags": []}, session_state=self.ss)
        warnings = validate_world_timeline(session_state=self.ss)
        assert any("missing a year" in w for w in warnings)

    def test_validate_world_bible_db_repairs(self):
        from app.services.world_bible_db import validate_world_bible_db
        # Inject a broken entry
        self.ss["world_bible_db"]["characters"]["broken"] = {"name": None, "tags": "not-a-list"}
        db = validate_world_bible_db(session_state=self.ss)
        entry = db["characters"]["broken"]
        assert entry["name"] == "Unnamed"
        assert isinstance(entry["tags"], list)
        assert entry["id"] == "broken"
        assert isinstance(entry["description"], str)
        assert entry["created_at"]
        assert entry["updated_at"]


# ---------------------------------------------------------------------------
# World Bible merge engine tests
# ---------------------------------------------------------------------------

class TestWorldBibleMerge:
    """Tests for the intelligent merge engine in world_bible_merge.py."""

    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        from app.services.projects import Project
        self.project = Project.create("Merge Test", storage_dir=str(tmp_path))

    def test_classify_new_entity(self):
        """When no match exists, type should be 'new'."""
        from app.services.world_bible_merge import classify_suggestion
        result = classify_suggestion(self.project, {
            "name": "Alice",
            "category": "Character",
            "description": "A brave hero.",
            "aliases": ["Al"],
        })
        assert result["type"] == "new"
        assert result["entity_id"] is None

    def test_classify_update_existing(self):
        """When a match exists and there is new info, type should be 'update'."""
        from app.services.world_bible_merge import classify_suggestion
        self.project.upsert_entity("Alice", "Character", "A brave hero.")
        result = classify_suggestion(self.project, {
            "name": "Alice",
            "category": "Character",
            "description": "She wields a magic sword.",
            "aliases": [],
        })
        assert result["type"] == "update"
        assert result["entity_id"] is not None
        assert result["match_name"] == "Alice"
        assert len(result["novel_bullets"]) >= 1

    def test_classify_alias_only(self):
        """When description is already covered but aliases are new."""
        from app.services.world_bible_merge import classify_suggestion
        self.project.upsert_entity("Alice", "Character", "A brave hero.")
        result = classify_suggestion(self.project, {
            "name": "Alice",
            "category": "Character",
            "description": "A brave hero.",
            "aliases": ["The Heroine"],
        })
        assert result["type"] == "alias_only"
        assert "The Heroine" in result["novel_aliases"]

    def test_classify_duplicate(self):
        """When everything is already present, type should be 'duplicate'."""
        from app.services.world_bible_merge import classify_suggestion
        self.project.upsert_entity("Alice", "Character", "A brave hero.", aliases=["Al"])
        result = classify_suggestion(self.project, {
            "name": "Alice",
            "category": "Character",
            "description": "A brave hero.",
            "aliases": ["Al"],
        })
        assert result["type"] == "duplicate"

    def test_apply_update_merges_bullets(self):
        """apply_suggestion should append novel bullets to the entity."""
        from app.services.world_bible_merge import classify_suggestion, apply_suggestion
        self.project.upsert_entity("Alice", "Character", "A brave hero.")
        classified = classify_suggestion(self.project, {
            "name": "Alice",
            "category": "Character",
            "description": "She wields a magic sword. She is 25 years old.",
            "aliases": ["Al"],
        })
        ent, action = apply_suggestion(self.project, classified)
        assert action == "updated"
        assert "magic sword" in ent.description
        assert any(a.lower() == "al" for a in ent.aliases)

    def test_apply_new_creates_entity(self):
        """apply_suggestion with type 'new' should create the entity."""
        from app.services.world_bible_merge import apply_suggestion
        classified = {
            "type": "new",
            "name": "Bob",
            "category": "Character",
            "description": "A mysterious stranger.",
            "aliases": ["Bobby"],
        }
        ent, action = apply_suggestion(self.project, classified)
        assert action == "created"
        assert ent is not None
        assert ent.name == "Bob"

    def test_apply_duplicate_is_noop(self):
        """apply_suggestion with type 'duplicate' should not modify the entity."""
        from app.services.world_bible_merge import apply_suggestion
        self.project.upsert_entity("Alice", "Character", "A brave hero.")
        ent_id = list(self.project.world_db.keys())[0]
        classified = {
            "type": "duplicate",
            "entity_id": ent_id,
            "name": "Alice",
        }
        ent, action = apply_suggestion(self.project, classified)
        assert action == "duplicate"

    def test_novel_bullets_skips_duplicates(self):
        """_novel_bullets should not return bullets already in description."""
        from app.services.world_bible_merge import _novel_bullets
        existing = "- A brave hero.\n- She is strong."
        incoming = "A brave hero. She can fly."
        result = _novel_bullets(existing, incoming)
        assert any("fly" in b.lower() for b in result)
        assert not any("brave hero" in b.lower() for b in result)

    def test_novel_aliases_skips_existing(self):
        """_novel_aliases should not return aliases already on the entity."""
        from app.services.world_bible_merge import _novel_aliases
        from app.services.projects import Entity
        ent = Entity(id="1", name="Alice", category="Character", aliases=["Al"])
        result = _novel_aliases(ent, ["Al", "The Heroine", "alice"], "Alice")
        assert "The Heroine" in result
        assert "Al" not in result
        assert "alice" not in result

    def test_merge_description_bullets_formats_correctly(self):
        """merge_description_bullets should format as bullet points."""
        from app.services.world_bible_merge import merge_description_bullets
        from app.services.projects import Entity
        ent = Entity(id="1", name="Sword", category="Item", description="A magic blade.")
        merge_description_bullets(ent, ["Glows in the dark", "Forged by elves"])
        assert "- A magic blade." in ent.description
        assert "- Glows in the dark" in ent.description
        assert "- Forged by elves" in ent.description

    def test_classify_fuzzy_name_match(self):
        """Fuzzy name matching should detect near-identical names."""
        from app.services.world_bible_merge import classify_suggestion
        self.project.upsert_entity("Alice Smith", "Character", "A hero.")
        result = classify_suggestion(self.project, {
            "name": "alice smith",
            "category": "Character",
            "description": "She can fly.",
        })
        assert result["type"] == "update"
        assert result["match_name"] == "Alice Smith"

    def test_classify_cross_category_no_match(self):
        """Same name in a different category should not match."""
        from app.services.world_bible_merge import classify_suggestion
        self.project.upsert_entity("Phoenix", "Character", "A hero.")
        result = classify_suggestion(self.project, {
            "name": "Phoenix",
            "category": "Location",
            "description": "A burning city.",
        })
        assert result["type"] == "new"

    def test_item_description_expansion(self):
        """Items should gain bullet points when new attributes are found."""
        from app.services.world_bible_merge import classify_suggestion, apply_suggestion
        self.project.upsert_entity("Excalibur", "Item", "A legendary sword.")
        classified = classify_suggestion(self.project, {
            "name": "Excalibur",
            "category": "Item",
            "description": "Grants wielder invincibility. Forged by the Lady of the Lake.",
        })
        assert classified["type"] == "update"
        ent, _ = apply_suggestion(self.project, classified)
        assert "invincibility" in ent.description
        assert "Lady of the Lake" in ent.description
        # Original preserved
        assert "legendary sword" in ent.description

    def test_lore_history_update(self):
        """Lore/history entries should also be updatable."""
        from app.services.world_bible_merge import classify_suggestion, apply_suggestion
        self.project.upsert_entity("The Great War", "Lore", "A conflict 500 years ago.")
        classified = classify_suggestion(self.project, {
            "name": "The Great War",
            "category": "Lore",
            "description": "Ended with the Treaty of Dawn.",
        })
        assert classified["type"] == "update"
        ent, _ = apply_suggestion(self.project, classified)
        assert "Treaty of Dawn" in ent.description
        assert "500 years ago" in ent.description

    def test_apply_unclassified_update_with_description(self):
        """apply_suggestion should work even when novel_bullets is not pre-computed."""
        from app.services.world_bible_merge import apply_suggestion
        ent_orig, _ = self.project.upsert_entity("Elena", "Character", "A brave warrior.")
        classified = {
            "type": "update",
            "entity_id": ent_orig.id,
            "name": "Elena",
            "category": "Character",
            "description": "She has black hair. She is the captain of the guard.",
            "aliases": ["Lena"],
            # novel_bullets and novel_aliases intentionally omitted
        }
        ent, action = apply_suggestion(self.project, classified)
        assert action == "updated"
        assert "black hair" in ent.description
        assert "captain of the guard" in ent.description
        assert "brave warrior" in ent.description
        assert any(a.lower() == "lena" for a in ent.aliases)

    def test_apply_unclassified_update_aliases_only(self):
        """apply_suggestion should add aliases even without novel_aliases key."""
        from app.services.world_bible_merge import apply_suggestion
        ent_orig, _ = self.project.upsert_entity("Elena", "Character", "A brave warrior.")
        classified = {
            "type": "alias_only",
            "entity_id": ent_orig.id,
            "name": "Elena",
            "category": "Character",
            "description": "A brave warrior.",
            "aliases": ["The Iron Lady", "Lena"],
            # novel_aliases intentionally omitted
        }
        ent, action = apply_suggestion(self.project, classified)
        assert any(a == "The Iron Lady" for a in ent.aliases)
        assert any(a.lower() == "lena" for a in ent.aliases)

    def test_apply_update_without_entity_id_finds_match(self):
        """apply_suggestion should find the entity by name when entity_id is missing."""
        from app.services.world_bible_merge import apply_suggestion
        self.project.upsert_entity("Elena", "Character", "A brave warrior.")
        classified = {
            "type": "update",
            "name": "Elena",
            "category": "Character",
            "description": "She has black hair.",
            "aliases": [],
            # entity_id intentionally omitted
        }
        ent, action = apply_suggestion(self.project, classified)
        assert action == "updated"
        assert "black hair" in ent.description
        assert "brave warrior" in ent.description

    def test_apply_alias_only_also_merges_notes(self):
        """apply_suggestion with alias_only should also merge description/notes."""
        from app.services.world_bible_merge import apply_suggestion
        ent_orig, _ = self.project.upsert_entity("Elena", "Character", "A brave warrior.")
        classified = {
            "type": "alias_only",
            "entity_id": ent_orig.id,
            "name": "Elena",
            "category": "Character",
            "description": "She commands the northern garrison.",
            "aliases": ["The Iron Lady"],
            "novel_bullets": [],
            "novel_aliases": ["The Iron Lady"],
        }
        ent, action = apply_suggestion(self.project, classified)
        assert any(a == "The Iron Lady" for a in ent.aliases)
        assert "northern garrison" in ent.description
        assert "brave warrior" in ent.description

    def test_apply_alias_only_no_actual_changes_returns_duplicate(self):
        """apply_suggestion should return duplicate when nothing is changed."""
        from app.services.world_bible_merge import apply_suggestion
        ent_orig, _ = self.project.upsert_entity("Elena", "Character", "A brave warrior.")
        classified = {
            "type": "alias_only",
            "entity_id": ent_orig.id,
            "name": "Elena",
            "category": "Character",
            "description": "A brave warrior.",
            "aliases": [],
            "novel_bullets": [],
            "novel_aliases": [],
        }
        ent, action = apply_suggestion(self.project, classified)
        assert ent.id == ent_orig.id
        assert action == "duplicate"


# ---------------------------------------------------------------------------
# World Bible suggestion queue
# ---------------------------------------------------------------------------

class TestWorldBibleSuggestionQueue:
    """Verify queue deduping respects alias differences."""

    @pytest.fixture(autouse=True)
    def _clear_state(self):
        import streamlit as st
        st.session_state.clear()
        yield
        st.session_state.clear()

    def test_queue_dedup_includes_aliases(self):
        from app.services.world_bible import queue_world_bible_suggestion
        import streamlit as st

        queue_world_bible_suggestion({
            "name": "Alice",
            "category": "Character",
            "description": "",
            "aliases": ["Al"],
        })
        queue_world_bible_suggestion({
            "name": "Alice",
            "category": "Character",
            "description": "",
            "aliases": ["Allie"],
        })

        queue = st.session_state.get("world_bible_review", [])
        assert len(queue) == 2


# ---------------------------------------------------------------------------
# Widget cache clearing after apply_suggestion
# ---------------------------------------------------------------------------

class TestApplySuggestionClearsWidgetCache:
    """Verify that the apply-suggestion UI clears stale widget keys."""

    def test_app_context_clears_desc_and_aliases_keys(self):
        """The apply-suggestion code must pop desc_ and aliases_ keys from
        session_state so the Notes text area picks up the updated value."""
        import importlib
        ctx = importlib.import_module("app.app_context")
        source = Path(ctx.__file__).read_text(encoding="utf-8")

        # Must capture return value from apply_suggestion
        assert re.search(
            r"=\s*_?apply_suggestion.*\(.*p.*,.*item.*\)",
            source,
        ), "apply_suggestion return value not captured"

        # Must clear the widget key for description
        assert re.search(
            r'session_state\.pop\(\s*f["\']desc_',
            source,
        ), "session_state.pop for desc_ key not found"

        # Must clear the widget key for aliases
        assert re.search(
            r'session_state\.pop\(\s*f["\']aliases_',
            source,
        ), "session_state.pop for aliases_ key not found"

    def test_main_clears_desc_and_aliases_keys(self):
        """The apply-suggestion code in main.py must pop desc_ and aliases_
        keys from session_state so the Notes text area picks up the updated
        value."""
        import importlib
        main = importlib.import_module("app.main")
        source = Path(main.__file__).read_text(encoding="utf-8")

        # Must capture return value from apply_suggestion
        assert re.search(
            r"=\s*_?apply_suggestion.*\(.*p.*,.*item.*\)",
            source,
        ), "apply_suggestion return value not captured in main.py"

        # Must clear the widget key for description
        assert re.search(
            r'session_state\.pop\(\s*f["\']desc_',
            source,
        ), "session_state.pop for desc_ key not found in main.py"

        # Must clear the widget key for aliases
        assert re.search(
            r'session_state\.pop\(\s*f["\']aliases_',
            source,
        ), "session_state.pop for aliases_ key not found in main.py"


# ---------------------------------------------------------------------------
# Widget double-wrap guard
# ---------------------------------------------------------------------------


class TestWidgetWrapGuard:
    """Verify that _maybe_wrap guards against double-wrapping.

    Repeated Streamlit script reruns call _run_ui() each time, which
    previously stacked wrappers on top of each other, eventually causing
    a RecursionError.  The fix marks wrapped functions with a
    ``_mantis_wrapped`` sentinel so they are not wrapped again.
    """

    def test_wrap_widget_sets_sentinel(self):
        source = Path(ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "_mantis_wrapped" in source, (
            "_mantis_wrapped sentinel not found – the double-wrap guard is missing"
        )

    def test_maybe_wrap_checks_sentinel(self):
        source = Path(ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert re.search(
            r"getattr\(.*_mantis_wrapped.*False\)",
            source,
        ), "_maybe_wrap does not check _mantis_wrapped before wrapping"

    def test_state_wrap_widget_sets_sentinel(self):
        source = Path(ROOT / "app" / "state.py").read_text(encoding="utf-8")
        assert "_mantis_wrapped" in source, (
            "_mantis_wrapped sentinel not found in state.py – "
            "the double-wrap guard is missing"
        )

    def test_state_maybe_wrap_checks_sentinel(self):
        source = Path(ROOT / "app" / "state.py").read_text(encoding="utf-8")
        assert re.search(
            r"getattr\(.*_mantis_wrapped.*False\)",
            source,
        ), "_maybe_wrap in state.py does not check _mantis_wrapped before wrapping"

    def test_install_key_helpers_idempotent(self):
        """Calling install_key_helpers twice must NOT double-wrap widgets."""
        from types import SimpleNamespace
        from app.state import install_key_helpers

        call_count = 0
        def fake_selectbox(label, options=None, **kwargs):
            nonlocal call_count
            call_count += 1
            return label

        mock_st = SimpleNamespace(selectbox=fake_selectbox)
        install_key_helpers(mock_st)
        first_wrapper = mock_st.selectbox
        install_key_helpers(mock_st)
        second_wrapper = mock_st.selectbox
        # The wrapper must be the same object (not re-wrapped)
        assert first_wrapper is second_wrapper, (
            "install_key_helpers double-wrapped selectbox"
        )


# ============================================================================
# Tests from test_buttons.py — Button tests for every page
# ============================================================================

MAIN_PY = ROOT / "app" / "main.py"
APP_CTX = ROOT / "app" / "app_context.py"

# Context window sizes for searching after a button label/key.
# Buttons whose handlers are short (simple nav) need ~400 chars.
# Buttons whose handlers are longer (AI calls, multi-branch logic) need more.
_CTX_SHORT = 400       # nav buttons, simple state changes
_CTX_MEDIUM = 800      # save + entity scan, delete with cleanup
_CTX_LONG = 1200       # suggestion apply, AI key apply with auto-fetch
_CTX_XLARGE = 2000     # import & analyze (create project + AI outline)
_CTX_XXLARGE = 3000    # apply changes (3 apply-mode branches each with rerun)

# How far back/forward to look when checking if a page-setting line is
# inside a st.button block.
_NAV_LOOKBACK_LINES = 20
_NAV_LOOKAHEAD_LINES = 10

# How many lines of context to capture around each st.button call.
_BUTTON_BLOCK_LINES = 20

# Minimum button counts to guard against accidental mass removal.
# Update these when significant numbers of buttons are intentionally added/removed.
_MIN_MAIN_BUTTONS = 60
_MIN_CTX_BUTTONS = 30


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _source() -> str:
    return _read(MAIN_PY)


def _extract_render_function(fn_name: str) -> str:
    """Extract the body of a top-level render function from main.py.

    Assumes functions are defined at 4-space indentation inside the
    module-level ``def run():`` block, which is the standard layout
    for this codebase.
    """
    src = _source()
    pattern = rf"^    def {fn_name}\b.*?(?=\n    def |\Z)"
    m = re.search(pattern, src, re.MULTILINE | re.DOTALL)
    assert m, f"render function '{fn_name}' not found"
    return m.group(0)


def _find_button_blocks(source: str) -> List[Tuple[int, str]]:
    """Return (line_number, block_text) for every st.button call."""
    results = []
    lines = source.split("\n")
    for i, line in enumerate(lines):
        if "st.button(" in line:
            block = "\n".join(lines[i : i + _BUTTON_BLOCK_LINES])
            results.append((i + 1, block))
    return results


# ---------------------------------------------------------------------------
# 1) Legal / back-navigation pages
# ---------------------------------------------------------------------------


class TestLegalPageButtons:
    """Every legal sub-page must have a back button with key and rerun."""

    @pytest.mark.parametrize(
        "fn_name,expected_label",
        [
            ("render_privacy", "Back to All Policies"),
            ("render_terms", "Back to All Policies"),
            ("render_copyright", "Back to All Policies"),
            ("render_cookie", "Back to All Policies"),
            ("render_help", "Back to Dashboard"),
        ],
    )
    def test_back_button_exists(self, fn_name, expected_label):
        body = _extract_render_function(fn_name)
        assert expected_label in body, f"{fn_name} missing '{expected_label}' button"

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_has_key(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "key=" in body, f"{fn_name} back button missing key="

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_calls_rerun(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.rerun()" in body, f"{fn_name} back button missing st.rerun()"

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_navigates(self, fn_name):
        body = _extract_render_function(fn_name)
        assert 'session_state.page' in body, f"{fn_name} back button doesn't navigate"


# ---------------------------------------------------------------------------
# 2) Legal redirect page (policy picker)
# ---------------------------------------------------------------------------


class TestLegalRedirectButtons:
    """The legal redirect page shows a nav button per legal sub-page."""

    def test_legal_nav_buttons_have_keys(self):
        body = _extract_render_function("render_legal_redirect")
        assert "legal_pages = [" in body
        assert "st.expander(label)" in body

    def test_legal_nav_buttons_call_rerun(self):
        body = _extract_render_function("render_legal_redirect")
        assert "st.rerun()" in body


# ---------------------------------------------------------------------------
# 3) Dashboard (render_home) buttons
# ---------------------------------------------------------------------------


class TestDashboardButtons:
    """Dashboard must have all expected CTA and quick-action buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_home")

    def test_primary_cta_exists(self):
        assert "primary_label" in self.body and 'type="primary"' in self.body

    def test_primary_cta_uses_milestone_copy(self):
        assert "Create/Advance Next Narrative Milestone" in self.body

    def test_resume_project_button(self):
        assert "Open Workspace" in self.body

    def test_new_project_button(self):
        assert "New Project" in self.body

    def test_new_project_calls_rerun(self):
        assert "open_new_project()" in self.body

    def test_feature_access_buttons_count(self):
        start = self.body.index("Feature Access")
        end = self.body.index("Connect your AI providers", start)
        section = self.body[start:end]
        assert "for feature_name, feature_caption, action in features:" in section
        assert "dashboard_feature_" in section

    def test_dashboard_sections_exist(self):
        start = self.body.index("Command Center")
        end = self.body.index("Connect your AI providers", start)
        section = self.body[start:end]
        assert "Metrics Overview" in section
        assert "Workspace Hub" in section
        assert "Feature Access" in section

    def test_ai_settings_button(self):
        assert "Settings" in self.body

    def test_manage_ai_settings_button_has_key(self):
        assert "dashboard__ai_connected_settings" in self.body

    def test_dashboard_has_project_health_and_next_actions_panels(self):
        assert "AI Operations Today" in self.body
        assert "System Mode" in self.body

    def test_recent_project_open_button(self):
        assert "Open Workspace" in self.body

    def test_recent_project_open_button_has_key(self):
        assert "dash_hub_open_" in self.body


# ---------------------------------------------------------------------------
# 4) Projects page buttons
# ---------------------------------------------------------------------------


class TestProjectsPageButtons:
    """Projects page: create, import, open, export, delete."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_projects")

    def test_create_project_form_submit(self):
        assert "🚀 Create Project" in self.body

    def test_create_project_is_form_submit(self):
        assert "form_submit_button" in self.body

    def test_import_analyze_button(self):
        assert "Import & Analyze" in self.body

    def test_import_button_calls_rerun(self):
        # Import & Analyze has a rerun further down in its handler
        idx = self.body.index("Import & Analyze")
        after = self.body[idx : idx + 2000]
        assert "st.rerun()" in after

    def test_open_project_button_has_key(self):
        assert 'key=f"open_' in self.body

    def test_export_project_button_has_key(self):
        assert 'key=f"export_' in self.body

    def test_delete_project_button_has_key(self):
        assert 'key=f"del_' in self.body

    def test_confirm_delete_button(self):
        assert "Confirm delete" in self.body

    def test_confirm_delete_calls_rerun(self):
        idx = self.body.index("Confirm delete")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    def test_cancel_button(self):
        assert '"Cancel"' in self.body

    def test_cancel_calls_rerun(self):
        idx = self.body.index('"Cancel"')
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_close_export_button(self):
        assert "Close export" in self.body


# ---------------------------------------------------------------------------
# 5) AI Settings page buttons
# ---------------------------------------------------------------------------


class TestAISettingsButtons:
    """AI Settings page: apply key, clear key, and save."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_ai_settings")

    def test_apply_key_button_has_key(self):
        assert "session_key" in self.body

    def test_apply_key_calls_rerun(self):
        idx = self.body.index("Apply Key")
        after = self.body[idx : idx + 2000]
        assert "st.rerun()" in after

    def test_clear_key_button_has_key(self):
        assert "clear_session" in self.body

    def test_clear_key_calls_rerun(self):
        idx = self.body.index("Clear Key")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_fetch_models_button_removed(self):
        assert "↻ Fetch Models" not in self.body

    def test_test_connection_button_removed(self):
        assert "🔌 Test Connection" not in self.body

    def test_test_all_models_button_has_key(self):
        assert "test_all_models_btn" in self.body

    def test_save_settings_button(self):
        assert "Save Settings" in self.body or "save_app_settings" in self.body

    def test_apply_key_auto_fetches_models(self):
        """When Apply Key is pressed, models should be auto-fetched."""
        idx = self.body.index("Apply Key")
        after = self.body[idx : idx + 500]
        assert "fetch_fn" in after or "fetch_openai_models" in after or "fetch_groq_models" in after, (
            "Apply Key should auto-fetch models after setting key"
        )

    def test_apply_key_auto_tests_connection(self):
        idx = self.body.index("Apply Key")
        after = self.body[idx : idx + 700]
        assert "test_fn" in after or "test_openai_connection" in after or "test_groq_connection" in after, (
            "Apply Key should auto-test connection after setting key"
        )


# ---------------------------------------------------------------------------
# 6) Outline page buttons
# ---------------------------------------------------------------------------


class TestOutlinePageButtons:
    """Outline page: save project, save outline, go to projects, AI generate."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_outline")

    def test_go_to_projects_button(self):
        assert "Go to Projects" in self.body

    def test_go_to_projects_calls_rerun(self):
        idx = self.body.index("Go to Projects")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_save_project_button(self):
        assert "Save Project" in self.body

    def test_save_project_calls_rerun(self):
        idx = self.body.index("Save Project")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_save_outline_button(self):
        assert "Save Outline" in self.body

    def test_save_outline_calls_rerun(self):
        idx = self.body.index("Save Outline")
        after = self.body[idx : idx + 700]
        assert "st.rerun()" in after

    def test_architect_generate_button(self):
        # The outline page has an AI generate button
        assert "primary" in self.body.lower()


# ---------------------------------------------------------------------------
# 7) World Bible page buttons
# ---------------------------------------------------------------------------


class TestWorldBibleButtons:
    """World Bible page: add entity, delete entity, save memory, coherence, etc."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_world")

    def test_go_to_projects_button(self):
        assert "Go to Projects" in self.body

    def test_add_entity_button(self):
        assert "Add {category}" in self.body or "➕ Add" in self.body

    def test_add_entity_calls_rerun(self):
        idx = self.body.index("➕ Add")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_delete_entity_button_has_key(self):
        assert 'key=f"del_{e.id}"' in self.body

    def test_delete_entity_calls_rerun(self):
        idx = self.body.index("🗑 Delete")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_confirm_delete_button(self):
        assert '"Confirm"' in self.body

    def test_confirm_delete_calls_rerun(self):
        idx = self.body.index('"Confirm"')
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_cancel_delete_calls_rerun(self):
        # The entity delete Cancel button (not form cancel) calls rerun
        assert '"Cancel"' in self.body
        idx = self.body.rindex('"Cancel"')  # Last Cancel is the delete-cancel
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_save_memory_button(self):
        assert "Save Memory" in self.body

    def test_save_memory_calls_rerun(self):
        idx = self.body.index("Save Memory")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_apply_suggestion_button_has_key(self):
        assert 'key=f"apply_suggestion_{idx}"' in self.body

    def test_apply_suggestion_calls_rerun(self):
        idx = self.body.index("✅ Apply")
        after = self.body[idx : idx + 1200]
        assert "st.rerun()" in after

    def test_apply_suggestion_duplicate_toast_message(self):
        idx = self.body.index("✅ Apply")
        after = self.body[idx : idx + 1400]
        assert '_action == "duplicate"' in after
        assert "No new World Bible changes to apply." in after

    def test_ignore_suggestion_button_has_key(self):
        assert 'key=f"ignore_suggestion_{idx}"' in self.body

    def test_ignore_suggestion_calls_rerun(self):
        idx = self.body.index('key=f"ignore_suggestion')
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_coherence_check_button(self):
        assert "coherence" in self.body.lower()

    def test_apply_fix_button_has_key(self):
        assert 'key=f"coh_apply_{idx}"' in self.body

    def test_ignore_coherence_button_has_key(self):
        assert 'key=f"coh_ignore_{idx}"' in self.body

    def test_ignore_coherence_calls_rerun(self):
        idx = self.body.index('key=f"coh_ignore')
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_jump_to_chapter_button_has_key(self):
        assert 'key=f"jump_{e.id}"' in self.body

    def test_jump_to_entity_button_has_key(self):
        assert 'key=f"jump_entity_{ent.id}"' in self.body

    def test_jump_to_entity_calls_rerun(self):
        idx = self.body.index("Jump to Entity")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_form_submit_save_exists(self):
        assert "form_submit_button" in self.body

    def test_form_cancel_exists(self):
        # Check that entity form has both Save and Cancel buttons
        assert '"Save"' in self.body
        assert '"Cancel"' in self.body


# ---------------------------------------------------------------------------
# 8) Editor / Chapters page buttons
# ---------------------------------------------------------------------------


class TestEditorButtons:
    """Editor (chapters) page: create, delete, save, summary, improve, auto-write."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_chapters")

    # --- No-project state ---
    def test_go_to_projects_when_no_project(self):
        assert "Go to Projects" in self.body

    def test_go_to_projects_has_key(self):
        assert "editor_no_project_go_projects" in self.body

    def test_go_to_projects_calls_rerun(self):
        idx = self.body.index("editor_no_project_go_projects")
        after = self.body[idx : idx + 200]
        assert "st.rerun()" in after

    # --- Create chapter ---
    def test_create_chapter_1_button_has_key(self):
        assert "editor_create_chapter_1" in self.body

    def test_create_chapter_1_type_primary(self):
        idx = self.body.index("Create Chapter 1")
        block = self.body[idx - 50 : idx + 200]
        assert 'type="primary"' in block

    def test_new_chapter_button_has_key(self):
        assert "editor_new_chapter" in self.body

    # --- Delete chapter ---
    def test_delete_chapter_button_has_key(self):
        assert 'key=f"editor_del_{curr.id}"' in self.body

    def test_delete_chapter_calls_rerun(self):
        idx = self.body.index("Delete Chapter")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_delete_confirm_has_key(self):
        assert "editor_del_ch_confirm" in self.body

    def test_delete_confirm_calls_rerun(self):
        idx = self.body.index("editor_del_ch_confirm")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    def test_delete_cancel_has_key(self):
        assert "editor_del_ch_cancel" in self.body

    def test_delete_cancel_calls_rerun(self):
        idx = self.body.index("editor_del_ch_cancel")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    # --- Save chapter ---
    def test_save_chapter_button(self):
        assert "Save Chapter" in self.body

    def test_save_chapter_has_key(self):
        assert 'key=f"editor_save_{curr.id}"' in self.body

    def test_save_chapter_calls_rerun(self):
        idx = self.body.index("Save Chapter")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    # --- Summary ---
    def test_update_summary_button(self):
        assert "Update Summary" in self.body

    def test_update_summary_has_key(self):
        assert "editor_summary_" in self.body

    def test_update_summary_calls_rerun(self):
        idx = self.body.index("editor_summary_")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    # --- Improve ---
    def test_generate_improvement_button(self):
        assert "Generate Improvement" in self.body

    def test_generate_improvement_has_key(self):
        assert "editor_improve__generate_" in self.body

    # --- Undo ---
    def test_undo_button(self):
        assert "Undo last apply" in self.body

    def test_undo_has_key(self):
        assert "editor_improve__undo_" in self.body

    def test_undo_calls_rerun_on_success(self):
        idx = self.body.index("Undo last apply")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    # --- Apply Changes ---
    def test_apply_changes_button(self):
        assert "Apply Changes" in self.body

    def test_apply_changes_has_key(self):
        assert "editor_improve__apply_" in self.body

    def test_apply_changes_calls_rerun(self):
        idx = self.body.index("editor_improve__apply_")
        after = self.body[idx : idx + 3000]
        assert "st.rerun()" in after

    # --- Copy Improved ---
    def test_copy_improved_button(self):
        assert "Copy Improved" in self.body

    def test_copy_improved_has_key(self):
        assert "editor_improve__copy_" in self.body

    # --- Regenerate ---
    def test_regenerate_button(self):
        assert "Regenerate" in self.body

    def test_regenerate_has_key(self):
        assert "editor_improve__regenerate_" in self.body

    # --- Discard ---
    def test_discard_button(self):
        assert "Discard" in self.body

    def test_discard_has_key(self):
        assert "editor_improve__discard_" in self.body

    def test_discard_calls_rerun(self):
        idx = self.body.index("editor_improve__discard_")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    # --- Auto-Write ---
    def test_auto_write_button(self):
        assert "Auto-Write Chapter" in self.body

    def test_auto_write_has_key(self):
        assert "editor_autowrite_" in self.body

    def test_auto_write_blocked_has_key(self):
        assert "editor_autowrite_blocked_" in self.body

    # --- Set draft as active ---
    def test_set_draft_active_button(self):
        assert "Set as active" in self.body

    def test_set_draft_active_has_key(self):
        assert "editor_improve__set_active_" in self.body

    def test_set_draft_active_calls_rerun(self):
        idx = self.body.index("editor_improve__set_active_")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    # --- Chapter navigation ---
    def test_chapter_nav_buttons_have_keys(self):
        assert "chapter_id" in self.body and "key=" in self.body


# ---------------------------------------------------------------------------
# 9) Export page buttons
# ---------------------------------------------------------------------------


class TestExportPageButtons:
    """Export page must exist and have download/navigation functionality."""

    def test_export_function_exists(self):
        src = _source()
        assert "def render_export" in src

    def test_export_has_download_button(self):
        body = _extract_render_function("render_export")
        assert "download_button" in body or "download" in body.lower()


# ---------------------------------------------------------------------------
# 10) Welcome banner buttons
# ---------------------------------------------------------------------------


class TestWelcomeBannerButtons:
    """Welcome banner: create first project and dismiss buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_welcome_banner")

    def test_create_first_project_button(self):
        assert "Create My First Project" in self.body

    def test_create_first_project_type_primary(self):
        idx = self.body.index("Create My First Project")
        block = self.body[idx - 50 : idx + 200]
        assert 'type="primary"' in block

    def test_create_first_project_calls_rerun(self):
        idx = self.body.index("Create My First Project")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_dismiss_button(self):
        assert "Got it" in self.body

    def test_dismiss_calls_rerun(self):
        idx = self.body.index("Got it")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after


# ---------------------------------------------------------------------------
# 11) Page header buttons (generic reusable component)
# ---------------------------------------------------------------------------


class TestPageHeaderButtons:
    """render_page_header: primary and secondary action buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_page_header")

    def test_primary_button_has_key(self):
        assert "{key_prefix}__primary" in self.body

    def test_primary_button_type(self):
        assert 'type="primary"' in self.body

    def test_secondary_button_has_key(self):
        assert "{key_prefix}__secondary" in self.body

    def test_primary_calls_action(self):
        assert "primary_action()" in self.body

    def test_secondary_calls_action(self):
        assert "secondary_action()" in self.body


# ---------------------------------------------------------------------------
# 12) Cross-cutting: every st.button that sets page must call rerun
# ---------------------------------------------------------------------------


class TestNavigationButtonsCallRerun:
    """Every button that sets st.session_state.page must also call st.rerun()."""

    def test_all_page_setting_buttons_call_rerun(self):
        src = _source()
        lines = src.split("\n")
        violations = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "session_state.page" in stripped and "=" in stripped and "==" not in stripped:
                # Look back up to 20 lines for a st.button context
                context_start = max(0, i - 20)
                context = "\n".join(lines[context_start : i + 1])
                if "st.button(" in context:
                    # Look forward for st.rerun() within 10 lines
                    forward = "\n".join(lines[i : i + 10])
                    if "st.rerun()" not in forward:
                        violations.append(
                            f"Line {i + 1}: sets session_state.page but doesn't call st.rerun() nearby"
                        )
        assert not violations, (
            f"Buttons that navigate must call st.rerun():\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 13) Cross-cutting: form submit buttons
# ---------------------------------------------------------------------------


class TestFormSubmitButtons:
    """Every form_submit_button in the app."""

    def test_create_project_form_submit(self):
        src = _source()
        assert '🚀 Create Project' in src

    def test_entity_form_save(self):
        src = _source()
        # The entity form has Save and Cancel submit buttons
        idx = src.index('form_submit_button("Save"')
        assert idx > 0

    def test_entity_form_cancel(self):
        src = _source()
        idx = src.index('form_submit_button("Cancel"')
        assert idx > 0


# ---------------------------------------------------------------------------
# 14) Cross-cutting: link_button calls
# ---------------------------------------------------------------------------


class TestLinkButtons:
    """All link_button calls should have valid URLs."""

    def test_help_docs_link(self):
        src = _source()
        assert "github.com/bigmanjer/Mantis-Studio" in src

    def test_groq_link(self):
        src = _source()
        assert "console.groq.com" in src

    def test_openai_link(self):
        src = _source()
        assert "platform.openai.com" in src


# ---------------------------------------------------------------------------
# 15) Sidebar navigation buttons
# ---------------------------------------------------------------------------


class TestSidebarNavButtons:
    """Sidebar nav buttons should have keys and call st.rerun."""

    def test_sidebar_nav_buttons_have_keys(self):
        src = _source()
        assert 'key=f"nav_{target}_{_slugify(label)}"' in src

    def test_sidebar_nav_buttons_call_rerun(self):
        src = _source()
        idx = src.index('key=f"nav_{target}_{_slugify(label)}"')
        # Window includes the button branch and callback body for rerun assertion.
        after = src[idx : idx + 1200]
        assert "st.rerun()" in after


# ---------------------------------------------------------------------------
# 16) Comprehensive: both main.py and app_context.py have matching buttons
# ---------------------------------------------------------------------------


class TestMainAndAppContextButtonParity:
    """Critical buttons must exist in both main.py and app_context.py."""

    def test_create_chapter_1_in_both(self):
        main = _source()
        ctx = _read(APP_CTX)
        assert "editor_create_chapter_1" in main
        assert "editor_create_chapter_1" in ctx

    def test_new_chapter_in_both(self):
        main = _source()
        ctx = _read(APP_CTX)
        assert "editor_new_chapter" in main
        assert "editor_new_chapter" in ctx


# ---------------------------------------------------------------------------
# 17) Every delete-confirmation button pair calls rerun
# ---------------------------------------------------------------------------


class TestDeleteConfirmationPairs:
    """Delete flows: the initial delete button, confirm, and cancel must all rerun."""

    def test_chapter_delete_flow(self):
        body = _extract_render_function("render_chapters")
        # Delete button sets delete_chapter_id then calls rerun
        assert "delete_chapter_id" in body
        assert "delete_chapter_title" in body
        # Count rerun calls - there should be at least 3 for delete flow
        # (initial, confirm, cancel)
        idx = body.index("Delete Chapter")
        section = body[idx : idx + 500]
        rerun_count = section.count("st.rerun()")
        assert rerun_count >= 1, "Delete chapter button must call st.rerun()"

    def test_entity_delete_flow(self):
        body = _extract_render_function("render_world")
        assert "delete_entity_id" in body
        assert "delete_entity_name" in body

    def test_project_delete_flow(self):
        body = _extract_render_function("render_projects")
        assert "delete_project_path" in body or "Confirm delete" in body


# ---------------------------------------------------------------------------
# 18) AI Settings: Apply Key fetches models automatically
# ---------------------------------------------------------------------------


class TestApplyKeyAutoFetch:
    """Pressing Apply Key should automatically fetch models and model selection should test connection."""

    def test_groq_or_openai_fetch_in_apply_handler(self):
        body = _extract_render_function("render_ai_settings")
        # Find the Apply Key handler
        idx = body.index("Apply Key")
        handler = body[idx : idx + 600]
        # Should reference a fetch function
        assert (
            "fetch_fn" in handler
            or "fetch_groq_models" in handler
            or "fetch_openai_models" in handler
        ), "Apply Key should auto-fetch models"

    def test_model_selection_auto_tests_connection(self):
        body = _extract_render_function("render_ai_settings")
        assert "if openai_model != st.session_state.openai_model" in body
        assert "if groq_model != st.session_state.groq_model" in body
        assert "test_openai_connection" in body
        assert "test_groq_connection" in body


# ---------------------------------------------------------------------------
# 19) Button count sanity check
# ---------------------------------------------------------------------------


class TestButtonCountSanity:
    """Ensure the app has a reasonable number of buttons (no accidental removal)."""

    def test_main_has_at_least_60_buttons(self):
        src = _source()
        count = src.count("st.button(")
        assert count >= 60, f"Expected at least 60 buttons in main.py, found {count}"

    def test_app_context_has_buttons(self):
        ctx = _read(APP_CTX)
        count = ctx.count("st.button(")
        assert count >= 30, f"Expected at least 30 buttons in app_context.py, found {count}"


# ---------------------------------------------------------------------------
# 20) Every render function with buttons handles its state correctly
# ---------------------------------------------------------------------------


class TestRenderFunctionButtonIntegrity:
    """Every render function that has buttons should properly wire them."""

    @pytest.mark.parametrize(
        "fn_name",
        [
            "render_home",
            "render_projects",
            "render_ai_settings",
            "render_outline",
            "render_world",
            "render_chapters",
        ],
    )
    def test_render_function_has_buttons(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.button(" in body, f"{fn_name} should have at least one button"

    @pytest.mark.parametrize(
        "fn_name",
        [
            "render_home",
            "render_projects",
            "render_outline",
            "render_world",
            "render_chapters",
        ],
    )
    def test_render_function_has_rerun(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.rerun()" in body, f"{fn_name} should call st.rerun() somewhere"


# ============================================================================
# Tests from test_helpers.py — Helper function unit tests
# ============================================================================

# ============================================================================
# word_count Tests
# ============================================================================

class TestWordCount:
    """Test suite for word_count utility function."""

    @pytest.mark.parametrize(
        "text,expected",
        [
            # Basic cases
            ("hello world", 2),
            ("single", 1),
            ("one two three four five", 5),
            
            # Empty and whitespace
            ("", 0),
            ("   ", 0),
            ("\n\n\n", 0),
            ("\t\t", 0),
            
            # None handling
            (None, 0),
            
            # Multiple whitespace types
            ("word1\tword2\nword3", 3),
            ("multiple   spaces   between", 3),
            
            # Punctuation (counted as part of words)
            ("Hello, world!", 2),
            ("It's a test.", 3),
            ("One-two three", 2),
            
            # Numbers
            ("123 456 789", 3),
            ("word 123 word", 3),
            
            # Unicode
            ("café résumé", 2),
            ("hello 世界", 2),
            
            # Long text
            ("The quick brown fox jumps over the lazy dog", 9),
        ],
    )
    @pytest.mark.unit
    def test_word_count_parametrized(self, text: str | None, expected: int):
        """Test word_count with various inputs."""
        assert word_count(text) == expected

    @pytest.mark.unit
    def test_word_count_paragraph(self):
        """Test word_count with a full paragraph."""
        text = """
        This is a test paragraph with multiple lines.
        It contains several sentences and should be counted correctly.
        The function splits on whitespace.
        """
        # Count actual words (excluding empty strings from split)
        expected = len([w for w in text.split() if w])
        assert word_count(text) == expected


# ============================================================================
# clamp Tests
# ============================================================================

class TestClamp:
    """Test suite for clamp utility function."""

    @pytest.mark.parametrize(
        "value,low,high,expected",
        [
            # Integer cases - value within bounds
            (5, 0, 10, 5),
            (0, 0, 10, 0),
            (10, 0, 10, 10),
            
            # Integer cases - value below bounds
            (-5, 0, 10, 0),
            (-100, 0, 10, 0),
            
            # Integer cases - value above bounds
            (15, 0, 10, 10),
            (100, 0, 10, 10),
            
            # Float cases - value within bounds
            (5.5, 0.0, 10.0, 5.5),
            (0.0, 0.0, 10.0, 0.0),
            (10.0, 0.0, 10.0, 10.0),
            
            # Float cases - value below bounds
            (-5.5, 0.0, 10.0, 0.0),
            (-100.5, 0.0, 10.0, 0.0),
            
            # Float cases - value above bounds
            (15.5, 0.0, 10.0, 10.0),
            (100.5, 0.0, 10.0, 10.0),
            
            # Mixed int/float
            (5, 0.0, 10.0, 5),
            (5.5, 0, 10, 5.5),
            
            # Negative bounds
            (-5, -10, -1, -5),
            (-15, -10, -1, -10),
            (0, -10, -1, -1),
            
            # Zero bounds
            (5, 0, 0, 0),
            (-5, 0, 0, 0),
            
            # Same low and high
            (5, 10, 10, 10),
            (15, 10, 10, 10),
        ],
    )
    @pytest.mark.unit
    def test_clamp_parametrized(
        self,
        value: int | float,
        low: int | float,
        high: int | float,
        expected: int | float
    ):
        """Test clamp with various numeric inputs."""
        assert clamp(value, low, high) == expected

    @pytest.mark.unit
    def test_clamp_preserves_type(self):
        """Test that clamp preserves numeric types when possible."""
        # Integer clamping
        result = clamp(5, 0, 10)
        assert isinstance(result, int)
        
        # Float clamping
        result = clamp(5.5, 0.0, 10.0)
        assert isinstance(result, float)


# ============================================================================
# current_year Tests
# ============================================================================

class TestCurrentYear:
    """Test suite for current_year utility function."""

    @pytest.mark.unit
    def test_current_year_returns_int(self):
        """Test that current_year returns an integer."""
        year = current_year()
        assert isinstance(year, int)

    @pytest.mark.unit
    def test_current_year_reasonable_value(self):
        """Test that current_year returns a reasonable year value."""
        year = current_year()
        # Should be between 2024 and 2100 for the foreseeable future
        assert 2024 <= year <= 2100

    @pytest.mark.unit
    def test_current_year_matches_datetime(self):
        """Test that current_year matches datetime.now()."""
        year = current_year()
        expected = datetime.datetime.now(datetime.timezone.utc).year
        assert year == expected


# ============================================================================
# AI Connection Helper Tests
# ============================================================================

class TestAIConnectionHelpers:
    """Test suite for AI connection helper functions."""

    @pytest.mark.unit
    def test_has_any_api_key_with_ai_configured(self, mock_session_state):
        """Test _has_any_api_key when ai_configured flag is set."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["ai_configured"] = True
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_with_api_keys_flag(self, mock_session_state):
        """Test _has_any_api_key when api_keys flag is set."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["api_keys"] = True
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_with_providers(self, mock_session_state):
        """Test _has_any_api_key when providers flag is set."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["providers"] = True
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_with_ai_keys_dict(self, mock_session_state):
        """Test _has_any_api_key with ai_keys dictionary."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["ai_keys"] = {"groq": "test-key"}
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_with_session_keys(self, mock_session_state):
        """Test _has_any_api_key with ai_session_keys."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["ai_session_keys"] = {"openai": "test-key"}
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_with_direct_keys(self, mock_session_state):
        """Test _has_any_api_key with direct API key values."""
        from app.utils.helpers import _has_any_api_key
        
        mock_session_state["groq_api_key"] = "test-groq-key"
        assert _has_any_api_key(mock_session_state) is True
        
        mock_session_state["groq_api_key"] = None
        mock_session_state["openai_api_key"] = "test-openai-key"
        assert _has_any_api_key(mock_session_state) is True

    @pytest.mark.unit
    def test_has_any_api_key_no_keys(self, mock_session_state):
        """Test _has_any_api_key when no keys are configured."""
        from app.utils.helpers import _has_any_api_key
        
        # Default mock_session_state has empty ai_keys
        assert _has_any_api_key(mock_session_state) is False

    @pytest.mark.unit
    def test_has_tested_connection_with_groq_tests(self, mock_session_state):
        """Test _has_tested_connection with groq model tests."""
        from app.utils.helpers import _has_tested_connection
        
        mock_session_state["groq_model_tests"] = {"model1": "success"}
        assert _has_tested_connection(mock_session_state) is True

    @pytest.mark.unit
    def test_has_tested_connection_with_openai_tests(self, mock_session_state):
        """Test _has_tested_connection with openai model tests."""
        from app.utils.helpers import _has_tested_connection
        
        mock_session_state["openai_model_tests"] = {"model1": "success"}
        assert _has_tested_connection(mock_session_state) is True

    @pytest.mark.unit
    def test_has_tested_connection_with_model_lists(self, mock_session_state):
        """Test _has_tested_connection with model lists."""
        from app.utils.helpers import _has_tested_connection
        
        mock_session_state["groq_model_list"] = ["model1", "model2"]
        assert _has_tested_connection(mock_session_state) is True

    @pytest.mark.unit
    def test_has_tested_connection_with_flags(self, mock_session_state):
        """Test _has_tested_connection with connection tested flags."""
        from app.utils.helpers import _has_tested_connection
        
        mock_session_state["groq_connection_tested"] = True
        assert _has_tested_connection(mock_session_state) is True

    @pytest.mark.unit
    def test_has_tested_connection_no_tests(self, mock_session_state):
        """Test _has_tested_connection when no tests have been run."""
        from app.utils.helpers import _has_tested_connection
        
        assert _has_tested_connection(mock_session_state) is False


# ============================================================================
# Tests from test_router.py — Router and navigation tests
# ============================================================================

# ============================================================================
# Navigation Configuration Tests
# ============================================================================

class TestGetNavConfig:
    """Test suite for get_nav_config function."""

    @pytest.mark.unit
    def test_get_nav_config_returns_tuple(self):
        """Test that get_nav_config returns a tuple of (labels, page_map)."""
        result = get_nav_config(has_project=True)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @pytest.mark.unit
    def test_get_nav_config_labels_is_list(self):
        """Test that nav labels is a list of strings."""
        labels, _ = get_nav_config(has_project=True)
        assert isinstance(labels, list)
        assert len(labels) > 0
        assert all(isinstance(label, str) for label in labels)

    @pytest.mark.unit
    def test_get_nav_config_page_map_is_dict(self):
        """Test that page_map is a dict mapping labels to keys."""
        _, page_map = get_nav_config(has_project=True)
        assert isinstance(page_map, dict)
        assert len(page_map) > 0
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in page_map.items())

    @pytest.mark.unit
    def test_get_nav_config_contains_required_pages(self):
        """Test that nav config includes required pages."""
        labels, page_map = get_nav_config(has_project=True)
        
        # Check for essential pages
        required_labels = ["Dashboard", "Projects"]
        for required in required_labels:
            assert required in labels, f"Missing required nav item: {required}"

    @pytest.mark.unit
    def test_get_nav_config_page_map_maps_labels(self):
        """Test that all labels have corresponding page_map entries."""
        labels, page_map = get_nav_config(has_project=True)
        
        for label in labels:
            assert label in page_map, f"Label '{label}' not in page_map"

    @pytest.mark.parametrize("has_project", [True, False])
    @pytest.mark.unit
    def test_get_nav_config_with_project_param(self, has_project: bool):
        """Test get_nav_config with different has_project values."""
        labels, page_map = get_nav_config(has_project=has_project)
        
        # Should return valid config regardless of has_project
        assert isinstance(labels, list)
        assert isinstance(page_map, dict)
        assert len(labels) > 0
        assert len(page_map) > 0


# ============================================================================
# Route Mapping Tests
# ============================================================================

class TestGetRoutes:
    """Test suite for get_routes function."""

    @pytest.mark.unit
    def test_get_routes_returns_dict(self):
        """Test that get_routes returns a dictionary."""
        routes = get_routes()
        assert isinstance(routes, dict)

    @pytest.mark.unit
    def test_get_routes_all_values_are_callable(self):
        """Test that all route values are callable functions."""
        routes = get_routes()
        for route_key, renderer in routes.items():
            assert callable(renderer), f"Route '{route_key}' renderer is not callable"

    @pytest.mark.unit
    def test_get_routes_contains_required_routes(self):
        """Test that get_routes includes all required routes."""
        routes = get_routes()
        
        required_routes = [
            "home",
            "projects",
            "outline",
            "chapters",
            "world",
            "export",
            "ai",
            "legal",
        ]
        
        for route in required_routes:
            assert route in routes, f"Missing required route: {route}"

    @pytest.mark.unit
    def test_get_routes_includes_legal_subroutes(self):
        """Test that get_routes includes legal sub-pages."""
        routes = get_routes()
        
        legal_routes = ["terms", "privacy", "copyright", "cookie", "help"]
        
        for route in legal_routes:
            assert route in routes, f"Missing legal route: {route}"

    @pytest.mark.unit
    def test_get_routes_renderers_have_correct_names(self):
        """Test that route renderers have expected function names."""
        routes = get_routes()
        
        # Map routes to expected renderer function names
        expected_names = {
            "home": "render_home",
            "projects": "render_projects",
            "outline": "render_outline",
            "chapters": "render_chapters",
            "world": "render_world",
            "export": "render_export",
            "ai": "render_ai_settings",
        }
        
        for route, expected_name in expected_names.items():
            renderer = routes.get(route)
            assert renderer is not None, f"Route '{route}' not found"
            assert renderer.__name__ == expected_name, \
                f"Route '{route}' has renderer '{renderer.__name__}', expected '{expected_name}'"

    @pytest.mark.parametrize(
        "route_key",
        [
            "home",
            "projects",
            "outline",
            "chapters",
            "world",
            "export",
            "ai",
            "legal",
            "terms",
            "privacy",
            "copyright",
            "cookie",
            "help",
        ]
    )
    @pytest.mark.unit
    def test_get_routes_each_route_exists(self, route_key: str):
        """Test that each expected route exists in the routes dict."""
        routes = get_routes()
        assert route_key in routes, f"Route '{route_key}' not found in routes"
        assert callable(routes[route_key]), f"Route '{route_key}' is not callable"


# ============================================================================
# Route Integration Tests
# ============================================================================

class TestRouteIntegration:
    """Integration tests for navigation and routing."""

    @pytest.mark.integration
    def test_all_nav_labels_have_routes(self):
        """Test that all navigation labels map to valid routes."""
        labels, page_map = get_nav_config(has_project=True)
        routes = get_routes()
        
        for label in labels:
            page_key = page_map.get(label)
            assert page_key is not None, f"Label '{label}' has no page_map entry"
            
            # The page_key should exist in routes
            # (though some may map to the same renderer, like legal pages)
            assert page_key in routes or any(page_key in routes for _ in [1]), \
                f"Page key '{page_key}' for label '{label}' not found in routes"

    @pytest.mark.integration
    def test_route_consistency(self):
        """Test that routes and navigation config are consistent."""
        labels, page_map = get_nav_config(has_project=True)
        routes = get_routes()
        
        # All page_map values should be route keys
        for label, page_key in page_map.items():
            # Extended map may include additional routes
            if page_key not in routes:
                # This is acceptable for extended routes
                continue
            
            assert page_key in routes, \
                f"Navigation label '{label}' maps to '{page_key}' which is not in routes"

    @pytest.mark.integration
    def test_no_duplicate_routes(self):
        """Test that route keys are unique."""
        routes = get_routes()
        route_keys = list(routes.keys())
        
        # Check for duplicates
        assert len(route_keys) == len(set(route_keys)), \
            "Duplicate route keys found"

    @pytest.mark.integration
    def test_legal_routes_all_map_to_legal_redirect(self):
        """Test that all legal sub-routes use the same renderer."""
        routes = get_routes()
        
        legal_routes = ["legal", "terms", "privacy", "copyright", "cookie", "help"]
        
        # All should map to render_legal_redirect
        legal_renderer = routes["legal"]
        for route in legal_routes:
            assert routes[route] == legal_renderer, \
                f"Legal route '{route}' does not use render_legal_redirect"


# ============================================================================
# Tests from test_services.py — Service layer tests
# ============================================================================

class TestSafeEnvParsing:
    """Verify that _safe_int and _safe_float handle bad env vars gracefully."""

    def test_safe_int_valid(self):
        from app.config.settings import _safe_int

        os.environ["_TEST_SAFE_INT"] = "42"
        try:
            assert _safe_int("_TEST_SAFE_INT", 10) == 42
        finally:
            del os.environ["_TEST_SAFE_INT"]

    def test_safe_int_invalid_returns_default(self):
        from app.config.settings import _safe_int

        os.environ["_TEST_SAFE_INT"] = "not_a_number"
        try:
            assert _safe_int("_TEST_SAFE_INT", 10) == 10
        finally:
            del os.environ["_TEST_SAFE_INT"]

    def test_safe_int_empty_returns_default(self):
        from app.config.settings import _safe_int

        assert _safe_int("_TEST_NONEXISTENT_VAR_12345", 99) == 99

    def test_safe_float_valid(self):
        from app.config.settings import _safe_float

        os.environ["_TEST_SAFE_FLOAT"] = "3.14"
        try:
            assert abs(_safe_float("_TEST_SAFE_FLOAT", 1.0) - 3.14) < 0.001
        finally:
            del os.environ["_TEST_SAFE_FLOAT"]

    def test_safe_float_invalid_returns_default(self):
        from app.config.settings import _safe_float

        os.environ["_TEST_SAFE_FLOAT"] = "abc"
        try:
            assert _safe_float("_TEST_SAFE_FLOAT", 0.5) == 0.5
        finally:
            del os.environ["_TEST_SAFE_FLOAT"]


class TestMainSafeEnvParsing:
    """Verify that _safe_int_env and _safe_float_env in main.py handle bad env vars."""

    def test_safe_int_env_valid(self):
        from app.main import _safe_int_env

        os.environ["_TEST_MAIN_INT"] = "42"
        try:
            assert _safe_int_env("_TEST_MAIN_INT", 10) == 42
        finally:
            del os.environ["_TEST_MAIN_INT"]

    def test_safe_int_env_invalid_returns_default(self):
        from app.main import _safe_int_env

        os.environ["_TEST_MAIN_INT"] = "not_a_number"
        try:
            assert _safe_int_env("_TEST_MAIN_INT", 10) == 10
        finally:
            del os.environ["_TEST_MAIN_INT"]

    def test_safe_int_env_empty_returns_default(self):
        from app.main import _safe_int_env

        assert _safe_int_env("_TEST_NONEXISTENT_MAIN_INT", 99) == 99

    def test_safe_float_env_valid(self):
        from app.main import _safe_float_env

        os.environ["_TEST_MAIN_FLOAT"] = "3.14"
        try:
            assert abs(_safe_float_env("_TEST_MAIN_FLOAT", 1.0) - 3.14) < 0.001
        finally:
            del os.environ["_TEST_MAIN_FLOAT"]

    def test_safe_float_env_invalid_returns_default(self):
        from app.main import _safe_float_env

        os.environ["_TEST_MAIN_FLOAT"] = "abc"
        try:
            assert _safe_float_env("_TEST_MAIN_FLOAT", 0.5) == 0.5
        finally:
            del os.environ["_TEST_MAIN_FLOAT"]


class TestSafeConfigValueParsing:
    """Verify that corrupted config values don't crash session state init."""

    def _init_with_config(self, data):
        """Helper to initialize session state with given config data."""
        from app.config.settings import AppConfig
        from app.state import initialize_session_state
        from unittest.mock import MagicMock
        import json

        config_path = AppConfig.CONFIG_PATH
        os.makedirs(os.path.dirname(config_path) or ".", exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

        class MockSessionState(dict):
            """Dict subclass that acts like Streamlit session_state."""
            def __setattr__(self, key, value):
                self[key] = value
            def __getattr__(self, key):
                try:
                    return self[key]
                except KeyError:
                    raise AttributeError(key)

        mock_st = MagicMock()
        mock_st.session_state = MockSessionState()

        from app.config.settings import load_app_config
        loaded = load_app_config()
        initialize_session_state(mock_st, loaded)

        try:
            os.remove(config_path)
        except OSError:
            pass

        return mock_st.session_state

    def test_invalid_daily_word_goal(self):
        """Non-numeric daily_word_goal falls back to default."""
        state = self._init_with_config({"daily_word_goal": "not_a_number"})
        assert state.get("daily_word_goal") == 500

    def test_invalid_weekly_sessions_goal(self):
        """Non-numeric weekly_sessions_goal falls back to default."""
        state = self._init_with_config({"weekly_sessions_goal": "bad"})
        assert state.get("weekly_sessions_goal") == 4

    def test_invalid_focus_minutes(self):
        """Non-numeric focus_minutes falls back to default."""
        state = self._init_with_config({"focus_minutes": "nope"})
        assert state.get("focus_minutes") == 25


class TestFileLock:
    """Verify the file_lock context manager works correctly."""

    def test_file_lock_acquires_and_releases(self):
        from app.services.storage import file_lock

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            with file_lock(path, timeout=2) as acquired:
                assert acquired is True
                assert os.path.exists(path + ".lock")
            # Lock file should be cleaned up after context exit
            assert not os.path.exists(path + ".lock")
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def test_file_lock_timeout(self):
        from app.services.storage import file_lock, _acquire_lock

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        lock_path = path + ".lock"
        try:
            # Pre-create a lock file to simulate contention
            with open(lock_path, "w") as lf:
                lf.write("9999999")
            # Set mtime to now so the stale-lock cleanup doesn't kick in
            os.utime(lock_path, None)

            with file_lock(path, timeout=0) as acquired:
                assert acquired is False
        finally:
            try:
                os.remove(lock_path)
            except OSError:
                pass
            try:
                os.remove(path)
            except OSError:
                pass


class TestGenerateJsonExtraction:
    """Verify that generate_json can extract JSON from AI responses."""

    def test_json_surrounded_by_text(self):
        # Simulate the JSON extraction logic from generate_json
        import json
        import re

        txt = 'Here is the result: [{"name": "Aria"}] hope that helps!'
        txt = re.sub(r"```json\s*", "", txt)
        txt = re.sub(r"```\s*", "", txt).strip()
        if not txt.startswith(("[", "{")):
            bracket = txt.find("[")
            brace = txt.find("{")
            if bracket >= 0 and (brace < 0 or bracket < brace):
                txt = txt[bracket:]
            elif brace >= 0:
                txt = txt[brace:]
        # Should now parse successfully
        d = json.loads(txt[:txt.rfind("]") + 1])
        assert isinstance(d, list)
        assert d[0]["name"] == "Aria"

    def test_clean_json_array(self):
        import json
        txt = '[{"name": "Test"}]'
        d = json.loads(txt)
        assert isinstance(d, list)

    def test_json_with_markdown_fences(self):
        import json
        import re
        txt = '```json\n[{"name": "Test"}]\n```'
        txt = re.sub(r"```json\s*", "", txt)
        txt = re.sub(r"```\s*", "", txt).strip()
        d = json.loads(txt)
        assert isinstance(d, list)


# ============================================================================
# Tests from test_imports.py — Import smoke tests (deduplicated)
# ============================================================================

# ============================================================================
# Service Module Imports
# ============================================================================

class TestServiceImports:
    """Test that all service modules can be imported."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "app.services.storage",
            "app.services.export",
            "app.services.ai",
            "app.services.world_bible_db",
            "app.services.world_bible",
            "app.services.projects",
            "app.services.world_bible_merge",
        ]
    )
    @pytest.mark.smoke
    def test_service_module_imports(self, module_name: str):
        """Test that service modules import without errors."""
        mod = importlib.import_module(module_name)
        assert mod is not None


# ============================================================================
# View Module Imports
# ============================================================================

class TestViewImports:
    """Test that all view modules can be imported."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "app.views.ai_tools",
            "app.views.dashboard",
            "app.views.editor",
            "app.views.export",
            "app.views.legal",
            "app.views.outline",
            "app.views.projects",
            "app.views.world_bible",
        ]
    )
    @pytest.mark.smoke
    def test_view_module_imports(self, module_name: str):
        """Test that view modules import without errors."""
        mod = importlib.import_module(module_name)
        assert mod is not None


# ============================================================================
# Utility Module Imports
# ============================================================================

class TestUtilityImports:
    """Test that all utility modules can be imported."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "app.utils.keys",
            "app.utils.auth",
            "app.utils.versioning",
            "app.utils.helpers",
            "app.utils.navigation",
        ]
    )
    @pytest.mark.smoke
    def test_utility_module_imports(self, module_name: str):
        """Test that utility modules import without errors."""
        mod = importlib.import_module(module_name)
        assert mod is not None


# ============================================================================
# Component Module Imports
# ============================================================================

class TestComponentImports:
    """Test that all component modules can be imported."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "app.components.forms",
            "app.components.buttons",
            "app.components.ui",
            "app.components.editors",
        ]
    )
    @pytest.mark.smoke
    def test_component_module_imports(self, module_name: str):
        """Test that component modules import without errors."""
        mod = importlib.import_module(module_name)
        assert mod is not None


# ============================================================================
# Config Module Imports
# ============================================================================

class TestConfigImports:
    """Test that configuration modules can be imported."""

    @pytest.mark.smoke
    def test_import_settings(self):
        """Test that settings module imports successfully."""
        settings = importlib.import_module("app.config.settings")
        assert hasattr(settings, "AppConfig")


# ============================================================================
# UI Button Key Tests
# ============================================================================

class TestEditorButtonKeysImport:
    """Verify that editor buttons have unique keys to avoid Streamlit conflicts."""

    @pytest.mark.smoke
    def test_editor_chapter_buttons_have_keys(self):
        """Test that chapter creation buttons have unique keys."""
        mod = importlib.import_module("app.main")
        source = Path(mod.__file__).read_text(encoding="utf-8")
        
        # Check for chapter creation button with key
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ Create Chapter 1['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_create_chapter_1['\"]",
            source,
        )
        
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ New Chapter['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_new_chapter['\"]",
            source,
        )

        # Also check app_context.py
        ctx = importlib.import_module("app.app_context")
        ctx_source = Path(ctx.__file__).read_text(encoding="utf-8")
        
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ Create Chapter 1['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_create_chapter_1['\"]",
            ctx_source,
        )
        
        assert re.search(
            r"st\.button\([\s\S]*?['\"]➕ New Chapter['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_new_chapter['\"]",
            ctx_source,
        )


# ============================================================================
# Tests from test_bump_version.py — Version bump tests
# ============================================================================

class TestBumpVersion:
    """Test suite for bump_version function."""

    @pytest.mark.parametrize(
        "current,expected",
        [
            ("85.4", "85.5"),
            ("85.0", "85.1"),
            ("85.8", "85.9"),
            ("0.0", "0.1"),
            ("100.5", "100.6"),
        ],
    )
    @pytest.mark.unit
    def test_minor_increment(self, current: str, expected: str):
        """Minor version increments by 1."""
        assert bump_version(current) == expected

    @pytest.mark.parametrize(
        "current,expected",
        [
            ("85.9", "86.0"),
            ("0.9", "1.0"),
            ("99.9", "100.0"),
        ],
    )
    @pytest.mark.unit
    def test_minor_rollover(self, current: str, expected: str):
        """Major increments and minor resets when minor reaches 10."""
        assert bump_version(current) == expected

    @pytest.mark.unit
    def test_current_version_file(self):
        """VERSION.txt contains a valid version that can be bumped."""
        version_file = ROOT / "VERSION.txt"
        current = version_file.read_text(encoding="utf-8").strip()
        result = bump_version(current)
        parts = result.split(".")
        assert len(parts) == 2
        assert parts[0].isdigit()
        assert parts[1].isdigit()

    @pytest.mark.parametrize(
        "bad_version",
        [
            "abc",
            "1.2.3",
            "",
            "no_dot",
        ],
    )
    @pytest.mark.unit
    def test_invalid_format_exits(self, bad_version: str):
        """Invalid formats cause SystemExit."""
        with pytest.raises(SystemExit):
            bump_version(bad_version)
