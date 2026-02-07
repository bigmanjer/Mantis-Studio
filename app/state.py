from __future__ import annotations

from contextlib import contextmanager
import uuid
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

        return _wrapped

    def _wrap_widget_no_label(widget_fn, widget_type: str):
        def _wrapped(*args, **kwargs):
            kwargs["key"] = _auto_key(widget_type, None, kwargs.get("key"))
            return widget_fn(*args, **kwargs)

        return _wrapped

    def _maybe_wrap(attr: str, widget_type: str, has_label: bool = True) -> None:
        widget = getattr(st, attr, None)
        if not widget:
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


def initialize_session_state(st, auth, config_data: Dict[str, str]) -> Dict[str, str]:
    user = auth.get_current_user()
    logged_in = auth.is_authenticated()
    is_guest = not logged_in
    st.session_state["guest_mode"] = is_guest
    if is_guest:
        st.session_state.setdefault("guest_session_id", uuid.uuid4().hex[:8])
    st.session_state.setdefault("ai_keys", {})

    def _resolve_api_key(provider: str, default_value: str) -> str:
        session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
        if session_key:
            return session_key
        if logged_in:
            config_key = config_data.get(f"{provider}_api_key", "")
            if config_key:
                return config_key
        return default_value or ""


    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = config_data.get("ui_theme", "Dark")
    if "daily_word_goal" not in st.session_state:
        st.session_state.daily_word_goal = int(config_data.get("daily_word_goal", 500))
    if "weekly_sessions_goal" not in st.session_state:
        st.session_state.weekly_sessions_goal = int(config_data.get("weekly_sessions_goal", 4))
    if "focus_minutes" not in st.session_state:
        st.session_state.focus_minutes = int(config_data.get("focus_minutes", 25))
    if "activity_log" not in st.session_state:
        st.session_state.activity_log = list(config_data.get("activity_log", []))
    if "projects_refresh_token" not in st.session_state:
        st.session_state.projects_refresh_token = 0
    if "delete_project_path" not in st.session_state:
        st.session_state.delete_project_path = None
    if "delete_project_title" not in st.session_state:
        st.session_state.delete_project_title = None
    if "delete_entity_id" not in st.session_state:
        st.session_state.delete_entity_id = None
    if "delete_entity_name" not in st.session_state:
        st.session_state.delete_entity_name = None
    if "export_project_path" not in st.session_state:
        st.session_state.export_project_path = None
    if "world_search" not in st.session_state:
        st.session_state.world_search = ""
    if "world_search_pending" not in st.session_state:
        st.session_state.world_search_pending = None
    if "world_focus_entity" not in st.session_state:
        st.session_state.world_focus_entity = None
    if "world_focus_tab" not in st.session_state:
        st.session_state.world_focus_tab = None
    if "world_tabs" not in st.session_state:
        st.session_state.world_tabs = "Characters"
    if "world_bible_review" not in st.session_state:
        st.session_state.world_bible_review = []
    if "last_entity_scan" not in st.session_state:
        st.session_state.last_entity_scan = None
    if "locked_chapters" not in st.session_state:
        st.session_state.locked_chapters = set()
    if "_chapter_sync_id" not in st.session_state:
        st.session_state._chapter_sync_id = None
    if "_chapter_sync_text" not in st.session_state:
        st.session_state._chapter_sync_text = None
    if "curr_chap_id" not in st.session_state:
        st.session_state.curr_chap_id = None
    if "out_txt_project_id" not in st.session_state:
        st.session_state.out_txt_project_id = None
    if "_outline_sync" not in st.session_state:
        st.session_state._outline_sync = None
    st.session_state.setdefault("canon_health_log", [])

    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "projects_dir" not in st.session_state:
        st.session_state.projects_dir = None
    if "project" not in st.session_state:
        st.session_state.project = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "auto_save" not in st.session_state:
        st.session_state.auto_save = not is_guest
    if "ghost_text" not in st.session_state:
        st.session_state.ghost_text = ""
    if "pending_improvement_text" not in st.session_state:
        st.session_state.pending_improvement_text = ""
    if "pending_improvement_meta" not in st.session_state:
        st.session_state.pending_improvement_meta = {}
    if "chapter_text_prev" not in st.session_state:
        st.session_state.chapter_text_prev = {}
    if "chapter_drafts" not in st.session_state:
        st.session_state.chapter_drafts = []
    if "editor_improve__copy_buffer" not in st.session_state:
        st.session_state.editor_improve__copy_buffer = ""
    if "first_run" not in st.session_state:
        st.session_state.first_run = True
    if "is_premium" not in st.session_state:
        st.session_state.is_premium = True
    if "guest_mode" not in st.session_state:
        st.session_state.guest_mode = is_guest
    if "pending_action" not in st.session_state:
        st.session_state.pending_action = None
    if "guest_project" not in st.session_state:
        st.session_state.guest_project = None
    if "openai_base_url" not in st.session_state:
        st.session_state.openai_base_url = config_data.get(
            "openai_base_url",
            AppConfig.OPENAI_API_URL,
        )
    st.session_state.openai_api_key = _resolve_api_key("openai", AppConfig.OPENAI_API_KEY)
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = config_data.get(
            "openai_model",
            AppConfig.OPENAI_MODEL,
        )
    if "openai_model_list" not in st.session_state:
        st.session_state.openai_model_list = []
    if "openai_model_tests" not in st.session_state:
        st.session_state.openai_model_tests = {}
    if "groq_base_url" not in st.session_state:
        st.session_state.groq_base_url = config_data.get("groq_base_url", AppConfig.GROQ_API_URL)
    st.session_state.groq_api_key = _resolve_api_key("groq", AppConfig.GROQ_API_KEY)
    if "groq_model" not in st.session_state:
        st.session_state.groq_model = config_data.get("groq_model", AppConfig.DEFAULT_MODEL)
    if "groq_model_list" not in st.session_state:
        st.session_state.groq_model_list = []
    if "groq_model_tests" not in st.session_state:
        st.session_state.groq_model_tests = {}
    if "_force_nav" not in st.session_state:
        st.session_state._force_nav = False

    AppConfig.GROQ_API_URL = st.session_state.groq_base_url
    AppConfig.GROQ_API_KEY = _resolve_api_key("groq", AppConfig.GROQ_API_KEY)
    AppConfig.DEFAULT_MODEL = st.session_state.groq_model
    AppConfig.OPENAI_API_URL = st.session_state.openai_base_url
    AppConfig.OPENAI_API_KEY = _resolve_api_key("openai", AppConfig.OPENAI_API_KEY)
    AppConfig.OPENAI_MODEL = st.session_state.openai_model

    return {
        "user": user,
        "logged_in": logged_in,
        "is_guest": is_guest,
    }
