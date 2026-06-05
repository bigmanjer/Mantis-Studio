from __future__ import annotations

import importlib
import os
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


class TestImports:
    @pytest.mark.parametrize(
        "module_name",
        [
            "app.main",
            "app.router",
            "app.state",
            "app.utils.navigation",
            "app.utils.helpers",
            "app.layout.layout",
            "app.layout.enhanced_sidebar",
            "app.services.projects",
            "app.services.storage",
            "app.services.ai",
            "scripts.toolbox",
        ],
    )
    def test_module_imports(self, module_name: str):
        mod = importlib.import_module(module_name)
        assert mod is not None


class TestProjectLifecycle:
    @pytest.fixture(autouse=True)
    def _tmpdir(self, tmp_path):
        self.storage = str(tmp_path / "projects")
        os.makedirs(self.storage, exist_ok=True)

    def _make_project(self, title="Test", **kw):
        from app.main import Project
        return Project.create(title, storage_dir=self.storage, **kw)

    def test_create_save_load_delete(self):
        from app.main import Project

        p = self._make_project("My Story", author="Author", genre="Fantasy")
        p.outline = "Chapter 1: Start"
        p.add_chapter("Chapter 1", "Hello world")
        p.add_entity("Alice", "Character", "Lead")

        path = p.save()
        assert path and Path(path).exists()

        loaded = Project.load(path)
        assert loaded.title == "My Story"
        assert loaded.author == "Author"
        assert loaded.genre == "Fantasy"
        assert loaded.outline == "Chapter 1: Start"
        assert len(loaded.get_ordered_chapters()) == 1
        assert len(loaded.world_db) == 1

        ok, _msg = Project.delete_file(path)
        assert ok is True
        assert not Path(path).exists()

    def test_chapter_order_and_word_count(self):
        p = self._make_project("Order")
        p.add_chapter("One", "one two")
        p.add_chapter("Two", "three four five")
        ordered = p.get_ordered_chapters()
        assert [c.index for c in ordered] == [1, 2]
        assert p.get_total_word_count() == 5

    def test_delete_chapter_reindexes(self):
        p = self._make_project("Delete")
        c1 = p.add_chapter("One", "a")
        c2 = p.add_chapter("Two", "b")
        c3 = p.add_chapter("Three", "c")
        p.delete_chapter(c2.id)
        ordered = p.get_ordered_chapters()
        assert len(ordered) == 2
        assert [c.index for c in ordered] == [1, 2]
        assert ordered[0].title == c1.title
        assert ordered[1].title == c3.title

    def test_entity_upsert_merge(self):
        p = self._make_project("Entities")
        p.upsert_entity("Alice", "Character", "Brave", allow_merge=True)
        p.upsert_entity("Alice", "Character", "Leader", allow_merge=True)
        alices = [e for e in p.world_db.values() if e.name == "Alice"]
        assert len(alices) == 1


class TestNavigationConfig:
    def test_nav_config_contains_core_routes(self):
        from app.utils.navigation import get_nav_config

        labels, page_map = get_nav_config(True)
        assert "Dashboard" in labels
        assert "Projects" in labels
        assert page_map["Dashboard"] == "home"
        assert page_map["Projects"] == "projects"

    def test_routes_contains_core_pages(self):
        from app.router import get_routes

        routes = get_routes()
        for key in ["home", "projects", "outline", "chapters", "world", "ai", "legal"]:
            assert key in routes
            assert callable(routes[key])


class TestUtilities:
    def test_helper_functions(self):
        from app.utils.helpers import word_count, clamp, current_year

        assert word_count("one two three") == 3
        assert clamp(5, 1, 10) == 5
        assert clamp(-1, 1, 10) == 1
        assert isinstance(current_year(), int)

    def test_sanitize_chapter_title(self):
        from app.main import sanitize_chapter_title

        assert sanitize_chapter_title("  Hello World  ") == "Hello World"
        assert sanitize_chapter_title("**Bold**") == "Bold"


class TestToolbox:
    def test_bump_version(self):
        from scripts.toolbox import bump_version

        assert bump_version("1.0") == "1.1"
        assert bump_version("1.9") == "2.0"

    def test_health_command_callable(self):
        from scripts import toolbox

        assert callable(toolbox.cmd_health)
        assert callable(toolbox.cmd_smoke)
        assert callable(toolbox.cmd_test)
        assert callable(toolbox.cmd_qa)


class TestConfigRoundTrip:
    def test_load_save_app_config_roundtrip(self, tmp_path):
        from app.main import AppConfig, load_app_config, save_app_config

        cfg = tmp_path / "config.json"
        original = AppConfig.CONFIG_PATH
        try:
            AppConfig.CONFIG_PATH = str(cfg)
            save_app_config({"ui_theme": "Dark", "daily_word_goal": "1000"})
            loaded = load_app_config()
            assert loaded.get("ui_theme") == "Dark"
            assert loaded.get("daily_word_goal") == "1000"
        finally:
            AppConfig.CONFIG_PATH = original
