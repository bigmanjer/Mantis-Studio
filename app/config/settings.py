from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict


logger = logging.getLogger("MANTIS")


def _safe_int(env_var: str, default: int) -> int:
    """Read an integer from an environment variable with a safe fallback."""
    raw = os.getenv(env_var, "")
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        logger.warning(
            "Invalid integer for %s=%r, using default %s", env_var, raw, default
        )
        return default


def _safe_float(env_var: str, default: float) -> float:
    """Read a float from an environment variable with a safe fallback."""
    raw = os.getenv(env_var, "")
    if not raw:
        return default
    try:
        return float(raw)
    except (ValueError, TypeError):
        logger.warning(
            "Invalid float for %s=%r, using default %s", env_var, raw, default
        )
        return default


def get_app_version() -> str:
    """Return the user-visible app version.

    Priority:
      1) Explicit env var (useful for CI/CD overrides)
      2) VERSION.txt next to repo root (repo-controlled)
      3) A safe fallback string
    """
    env_version = os.getenv("MANTIS_APP_VERSION")
    if env_version:
        return env_version

    try:
        version_path = Path(__file__).resolve().parents[2] / "VERSION.txt"
        if version_path.exists():
            raw = version_path.read_text(encoding="utf-8").strip()
            if raw:
                return raw
    except Exception:
        # Never block app start on version metadata.
        pass

    return "47.0"


class AppConfig:
    APP_NAME = "MANTIS Studio"
    VERSION = get_app_version()
    PROJECTS_DIR = os.getenv("MANTIS_PROJECTS_DIR", "projects")
    BACKUPS_DIR = os.path.join(PROJECTS_DIR, ".backups")

    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_TIMEOUT = _safe_int("GROQ_TIMEOUT", 300)
    DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    CONFIG_PATH = os.getenv(
        "MANTIS_CONFIG_PATH",
        os.path.join(PROJECTS_DIR, ".mantis_config.json"),
    )
    MAX_PROMPT_CHARS = 16000
    SUMMARY_CONTEXT_CHARS = 4000
    MAX_UPLOAD_MB = _safe_int("MANTIS_MAX_UPLOAD_MB", 10)
    SAVE_LOCK_TIMEOUT = _safe_int("MANTIS_SAVE_LOCK_TIMEOUT", 5)
    SAVE_LOCK_RETRY_SLEEP = _safe_float("MANTIS_SAVE_LOCK_RETRY_SLEEP", 0.1)
    WORLD_BIBLE_CONFIDENCE = _safe_float("MANTIS_WORLD_BIBLE_CONFIDENCE", 0.75)


def ensure_storage_dirs() -> None:
    os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
    os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)



logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_app_config() -> Dict[str, str]:
    try:
        with open(AppConfig.CONFIG_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                return data
    except FileNotFoundError:
        return {}
    except Exception:
        logger.warning("Failed to load app config", exc_info=True)
    return {}


def save_app_config(data: Dict[str, str]) -> None:
    try:
        os.makedirs(os.path.dirname(AppConfig.CONFIG_PATH) or ".", exist_ok=True)
        tmp = AppConfig.CONFIG_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, AppConfig.CONFIG_PATH)
    except Exception:
        logger.warning("Failed to save app config", exc_info=True)
