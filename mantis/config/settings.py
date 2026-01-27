from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict


logger = logging.getLogger("MANTIS")


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
    USERS_DIR = os.getenv("MANTIS_USERS_DIR", os.path.join(PROJECTS_DIR, "users"))
    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_TIMEOUT = int(os.getenv("GROQ_TIMEOUT", "300"))
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
    MAX_UPLOAD_MB = int(os.getenv("MANTIS_MAX_UPLOAD_MB", "10"))
    SAVE_LOCK_TIMEOUT = int(os.getenv("MANTIS_SAVE_LOCK_TIMEOUT", "5"))
    SAVE_LOCK_RETRY_SLEEP = float(os.getenv("MANTIS_SAVE_LOCK_RETRY_SLEEP", "0.1"))
    WORLD_BIBLE_CONFIDENCE = float(os.getenv("MANTIS_WORLD_BIBLE_CONFIDENCE", "0.75"))


def ensure_storage_dirs() -> None:
    os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
    os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)
    os.makedirs(AppConfig.USERS_DIR, exist_ok=True)


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
        with open(AppConfig.CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        logger.warning("Failed to save app config", exc_info=True)
