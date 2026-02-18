"""UI Context and utilities for Mantis Studio views.

This module provides shared utilities and helpers that all views need,
extracted from the main _run_ui() function to enable modular view development.
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple

from app.config.settings import AppConfig

logger = logging.getLogger("MANTIS")


class UIContext:
    """Shared context for all view rendering functions.
    
    Provides access to Streamlit instance, assets, utilities, and helpers
    without requiring views to have complex closure dependencies.
    """
    
    def __init__(self, st):
        """Initialize UI context with Streamlit instance.
        
        Args:
            st: Streamlit module instance
            
        Instance Attributes:
            st: Streamlit module reference
            widget_counters: Track auto-generated widget keys by type
            key_prefix_stack: Stack of key scopes for namespacing
            assets_dir: Path to assets directory
        """
        self.st = st
        self.widget_counters: Dict[Tuple[str, str, str], int] = {}
        self.key_prefix_stack: List[str] = []
        self.assets_dir = Path(__file__).resolve().parents[1] / "assets"
        
    def init_state(self, key: str, default: Any) -> None:
        """Initialize session state key if it doesn't exist."""
        if key not in self.st.session_state:
            self.st.session_state[key] = default
    
    def queue_widget_update(self, key: str, value: Any) -> None:
        """Queue a widget value update for next cycle."""
        pending = self.st.session_state.setdefault("_pending_widget_updates", {})
        pending[key] = value
    
    def apply_pending_widget_updates(self) -> None:
        """Apply all queued widget updates."""
        pending = self.st.session_state.pop("_pending_widget_updates", None)
        if pending:
            for k, v in pending.items():
                self.st.session_state[k] = v
    
    @contextmanager
    def key_scope(self, prefix: str) -> Generator[None, None, None]:
        """Context manager for scoping widget keys to prevent collisions."""
        self.key_prefix_stack.append(prefix)
        try:
            yield
        finally:
            self.key_prefix_stack.pop()
    
    def _current_prefix(self) -> str:
        """Get current key prefix from stack."""
        return "__".join(self.key_prefix_stack) or "global"
    
    def _slugify(self, value: str) -> str:
        """Convert string to slug for widget key."""
        import re
        slug = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
        return slug[:40] or "widget"
    
    def auto_key(self, widget_type: str, label: Optional[str], key: Optional[str]) -> str:
        """Generate unique widget key automatically."""
        if key:
            return key
        prefix = self._current_prefix()
        slug = self._slugify(label or widget_type)
        counter_key = (prefix, widget_type, slug)
        self.widget_counters[counter_key] = self.widget_counters.get(counter_key, 0) + 1
        index = self.widget_counters[counter_key]
        return f"{prefix}__{widget_type}__{slug}__{index}"
    
    def record_action(self, action_label: Optional[str], action_key: Optional[str]) -> None:
        """Record user action with timestamp."""
        label = (action_label or action_key or "action").strip()
        self.st.session_state["last_action"] = label
        self.st.session_state["last_action_ts"] = time.time()
    
    def cooldown_remaining(self, action_key: str, seconds: int) -> float:
        """Check cooldown remaining for an action (in seconds)."""
        cooldowns = self.st.session_state.setdefault("_cooldowns", {})
        last_time = cooldowns.get(action_key, 0.0)
        elapsed = time.time() - last_time
        remaining = max(0.0, seconds - elapsed)
        return remaining
    
    def mark_action(self, action_key: str) -> None:
        """Mark an action as completed (for cooldown tracking)."""
        cooldowns = self.st.session_state.setdefault("_cooldowns", {})
        cooldowns[action_key] = time.time()
    
    def load_asset_bytes(self, filename: str) -> Optional[bytes]:
        """Load asset file as bytes (cached via Streamlit)."""
        # Note: Caching is handled by Streamlit's built-in caching when called through st
        path = self.assets_dir / filename
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except Exception:
            logger.warning(f"Failed to load asset {path}", exc_info=True)
            return None
    
    def asset_base64(self, filename: str) -> str:
        """Load asset and return as base64 string."""
        import base64
        payload = self.load_asset_bytes(filename)
        if not payload:
            return ""
        return base64.b64encode(payload).decode("utf-8")
    
    def persist_project(self, project: Any, *, action: str = "save") -> bool:
        """Save project to local storage."""
        path = project.save()
        if not path:
            logger.error(f"persist_project failed for '{project.title}' (action={action})")
            try:
                self.st.toast("⚠️ Save failed — check file permissions and disk space.", icon="⚠️")
            except Exception as e:
                self.st.error(f"Save failed for '{project.title}': {e}")
            return False
        
        try:
            self.st.toast(f"✅ {action.capitalize()} successful!", icon="✅")
        except Exception:
            pass  # Non-critical
        return True
    
    def load_project_safe(self, path: str) -> Optional[Any]:
        """Load a project with error handling."""
        try:
            from app.services.projects import Project
            return Project.load(path)
        except Exception as e:
            logger.error(f"Failed to load project from {path}: {e}", exc_info=True)
            try:
                self.st.error(f"⚠️ Failed to load project: {e}")
            except Exception:
                pass
            return None
    
    def get_active_projects_dir(self) -> str:
        """Get the active projects directory path."""
        return self.st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR
    
    def get_ai_model(self) -> str:
        """Get the currently configured AI model."""
        provider = self.st.session_state.get("ai_provider", "groq")
        if provider == "openai":
            return self.st.session_state.get("openai_model", AppConfig.OPENAI_MODEL)
        return self.st.session_state.get("groq_model", AppConfig.DEFAULT_MODEL)
    
    def get_ai_key(self) -> str:
        """Get the active AI API key."""
        provider = self.st.session_state.get("ai_provider", "groq")
        if provider == "openai":
            return self.st.session_state.get("openai_api_key", "")
        return self.st.session_state.get("groq_api_key", "")
    
    def get_active_key_status(self) -> Tuple[bool, str]:
        """Check if active AI provider has valid key configured."""
        provider = self.st.session_state.get("ai_provider", "groq")
        keys = self.st.session_state.get("ai_session_keys", {})
        key = keys.get(provider, "")
        
        if not key or len(key) < 8:
            return False, f"No {provider.upper()} API key configured"
        return True, f"{provider.upper()} key configured"
    
    def debug_enabled(self) -> bool:
        """Check if debug mode is enabled."""
        try:
            secrets = self.st.secrets
        except Exception:
            secrets = {}
        
        if isinstance(secrets, dict):
            return bool(secrets.get("DEBUG")) or bool(self.st.session_state.get("debug"))
        
        try:
            return bool(secrets["DEBUG"]) or bool(self.st.session_state.get("debug"))
        except Exception:
            return bool(self.st.session_state.get("debug"))


def create_ui_context(st) -> UIContext:
    """Factory function to create UI context."""
    return UIContext(st)
