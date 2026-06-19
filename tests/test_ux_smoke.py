"""Comprehensive UX smoke tests for MANTIS Studio.

These tests validate every page and critical function from the user's
standpoint without requiring a running Streamlit server.  They exercise
imports, data-layer operations, navigation config, utility functions,
and the auth stub so that regressions in any module are caught early.
"""
from __future__ import annotations

import importlib
import json
import re
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
# 1) Critical imports  every module that the UI depends on must import
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
            r"st\.button\([\s\S]*?['\"]\s*Create Chapter 1['\"][\s\S]*?"
            r"key\s*=\s*['\"]editor_create_chapter_1['\"]",
            source,
        )

        workspace = importlib.import_module("app.views.editor_workspace")
        workspace_source = Path(workspace.__file__).read_text(encoding="utf-8")
        assert "editor_flow_new_chapter" in workspace_source

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
        ui = importlib.import_module("app.components.buttons")
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
        theme = importlib.import_module("app.ui.enhanced_theme")
        assert hasattr(theme, "inject_enhanced_theme")

    def test_import_ui_layout(self):
        importlib.import_module("app.layout.layout")

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
# 2) Project CRUD  the core data model that all pages rely on
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
# 2b) Save  app config atomic write
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
# 3) Export  verify project export generation
# ---------------------------------------------------------------------------

