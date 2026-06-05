"""Integration tests for AI functionality using stdlib mocks only.

These tests avoid third-party network mocking dependencies so the suite can run in
restricted CI/offline environments.
"""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Ensure app package is importable
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import AppConfig
from app.services.ai import AIEngine, _truncate_prompt, sanitize_ai_input


class MockHTTPResponse:
    """Tiny response object compatible with AIEngine's usage."""

    def __init__(self, *, status_code: int = 200, json_data=None, text: str = "", iter_lines_data=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self._iter_lines_data = iter_lines_data or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data

    def iter_lines(self):
        return iter(self._iter_lines_data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class TestAIEngineIntegration:
    @pytest.fixture
    def ai_engine(self):
        return AIEngine(timeout=5)

    def test_probe_models_success(self, ai_engine):
        with patch.object(
            ai_engine.session,
            "get",
            return_value=MockHTTPResponse(
                json_data={
                    "data": [
                        {"id": "llama-3.1-8b-instant"},
                        {"id": "mixtral-8x7b-32768"},
                        {"id": "gemma-7b-it"},
                    ]
                }
            ),
        ):
            models = ai_engine.probe_models("sk-test-key")

        assert len(models) == 3
        assert "llama-3.1-8b-instant" in models
        assert "mixtral-8x7b-32768" in models

    def test_probe_models_failure(self, ai_engine):
        with patch.object(ai_engine.session, "get", side_effect=requests.HTTPError("401")):
            models = ai_engine.probe_models("invalid-key")
        assert models == []

    def test_generate_non_streaming(self, ai_engine):
        stream_resp = MockHTTPResponse(iter_lines_data=[])
        nonstream_resp = MockHTTPResponse(
            json_data={
                "choices": [{"message": {"content": "Chapter 1: The Beginning\n\nOnce upon a time..."}}]
            }
        )
        with patch.object(ai_engine.session, "post", side_effect=[stream_resp, nonstream_resp]):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                result = ai_engine.generate("Generate a story", "llama-3.1-8b-instant")

        assert "text" in result
        assert "Chapter 1: The Beginning" in result["text"]

    def test_generate_with_api_error(self, ai_engine):
        with patch.object(ai_engine.session, "post", side_effect=requests.HTTPError("500")):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                result = ai_engine.generate("Generate a story", "llama-3.1-8b-instant")

        assert "text" in result
        assert "failed" in result["text"].lower() or "error" in result["text"].lower()

    def test_generate_without_api_key(self, ai_engine):
        with patch.object(AppConfig, "GROQ_API_KEY", ""):
            chunks = list(ai_engine.generate_stream("Test prompt", "llama-3.1-8b-instant"))

        assert len(chunks) > 0
        assert "API key not configured" in chunks[0]

    def test_generate_without_model(self, ai_engine):
        with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
            chunks = list(ai_engine.generate_stream("Test prompt", ""))

        assert len(chunks) > 0
        assert "model not configured" in chunks[0]


class TestAISanitization:
    def test_sanitize_removes_null_bytes(self):
        assert sanitize_ai_input("Hello\x00World\x00") == "HelloWorld"

    def test_sanitize_strips_whitespace(self):
        assert sanitize_ai_input("  \n  Hello World  \n  ") == "Hello World"

    def test_sanitize_respects_max_length(self):
        assert len(sanitize_ai_input("a" * 1000, max_length=100)) == 100

    def test_sanitize_handles_empty_input(self):
        assert sanitize_ai_input("") == ""
        assert sanitize_ai_input(None) == ""
        assert sanitize_ai_input("   ") == ""

    def test_truncate_prompt_logs_warning(self):
        with patch("app.services.ai.logger") as mock_logger:
            result = _truncate_prompt("x" * 50000, 10000)

        assert len(result) == 10000
        mock_logger.warning.assert_called_once()


class TestAIStreamingGeneration:
    def test_streaming_chunks_collected(self):
        stream_lines = [
            b'data: {"choices":[{"delta":{"content":"Line 1\\n"}}]}',
            b'data: {"choices":[{"delta":{"content":"Line 2\\n"}}]}',
            b'data: {"choices":[{"delta":{"content":"Line 3"}}]}',
            b"data: [DONE]",
        ]
        stream_resp = MockHTTPResponse(iter_lines_data=stream_lines)

        ai_engine = AIEngine()
        with patch.object(ai_engine.session, "post", return_value=stream_resp):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                chunks = list(ai_engine.generate_stream("Test", "llama-3.1-8b-instant"))

        full_text = "".join(chunks)
        assert "Line 1" in full_text
        assert "Line 2" in full_text
        assert "Line 3" in full_text

    def test_streaming_handles_timeout(self):
        ai_engine = AIEngine(timeout=1)
        with patch.object(ai_engine.session, "post", side_effect=requests.exceptions.Timeout("timeout")):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                chunks = list(ai_engine.generate_stream("Test", "llama-3.1-8b-instant"))

        full_text = "".join(chunks)
        assert "error" in full_text.lower() or "failed" in full_text.lower()


class TestAIErrorHandling:
    @pytest.mark.parametrize("status_code", [401, 429])
    def test_http_errors(self, status_code):
        ai_engine = AIEngine()
        with patch.object(ai_engine.session, "post", return_value=MockHTTPResponse(status_code=status_code)):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        assert "failed" in result["text"].lower()

    def test_malformed_json_response(self):
        ai_engine = AIEngine()
        stream_resp = MockHTTPResponse(iter_lines_data=[])
        malformed_json_resp = MockHTTPResponse(json_data=json.JSONDecodeError("msg", "doc", 1))

        with patch.object(ai_engine.session, "post", side_effect=[stream_resp, malformed_json_resp]):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        assert "failed" in result["text"].lower() or result["text"] == ""

    def test_missing_choices_in_response(self):
        ai_engine = AIEngine()
        stream_resp = MockHTTPResponse(iter_lines_data=[])
        missing_choices_resp = MockHTTPResponse(json_data={"data": []})

        with patch.object(ai_engine.session, "post", side_effect=[stream_resp, missing_choices_resp]):
            with patch.object(AppConfig, "GROQ_API_KEY", "sk-test-key"):
                result = ai_engine.generate("Test", "llama-3.1-8b-instant")

        assert "text" in result
        assert "empty" in result["text"].lower() or result["text"] == ""
