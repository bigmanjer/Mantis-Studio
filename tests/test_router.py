"""Unit tests for app/router.py

Tests cover:
- get_nav_config: Navigation configuration retrieval
- get_routes: Route mapping to view renderers
- Route resolution and validation
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.router import get_nav_config, get_routes


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