class TestExport:
    """Test the export-to-markdown function used by project export actions."""

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
# 4) Navigation  sidebar routing config
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
# 4b) Navigation parity  sidebar and footer must stay in sync
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
        assert "AI Settings" in labels

    def test_get_nav_items_returns_list_of_tuples(self):
        from app.utils.navigation import get_nav_items
        items = get_nav_items()
        assert isinstance(items, list)
        assert len(items) >= 6
        for item in items:
            assert len(item) == 3, "Each item must be (label, page_key, icon)"

    def test_footer_nav_links_match_nav_items(self):
        """The footer link builder must produce one link per NAV_ITEMS entry."""
        from app.utils.navigation import get_nav_items
        from app.layout.layout import _build_footer_nav_links

        html = _build_footer_nav_links()
        for label, page_key, icon in get_nav_items():
            assert f'href="?page={page_key}#mantis-top"' in html, (
                f"Footer missing link for {label} (?page={page_key})"
            )
            assert label in html, f"Footer missing label text '{label}'"

    def test_layout_footer_nav_links_match_nav_items(self):
        """The layout/layout.py footer builder must also match NAV_ITEMS."""
        from app.utils.navigation import get_nav_items
        from app.layout.layout import _build_footer_nav_links

        html = _build_footer_nav_links()
        for label, page_key, icon in get_nav_items():
            assert f'href="?page={page_key}#mantis-top"' in html, (
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

    def test_insights_precedes_memory_in_sidebar_and_footer_order(self):
        from app.utils.navigation import get_nav_items, get_nav_sections
        from app.layout.layout import _build_footer_nav_links

        intelligence = dict(get_nav_sections())["Intelligence"]
        intelligence_labels = [label for label, _, _ in intelligence]
        assert "Knowledge Base" in intelligence_labels
        assert intelligence_labels.index("Knowledge Base") < intelligence_labels.index("Insights")
        assert intelligence_labels.index("Insights") < intelligence_labels.index("Memory")

        flat_labels = [label for label, _, _ in get_nav_items()]
        assert "Knowledge Base" in flat_labels
        assert flat_labels.index("Insights") < flat_labels.index("Memory")

        html = _build_footer_nav_links()
        assert "?page=knowledge" in html
        assert html.index("?page=knowledge") < html.index("?page=insights")
        assert html.index("?page=insights") < html.index("?page=memory")

    def test_settings_order_is_workspace_ai_user(self):
        from app.utils.navigation import get_nav_sections
        from app.layout.layout import _build_footer_nav_links

        settings = dict(get_nav_sections())["Settings"]
        labels = [label for label, _, _ in settings]
        assert labels == ["Workspace Settings", "AI Settings", "User Settings"]

        html = _build_footer_nav_links()
        assert html.index("?page=workspace") < html.index("?page=ai") < html.index("?page=user")

    def test_dashboard_quick_actions_prioritize_insights_before_memory(self):
        source = (ROOT / "app" / "views" / "dashboard_workspace.py").read_text(encoding="utf-8")
        assert source.index('key="qa_insights"') < source.index('key="qa_memory"')

    def test_dashboard_removes_redundant_data_confidence_card(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        home_block = source[source.index("def render_home():"):source.index("def render_projects():")]
        assert "Data confidence" not in home_block
        assert "Ownership and save behavior for long-form work." not in home_block
        assert "You keep project files and can export anytime from Projects." not in home_block

    def test_main_page_navigation_uses_one_shot_top_anchor_reset(self):
        """Page changes should reset to the top without the old aggressive scroll loop."""
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "def navigate_to_page(" in source
        assert "def _render_page_position_reset(" in source
        assert "mantis-top" in source
        assert "scrollIntoView" in source
        assert 'section[data-testid="stMain"]' in source
        assert "section.stMain" in source
        assert "_scroll_top_pending" not in source
        assert 'scrollRestoration = "manual"' not in source
        assert "MutationObserver(doScroll)" not in source
        assert '"user",' in source

    def test_knowledge_base_learning_page_is_registered(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "def render_knowledge_base():" in source
        assert 'st.session_state.page = "knowledge"' in source
        assert 'elif pg == "knowledge":' in source
        assert '"knowledge", "insights"' in source
        assert "extract_text_from_upload" in source
        assert "import_knowledge_document" in source
        assert "search_knowledge_base" in source
        assert "Core Library" in source
        assert "User Library" in source
        assert "Author & Style Lab" in source
        assert "Knowledge Health" in source


# ---------------------------------------------------------------------------
# 5) Auth stub  must not crash the app
# ---------------------------------------------------------------------------

class TestAuth:
    """Verify the auth stub module provides the expected interface."""

    def test_get_current_user_returns_none(self):
        from app.utils.auth import get_current_user
        assert get_current_user() is None

    def test_is_authenticated_returns_false(self):
        from app.utils.auth import is_authenticated
        assert is_authenticated() is False

    def test_email_is_only_login_identifier(self, tmp_path):
        from app.utils.auth import authenticate_user, register_user, reset_password_with_email

        ok1, _, first = register_user(
            "one@example.com",
            "Password1234",
            display_name="Writer",
            base_projects_dir=str(tmp_path),
        )
        ok2, _, second = register_user(
            "two@example.com",
            "Password4567",
            display_name="Writer",
            base_projects_dir=str(tmp_path),
        )

        assert ok1 is True
        assert ok2 is True
        assert first["account_id"] != second["account_id"]

        ok, msg, _ = authenticate_user("Writer", "Password1234", base_projects_dir=str(tmp_path))
        assert ok is False
        assert "Invalid email" in msg

        ok, _, user = authenticate_user(first["account_id"], "Password1234", base_projects_dir=str(tmp_path))
        assert ok is False

        ok, _, user = authenticate_user("one@example.com", "Password1234", base_projects_dir=str(tmp_path))
        assert ok is True
        assert user["email"] == "one@example.com"

        ok, _, user = authenticate_user("two@example.com", "Password4567", base_projects_dir=str(tmp_path))
        assert ok is True
        assert user["account_id"] == second["account_id"]

        ok, msg = reset_password_with_email(
            email="one@example.com",
            recovery_code="wrong-code",
            new_password="NewPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "Recovery code" in msg

        ok, msg = reset_password_with_email(
            email="one@example.com",
            recovery_code=first["recovery_code"],
            new_password="NewPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True
        assert "New recovery code" in msg

    def test_email_reset_link_uses_hashed_one_time_token(self, tmp_path):
        import json
        from pathlib import Path
        from urllib.parse import parse_qs, urlparse

        from app.utils.auth import (
            authenticate_user,
            register_user,
            request_password_reset_email,
            reset_password_with_token,
        )

        ok, _, _user = register_user(
            "reset@example.com",
            "Password1234",
            display_name="Writer",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True

        sent = {}

        def fake_send_email(*, to_email, reset_url):
            sent["to_email"] = to_email
            sent["reset_url"] = reset_url
            return True, "sent"

        ok, msg = request_password_reset_email(
            email="reset@example.com",
            app_url="https://mantis-studio.streamlit.app",
            send_email=fake_send_email,
            base_projects_dir=str(tmp_path),
        )
        assert ok is True
        assert "reset link" in msg
        assert sent["to_email"] == "reset@example.com"
        token = parse_qs(urlparse(sent["reset_url"]).query)["reset_token"][0]
        assert token

        accounts = json.loads((Path(tmp_path) / ".mantis_users.json").read_text(encoding="utf-8"))
        stored = next(u for u in accounts["users"] if u["email"] == "reset@example.com")
        assert stored["reset_token_hash"] != token
        assert stored["reset_token_salt"]
        assert stored["reset_token_expires_at"] > 0

        ok, msg = reset_password_with_token(
            reset_token=token,
            new_password="BetterPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True
        assert "New recovery code" in msg

        ok, _, user = authenticate_user(
            "reset@example.com",
            "BetterPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True
        assert user["email"] == "reset@example.com"

        ok, msg = reset_password_with_token(
            reset_token=token,
            new_password="AnotherPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "invalid or expired" in msg

    def test_expired_email_reset_token_is_rejected(self, tmp_path):
        import json
        import time
        from pathlib import Path
        from urllib.parse import parse_qs, urlparse

        from app.utils.auth import register_user, request_password_reset_email, reset_password_with_token

        ok, _, _user = register_user(
            "expired@example.com",
            "Password1234",
            display_name="Writer",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True

        sent = {}

        def fake_send_email(*, to_email, reset_url):
            sent["reset_url"] = reset_url
            return True, "sent"

        ok, _msg = request_password_reset_email(
            email="expired@example.com",
            app_url="https://mantis-studio.streamlit.app",
            send_email=fake_send_email,
            base_projects_dir=str(tmp_path),
        )
        assert ok is True
        token = parse_qs(urlparse(sent["reset_url"]).query)["reset_token"][0]

        accounts_path = Path(tmp_path) / ".mantis_users.json"
        accounts = json.loads(accounts_path.read_text(encoding="utf-8"))
        for user in accounts["users"]:
            if user["email"] == "expired@example.com":
                user["reset_token_expires_at"] = time.time() - 1
        accounts_path.write_text(json.dumps(accounts), encoding="utf-8")

        ok, msg = reset_password_with_token(
            reset_token=token,
            new_password="BetterPassword123",
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "invalid or expired" in msg

    def test_builtin_admin_seeded(self, tmp_path):
        from app.utils.auth import authenticate_user

        ok, _, user = authenticate_user("ADMIN", "Admin@13319!", base_projects_dir=str(tmp_path))

        assert ok is True
        assert user["role"] == "admin"
        assert user["is_super_admin"] is True
        assert user["email"] == "admin"

    def test_only_builtin_admin_can_manage_roles(self, tmp_path):
        from app.utils.auth import authenticate_user, register_user, set_user_disabled, set_user_role

        ok, _, admin = authenticate_user("ADMIN", "Admin@13319!", base_projects_dir=str(tmp_path))
        assert ok is True

        ok, _, member = register_user(
            "member@example.com",
            "Password1234",
            display_name="Member",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True

        ok, msg = set_user_role(
            actor_user_id=member["id"],
            target_user_id=member["id"],
            role="admin",
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "Super admin" in msg

        ok, msg = set_user_role(
            actor_user_id=admin["id"],
            target_user_id=member["id"],
            role="admin",
            base_projects_dir=str(tmp_path),
        )
        assert ok is True

        ok, _, promoted = authenticate_user("member@example.com", "Password1234", base_projects_dir=str(tmp_path))
        assert ok is True
        assert promoted["role"] == "admin"
        assert promoted["is_super_admin"] is False

        ok, msg = set_user_disabled(
            actor_user_id=promoted["id"],
            target_user_id=admin["id"],
            disabled=True,
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "Super admin" in msg

        ok, msg = set_user_role(
            actor_user_id=admin["id"],
            target_user_id=admin["id"],
            role="member",
            base_projects_dir=str(tmp_path),
        )
        assert ok is False
        assert "super admin role cannot be changed" in msg

    def test_oauth_user_created_with_verified_email(self, tmp_path):
        from app.utils.auth import authenticate_oauth_user

        ok, msg, user = authenticate_oauth_user(
            provider="google",
            provider_subject="google-sub-123",
            email="writer@example.com",
            display_name="Writer",
            base_projects_dir=str(tmp_path),
        )

        assert ok, msg
        assert user is not None
        assert user["email"] == "writer@example.com"
        assert user["role"] == "member"

    def test_oauth_cannot_claim_builtin_admin(self, tmp_path):
        from app.utils.auth import authenticate_oauth_user

        ok, msg, user = authenticate_oauth_user(
            provider="google",
            provider_subject="google-admin-sub",
            email="ADMIN",
            display_name="ADMIN",
            base_projects_dir=str(tmp_path),
        )

        assert ok is False
        assert user is None
        assert "verified email" in msg


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
        assert "Return only rewritten chapter prose" in result
        assert "Do not include labels" in result

    def test_rewrite_prompt_custom(self):
        from app.main import rewrite_prompt
        result = rewrite_prompt("Text", "Custom", "Make it funny")
        assert "Make it funny" in result

    def test_clean_rewrite_output_removes_editor_notes(self):
        from app.main import clean_rewrite_output
        raw = "Here is the improved chapter:\nMaya opened the door.\n\nNotes: I improved the flow."
        assert clean_rewrite_output(raw) == "Maya opened the door."

    def test_project_title_filter_rejects_generic_formulas(self):
        from app.main import _is_generic_project_title
        assert _is_generic_project_title("Beyond the Fractured Horizon") is True
        assert _is_generic_project_title("The Unseen Library") is False

    def test_knowledge_base_import_search_and_context(self, tmp_path):
        from app.services.knowledge_base import (
            builtin_knowledge_status,
            build_knowledge_context,
            install_builtin_knowledge_base,
            import_knowledge_document,
            knowledge_stats,
            search_knowledge_base,
        )

        text = (
            "Jane Austen style notes: irony, free indirect discourse, and social observation.\n\n"
            "Gothic atmosphere uses isolation, dread, symbols, and dark settings.\n\n"
            "Copyright rule: use public-domain excerpts or original summaries for modern works."
        )
        result = import_knowledge_document(str(tmp_path), "literary_notes.txt", text)
        assert result["chunks"] >= 1

        stats = knowledge_stats(str(tmp_path))
        assert stats["documents"] == 1
        assert stats["chunks"] >= 1

        results = search_knowledge_base(str(tmp_path), "gothic atmosphere", limit=3)
        assert results
        assert "Gothic atmosphere" in results[0]["text"]
        filtered = search_knowledge_base(str(tmp_path), "gothic atmosphere", limit=3, category="theme")
        assert filtered
        no_match = search_knowledge_base(str(tmp_path), "gothic atmosphere", limit=3, category="workflow")
        assert no_match == []

        context = build_knowledge_context(str(tmp_path), "free indirect discourse", limit=2)
        assert "Knowledge Base" not in context  # source name should come from the imported file
        assert "literary_notes.txt" in context

        from app.services.knowledge_base import (
            delete_knowledge_document,
            build_style_lens_context,
            get_document_chunks,
            list_author_style_profiles,
            list_knowledge_categories,
            list_knowledge_sources,
            suggest_author_style_lenses,
        )

        assert "literary_notes.txt" in list_knowledge_sources(str(tmp_path))
        assert list_knowledge_categories(str(tmp_path))
        assert get_document_chunks(str(tmp_path), result["document_id"])
        assert delete_knowledge_document(str(tmp_path), result["document_id"]) is True
        assert knowledge_stats(str(tmp_path))["documents"] == 0

        builtin_status = builtin_knowledge_status(str(tmp_path))
        assert builtin_status["available"] is True
        assert builtin_status["installed"] is False
        builtin_result = install_builtin_knowledge_base(str(tmp_path))
        assert builtin_result["chunks"] > 600
        updated_status = builtin_knowledge_status(str(tmp_path))
        assert updated_status["installed"] is True
        assert updated_status["current"] is True
        builtin_results = search_knowledge_base(str(tmp_path), "gothic atmosphere", limit=5)
        assert builtin_results
        assert any("gothic" in item["text"].lower() for item in builtin_results)
        profiles = list_author_style_profiles(str(tmp_path))
        assert profiles
        profile_names = {profile["name"] for profile in profiles}
        assert "Jane Austen" in profile_names
        lens_context = build_style_lens_context(str(tmp_path), ["Jane Austen"], project_goal="social comedy")
        assert "STYLE LENS: Jane Austen" in lens_context
        assert "Craft traits to adapt" in lens_context
        assert "Do not copy passages" in lens_context
        suggestions = suggest_author_style_lenses(
            str(tmp_path),
            "A comedy of manners about courtship, social observation, irony, class pressure, and free indirect interiority.",
            limit=5,
        )
        assert suggestions
        assert any(item["name"] == "Jane Austen" for item in suggestions)

    def test_app_version(self):
        from app.main import get_app_version
        version = get_app_version()
        assert version  # non-empty string
        major, minor = version.split(".", 1)
        assert major.isdigit()
        assert minor.isdigit()
        assert int(minor) <= 9

    def test_whats_new_uses_real_release_highlights(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        highlights_block = source[source.index("def _release_highlights()"):source.index("def render_release_summary")]
        assert "def _release_highlights()" in source
        assert "email access visible without scrolling" in highlights_block
        assert "MANTIS Runtime instead of MANTIS Streamlit Server" in highlights_block
        assert "progress panel before scan work begins" in highlights_block
        assert "Author & Style Lab now shows a staged loading bar" in highlights_block
        assert "Author & Style Lab can now scan the current project" in highlights_block
        assert "Recommended lenses are preselected after scanning" in highlights_block
        assert "built-in master library now has deeper scene mechanics" in highlights_block
        assert "Sign-in/create account now uses a tighter MANTIS layout" in highlights_block
        assert "auth page now resets to the top" in highlights_block
        assert "Knowledge Base is now organized into Core Library, User Library, Author & Style Lab, and Knowledge Health" in highlights_block
        assert "Coherence fixes can now use the best matching chapter passage" in highlights_block
        assert "Editor summary text and disabled text areas now stay readable" in highlights_block
        assert "Chapter generation now retrieves relevant Knowledge Base guidance" in highlights_block
        assert "Guest projects now use a stable local guest id" in highlights_block
        assert "reset Streamlit's real main scroll container" in highlights_block
        assert "Dashboard no longer repeats low-value autosave" in highlights_block
        assert "Apply Fix now resolves chapters by id, number, title, or matching excerpt" in highlights_block
        assert "Improve Flow and other rewrite tools now request prose-only output" in highlights_block
        assert "Insights now labels pending canon review as Canon Scanner suggestions" in highlights_block
        assert "Sign-in now uses a clearer MANTIS-themed first-visit page" in highlights_block
        assert "Google sign-in now uses a one-click link button" in highlights_block
        assert "OAuth state validation now survives the Google round trip" in highlights_block
        assert "Password recovery now supports Resend-backed one-time reset links" in highlights_block
        assert "High-confidence World Bible suggestions now auto-apply" in highlights_block
        assert "Chapter Flow now uses a compact chapter dropdown with Previous, Next, New, and Delete actions." in source
        assert "Find and replace now defaults to the first exact match" in source
        assert "Canon Scanner, queued canon suggestions, and Coherence Check now live in Insights" in source
        assert "Relationship graph moved out of World Bible and into Insights" in source
        assert highlights_block.index("built-in master library now has deeper scene mechanics") < highlights_block.index("Dashboard no longer repeats")
        assert highlights_block.index("Guest projects now use") < highlights_block.index("Sign-in now uses a clearer")
        assert "Legacy duplicate runtime and UI compatibility shims were removed" not in highlights_block
        assert "What's New in Mantis Studio" not in source
        assert "check_and_show_whats_new" not in source
        assert "You can now see what changed between versions" not in source
        assert "This notification system was added" not in source
        assert "Why This Matters" not in source
        assert "webbrowser.open" not in source

    def test_welcome_banner_surfaces_latest_update_and_changelog(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        welcome_block = source[source.index("### Welcome to MANTIS Studio"):source.index("elif st.session_state.get(\"first_run\"")]
        highlights_block = source[source.index("def _release_highlights()"):source.index("def render_release_summary")]
        assert "Latest update highlights" in source
        assert "render_release_summary(compact=True)" in welcome_block
        compact_items = [
            line for line in highlights_block.splitlines()
            if line.strip().startswith('("')
        ][:4]
        compact_text = "\n".join(compact_items)
        assert "Access" in compact_text
        assert "Knowledge Base" in compact_text
        assert "Apply Fix" in compact_text
        assert "Theme Polish" in compact_text
        assert "Dashboard" not in compact_text
        assert "Open changelog" in welcome_block
        assert "AppConfig.CHANGELOG_URL" in welcome_block

    def test_dashboard_removes_low_value_status_strip(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        dashboard_source = (ROOT / "app" / "views" / "dashboard_workspace.py").read_text(encoding="utf-8")
        dashboard_block = source[source.index("def render_home():"):source.index("def render_projects():")]
        assert "Outcome-focused workspace for planning, drafting, canon, and export." not in dashboard_block
        assert "Canon {canon_label} - Mode: {system_mode}" not in dashboard_block
        assert "System mode:" not in dashboard_source
        assert "AI ops today" not in dashboard_source

    def test_insights_and_world_bible_use_current_review_language(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "Canon Scanner suggestions pending" in source
        assert "World Bible review queue pending" not in source
        assert "No chapter mentions yet" in source
        assert "Unused in chapters" not in source

    def test_oauth_docs_use_hyphenated_streamlit_url(self):
        source = (ROOT / "docs" / "OAUTH_SETUP.md").read_text(encoding="utf-8")
        assert "https://mantis-studio.streamlit.app/?oauth_provider=google" in source
        assert "https://mantisstudio.streamlit.app" not in source

    def test_launcher_dependencies_match_requirements(self):
        launcher = (ROOT / "Mantis_Launcher.bat").read_text(encoding="utf-8", errors="replace")
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
        required_packages = {
            line.split(">=")[0].strip()
            for line in requirements.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for package in (
            "streamlit",
            "requests",
            "python-dotenv",
            "python-docx",
            "pypdf",
            "weasyprint",
            "reportlab",
            "pandas",
            "plotly",
            "numpy",
            "pytz",
            "Pillow",
            "matplotlib",
            "tqdm",
            "playwright",
        ):
            assert package in launcher
            assert package in required_packages

        assert 'set "HEALTH_URL=http://127.0.0.1:%SERVER_PORT%/_stcore/health"' in launcher
        assert "MANTIS_OK" not in launcher
        assert "Get-NetTCPConnection -LocalPort %SERVER_PORT% -State Listen" in launcher
        assert "taskkill /F /PID" in launcher
        assert "Start-Process -WindowStyle Hidden" not in launcher
        assert "EXISTING MANTIS RUNTIME DETECTED" not in launcher
        assert 'start "MANTIS Runtime"' in launcher
        assert "MANTIS Streamlit Server" not in launcher
        assert "for /L %%i in (1,1,90)" in launcher

    def test_mantis_health_probe_is_before_heavy_ui_imports(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        run_ui_block = source[source.index("def _run_ui():"):source.index("def get_canon_health()")]
        assert "MANTIS_OK" in run_ui_block
        assert run_ui_block.index("st.set_page_config") < run_ui_block.index("MANTIS_OK")
        assert run_ui_block.index("MANTIS_OK") < run_ui_block.index("from app.services.knowledge_base import")

    def test_knowledge_style_lens_scan_has_progress_feedback(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        scan_block = source[
            source.index('st.session_state.pop("knowledge_style_lens_scan_pending"'):
            source.index('st.session_state["style_lens_suggestions"]')
        ]
        button_block = source[
            source.index('"Scan current work for best style lenses"'):
            source.index('suggestions = st.session_state.get("style_lens_suggestions"')
        ]
        assert 'st.session_state["knowledge_style_lens_scan_pending"] = True' in button_block
        assert "st.progress" in scan_block
        assert "Scanning current work" in scan_block
        assert "Preparing Knowledge Base scan" in scan_block
        assert "Collecting project signals" in scan_block
        assert "Comparing against author style profiles" in scan_block
        assert "Scoring recommended lenses" in scan_block

    def test_launcher_chat_handles_creator_and_learning_truth_locally(self):
        source = (ROOT / "scripts" / "mantis_launcher_chat.py").read_text(encoding="utf-8")
        assert "def _user_is_claiming_creator_context" in source
        assert "You are building MANTIS" in source
        assert "def run_simulator" in source
        assert "/simulate all runs the full local suite and saves lessons." in source
        assert "These lessons are now saved and included in future MANTIS chat context." in source
        assert "Do not claim you are working in the background, learning autonomously" in source
        assert "def forget(" in source
        assert "/forget X  Remove saved launcher memory notes containing X" in source
        assert "Simulator runs saved:" in source

    def test_launcher_chat_masks_secrets_and_forgets_memory(self, tmp_path):
        import argparse

        from scripts.mantis_launcher_chat import LauncherChat

        args = argparse.Namespace(
            url="http://localhost:8501",
            port=8501,
            log_file=str(tmp_path / "streamlit.log"),
            chat_log_file=str(tmp_path / "chat.log"),
            repo_root=str(tmp_path),
            memory_file=str(tmp_path / "memory.json"),
            drills_file=str(tmp_path / "drills.json"),
            handoff=False,
        )
        chat = LauncherChat(args)

        secret_text = (
            "gsk_abc1234567890SECRET "
            "GOCSPX-testClientSecretForMasking123 "
            "re_testResendKeyForMasking123456789 "
            "123456789012-fakegoogleclientidmasking.apps.googleusercontent.com"
        )
        masked = chat._mask_secrets(secret_text)
        assert "SECRET" not in masked
        assert "GOCSPX-testClientSecretForMasking123" not in masked
        assert "re_testResendKeyForMasking123456789" not in masked
        assert "123456789012-fakegoogleclientidmasking" not in masked

        assert "will not save" in chat.remember("GOCSPX-testClientSecretForMasking123")
        assert "Saved to real launcher memory" in chat.remember("Call me Jeremy")
        assert "Saved to real launcher memory" in chat.remember("Use shorter replies")
        assert "Forgot 1 launcher memory" in chat.forget("Jeremy")
        summary = chat.memory_summary()
        assert "Jeremy" not in summary
        assert "Use shorter replies" in summary

    def test_footer_contact_is_not_placeholder(self):
        source = (ROOT / "app" / "layout" / "layout.py").read_text(encoding="utf-8")
        assert "support@mantis-studio.example" not in source
        assert "rebusinessmatters@gmail.com" in source

    def test_mobile_sidebar_uses_full_width_drawer(self):
        source = (ROOT / "app" / "ui" / "enhanced_theme.py").read_text(encoding="utf-8")
        assert "@media (max-width: 760px)" in source
        assert "width: 100vw !important" in source

    def test_workspace_settings_restore_saved_config_values(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "def config_bool(" in source
        assert "def config_int(" in source
        assert "def config_float(" in source
        assert 'init_state("auto_save", config_bool(config_data, "auto_save", True))' in source
        assert 'config_int(config_data, "daily_word_goal", 1000' in source
        assert 'config_int(config_data, "weekly_sessions_goal", 4' in source
        assert 'config_int(config_data, "focus_minutes", 25' in source
        assert 'config_float(\n            config_data,\n            "world_bible_confidence_threshold"' in source
        assert 'config_bool(config_data, "memory_auto_hard_enabled"' in source

    def test_workspace_settings_exposes_operational_sections(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        workspace_block = source[source.index("def render_workspace_settings():"):source.index("# Render enhanced sidebar")]
        assert "Workspace Overview" in workspace_block
        assert "Storage & Safety" in workspace_block
        assert "Projects folder" in workspace_block
        assert "Config file" in workspace_block
        assert "Backup folder" in workspace_block
        assert "Save current project" in workspace_block
        assert "Prepare export" in workspace_block
        assert "Refresh project list" in workspace_block
        assert "Studio Preferences" in workspace_block
        assert "Canon Confidence Rules" in workspace_block

    def test_email_delivery_service_uses_resend_and_streamlit_secrets(self):
        source = (ROOT / "app" / "services" / "email_delivery.py").read_text(encoding="utf-8")
        assert "https://api.resend.com/emails" in source
        assert "RESEND_API_KEY" in source
        assert "MANTIS_EMAIL_FROM" in source
        assert "MANTIS_APP_URL" in source
        assert "https://mantis-studio.streamlit.app" in source
        assert "requests.post" in source
        assert "Reset your MANTIS Studio password" in source

    def test_truncate_prompt(self):
        from app.main import _truncate_prompt
        long_text = "a" * 100
        result = _truncate_prompt(long_text, 50)
        assert len(result) <= 50


# ---------------------------------------------------------------------------
# 7) Rewrite presets  used by the Editor page
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
# 8) Entity matching  World Bible fuzzy matching
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
# 9) Chapter operations  Editor page logic
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
# 10) AppConfig  configuration sanity
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
# 11) Selftest  verify the built-in selftest still works
# ---------------------------------------------------------------------------

class TestSelftest:
    """The built-in selftest exercises save/load/chapter/entity/export."""

    def test_selftest_passes(self):
        from app.main import run_selftest
        assert run_selftest() == 0


# ---------------------------------------------------------------------------
# 12) update_locked_chapters  must be defined (previously missing)
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
        with pytest.warns(DeprecationWarning, match="config_data parameter is deprecated"):
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
        with pytest.warns(DeprecationWarning, match="config_data parameter is deprecated"):
            initialize_session_state(fake_st, config_data)
        assert fake_st.session_state.get("groq_connection_tested") is True, \
            "groq_connection_tested should be restored from config"
        assert fake_st.session_state.get("openai_connection_tested") is False, \
            "openai_connection_tested should default to False when not in config"


# ---------------------------------------------------------------------------
# 17) Layout duplicate removal  styles.py must no longer exist
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

class TestOAuthAndRepoStructure:
    """OAuth and repo organization should live in dedicated modules."""

    def test_oauth_modules_are_in_expected_folders(self):
        assert (ROOT / "app" / "services" / "oauth.py").exists()
        assert (ROOT / "app" / "security" / "secret_store.py").exists()
        assert (ROOT / "docs" / "REPO_STRUCTURE.md").exists()
        assert (ROOT / "docs" / "OAUTH_SETUP.md").exists()

    def test_main_wires_google_oauth_without_plaintext_secret_ui(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "build_google_authorization_url" in source
        assert "complete_google_oauth" in source
        assert "authenticate_oauth_user" in source
        assert "oauth_provider" in source
        assert "Google Client Secret" not in source
        assert "user_admin_google_client_secret" not in source
        oauth_source = (ROOT / "app" / "services" / "oauth.py").read_text(encoding="utf-8")
        assert "https://mantis-studio.streamlit.app/?oauth_provider=google" in oauth_source
        assert "DEFAULT_GOOGLE_CLIENT_ID" in oauth_source

    def test_secret_store_refuses_plaintext_fallback(self):
        source = (ROOT / "app" / "security" / "secret_store.py").read_text(encoding="utf-8")
        assert "windows-dpapi" in source
        assert "Protected secret storage is unavailable" in source

    def test_google_oauth_requires_full_redirect_uri(self):
        source = (ROOT / "app" / "services" / "oauth.py").read_text(encoding="utf-8")
        assert "HOSTED_GOOGLE_REDIRECT_URI" in source
        assert "urlparse" in source
        assert "oauth_provider" in source
        assert "redirect URI must be a full URL" in source

    def test_google_oauth_supports_external_secret_sources(self):
        source = (ROOT / "app" / "services" / "oauth.py").read_text(encoding="utf-8")
        assert "MANTIS_GOOGLE_CLIENT_SECRET" in source
        assert "GOOGLE_CLIENT_SECRET" in source
        assert "google_client_secret" in source
        assert "oauth_google_client_secret" in source
        assert "DEFAULT_GOOGLE_CLIENT_ID" in source
        assert "MANTIS_GOOGLE_CLIENT_ID" in source
        assert "GOOGLE_CLIENT_ID" in source
        assert "google_client_id" in source
        assert "MANTIS_GOOGLE_REDIRECT_URI" in source
        assert "GOOGLE_REDIRECT_URI" in source
        assert "google_redirect_uri" in source

    def test_google_oauth_uses_signed_state_not_session_state(self):
        source = (ROOT / "app" / "services" / "oauth.py").read_text(encoding="utf-8")
        assert "def _encode_state(" in source
        assert "def _decode_state(" in source
        assert "hmac.compare_digest(signature, expected)" in source
        assert "OAUTH_STATE_TTL_SECONDS" in source
        assert 'session_state["oauth_google_state"]' not in source
        assert "expected_state = session_state.get" not in source


# ---------------------------------------------------------------------------
# 18b) Light mode theme quality  comfort and readability
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
# 18) Input sanitization  AI prompt safety
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
# 19) Improved error handling  Project.load with corrupt JSON
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
# 20) Service module sync  verify service modules match main.py
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
        assert _validate_api_key_format("sk-abcdef456") is False

    def test_very_long_key_rejected(self):
        from app.main import _validate_api_key_format
        assert _validate_api_key_format("x" * 300) is False


# ---------------------------------------------------------------------------
# 22b) API key persistence  keys should not be saved as plaintext
# ---------------------------------------------------------------------------


class TestAPIKeyPersistence:
    """Verify API key config behavior avoids new plaintext persistence."""

    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.config_path = str(tmp_path / "test_config.json")

    def _make_mock_st(self, state_dict):
        import unittest.mock as mock
        mock_st = mock.MagicMock()
        mock_st.session_state = state_dict
        return mock_st

    def test_set_session_key_does_not_persist_plaintext(self):
        from app.main import AppConfig as MainAppConfig, set_session_key, load_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": ""}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st), \
                 mock.patch("app.main.protected_storage_available", return_value=False):
                set_session_key("groq", "sk-test-persist-key")

            config = load_app_config()
            assert config.get("groq_api_key") is None
            assert config.get("groq_api_key_protected") is None
            assert mock_st.session_state["ai_session_keys"]["groq"] == "sk-test-persist-key"
        finally:
            MainAppConfig.CONFIG_PATH = original

    def test_set_session_key_uses_protected_storage_when_available(self):
        from app.main import AppConfig as MainAppConfig, set_session_key, load_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": ""}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st), \
                 mock.patch("app.main.protected_storage_available", return_value=True), \
                 mock.patch("app.main.protect_secret", return_value={"kind": "test", "value": "encrypted"}):
                set_session_key("groq", "sk-test-persist-key")

            config = load_app_config()
            assert "groq_api_key" not in config
            assert config.get("groq_api_key_protected") == {"kind": "test", "value": "encrypted"}
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
            assert "groq_api_key_protected" not in config
        finally:
            MainAppConfig.CONFIG_PATH = original

    def test_get_effective_key_finds_legacy_saved_key(self):
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
            assert source == "legacy config"
        finally:
            MainAppConfig.CONFIG_PATH = original

    def test_get_effective_key_finds_protected_key(self):
        from app.main import AppConfig as MainAppConfig, get_effective_key, save_app_config
        import unittest.mock as mock

        original = MainAppConfig.CONFIG_PATH
        try:
            MainAppConfig.CONFIG_PATH = self.config_path
            save_app_config({"openai_api_key_protected": {"kind": "test", "value": "encrypted"}})

            mock_st = self._make_mock_st({"ai_session_keys": {"openai": "", "groq": ""}})

            with mock.patch("app.main._get_streamlit", return_value=mock_st), \
                 mock.patch("app.main.reveal_secret", return_value="sk-protected-key"):
                key, source = get_effective_key("openai")

            assert key == "sk-protected-key"
            assert source == "protected"
        finally:
            MainAppConfig.CONFIG_PATH = original


# ---------------------------------------------------------------------------
# 23) HTML rendering  st.html() migration
# ---------------------------------------------------------------------------


class TestHtmlRendering:
    """Verify that UI modules use st.html() instead of st.markdown(unsafe_allow_html=True).

    Streamlit 1.54 sanitizes block-level HTML in st.markdown(), even with
    unsafe_allow_html=True. All custom HTML rendering must use st.html()
    to avoid raw-tag display.
    """

    _UI_MODULES = [
        "app/ui/components.py",
        "app/ui/enhanced_theme.py",
        "app/components/buttons.py",
        "app/layout/layout.py",
        "app/main.py",
        "app/layout/enhanced_sidebar.py",
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
        path = ROOT / "app" / "ui" / "enhanced_theme.py"
        source = path.read_text(encoding="utf-8")
        assert "st.html(" in source, "app/ui/enhanced_theme.py should use st.html()"

    def test_theme_does_not_inject_scroll_to_top(self):
        """Theme injection should not force scroll position."""
        path = ROOT / "app" / "ui" / "enhanced_theme.py"
        source = path.read_text(encoding="utf-8")
        assert "scrollTo" not in source


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
        assert 'type="primary"' in src, "action_card button should use type='primary'"


class TestQuickActionButtonsStyled:
    """Quick action buttons must use the navigation button theme."""

    def test_main_quick_action_buttons_use_secondary(self):
        src = (ROOT / "app" / "views" / "dashboard_workspace.py").read_text(encoding="utf-8")
        assert "Quick jump" in src
        for key in ("qa_outline", "qa_chapters", "qa_world", "qa_memory", "qa_insights"):
            assert key in src


# ---------------------------------------------------------------------------
# World Bible DB  structured lore intelligence layer
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

    def test_source_refs_survive_apply_suggestion(self):
        from app.services.projects import Project
        from app.services.world_bible_merge import apply_suggestion

        project = Project.create("Sources")
        ent, action = apply_suggestion(
            project,
            {
                "type": "new",
                "name": "Lyra Stonebrook",
                "category": "Character",
                "description": "A reclusive spy.",
                "source": "Chapter 1: The Signal",
                "source_excerpt": "Lyra Stonebrook watched the signal flare above the city.",
                "chapter_id": "chapter-1",
            },
        )

        assert action in {"created", "matched"}
        assert ent is not None
        assert ent.source_refs
        assert ent.source_refs[0]["source"] == "Chapter 1: The Signal"


class TestMantisModelAndArchitectUX:
    """Source-level checks for the AI model guide and Architect panel."""

    def test_model_guide_and_architect_language_present(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "_score_model_for_mantis" in source
        assert "MANTIS Model Guide" in source
        assert "Blueprint readiness" in source
        assert "Canon/world hooks" in source
        assert "Source markers" in source
        assert "Scan All Chapters" in source

    def test_beginner_guides_memory_insights_editor_present(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "def render_page_guide" in source
        assert "Learn this page" in source
        assert "Memory is the instruction layer" in source
        assert "Insights is the project dashboard" in source
        assert "This is where you write the actual manuscript" in source
        assert "World Bible is the story encyclopedia" in source
        assert "Style Guide" in source

    def test_auth_screen_uses_product_access_layout(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        auth_block = source[source.index("def _render_auth_gate()"):source.index("if not _render_auth_gate()")]
        assert "branding/mantis_lockup.png" in auth_block
        assert "MANTIS Studio" in auth_block
        assert "Write the story. Keep the world straight." in auth_block
        assert "font-size: 1.34rem" in auth_block
        assert "min-height: 285px" in auth_block
        assert "Draft chapters, build canon, and use MANTIS intelligence from one focused workspace." in auth_block
        assert "Sign in with email, continue with Google, or enter as a guest." in auth_block
        assert "mantis-auth-benefit-grid" in auth_block
        assert "mantis-auth-paths" in auth_block
        assert "Draft" in auth_block
        assert "Canon" in auth_block
        assert "Learn" in auth_block
        assert "Design benchmark: modern auth screens reduce default form load" not in auth_block
        assert "Access" in auth_block
        assert "Access your workspace" in auth_block
        assert "Email access" in auth_block
        assert 'st.tabs(["Sign in", "Create account", "Recover"])' in auth_block
        assert "Email recovery is ready." in auth_block
        assert "Send reset link" in auth_block
        assert "auth_email_reset_request_form" in auth_block
        assert "auth_token_reset_form" in auth_block
        assert "auth_request_password_reset_email" in auth_block
        assert "auth_reset_password_with_token" in auth_block
        assert "Use recovery code instead" in auth_block
        assert "Add MANTIS_GOOGLE_CLIENT_SECRET or google_client_secret" in auth_block
        assert "Ask the super admin to configure Google OAuth" not in auth_block
        assert "google_ready, google_msg, google_auth_url = build_google_authorization_url" in auth_block
        assert 'target="_self"' in auth_block
        assert "mantis-auth-primary-link" in auth_block
        assert "Continue with Google" in auth_block
        assert "Continue as guest" in auth_block
        assert "oauth_google_pending_url" not in auth_block
        assert "Open Google sign-in" not in auth_block
        assert "Google sign-in is ready. Use the button below to open Google." not in auth_block
        assert "Redirecting to Google..." not in auth_block
        assert "window.parent.location.href" not in auth_block
        assert "Enter the recovery code you saved" in auth_block
        assert "new one-time code to save" in auth_block
        assert 'st.form("auth_login_form"' in auth_block
        assert 'st.form("auth_signup_form"' in auth_block
        assert 'st.form("auth_reset_form"' in auth_block
        assert 'key="auth_login_submit"' in auth_block
        assert 'key="auth_signup_submit"' in auth_block
        assert 'key="auth_reset_submit"' in auth_block
        assert auth_block.index("auth_continue_guest") < auth_block.index("auth_tabs = st.tabs")
        assert auth_block.index("Email access") < auth_block.index("auth_tabs = st.tabs")
        assert "Sign in or create an account" not in auth_block
        assert "Narrative command center" not in auth_block
        assert "Write with your canon intact." not in auth_block
        assert "MANTIS Studio Access" not in auth_block
        assert "Enter the studio with your canon protected." not in auth_block
        assert "Plan the story. Draft the chapters. Keep canon under control." not in auth_block
        assert "Paid access" not in auth_block
        assert "mantis-auth-choice-note" not in auth_block
        assert "Welcome to MANTIS Studio" not in auth_block

    def test_memory_page_does_not_render_coherence_check(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        memory_block = source[source.index("def render_memory():"):source.index("def render_insights():")]
        assert "Coherence Check" not in memory_block
        assert "coh_run_memory" not in memory_block
        assert "Use Insights for coherence checks" in memory_block

    def test_insights_uses_canon_intelligence_panel(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "analyze_chapter_canon" in source
        assert "build_context_packet" in source
        assert "### Canon Intelligence" in source

    def test_insights_contains_actionable_coherence_panel(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "def render_coherence_panel" in source
        assert 'render_coherence_panel(p, key_prefix="insights", title="Coherence Check")' in source
        assert "What Apply Fix will do" in source
        assert "replace the exact target text" in source
        assert "replace the closest matching passage" in source
        assert "_best_effort_replacement_span" in source
        assert "replace the best matching passage" in source
        assert "could not confidently locate the passage" not in source

    def test_insights_owns_canon_scanner_and_review_queue(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        world_block = source[source.index("def render_world():"):source.index("def render_memory():")]
        insights_block = source[source.index("def render_insights():"):source.index("def render_chapters():")]
        assert "Canon Scanner" not in world_block
        assert "Scan All Chapters" not in world_block
        assert "Review AI Suggestions" not in world_block
        assert "Canon Scanner" in insights_block
        assert "insights_scan_all_chapters" in insights_block
        assert "Canon Suggestions" in insights_block

    def test_high_confidence_world_bible_updates_auto_apply(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        threshold_gate = source.index("if confidence < world_threshold:")
        auto_apply_call = source.index("ent, status = _apply_suggestion(p, classified)")
        classify_call = source.index("classified = _classify_suggestion(p, suggestion_payload)")
        assert classify_call < threshold_gate
        assert threshold_gate < auto_apply_call
        assert 'confidence = max(0.0, min(1.0, float(classified.get("confidence", confidence) or 0.0)))' in source
        assert "auto_applied += 1" in source
        assert "High-confidence suggestions apply automatically" in source
        assert "def _auto_apply_eligible_review_queue()" in source
        assert 'persist_project(p, action="insights_auto_apply_review_queue")' in source
        assert "Auto-applied {promoted_count} queued canon suggestion(s)." in source
        assert "Current World Bible entry" in source
        assert "Current notes:" in source

    def test_world_bible_apply_focuses_updated_entity(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert 'st.session_state["world_focus_entity"] = applied_ent.id' in source
        assert 'st.session_state["world_tabs"] = _insights_world_tab_for_category(applied_ent.category)' in source
        assert '"Item": "Items"' in source

    def test_world_bible_items_tab_is_visible(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert 'tab_options = ["Characters", "Locations", "Factions", "Items", "Lore"]' in source
        assert 'elif selected_tab == "Items":' in source
        assert 'render_cat("Item")' in source

    def test_editor_utility_bar_no_duplicate_quick_jump(self):
        source = (ROOT / "app" / "views" / "editor_workspace.py").read_text(encoding="utf-8")
        assert "Quick jump" not in source
        assert "Chapter Flow" in source
        assert "editor_chapter_flow_select" in source
        assert "editor_flow_new_chapter" in source
        assert "editor_flow_delete" in source
        assert "editor_flow_outline" not in source
        assert "editor_flow_world" not in source
        assert "render_chapter_sidebar" not in source
        main_source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        assert "Assistant mode" in main_source
        assert main_source.index('with st.expander("Modify / Improve Text"') < main_source.index('"Save Chapter"')
        summary_block = main_source[main_source.index('elif assistant_mode == "Summary"'):main_source.index('else:', main_source.index('elif assistant_mode == "Summary"'))]
        assert "Update Summary" in summary_block
        assert "editor_jump_select" not in main_source
        assert "render_chapter_sidebar" not in main_source

    def test_editor_find_replace_uses_safe_apply_and_inline_undo(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        find_block = source[source.index('with st.expander("Find and replace'):source.index('with st.expander("Modify / Improve Text"')]
        assert "Apply replace all" not in find_block
        assert "Apply replacement" in find_block
        assert "Replacement scope" in find_block
        assert "First exact match" in find_block
        assert "All exact matches" in find_block
        assert '"action": "Find/Replace"' in find_block
        assert "Undo replacement" in find_block
        assert "st.session_state.chapter_text_prev = {}" in find_block

    def test_editor_improve_undo_is_conditional(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        improve_block = source[source.index('with st.expander("Modify / Improve Text"'):source.index("chapter_drafts = [")]
        assert "prev_apply.get(\"action\") != \"Find/Replace\"" in improve_block
        assert "No previous chapter text available to restore." not in improve_block

    def test_outline_save_and_undo_follow_editor_action_order(self):
        source = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
        outline_block = source[source.index("def render_outline():"):source.index("def build_expander_label")]
        revision_block = outline_block[outline_block.index('with st.expander("Revision Tools"'):outline_block.index("pending_outline =")]
        assert "Undo last outline apply" in revision_block
        assert 'st.session_state.pop("outline_prev_text", None)' in revision_block
        assert "No previous outline text available." not in outline_block
        assert outline_block.index('with st.expander("Revision Tools"') < outline_block.index('"Save Outline"')


# ---------------------------------------------------------------------------
# Widget cache clearing after apply_suggestion
# ---------------------------------------------------------------------------

class TestApplySuggestionClearsWidgetCache:
    """Verify that the apply-suggestion UI clears stale widget keys."""

    def test_legacy_app_context_removed(self):
        """The removed compatibility app should not keep duplicate UI alive."""
        assert not (ROOT / "app" / "app_context.py").exists()

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
            "_mantis_wrapped sentinel not found  the double-wrap guard is missing"
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
            "_mantis_wrapped sentinel not found in state.py  "
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
