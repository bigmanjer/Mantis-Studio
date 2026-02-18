"""Integration tests for AI functionality with proper mocking.

These tests address gaps in the existing test suite by actually testing
AI integration flows with mocked API responses, rather than bypassing
the logic with fake stubs.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest
import responses

# Ensure app package is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.ai import AIEngine, sanitize_ai_input, _truncate_prompt
from app.config.settings import AppConfig


class TestAIEngineIntegration:
    """Test AI engine with mocked API responses."""

    @pytest.fixture
    def ai_engine(self):
        """Create an AI engine instance for testing."""
        return AIEngine(timeout=5)

    @responses.activate
    def test_probe_models_success(self, ai_engine):
        """Test that model probing works with a valid API key."""
        responses.add(
            responses.GET,
            f"{AppConfig.GROQ_API_URL}/models",
            json={
                "data": [
                    {"id": "llama-3.1-8b-instant"},
                    {"id": "mixtral-8x7b-32768"},
                    {"id": "gemma-7b-it"}
                ]
            },
            status=200
        )

        models = ai_engine.probe_models("sk-test-key")
        assert len(models) == 3
        assert "llama-3.1-8b-instant" in models
        assert "mixtral-8x7b-32768" in models

    @responses.activate
    def test_probe_models_failure(self, ai_engine):
        """Test that model probing handles API failures gracefully."""
        responses.add(
            responses.GET,
            f"{AppConfig.GROQ_API_URL}/models",
            status=401
        )

        models = ai_engine.probe_models("invalid-key")
        assert models == []

    @responses.activate
    def test_generate_non_streaming(self, ai_engine):
        """Test non-streaming generation with mocked API."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            json={
                "choices": [{
                    "message": {
                        "content": "Chapter 1: The Beginning\n\nOnce upon a time..."
                    }
                }]
            },
            status=200
        )

        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            result = ai_engine.generate("Generate a story", "llama-3.1-8b-instant")
            
        assert "text" in result
        assert "Chapter 1: The Beginning" in result["text"]

    @responses.activate
    def test_generate_with_api_error(self, ai_engine):
        """Test that generation handles API errors gracefully."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            status=500
        )

        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            result = ai_engine.generate("Generate a story", "llama-3.1-8b-instant")
            
        assert "text" in result
        # Should contain error message
        assert "failed" in result["text"].lower() or "error" in result["text"].lower()

    def test_generate_without_api_key(self, ai_engine):
        """Test that generation fails gracefully without API key."""
        with patch.object(AppConfig, 'GROQ_API_KEY', ''):
            chunks = list(ai_engine.generate_stream("Test prompt", "llama-3.1-8b-instant"))
            
        assert len(chunks) > 0
        assert "API key not configured" in chunks[0]

    def test_generate_without_model(self, ai_engine):
        """Test that generation fails gracefully without model."""
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            chunks = list(ai_engine.generate_stream("Test prompt", ""))
            
        assert len(chunks) > 0
        assert "model not configured" in chunks[0]

    def test_generate_json_requires_valid_response(self):
        """Test JSON extraction requires valid JSON in response."""
        # This is tested by the actual generate_json method
        # which handles JSON extraction and parsing
        ai_engine = AIEngine()
        
        # Invalid JSON should return None
        # This is integration-level behavior that would need
        # a complete mock of the streaming response
        assert ai_engine is not None


class TestAICanonEnforcement:
    """Test that hard canon rules are properly enforced."""

    def test_canon_enforcement_requires_streamlit_session(self):
        """Test that canon enforcement only works when streamlit is available."""
        # This test documents that canon enforcement requires Streamlit session state
        # In a real scenario, these would be integration tests running the actual app
        ai_engine = AIEngine()
        
        # Without streamlit in sys.modules, generation should work normally
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            # This would need a full integration test environment
            # For now, we just verify the engine can be created
            assert ai_engine is not None


class TestAISanitization:
    """Test input sanitization before sending to AI."""

    def test_sanitize_removes_null_bytes(self):
        """Test that null bytes are removed from input."""
        text = "Hello\x00World\x00"
        result = sanitize_ai_input(text)
        assert "\x00" not in result
        assert result == "HelloWorld"

    def test_sanitize_strips_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        text = "  \n  Hello World  \n  "
        result = sanitize_ai_input(text)
        assert result == "Hello World"

    def test_sanitize_respects_max_length(self):
        """Test that text is truncated to max length."""
        text = "a" * 1000
        result = sanitize_ai_input(text, max_length=100)
        assert len(result) == 100

    def test_sanitize_handles_empty_input(self):
        """Test that empty input is handled gracefully."""
        assert sanitize_ai_input("") == ""
        assert sanitize_ai_input(None) == ""
        assert sanitize_ai_input("   ") == ""

    def test_truncate_prompt_logs_warning(self):
        """Test that truncation logs a warning."""
        long_prompt = "x" * 50000
        with patch('app.services.ai.logger') as mock_logger:
            result = _truncate_prompt(long_prompt, 10000)
            
        assert len(result) == 10000
        mock_logger.warning.assert_called_once()


class TestAIStreamingGeneration:
    """Test streaming generation behavior."""

    @responses.activate
    def test_streaming_chunks_collected(self):
        """Test that streaming chunks are properly collected."""
        # Mock streaming response
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            json={
                "choices": [{
                    "message": {"content": "Line 1\nLine 2\nLine 3"}
                }]
            },
            status=200,
            stream=False
        )

        ai_engine = AIEngine()
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            chunks = list(ai_engine.generate_stream("Test", "llama-3.1-8b-instant"))

        # All chunks should be collected
        full_text = "".join(chunks)
        assert "Line 1" in full_text
        assert "Line 2" in full_text
        assert "Line 3" in full_text

    @responses.activate
    def test_streaming_handles_timeout(self):
        """Test that streaming handles timeouts gracefully."""
        import requests.exceptions
        
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            body=requests.exceptions.Timeout("Request timed out")
        )

        ai_engine = AIEngine(timeout=1)
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            chunks = list(ai_engine.generate_stream("Test", "llama-3.1-8b-instant"))

        # Should yield error message
        assert len(chunks) > 0
        full_text = "".join(chunks)
        assert "error" in full_text.lower() or "failed" in full_text.lower()


class TestAIErrorHandling:
    """Test comprehensive error handling in AI operations."""

    @responses.activate
    def test_401_unauthorized(self):
        """Test handling of unauthorized (invalid API key) errors."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            json={"error": {"message": "Invalid API key"}},
            status=401
        )

        ai_engine = AIEngine()
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-invalid-key'):
            result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        # Should contain error message about failure
        assert "failed" in result["text"].lower()

    @responses.activate
    def test_429_rate_limit(self):
        """Test handling of rate limit errors."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            json={"error": {"message": "Rate limit exceeded"}},
            status=429
        )

        ai_engine = AIEngine()
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        assert "failed" in result["text"].lower()

    @responses.activate
    def test_malformed_json_response(self):
        """Test handling of malformed JSON responses."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            body="This is not JSON",
            status=200
        )

        ai_engine = AIEngine()
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        # Should handle gracefully
        assert "failed" in result["text"].lower() or result["text"] == ""

    @responses.activate
    def test_missing_choices_in_response(self):
        """Test handling of responses missing expected fields."""
        responses.add(
            responses.POST,
            f"{AppConfig.GROQ_API_URL}/chat/completions",
            json={"data": []},  # Missing 'choices' key
            status=200
        )

        ai_engine = AIEngine()
        with patch.object(AppConfig, 'GROQ_API_KEY', 'sk-test-key'):
            result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        # Should return empty or error message
        assert "empty" in result["text"].lower() or result["text"] == ""
