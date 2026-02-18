from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator
from typing import Dict, List, Optional, Tuple

from app.config.settings import AppConfig


def _safe_int(value: object, default: int) -> int:
    """Parse *value* as an integer, returning *default* on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float) -> float:
    """Parse *value* as a float, returning *default* on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ui_key(name: str) -> str:
    """Stable widget key helper (returns the same key string)."""
    return name


def install_key_helpers(st) -> Tuple[contextmanager, Dict[Tuple[str, str, str], int]]:
    widget_counters: Dict[Tuple[str, str, str], int] = {}
    key_prefix_stack: List[str] = []

    def _current_prefix() -> str:
        return "__".join(key_prefix_stack) or "global"

    def _slugify(value: str) -> str:
        import re

        slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
        return slug[:40] or "widget"

    def _auto_key(widget_type: str, label: Optional[str], key: Optional[str]) -> str:
        if key:
            return key
        prefix = _current_prefix()
        slug = _slugify(label or widget_type)
        counter_key = (prefix, widget_type, slug)
        widget_counters[counter_key] = widget_counters.get(counter_key, 0) + 1
        index = widget_counters[counter_key]
        return f"{prefix}__{slug}__{index}"

    @contextmanager
    def key_scope(prefix: str) -> Generator[None, None, None]:
        key_prefix_stack.append(prefix)
        try:
            yield
        finally:
            key_prefix_stack.pop()

    def _wrap_widget(widget_fn, widget_type: str):
        def _wrapped(label=None, *args, **kwargs):
            kwargs["key"] = _auto_key(widget_type, label, kwargs.get("key"))
            return widget_fn(label, *args, **kwargs)

        _wrapped._mantis_wrapped = True
        return _wrapped

    def _wrap_widget_no_label(widget_fn, widget_type: str):
        def _wrapped(*args, **kwargs):
            kwargs["key"] = _auto_key(widget_type, None, kwargs.get("key"))
            return widget_fn(*args, **kwargs)

        _wrapped._mantis_wrapped = True
        return _wrapped

    def _maybe_wrap(attr: str, widget_type: str, has_label: bool = True) -> None:
        widget = getattr(st, attr, None)
        if not widget:
            return
        # Skip if already wrapped to avoid stacking wrappers on repeated
        # Streamlit reruns, which would eventually cause a RecursionError.
        if getattr(widget, "_mantis_wrapped", False):
            return
        if has_label:
            setattr(st, attr, _wrap_widget(widget, widget_type))
        else:
            setattr(st, attr, _wrap_widget_no_label(widget, widget_type))

    _maybe_wrap("text_input", "text_input")
    _maybe_wrap("text_area", "text_area")
    _maybe_wrap("number_input", "number_input")
    _maybe_wrap("selectbox", "selectbox")
    _maybe_wrap("multiselect", "multiselect")
    _maybe_wrap("slider", "slider")
    _maybe_wrap("radio", "radio")
    _maybe_wrap("checkbox", "checkbox")
    _maybe_wrap("button", "button")
    _maybe_wrap("file_uploader", "file_uploader")
    _maybe_wrap("download_button", "download_button")
    _maybe_wrap("expander", "expander")
    _maybe_wrap("form", "form")
    _maybe_wrap("form_submit_button", "form_submit_button")
    _maybe_wrap("toggle", "toggle")
    _maybe_wrap("feedback", "feedback")
    _maybe_wrap("date_input", "date_input")
    _maybe_wrap("time_input", "time_input")
    _maybe_wrap("color_picker", "color_picker")
    _maybe_wrap("camera_input", "camera_input")
    _maybe_wrap("audio_input", "audio_input")
    _maybe_wrap("chat_input", "chat_input", has_label=False)

    return key_scope, widget_counters


def initialize_session_state(st, config_data: Dict[str, str]) -> None:
    """Legacy wrapper - now delegates to app.session_init module.
    
    This function is maintained for backward compatibility with existing imports.
    New code should import from app.session_init directly.
    """
    from app.session_init import initialize_session_state as init_session
    init_session(st)
