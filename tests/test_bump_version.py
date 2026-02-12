"""Unit tests for scripts/bump_version.py

Tests cover:
- Normal minor increments (e.g., 85.4 -> 85.5)
- Minor rollover at 10 (e.g., 85.9 -> 86.0)
- Edge cases around zero and large numbers
- Invalid version format handling
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.bump_version import bump_version


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
