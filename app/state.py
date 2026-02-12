from __future__ import annotations

from contextlib import contextmanager
from collections.abc import Generator
from typing import Dict, List, Optional, Tuple

from app.config.settings import AppConfig


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
    st.session_state.setdefault("ai_keys", {})

    def _safe_int(value: object, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _resolve_api_key(provider: str, default_value: str) -> str:
        session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
        if session_key:
            return session_key
        config_key = config_data.get(f"{provider}_api_key", "")
        if config_key:
            return config_key
        return default_value or ""

    # ---- simple defaults (setdefault avoids overwriting) ----
    defaults: Dict[str, object] = {
        "ui_theme": config_data.get("ui_theme", "Dark"),
        "daily_word_goal": _safe_int(config_data.get("daily_word_goal"), 500),
        "weekly_sessions_goal": _safe_int(config_data.get("weekly_sessions_goal"), 4),
        "focus_minutes": _safe_int(config_data.get("focus_minutes"), 25),
        "projects_refresh_token": 0,
        "delete_project_path": None,
        "delete_project_title": None,
        "delete_entity_id": None,
        "delete_entity_name": None,
        "delete_chapter_id": None,
        "delete_chapter_title": None,
        "export_project_path": None,
        "world_search": "",
        "world_search_pending": None,
        "world_focus_entity": None,
        "world_focus_tab": None,
        "world_tabs": "Characters",
        "last_entity_scan": None,
        "_chapter_sync_id": None,
        "_chapter_sync_text": None,
        "curr_chap_id": None,
        "active_chapter_id": None,
        "chapters_project_id": None,
        "chapters": [],
        "out_txt_project_id": None,
        "_outline_sync": None,
        "user_id": None,
        "projects_dir": None,
        "project": None,
        "page": "home",
        "auto_save": True,
        "ghost_text": "",
        "pending_improvement_text": "",
        "first_run": True,
        "is_premium": True,
        "pending_action": None,
        "openai_base_url": config_data.get("openai_base_url", AppConfig.OPENAI_API_URL),
        "openai_model": config_data.get("openai_model", AppConfig.OPENAI_MODEL),
        "groq_base_url": config_data.get("groq_base_url", AppConfig.GROQ_API_URL),
        "groq_model": config_data.get("groq_model", AppConfig.DEFAULT_MODEL),
        "_force_nav": False,
        "editor_improve__copy_buffer": "",
    }
    for key, default in defaults.items():
        st.session_state.setdefault(key, default)

    # ---- mutable defaults (must not share references) ----
    st.session_state.setdefault("activity_log", list(config_data.get("activity_log", [])))
    st.session_state.setdefault("world_bible_review", [])
    st.session_state.setdefault("locked_chapters", set())
    st.session_state.setdefault("canon_health_log", [])
    st.session_state.setdefault("pending_improvement_meta", {})
    st.session_state.setdefault("chapter_text_prev", {})
    st.session_state.setdefault("chapter_drafts", [])
    st.session_state.setdefault("openai_model_list", [])
    st.session_state.setdefault("openai_model_tests", {})
    st.session_state.setdefault("groq_model_list", [])
    st.session_state.setdefault("groq_model_tests", {})
    st.session_state.setdefault("groq_connection_tested",
                                bool(config_data.get("groq_connection_tested")))
    st.session_state.setdefault("openai_connection_tested",
                                bool(config_data.get("openai_connection_tested")))

    # ---- Populate ai_session_keys from saved config so the warning check works ----
    if "ai_session_keys" not in st.session_state:
        st.session_state["ai_session_keys"] = {
            "groq": config_data.get("groq_api_key", ""),
            "openai": config_data.get("openai_api_key", ""),
        }

    # ---- World Bible structured database layer ----
    from app.services.world_bible_db import ensure_world_bible_db
    ensure_world_bible_db(st.session_state)

    # ---- always-overwritten keys (API keys refresh every run) ----
    st.session_state.openai_api_key = _resolve_api_key("openai", AppConfig.OPENAI_API_KEY)
    st.session_state.groq_api_key = _resolve_api_key("groq", AppConfig.GROQ_API_KEY)

    AppConfig.GROQ_API_URL = st.session_state.groq_base_url
    AppConfig.GROQ_API_KEY = _resolve_api_key("groq", AppConfig.GROQ_API_KEY)
    AppConfig.DEFAULT_MODEL = st.session_state.groq_model
    AppConfig.OPENAI_API_URL = st.session_state.openai_base_url
    AppConfig.OPENAI_API_KEY = _resolve_api_key("openai", AppConfig.OPENAI_API_KEY)
    AppConfig.OPENAI_MODEL = st.session_state.openai_model
