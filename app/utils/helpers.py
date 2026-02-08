"""Helper utilities for Mantis Studio."""
from __future__ import annotations

import datetime


def word_count(text: str | None) -> int:
    """Return the number of whitespace-delimited words in *text*."""
    return len((text or "").split())


def clamp(value: int | float, low: int | float, high: int | float) -> int | float:
    """Clamp *value* between *low* and *high* inclusive."""
    return max(low, min(value, high))


def current_year() -> int:
    """Return the current UTC year (avoids hard-coding)."""
    return datetime.datetime.now(datetime.timezone.utc).year
