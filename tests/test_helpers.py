"""Unit tests for app/utils/helpers.py

Tests cover:
- word_count: Word counting utility
- clamp: Value clamping between bounds
- current_year: Current year retrieval
- ai_connection_warning: AI connection status helpers
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.helpers import word_count, clamp, current_year


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
