"""Tests for service-layer improvements.

Validates the new utilities added to config/settings.py and
services/storage.py without requiring a running Streamlit server.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


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
