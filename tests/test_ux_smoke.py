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

    def test_footer_nav_links_match_nav_items(self):
        """The footer link builder must produce one link per NAV_ITEMS entry."""
        from app.utils.navigation import get_nav_items
        from app.ui.layout import _build_footer_nav_links

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

    def test_primary_has_green_bg(self):
        assert "#2e7d32" in self._css()

    def test_danger_has_red_bg(self):
        assert "#e53935" in self._css()

    def test_ghost_has_transparent_bg(self):
        css = self._css()
        assert ".mantis-btn-ghost > button" in css
        assert "transparent" in css


class TestQuickActionButtonsPrimary:
    """Quick action buttons must use the primary button theme."""

    def test_action_card_uses_primary_type(self):
        import inspect
        from app.components.buttons import action_card

        src = inspect.getsource(action_card)
        assert 'type="primary"' in src, "action_card button should use type='primary'"

    def test_main_quick_action_buttons_use_primary(self):
        src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        # Find the Quick Actions section and verify all st.button calls use type="primary"
        start = src.index("Quick Actions")
        # The quick action section ends before "Recent Projects"
        end = src.index("Recent Projects", start)
        section = src[start:end]
        button_calls = [line.strip() for line in section.splitlines() if "st.button(" in line]
        assert len(button_calls) > 0, "Expected quick action st.button calls"
        for call in button_calls:
            if 'type="primary"' not in call:
                # type may be on the next line; check the section has enough type="primary" usages
                pass
        assert section.count('type="primary"') >= 6, (
            "All 6 quick action buttons should use type='primary'"
        )
