"""Centralized session state initialization for Mantis Studio.

This module provides defensive initialization of all session state variables
to prevent unexpected resets and ensure consistent state across reruns.
"""
from __future__ import annotations

from typing import Any, Dict

from app.config.settings import AppConfig, load_app_config, logger


def _safe_int(value: object, default: int) -> int:
    """Parse value as an integer, returning default on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: object, default: float) -> float:
    """Parse value as a float, returning default on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolve_api_key(st, provider: str, config_data: Dict[str, str], default_value: str) -> str:
    """Resolve API key from session state, config, or default."""
    session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
    if session_key:
        return session_key
    config_key = config_data.get(f"{provider}_api_key", "")
    if config_key:
        return config_key
    return default_value or ""


def initialize_session_state(st) -> None:
    """Initialize all session state variables with defensive defaults.
    
    This function is idempotent - it only sets values that don't already exist.
    Safe to call on every rerun.
    
    NOTE: This is the new signature. The legacy version in app/state.py accepted
    a config_data parameter which is now loaded internally. If migrating from
    legacy code, simply remove the config_data argument:
    
    Before: initialize_session_state(st, config_data)
    After:  initialize_session_state(st)
    
    Args:
        st: The streamlit module instance
    """
    try:
        # Load config with error handling
        try:
            config_data = load_app_config()
            logger.info(f"Config loaded successfully: {len(config_data)} keys")
        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            config_data = {}
            # Non-blocking warning - app continues with defaults
            try:
                st.warning("⚠️ Configuration file not accessible. Using defaults.")
            except Exception:
                pass  # Ignore if st.warning fails
        
        # Core navigation and state
        st.session_state.setdefault("page", "home")
        st.session_state.setdefault("user_id", None)
        st.session_state.setdefault("projects_dir", None)
        st.session_state.setdefault("project", None)
        st.session_state.setdefault("first_run", True)
        st.session_state.setdefault("initialized", True)
        
        # UI preferences
        st.session_state.setdefault("ui_theme", config_data.get("ui_theme", "Dark"))
        st.session_state.setdefault("auto_save", True)
        st.session_state.setdefault("is_premium", True)
        
        # Goals and tracking
        st.session_state.setdefault("daily_word_goal", _safe_int(config_data.get("daily_word_goal"), 500))
        st.session_state.setdefault("weekly_sessions_goal", _safe_int(config_data.get("weekly_sessions_goal"), 4))
        st.session_state.setdefault("focus_minutes", _safe_int(config_data.get("focus_minutes"), 25))
        
        # Activity tracking (mutable defaults - create new instances)
        st.session_state.setdefault("activity_log", list(config_data.get("activity_log", [])))
        st.session_state.setdefault("canon_health_log", [])
        
        # Project management
        st.session_state.setdefault("projects_refresh_token", 0)
        st.session_state.setdefault("delete_project_path", None)
        st.session_state.setdefault("delete_project_title", None)
        
        # Chapter management
        st.session_state.setdefault("chapters", [])
        st.session_state.setdefault("chapters_project_id", None)
        st.session_state.setdefault("active_chapter_id", None)
        st.session_state.setdefault("curr_chap_id", None)
        st.session_state.setdefault("delete_chapter_id", None)
        st.session_state.setdefault("delete_chapter_title", None)
        st.session_state.setdefault("locked_chapters", set())
        st.session_state.setdefault("chapter_text_prev", {})
        st.session_state.setdefault("chapter_drafts", [])
        st.session_state.setdefault("_chapter_sync_id", None)
        st.session_state.setdefault("_chapter_sync_text", None)
        
        # Editor state
        st.session_state.setdefault("ghost_text", "")
        st.session_state.setdefault("pending_improvement_text", "")
        st.session_state.setdefault("pending_improvement_meta", {})
        st.session_state.setdefault("editor_improve__copy_buffer", "")
        
        # Outline management
        st.session_state.setdefault("out_txt_project_id", None)
        st.session_state.setdefault("_outline_sync", None)
        
        # World Bible / Entity management
        st.session_state.setdefault("world_search", "")
        st.session_state.setdefault("world_search_pending", None)
        st.session_state.setdefault("world_focus_entity", None)
        st.session_state.setdefault("world_focus_tab", None)
        st.session_state.setdefault("world_tabs", "Characters")
        st.session_state.setdefault("world_bible_review", [])
        st.session_state.setdefault("last_entity_scan", None)
        st.session_state.setdefault("delete_entity_id", None)
        st.session_state.setdefault("delete_entity_name", None)
        
        # World Bible structured database layer
        try:
            from app.services.world_bible_db import ensure_world_bible_db
            ensure_world_bible_db(st.session_state)
        except Exception as e:
            logger.warning(f"Failed to initialize world bible DB: {e}", exc_info=True)
        
        # Export management
        st.session_state.setdefault("export_project_path", None)
        
        # Navigation and actions
        st.session_state.setdefault("pending_action", None)
        st.session_state.setdefault("_force_nav", False)
        st.session_state.setdefault("last_action", "")
        st.session_state.setdefault("last_action_ts", None)
        
        # Error tracking
        st.session_state.setdefault("last_exception", "")
        
        # Debug mode
        st.session_state.setdefault("debug", False)
        
        # Widget updates queue
        st.session_state.setdefault("_pending_widget_updates", {})
        
        # AI configuration
        st.session_state.setdefault("ai_keys", {})
        st.session_state.setdefault("ai_provider", config_data.get("ai_provider", "groq"))
        
        # AI session keys - populate from config
        if "ai_session_keys" not in st.session_state:
            st.session_state["ai_session_keys"] = {
                "groq": config_data.get("groq_api_key", ""),
                "openai": config_data.get("openai_api_key", ""),
            }
        
        # OpenAI configuration
        st.session_state.setdefault("openai_base_url", config_data.get("openai_base_url", AppConfig.OPENAI_API_URL))
        st.session_state.setdefault("openai_model", config_data.get("openai_model", AppConfig.OPENAI_MODEL))
        st.session_state.setdefault("openai_key_input", "")
        st.session_state.setdefault("openai_model_list", [])
        st.session_state.setdefault("openai_model_tests", {})
        st.session_state.setdefault("openai_connection_tested", bool(config_data.get("openai_connection_tested")))
        
        # Groq configuration
        st.session_state.setdefault("groq_base_url", config_data.get("groq_base_url", AppConfig.GROQ_API_URL))
        st.session_state.setdefault("groq_model", config_data.get("groq_model", AppConfig.DEFAULT_MODEL))
        st.session_state.setdefault("groq_key_input", "")
        st.session_state.setdefault("groq_model_list", [])
        st.session_state.setdefault("groq_model_tests", {})
        st.session_state.setdefault("groq_connection_tested", bool(config_data.get("groq_connection_tested")))
        
        # Resolve and set API keys (always refresh on each run)
        st.session_state.openai_api_key = _resolve_api_key(st, "openai", config_data, AppConfig.OPENAI_API_KEY)
        st.session_state.groq_api_key = _resolve_api_key(st, "groq", config_data, AppConfig.GROQ_API_KEY)
        
        # Update AppConfig with session values
        AppConfig.GROQ_API_URL = st.session_state.groq_base_url
        AppConfig.GROQ_API_KEY = st.session_state.groq_api_key
        AppConfig.DEFAULT_MODEL = st.session_state.groq_model
        AppConfig.OPENAI_API_URL = st.session_state.openai_base_url
        AppConfig.OPENAI_API_KEY = st.session_state.openai_api_key
        AppConfig.OPENAI_MODEL = st.session_state.openai_model
        
        logger.info("Session state initialized successfully")
        
    except Exception as e:
        logger.error(f"Critical error in session state initialization: {e}", exc_info=True)
        # Set absolute minimum state to prevent total failure
        st.session_state.setdefault("page", "home")
        st.session_state.setdefault("initialized", True)
        st.session_state.setdefault("last_exception", str(e))
        try:
            st.error("⚠️ Failed to initialize application state. Some features may not work correctly.")
        except Exception:
            pass  # If even st.error fails, just continue


def apply_pending_widget_updates(st) -> None:
    """Apply any queued widget updates from the previous cycle."""
    try:
        pending = st.session_state.pop("_pending_widget_updates", None)
        if pending:
            for key, value in pending.items():
                st.session_state[key] = value
    except Exception as e:
        logger.warning(f"Failed to apply pending widget updates: {e}")


def queue_widget_update(st, key: str, value: Any) -> None:
    """Queue a widget update to be applied on next cycle."""
    try:
        pending = st.session_state.setdefault("_pending_widget_updates", {})
        pending[key] = value
    except Exception as e:
        logger.warning(f"Failed to queue widget update for {key}: {e}")
