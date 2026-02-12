"""Import smoke tests for Mantis Studio.

These tests verify that all critical modules can be imported without errors.
This catches:
- Syntax errors
- Missing dependencies
- Import cycles
- Module structure issues
"""
from __future__ import annotations

import importlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================================
# Critical Module Imports
# ============================================================================

class TestCriticalImports:
    """Verify that all modules the app needs can be imported without error."""

    @pytest.mark.smoke
    def test_import_main(self):
        """Test that app.main module imports successfully."""
        mod = importlib.import_module("app.main")
        assert hasattr(mod, "AppConfig")
        assert hasattr(mod, "Project")
        assert hasattr(mod, "run_selftest")

    @pytest.mark.smoke
    def test_import_difflib(self):
        """difflib is required for the editor diff view."""
        import difflib  # noqa: F401
        
        # Also verify it is imported in app.main
        mod = importlib.import_module("app.main")
        source = Path(mod.__file__).read_text(encoding="utf-8")
        assert "import difflib" in source

    @pytest.mark.smoke
    def test_import_auth_module(self):
        """app.utils.auth must exist and provide stub functions."""
        auth = importlib.import_module("app.utils.auth")
        assert callable(auth.get_current_user)
        assert callable(auth.is_authenticated)
        assert auth.is_authenticated() is False
        assert auth.get_current_user() is None

    @pytest.mark.smoke
    def test_import_navigation(self):
        """Test that navigation module imports and provides config."""
        nav = importlib.import_module("app.utils.navigation")
        labels, page_map = nav.get_nav_config(True)
        assert "Dashboard" in labels
        assert page_map.get("Dashboard") == "home"

    @pytest.mark.smoke
    def test_import_ui_components(self):
        """Test that UI components module has required helpers."""
        ui = importlib.import_module("app.components.ui")
        required = ("card", "section_header", "primary_button", "stat_tile", "action_card")
        missing = [name for name in required if not hasattr(ui, name)]
        assert not missing, f"Missing UI helpers: {', '.join(missing)}"

    @pytest.mark.smoke
    def test_import_keys(self):
        """Test that keys module provides key generation functions."""
        keys = importlib.import_module("app.utils.keys")
        assert callable(keys.ui_key)
        assert callable(keys.scoped_key)


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
            "app.views.chapters",
            "app.views.dashboard",
            "app.views.editor",
            "app.views.export",
            "app.views.home",
            "app.views.legal",
            "app.views.outline",
            "app.views.projects",
            "app.views.world",
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

class TestEditorButtonKeys:
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
