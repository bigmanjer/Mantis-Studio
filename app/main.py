#!/usr/bin/env python3
"""
MANTIS Studio - Main Entry Point

This is the primary Streamlit application entry point for MANTIS Studio.
It implements a state-driven (not page-driven) navigation system.

Run with:
    streamlit run app/main.py

Or with utility flags:
    python -m app.main --selftest    # Run self-tests
    python -m app.main --repair      # Repair project files

Architecture:
    - State-based navigation via st.session_state.page
    - Views are available in app/views/ directory
    - Business logic in app/services/ directory
    - All navigation happens within this single entry point
    - NO Streamlit multipage routing (no /pages directory)

Directory Structure:
    app/
    ├── state.py              # Session state schema + defaults
    ├── router.py             # Central navigation logic
    ├── layout/               # UI layout components (sidebar, header, styles)
    ├── views/                # UI screens (dashboard, projects, editor, etc.)
    ├── components/           # Reusable UI blocks
    ├── services/             # Business logic (projects, storage, auth, AI, export)
    └── utils/                # Utilities (versioning, helpers)
"""

import datetime
import difflib
import json
import logging
import os
import random
import re
import shutil
import sys
import time
import uuid
import webbrowser
from collections.abc import Generator
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from string import Template
from typing import Any, Callable, Dict, List, Optional

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.utils.navigation import get_nav_config

# NOTE: Streamlit-dependent utilities are imported inside _run_ui() so
# `python -m app.main --selftest` can run without Streamlit installed.


# ===== v45 BRANDING (SAFE, ORIGINAL TEMPLATE) =====
import base64
# ==================================================

SELFTEST_MODE = "--selftest" in sys.argv
REPAIR_MODE = "--repair" in sys.argv


# ============================================================
# 1) CONFIG
# ============================================================

def get_app_version() -> str:
    """Return the user-visible app version.

    Priority:
      1) Explicit env var (useful for CI/CD overrides)
      2) VERSION.txt next to this file (repo-controlled)
      3) A safe fallback string
    """
    env_version = os.getenv("MANTIS_APP_VERSION")
    if env_version:
        return env_version

    try:
        version_path = Path(__file__).resolve().parents[1] / "VERSION.txt"
        if version_path.exists():
            raw = version_path.read_text(encoding="utf-8").strip()
            if raw:
                return raw
    except Exception:
        # Never block app start on version metadata.
        pass

    return "47.0"


def _safe_int_env(env_var: str, default: int) -> int:
    raw = os.getenv(env_var, "")
    if not raw:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        return default


def _safe_float_env(env_var: str, default: float) -> float:
    raw = os.getenv(env_var, "")
    if not raw:
        return default
    try:
        return float(raw)
    except (ValueError, TypeError):
        return default


class AppConfig:
    APP_NAME = "MANTIS Studio"
    VERSION = get_app_version()
    PROJECTS_DIR = os.getenv("MANTIS_PROJECTS_DIR", "projects")
    BACKUPS_DIR = os.path.join(PROJECTS_DIR, ".backups")

    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_TIMEOUT = _safe_int_env("GROQ_TIMEOUT", 300)
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
    MAX_UPLOAD_MB = _safe_int_env("MANTIS_MAX_UPLOAD_MB", 10)
    SAVE_LOCK_TIMEOUT = _safe_int_env("MANTIS_SAVE_LOCK_TIMEOUT", 5)
    SAVE_LOCK_RETRY_SLEEP = _safe_float_env("MANTIS_SAVE_LOCK_RETRY_SLEEP", 0.1)
    WORLD_BIBLE_CONFIDENCE = _safe_float_env("MANTIS_WORLD_BIBLE_CONFIDENCE", 0.75)
    
    # Documentation URLs
    GETTING_STARTED_URL = "https://github.com/bigmanjer/Mantis-Studio/blob/main/GETTING_STARTED.md"


os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)


logging.basicConfig(
    level=logging.DEBUG if os.getenv("MANTIS_DEBUG") else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s"
)
logger = logging.getLogger("MANTIS")
logger.info("=" * 60)
logger.info("MANTIS Studio Starting...")
logger.info("=" * 60)


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


def _truncate_prompt(prompt: str, limit: int) -> str:
    if not prompt:
        return prompt
    if len(prompt) <= limit:
        return prompt
    logger.warning("Prompt length %s exceeded limit %s; truncating", len(prompt), limit)
    return prompt[:limit]


def sanitize_ai_input(text: str, max_length: int = 0) -> str:
    """Sanitize user-provided text before sending to AI APIs.

    Strips leading/trailing whitespace and removes null bytes.
    When *max_length* is positive the text is truncated to that limit.
    """
    if not text:
        return ""
    cleaned = text.strip().replace("\x00", "")
    if max_length > 0 and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


def _acquire_lock(lock_path: str, timeout: int, retry_sleep: float) -> bool:
    start = time.time()
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as lock_file:
                lock_file.write(str(os.getpid()))
            return True
        except FileExistsError:
            try:
                age = time.time() - os.path.getmtime(lock_path)
            except OSError:
                age = 0
            if age > max(timeout * 5, 5):
                try:
                    os.remove(lock_path)
                except OSError:
                    pass
            if time.time() - start >= timeout:
                return False
            time.sleep(retry_sleep)


def _release_lock(lock_path: str) -> None:
    try:
        os.remove(lock_path)
    except OSError:
        pass


def _get_streamlit():
    if "streamlit" not in sys.modules:
        return None
    try:
        import streamlit as st

        return st
    except Exception:
        return None


def _normalize_provider(provider: str) -> str:
    return (provider or "groq").strip().lower()


def _provider_label(provider: str) -> str:
    return "OpenAI" if _normalize_provider(provider) == "openai" else "Groq"


def _ensure_session_keys(st) -> Dict[str, str]:
    keys = st.session_state.setdefault("ai_session_keys", {})
    for provider in ("openai", "groq"):
        keys.setdefault(provider, "")
    st.session_state["ai_session_keys"] = keys
    return keys


def _validate_api_key_format(key: str) -> bool:
    """Basic sanity check for API key format.

    Returns ``True`` when the key looks plausible (only printable ASCII,
    reasonable length).  This is not authoritative – the real validation
    happens server-side – but it catches obvious mistakes like pasting
    HTML or binary content into the key field.
    """
    if not key:
        return False
    if len(key) < 8 or len(key) > 256:
        return False
    # Only printable ASCII characters (no control chars or non-ASCII)
    return all(32 <= ord(ch) < 127 for ch in key)


def set_session_key(provider: str, key: str) -> None:
    st = _get_streamlit()
    if not st:
        return
    provider = _normalize_provider(provider)
    cleaned = (key or "").strip()
    if cleaned and not _validate_api_key_format(cleaned):
        logger.warning("Rejected API key for %s: invalid format", provider)
        return
    keys = _ensure_session_keys(st)
    keys[provider] = cleaned
    st.session_state["ai_session_keys"] = keys
    # Persist to config file so the key survives a page refresh
    config = load_app_config()
    config[f"{provider}_api_key"] = cleaned
    save_app_config(config)


def clear_session_key(provider: str) -> None:
    st = _get_streamlit()
    if not st:
        return
    provider = _normalize_provider(provider)
    keys = _ensure_session_keys(st)
    keys[provider] = ""
    st.session_state["ai_session_keys"] = keys
    # Remove from config file as well
    config = load_app_config()
    config.pop(f"{provider}_api_key", None)
    save_app_config(config)


def _get_secret_key(st, provider: str) -> str:
    if not st or not hasattr(st, "secrets"):
        return ""
    try:
        secrets = st.secrets
        provider = _normalize_provider(provider)
        if provider == "openai":
            return str(
                secrets.get("openai_api_key")
                or secrets.get("OPENAI_API_KEY")
                or (secrets.get("openai") or {}).get("api_key")
                or ""
            ).strip()
        return str(
            secrets.get("groq_api_key")
            or secrets.get("GROQ_API_KEY")
            or (secrets.get("groq") or {}).get("api_key")
            or ""
        ).strip()
    except (KeyError, FileNotFoundError):
        return ""


def _get_server_default_key(provider: str) -> str:
    st = _get_streamlit()
    key = _get_secret_key(st, provider)
    if key:
        return key
    provider = _normalize_provider(provider)
    if provider == "openai":
        return (AppConfig.OPENAI_API_KEY or "").strip()
    return (AppConfig.GROQ_API_KEY or "").strip()


def get_effective_key(provider: str, user_id: Optional[str] = None) -> tuple[str, str]:
    provider = _normalize_provider(provider)
    st = _get_streamlit()
    if st:
        session_key = _ensure_session_keys(st).get(provider, "")
        if session_key:
            return session_key, "session"
    # Check config file for a previously saved key
    config = load_app_config()
    saved_key = (config.get(f"{provider}_api_key") or "").strip()
    if saved_key:
        return saved_key, "saved"
    default_key = _get_server_default_key(provider)
    if default_key:
        return default_key, "default"
    return "", "none"


def get_active_provider() -> str:
    st = _get_streamlit()
    if st:
        return _normalize_provider(st.session_state.get("ai_provider", "groq"))
    return "groq"


def _get_provider_base_url(provider: str) -> str:
    provider = _normalize_provider(provider)
    st = _get_streamlit()
    if provider == "openai":
        if st:
            return st.session_state.get("openai_base_url", AppConfig.OPENAI_API_URL)
        return AppConfig.OPENAI_API_URL
    if st:
        return st.session_state.get("groq_base_url", AppConfig.GROQ_API_URL)
    return AppConfig.GROQ_API_URL


# ============================================================
# 2) MODELS
# ============================================================

@dataclass
class Entity:
    id: str
    name: str
    category: str
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    tags: str = ""
    created_at: float = field(default_factory=time.time)

    def merge(self, new_desc: str):
        """Smart merge that avoids exact duplicates and formats as bullets."""
        if not new_desc:
            return
        new_desc = new_desc.strip()
        if not new_desc or new_desc in (self.description or ""):
            return

        # Normalize text to check for duplicates (basic)
        curr = (self.description or "").lower()
        current_sentences = set(re.split(r"[.!?\n]", curr))
        new_sentences = [s.strip() for s in re.split(r"[.!?\n]", new_desc) if s.strip()]

        to_add = []
        for s in new_sentences:
            if s.lower() not in current_sentences:
                to_add.append(s)

        if to_add:
            if self.description and not self.description.startswith("-"):
                self.description = f"- {self.description.strip()}"
            elif not self.description:
                self.description = ""

            for item in to_add:
                if self.description:
                    self.description += f"\n- {item}"
                else:
                    self.description = f"- {item}"


@dataclass
class Chapter:
    id: str
    index: int
    title: str = "Untitled Chapter"
    content: str = ""
    summary: str = ""
    word_count: int = 0
    target_words: int = 1000
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def update_content(self, new_text: str, source: str = "manual"):
        if self.content == new_text:
            return
        self.history.append(
            {"timestamp": time.time(), "source": source, "previous_text": self.content}
        )
        if len(self.history) > 10:
            self.history.pop(0)
        self.content = new_text
        self.word_count = len((new_text or "").split())
        self.modified_at = time.time()

    def restore_revision(self, text: str):
        self.content = text
        self.word_count = len((text or "").split())
        self.modified_at = time.time()


@dataclass
class Project:
    id: str
    title: str
    author: str = ""
    genre: str = ""
    outline: str = ""
    memory: str = ""
    memory_hard: str = ""
    memory_soft: str = ""
    author_note: str = ""
    style_guide: str = ""
    default_word_count: int = 1000
    world_db: Dict[str, Entity] = field(default_factory=dict)
    chapters: Dict[str, Chapter] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_modified: float = field(default_factory=time.time)
    filepath: Optional[str] = None
    storage_dir: Optional[str] = None

    @classmethod
    def create(
        cls,
        title: str,
        author: str = "",
        genre: str = "",
        storage_dir: Optional[str] = None,
    ) -> "Project":
        storage_dir = storage_dir or AppConfig.PROJECTS_DIR
        os.makedirs(storage_dir, exist_ok=True)
        final_title = (title or "").strip()
        if not final_title:
            base = "Untitled Project"
            final_title = base
            counter = 1
            if os.path.exists(storage_dir):
                while True:
                    found = False
                    for f in os.listdir(storage_dir):
                        if final_title.replace(" ", "_") in f:
                            found = True
                            break
                    if not found:
                        break
                    final_title = f"{base} ({counter})"
                    counter += 1
        return cls(
            id=str(uuid.uuid4()),
            title=final_title,
            author=author.strip(),
            genre=genre.strip(),
            storage_dir=storage_dir,
        )

    @staticmethod
    def _normalize_category(category: str) -> str:
        normalized = (category or "").strip().lower()
        mapping = {
            "character": "Character",
            "characters": "Character",
            "location": "Location",
            "locations": "Location",
            "faction": "Faction",
            "factions": "Faction",
            "lore": "Lore",
            "rule": "Lore",
            "rules": "Lore",
            "item": "Item",
            "items": "Item",
        }
        return mapping.get(normalized, "Lore")

    @staticmethod
    def _normalize_entity_name(name: str) -> str:
        base = (name or "").strip().lower()
        if not base:
            return ""
        base = re.sub(r"[\"'`]", "", base)
        base = re.sub(r"\((.*?)\)", r" \1 ", base)
        base = re.sub(r"\b(mr|mrs|ms|dr|prof|sir|madam)\.?\b", "", base)
        base = re.sub(r"[^\w\s/-]", " ", base)
        base = re.sub(r"\s+", " ", base).strip()
        abbrev_map = {
            "st": "saint",
            "mt": "mount",
            "ft": "fort",
        }
        tokens = [abbrev_map.get(token, token) for token in base.split()]
        return " ".join(tokens).strip()

    @classmethod
    def _entity_aliases(cls, name: str) -> List[str]:
        normalized = cls._normalize_entity_name(name)
        if not normalized:
            return []
        parts = re.split(r"\s*/\s*|\s+or\s+|\s+\|\s+", normalized)
        aliases = []
        for part in parts:
            part = part.strip()
            if part:
                aliases.append(part)
        if normalized not in aliases:
            aliases.append(normalized)
        return aliases

    @staticmethod
    def _token_set(name: str) -> set[str]:
        return {token for token in re.split(r"\s+", name) if token}

    @classmethod
    def _initials_match(cls, left_norm: str, right_norm: str) -> bool:
        left_tokens = left_norm.split()
        right_tokens = right_norm.split()
        if not left_tokens or not right_tokens:
            return False
        if left_tokens[-1] != right_tokens[-1]:
            return False
        left_initials = {t[0] for t in left_tokens[:-1] if len(t) == 1}
        right_initials = {t[0] for t in right_tokens[:-1] if len(t) == 1}
        if left_initials and right_tokens[0] and right_tokens[0][0] in left_initials:
            return True
        if right_initials and left_tokens[0] and left_tokens[0][0] in right_initials:
            return True
        return False

    @classmethod
    def _names_match(cls, left: str, right: str) -> bool:
        left_norm = cls._normalize_entity_name(left)
        right_norm = cls._normalize_entity_name(right)
        if not left_norm or not right_norm:
            return False
        if left_norm == right_norm:
            return True

        left_tokens = cls._token_set(left_norm)
        right_tokens = cls._token_set(right_norm)
        if left_tokens & right_tokens:
            if left_norm in right_norm or right_norm in left_norm:
                return True
            if len(left_tokens) > 1 and len(right_tokens) > 1:
                if left_tokens.intersection(right_tokens):
                    return True

        if cls._initials_match(left_norm, right_norm):
            return True

        similarity = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
        return similarity >= 0.85

    @classmethod
    def _merge_aliases(cls, entity: Entity, incoming: List[str], primary: str) -> None:
        normalized_existing = {
            cls._normalize_entity_name(entity.name)
        }
        for alias in entity.aliases:
            normalized_existing.add(cls._normalize_entity_name(alias))
        for alias in incoming:
            clean = (alias or "").strip()
            if not clean:
                continue
            normalized = cls._normalize_entity_name(clean)
            if not normalized or normalized in normalized_existing:
                continue
            if cls._normalize_entity_name(primary) == normalized:
                continue
            entity.aliases.append(clean)
            normalized_existing.add(normalized)

    def _build_match_aliases(self, name: str, aliases: Optional[List[str]] = None) -> List[str]:
        incoming_match_aliases = self._entity_aliases(name)
        for alias in (aliases or []):
            incoming_match_aliases.extend(self._entity_aliases(alias))
        return incoming_match_aliases

    def find_entity_match(
        self,
        name: str,
        category: str,
        aliases: Optional[List[str]] = None,
    ) -> Optional[Entity]:
        clean_name = (name or "").strip()
        if not clean_name:
            return None

        normalized_category = self._normalize_category(category)
        incoming_match_aliases = self._build_match_aliases(clean_name, aliases)

        for ent in self.world_db.values():
            if self._normalize_category(ent.category) != normalized_category:
                continue
            candidates = [ent.name] + (ent.aliases or [])
            matched = any(
                self._names_match(candidate, incoming)
                for candidate in candidates
                for incoming in incoming_match_aliases
            )
            if matched:
                return ent
        return None

    def upsert_entity(
        self,
        name: str,
        category: str,
        desc: str = "",
        aliases: Optional[List[str]] = None,
        allow_merge: bool = True,
        allow_alias: bool = True,
    ) -> tuple[Optional[Entity], str]:
        clean_name = (name or "").strip()
        if not clean_name:
            return None, "skipped"

        normalized_category = self._normalize_category(category)
        incoming_aliases = [a for a in (aliases or []) if (a or "").strip()]
        incoming_aliases = list(dict.fromkeys([a.strip() for a in incoming_aliases if a.strip()]))
        incoming_match_aliases = self._build_match_aliases(clean_name, incoming_aliases)

        for ent in self.world_db.values():
            if self._normalize_category(ent.category) != normalized_category:
                continue

            candidates = [ent.name] + (ent.aliases or [])
            matched = any(
                self._names_match(candidate, incoming)
                for candidate in candidates
                for incoming in incoming_match_aliases
            )
            if matched:
                if allow_alias:
                    self._merge_aliases(ent, [clean_name] + incoming_aliases, ent.name)
                if allow_merge:
                    ent.merge(desc)
                self.last_modified = time.time()
                return ent, "matched"

        e = Entity(
            id=str(uuid.uuid4()),
            name=clean_name,
            category=normalized_category,
            description=(desc or "").strip(),
            aliases=[],
        )
        if allow_alias:
            self._merge_aliases(e, incoming_aliases, clean_name)
        self.world_db[e.id] = e
        self.last_modified = time.time()
        return e, "created"

    def add_entity(self, name: str, category: str, desc: str = "") -> Optional[Entity]:
        """Smart Add with Fuzzy Matching."""
        ent, _ = self.upsert_entity(name, category, desc, allow_merge=True, allow_alias=True)
        return ent

    def delete_entity(self, eid: str):
        if eid in self.world_db:
            del self.world_db[eid]
            self.last_modified = time.time()

    def delete_chapter(self, cid: str):
        if cid in self.chapters:
            del self.chapters[cid]
            for new_idx, ch in enumerate(self.get_ordered_chapters(), start=1):
                ch.index = new_idx
            self.last_modified = time.time()

    def add_chapter(self, title: str = "Untitled", content: str = "") -> Chapter:
        existing = [c.index for c in self.chapters.values()]
        index = (max(existing) + 1) if existing else 1

        if (title == "Untitled" or title.startswith("Chapter")) and self.outline:
            pattern = re.compile(rf"Chapter {index}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
            match = pattern.search(self.outline)
            if match:
                raw_text = match.group(1).strip()
                split_text = re.split(r" [-–:] ", raw_text, 1)
                final_title = sanitize_chapter_title(split_text[0].strip())
                if len(final_title) > 2:
                    title = final_title

        c = Chapter(
            id=str(uuid.uuid4()),
            index=index,
            title=sanitize_chapter_title(title),
            content=content or "",
            target_words=self.default_word_count,
        )
        c.word_count = len((content or "").split())
        self.chapters[c.id] = c
        self.last_modified = time.time()
        return c

    def get_ordered_chapters(self) -> List[Chapter]:
        return sorted(self.chapters.values(), key=lambda c: c.index)

    def get_total_word_count(self) -> int:
        return sum(c.word_count for c in self.chapters.values())

    def import_text_file(self, full_text: str) -> int:
        split_pattern = r"(?i)\n\s*(?:chapter|part)\s+(?:\d+|[a-z]+)[:.]?\s*.*?(?=\n)"
        parts = re.split(split_pattern, full_text or "")
        headers = re.findall(split_pattern, full_text or "")
        if len(parts) < 2:
            self.add_chapter("Imported Text", full_text or "")
            return 1

        count = 0
        if parts[0].strip():
            self.add_chapter("Prologue", parts[0].strip())
            count += 1
        for i, content in enumerate(parts[1:]):
            if not content.strip():
                continue
            title = headers[i].strip() if i < len(headers) else f"Chapter {i+1}"
            title = sanitize_chapter_title(title)
            self.add_chapter(title, content.strip())
            count += 1
        return count

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d.pop("filepath", None)
        d.pop("storage_dir", None)
        d["world_db"] = {k: asdict(v) for k, v in self.world_db.items()}
        d["chapters"] = {k: asdict(v) for k, v in self.chapters.items()}
        return d

    def save(self) -> str:
        safe_title = re.sub(r'[<>:"/\\|?*]', "_", self.title)[:60]
        filename = f"{self.id}_{safe_title.replace(' ', '_')}.json"
        storage_dir = self.storage_dir or AppConfig.PROJECTS_DIR
        try:
            os.makedirs(storage_dir, exist_ok=True)
        except OSError:
            logger.error("Cannot create storage directory %s", storage_dir, exc_info=True)
            return ""
        path = os.path.join(storage_dir, filename)
        lock_path = path + ".lock"
        tmp = path + ".tmp"
        last_error: Optional[Exception] = None
        if not _acquire_lock(
            lock_path,
            AppConfig.SAVE_LOCK_TIMEOUT,
            AppConfig.SAVE_LOCK_RETRY_SLEEP,
        ):
            logger.error("Save lock timeout for %s", path)
            return ""
        try:
            saved = False
            for attempt in range(1, 4):
                try:
                    if os.path.exists(path):
                        os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)
                        stamp = time.strftime("%Y%m%d_%H%M%S")
                        backup_name = f"{stamp}__{os.path.basename(path)}"
                        backup_path = os.path.join(AppConfig.BACKUPS_DIR, backup_name)
                        try:
                            shutil.copy2(path, backup_path)
                        except Exception:
                            logger.warning("Backup failed for %s", path, exc_info=True)
                    with open(tmp, "w", encoding="utf-8") as f:
                        json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
                    os.replace(tmp, path)
                    saved = True
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning("Save attempt %s failed for %s", attempt, path, exc_info=True)
                    time.sleep(0.1)
            else:
                logger.error("Save failed after retries for %s: %s", path, last_error)
        finally:
            _release_lock(lock_path)
            # Clean up stale temp file on failure
            if not saved:
                try:
                    os.remove(tmp)
                except OSError:
                    pass

        if not saved:
            return ""

        self.filepath = path
        self.storage_dir = storage_dir
        self.last_modified = time.time()
        return path

    @classmethod
    def load(cls, path: str) -> "Project":
        try:
            with open(path, "r", encoding="utf-8") as fh:
                try:
                    data = json.load(fh)
                except json.JSONDecodeError as exc:
                    logger.error("Corrupt project file %s: %s", path, exc)
                    raise ValueError(
                        f"Cannot load project: file is not valid JSON ({path})"
                    ) from exc
        except FileNotFoundError as exc:
            logger.error("Project file not found: %s", path, exc_info=True)
            raise ValueError(f"Cannot load project: file not found ({path})") from exc
        if not isinstance(data, dict):
            raise ValueError(f"Cannot load project: expected JSON object ({path})")

        proj = cls(
            id=data.get("id") or str(uuid.uuid4()),
            title=data.get("title") or "Untitled Project",
        )
        proj.author = data.get("author", "")
        proj.genre = data.get("genre", "")
        proj.outline = data.get("outline", "")
        proj.memory = data.get("memory", data.get("memory_notes", ""))
        proj.memory_hard = data.get("memory_hard", "")
        proj.memory_soft = data.get("memory_soft", "")
        proj.author_note = data.get("author_note", data.get("authors_note", ""))
        proj.style_guide = data.get("style_guide", data.get("style_note", ""))
        proj.default_word_count = data.get("default_word_count", 1000)
        proj.created_at = data.get("created_at", time.time())
        proj.last_modified = data.get("last_modified", time.time())

        ent_fields = {f.name for f in fields(Entity)}
        world_db_data = data.get("world_db") or data.get("characters") or {}
        if isinstance(world_db_data, list):
            world_db_data = {
                (item.get("id") or str(uuid.uuid4())): item
                for item in world_db_data
                if isinstance(item, dict)
            }
        if not isinstance(world_db_data, dict):
            world_db_data = {}
        for k, v in world_db_data.items():
            if "category" not in v:
                v["category"] = "Character"
            clean = {key: val for key, val in v.items() if key in ent_fields}
            clean["id"] = clean.get("id") or k or str(uuid.uuid4())
            clean["name"] = clean.get("name") or "Unknown"
            clean["category"] = Project._normalize_category(clean.get("category", "Lore"))
            if "aliases" in clean and not isinstance(clean["aliases"], list):
                clean["aliases"] = [str(clean["aliases"])]
            try:
                proj.world_db[clean["id"]] = Entity(**clean)
            except TypeError:
                logger.warning("Skipping malformed entity entry: %s", k, exc_info=True)

        chap_fields = {f.name for f in fields(Chapter)}
        chapter_data = data.get("chapters") or {}
        if isinstance(chapter_data, list):
            chapter_data = {
                (item.get("id") or str(uuid.uuid4())): item
                for item in chapter_data
                if isinstance(item, dict)
            }
        if not isinstance(chapter_data, dict):
            chapter_data = {}
        fallback_index = 1
        for k, v in chapter_data.items():
            clean = {key: val for key, val in v.items() if key in chap_fields}
            clean["id"] = clean.get("id") or k or str(uuid.uuid4())
            try:
                clean_index = int(clean.get("index") or fallback_index)
            except (TypeError, ValueError):
                clean_index = fallback_index
            clean["index"] = clean_index
            clean["title"] = clean.get("title") or f"Chapter {clean_index}"
            fallback_index = max(fallback_index, clean_index + 1)
            try:
                proj.chapters[clean["id"]] = Chapter(**clean)
            except TypeError:
                logger.warning("Skipping malformed chapter entry: %s", k, exc_info=True)

        proj.storage_dir = os.path.dirname(path)
        proj.filepath = path
        return proj

    @classmethod
    def delete_file(cls, filepath: str):
        try:
            os.remove(filepath)
        except OSError:
            logger.warning("Failed to delete project file: %s", filepath, exc_info=True)


# ============================================================
# 3) AI ENGINE
# ============================================================

class AIEngine:
    def __init__(
        self,
        timeout: int = AppConfig.GROQ_TIMEOUT,
        base_url: Optional[str] = None,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = _normalize_provider(provider or get_active_provider())
        self.base_url = (base_url or _get_provider_base_url(self.provider)).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.api_key = (api_key or "").strip()

    def _resolve_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        key, _ = get_effective_key(self.provider)
        return key

    def probe_models(self, api_key: str) -> List[str]:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            r = self.session.get(f"{self.base_url}/models", headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            return [m.get("id") for m in data.get("data", []) if m.get("id")]
        except Exception:
            logger.warning("Model probe failed for %s", self.base_url, exc_info=True)
            return []

    def generate_stream(self, prompt: str, model: str) -> Generator[str, None, None]:
        if "streamlit" in sys.modules:
            import streamlit as st

            results = st.session_state.get("coherence_results", [])
            if len(results) > 2:
                yield (
                    "ERROR: Canon violation detected.\n"
                    "Resolve Hard Canon conflicts before generating AI content."
                )
                return
            project = st.session_state.get("project")
            hard_rules = ""
            if project:
                hard_rules = (project.memory_hard or project.memory or "").strip()
            if hard_rules:
                prompt = (
                    "HARD CANON RULES (NON-NEGOTIABLE):\n"
                    f"{hard_rules}\n\n"
                    f"{prompt}"
                )
        if not model:
            yield f"{_provider_label(self.provider)} model not configured."
            return

        api_key = self._resolve_api_key()
        if not api_key:
            yield f"{_provider_label(self.provider)} API key not configured."
            return

        prompt = sanitize_ai_input(prompt)
        prompt = _truncate_prompt(prompt, AppConfig.MAX_PROMPT_CHARS)
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {api_key}"

        def _groq_non_stream() -> Generator[str, None, None]:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            try:
                r = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                content = (choice.get("message") or {}).get("content") or choice.get("text") or ""
                if content:
                    yield content
                else:
                    yield f"{_provider_label(self.provider)} response empty."
            except requests.exceptions.Timeout:
                logger.warning("%s request timed out after %ss", _provider_label(self.provider), self.timeout)
                yield f"{_provider_label(self.provider)} request timed out. Try again or increase timeout."
            except requests.exceptions.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                logger.warning("%s HTTP %s error", _provider_label(self.provider), status, exc_info=True)
                if status == 401:
                    yield f"{_provider_label(self.provider)} API key is invalid or expired."
                elif status == 429:
                    yield f"{_provider_label(self.provider)} rate limit exceeded. Please wait and try again."
                else:
                    yield f"{_provider_label(self.provider)} generation failed (HTTP {status})."
            except Exception:
                logger.warning("%s non-stream generation failed", _provider_label(self.provider), exc_info=True)
                yield f"{_provider_label(self.provider)} generation failed."

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        try:
            with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
                timeout=self.timeout,
            ) as r:
                r.raise_for_status()
                yielded = False
                for raw in r.iter_lines():
                    if not raw:
                        continue
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line.replace("data:", "", 1).strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yielded = True
                        yield content
                if not yielded:
                    yield from _groq_non_stream()
        except Exception:
            logger.warning(
                "%s streaming generation failed, retrying non-stream",
                _provider_label(self.provider),
                exc_info=True,
            )
            yield from _groq_non_stream()

    def generate(self, prompt: str, model: str) -> Dict[str, str]:
        chunks: List[str] = []
        for chunk in self.generate_stream(prompt, model):
            chunks.append(chunk)
        return {"text": "".join(chunks)}

    def generate_json(self, prompt: str, model: str) -> Optional[List[Dict[str, Any]]]:
        res = self.generate(f"Return ONLY valid JSON. List of objects. No markdown.\n\n{prompt}", model)
        txt = (res.get("text", "") or "").strip()
        if not txt:
            return None
        txt = re.sub(r"```json\s*", "", txt)
        txt = re.sub(r"```\s*", "", txt).strip()
        # Try to extract JSON array or object even if surrounded by text
        if not txt.startswith(("[", "{")):
            bracket = txt.find("[")
            brace = txt.find("{")
            if bracket >= 0 and (brace < 0 or bracket < brace):
                txt = txt[bracket:]
            elif brace >= 0:
                txt = txt[brace:]
        try:
            d = json.loads(txt)
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                return [d]
            return None
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("JSON parse failed for AI response (length=%d)", len(txt))
            return None


class AnalysisEngine:
    @staticmethod
    def extract_entities(text: str, model: str) -> list:
        if not text or len(text) < 50:
            return []
        prompt = (
            "Analyze text. Identify Characters, Locations, Factions, and important Lore.\n"
            "Return JSON List: [{'name': 'X', 'category': 'Character|Location|Faction|Lore', "
            "'description': 'Z', 'aliases': ['Alt Name'], 'confidence': 0.0}]\n"
            f"TEXT:\n{text[:6000]}"
        )
        return AIEngine().generate_json(prompt, model) or []

    @staticmethod
    def generate_title(outline: str, genre: str, model: str) -> str:
        prompt = (
            f"GENRE: {genre}\n"
            f"OUTLINE: {outline[:2000]}\n"
            "TASK: Create a creative, catchy title for this story.\n"
            "RULES: Output ONLY the title. No quotes. No prefixes like 'Title:'."
        )
        raw = (AIEngine().generate(prompt, model).get("text", "Untitled") or "").strip()
        clean = re.sub(r"(?i)^(here is a title|sure|suggested title|title)[:\s-]*", "", raw).strip()
        clean = clean.replace('"', "").replace("'", "").strip()
        return clean.split("\n")[0] if clean else "Untitled"


    @staticmethod
    def detect_genre(outline: str, model: str) -> str:
        """
        Attempts to infer a concise genre label from the outline text.
        Uses AI if available, otherwise falls back to a lightweight heuristic.
        """
        outline = (outline or "").strip()
        if not outline:
            return ""

        # Heuristic fallback first (fast, offline-safe)
        low = outline.lower()
        heuristic_map = [
            ("space", "Science Fiction"),
            ("spaceship", "Science Fiction"),
            ("alien", "Science Fiction"),
            ("cyber", "Cyberpunk"),
            ("hacker", "Cyberpunk"),
            ("detective", "Mystery/Thriller"),
            ("murder", "Mystery/Thriller"),
            ("serial killer", "Mystery/Thriller"),
            ("dragon", "Fantasy"),
            ("magic", "Fantasy"),
            ("kingdom", "Fantasy"),
            ("vampire", "Horror"),
            ("zombie", "Horror"),
            ("haunted", "Horror"),
            ("romance", "Romance"),
            ("love triangle", "Romance"),
            ("coming of age", "Coming-of-Age"),
            ("war", "Historical/War"),
            ("wwii", "Historical/War"),
            ("post-apocalyptic", "Post-Apocalyptic"),
            ("apocalypse", "Post-Apocalyptic"),
        ]
        for needle, genre in heuristic_map:
            if needle in low:
                return genre

        # AI-based inference
        prompt = (
            "You are a book editor. Infer the most fitting genre from the outline.\n"
            "Rules:\n"
            "- Output ONLY a short genre label (2-4 words).\n"
            "- No quotes, no prefix, no punctuation at the end.\n\n"
            f"OUTLINE:\n{outline[:2500]}"
        )
        try:
            raw = (AIEngine().generate(prompt, model).get("text", "") or "").strip()
            raw = re.sub(r'(?i)^(genre)[:\s-]*', '', raw).strip()
            raw = raw.replace('"', "").replace("'", "").strip()
            genre = raw.splitlines()[0].strip()
            # Keep it clean / short
            genre = re.sub(r"[^\w\s/&-]", "", genre).strip()
            if len(genre) > 40:
                genre = genre[:40].strip()
            return genre
        except Exception:
            logger.warning("Genre detection failed", exc_info=True)
            return ""

    @staticmethod
    def enrich_entity(name: str, category: str, desc: str, model: str) -> str:
        prompt = (
            f"NAME: {name}\nCATEGORY: {category}\nCURRENT INFO: {desc}\n"
            "TASK: Expand on this entry with creative details, backstory, or physical description.\n"
            "RULES: Keep it concise (under 50 words). Bullet points are okay."
        )
        return AIEngine().generate(prompt, model).get("text", "") or ""

    @staticmethod
    def coherence_check(
        memory: str,
        author_note: str,
        style_guide: str,
        outline: str,
        world_bible: str,
        chapters: List[Dict[str, Any]],
        model: str,
    ) -> List[Dict[str, Any]]:
        if not chapters:
            return []
        prompt = (
            "You are a developmental editor checking continuity and canon coherence.\n"
            "Identify contradictions, timeline issues, or inconsistent details.\n"
            "Return ONLY JSON (no markdown) as a list of objects with keys:\n"
            "- chapter_index (number)\n"
            "- issue (short description)\n"
            "- target_excerpt (exact text to replace, must exist in the chapter)\n"
            "- suggested_rewrite (replacement text to fix coherence)\n"
            "- confidence (low|medium|high)\n\n"
            f"PROJECT MEMORY:\n{(memory or '')[:2000]}\n\n"
            f"AUTHOR NOTE:\n{(author_note or '')[:1200]}\n\n"
            f"STYLE GUIDE:\n{(style_guide or '')[:1200]}\n\n"
            f"WORLD BIBLE:\n{(world_bible or '')[:2400]}\n\n"
            f"OUTLINE:\n{(outline or '')[:2000]}\n\n"
            "CHAPTERS (summaries + excerpts):\n"
            f"{json.dumps(chapters, ensure_ascii=False)}"
        )
        return AIEngine().generate_json(prompt, model) or []


class StoryEngine:
    @staticmethod
    def summarize(text: str, model: str) -> str:
        if not text:
            return ""
        prompt = f"Summarize this scene concisely (under 100 words):\n\n{text[:4000]}"
        return AIEngine().generate(prompt, model).get("text", "") or ""

    @staticmethod
    def generate_chapter_prompt(project: Project, chapter_index: int, target_words: int) -> str:
        hard_rules = (project.memory_hard or project.memory or "").strip()[:1500]
        hard_block = f"HARD CANON RULES (STRICT):\n{hard_rules}\n\n" if hard_rules else ""
        soft_guidelines = (project.memory_soft or "").strip()[:1500]
        soft_block = f"SOFT GUIDELINES (STYLE/CONTEXT):\n{soft_guidelines}\n\n" if soft_guidelines else ""
        memory_context = (project.memory or "").strip()[:1500]
        memory_block = f"PROJECT MEMORY:\n{memory_context}\n\n" if memory_context else ""
        author_note = (project.author_note or "").strip()[:1200]
        author_block = f"AUTHOR NOTE:\n{author_note}\n\n" if author_note else ""
        style_guide = (project.style_guide or "").strip()[:1200]
        style_block = f"STYLE GUIDE:\n{style_guide}\n\n" if style_guide else ""
        outline_context = (project.outline or "")[:3000]
        match = re.search(rf"(?i)Chapter {chapter_index}[:\s]+(.*?)(?=\n|$)", project.outline or "")
        if match:
            specific_beat = match.group(1).strip()
            outline_context += f"\n\nCURRENT CHAPTER OBJECTIVE: {specific_beat}"

        prev_chaps = [c for c in project.get_ordered_chapters() if c.index < chapter_index]
        story_so_far = ""
        prev_text = ""

        if prev_chaps:
            story_so_far = "PREVIOUS EVENTS:\n"
            for c in prev_chaps[-5:]:
                summ = c.summary if c.summary else "No summary."
                story_so_far += f"Ch {c.index}: {summ}\n"
            prev_text = f"\nIMMEDIATELY PRECEDING SCENE:\n{(prev_chaps[-1].content or '')[-1500:]}\n"

        prompt = (
            f"TITLE: {project.title}\nGENRE: {project.genre}\n"
            f"{hard_block}"
            f"{soft_block}"
            f"{memory_block}"
            f"{author_block}"
            f"{style_block}"
            f"OUTLINE CONTEXT:\n{outline_context}\n\n"
            f"{story_so_far}"
            f"{prev_text}\n"
            f"TASK: Write Chapter {chapter_index}.\n"
            f"LENGTH GOAL: {target_words} words.\n"
            "INSTRUCTIONS:\n"
            "1. Continue directly from the preceding scene (if any).\n"
            "2. Match the writing style and tone of the previous text.\n"
            "3. Focus on the 'Current Chapter Objective' if provided.\n"
            "4. Do not output the chapter title. Just the story prose."
        )
        return prompt

    @staticmethod
    def reverse_engineer_outline(project: Project, model: str) -> str:
        chaps = project.get_ordered_chapters()
        if not chaps:
            return "No content."
        txt = ""
        for c in chaps:
            txt += f"Ch {c.index} ({c.title}): {c.summary or (c.content or '')[:300]}\n"
        prompt = f"Create a structured outline based on these chapters:\n\n{txt}"
        return AIEngine().generate(prompt, model).get("text", "") or ""


# ============================================================
# 4) UTILS
# ============================================================

REWRITE_PRESETS = {
    "Custom": "Use your own custom instructions",
    "Fix Grammar": "Correct grammar and spelling only.",
    "Improve Flow": "Fix awkward phrasing and sentence rhythm.",
    "Sensory Expansion": "Show, Don't Tell - Add smells, sounds, and textures.",
    "Deepen POV": "Add more internal monologue and emotional reaction.",
    "Make Witty": "Add humor, banter, and irony.",
    "Make Darker": "Grim, moody, noir-style descriptions.",
    "Expand": "Write more details, double the length.",
}

def rewrite_prompt(text: str, preset: str, custom: str = "") -> str:
    text = sanitize_ai_input(text, AppConfig.MAX_PROMPT_CHARS)
    custom = sanitize_ai_input(custom, 2000)
    instr = custom if preset == "Custom" else REWRITE_PRESETS.get(preset, "")
    return f"Act as an editor.\nTASK: {preset}\nDETAILS: {instr}\n\nINPUT TEXT:\n{text}"

def project_to_markdown(project: Project) -> str:
    md = [f"# {project.title}", f"**Genre:** {project.genre}\n"]
    if project.outline:
        md.append("## Outline")
        md.append(project.outline + "\n")
    if project.memory:
        md.append("## Memory")
        md.append(project.memory + "\n")
    if project.author_note:
        md.append("## Author Note")
        md.append(project.author_note + "\n")
    if project.style_guide:
        md.append("## Style Guide")
        md.append(project.style_guide + "\n")
    md.append("## World Bible")
    for c in project.world_db.values():
        md.append(f"- **{c.name}** ({c.category}): {c.description}")
    md.append("\n## Chapters")
    for c in project.get_ordered_chapters():
        md.append(f"### {c.index}. {c.title}")
        md.append((c.content or "") + "\n")
    return "\n".join(md)


def sanitize_chapter_title(title: str) -> str:
    raw = (title or "").strip()
    if not raw:
        return ""
    clean = raw.replace("“", "").replace("”", "").replace("’", "")
    clean = clean.replace('"', "").replace("'", "")
    clean = re.sub(r"^\*+|\*+$", "", clean).strip()
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean


# ============================================================
# 5) STREAMLIT UI (Appearance + First-time Onboarding)
# ============================================================



def _run_ui():
    import streamlit as st
    from contextlib import contextmanager
    from pathlib import Path
    from app.components.ui import action_card, card, primary_button, section_header, stat_tile
    from app.ui.components import card_block, cta_tile, empty_state, header_bar, render_tag_list
    from app.ui.ui_layout import render_card, render_metric, render_section_header
    from app.layout.layout import render_footer
    from app.ui.theme import inject_theme
    from app.utils.keys import ui_key
    # Import enhanced UI feedback components
    from app.ui.feedback import (
        loading_state,
        step_indicator,
        progress_bar_with_message,
        feedback_message,
        page_header as enhanced_page_header,
    )
    from app.ui.navigation import help_tooltip, quick_action_card

    widget_counters: Dict[tuple, int] = {}
    key_prefix_stack: List[str] = []

    ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

    @st.cache_data(show_spinner=False)
    def load_asset_bytes(filename: str) -> Optional[bytes]:
        path = ASSETS_DIR / filename
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except Exception:
            logging.getLogger("MANTIS").warning(
                "Failed to load asset %s",
                path,
                exc_info=True,
            )
            return None

    def asset_base64(filename: str) -> str:
        payload = load_asset_bytes(filename)
        if not payload:
            return ""
        return base64.b64encode(payload).decode("utf-8")

    def _current_prefix() -> str:
        return "__".join(key_prefix_stack) or "global"

    def _slugify(value: str) -> str:
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
        return ui_key(prefix, widget_type, slug, str(index))

    def init_state(key: str, default: Any) -> None:
        if key not in st.session_state:
            st.session_state[key] = default

    def queue_widget_update(key: str, value: Any) -> None:
        pending = st.session_state.setdefault("_pending_widget_updates", {})
        pending[key] = value

    def apply_pending_widget_updates() -> None:
        pending = st.session_state.pop("_pending_widget_updates", None)
        if pending:
            for pending_key, pending_value in pending.items():
                st.session_state[pending_key] = pending_value

    def _record_action(action_label: Optional[str], action_key: Optional[str]) -> None:
        label = (action_label or action_key or "action").strip()
        st.session_state["last_action"] = label
        st.session_state["last_action_ts"] = time.time()

    @contextmanager
    def key_scope(prefix: str) -> Generator[None, None, None]:
        key_prefix_stack.append(prefix)
        try:
            yield
        finally:
            key_prefix_stack.pop()

    def _wrap_widget(widget_fn, widget_type: str):
        def _wrapped(label=None, *args, **kwargs):
            resolved_key = _auto_key(widget_type, label, kwargs.get("key"))
            kwargs["key"] = resolved_key
            result = widget_fn(label, *args, **kwargs)
            if widget_type in {"button", "form_submit_button"} and result:
                _record_action(label, resolved_key)
            return result

        _wrapped._mantis_wrapped = True
        return _wrapped

    def _wrap_widget_no_label(widget_fn, widget_type: str):
        def _wrapped(*args, **kwargs):
            resolved_key = _auto_key(widget_type, None, kwargs.get("key"))
            kwargs["key"] = resolved_key
            result = widget_fn(*args, **kwargs)
            if widget_type in {"button", "form_submit_button"} and result:
                _record_action(None, resolved_key)
            return result

        _wrapped._mantis_wrapped = True
        return _wrapped

    def _maybe_wrap(name: str, widget_type: str, has_label: bool = True) -> None:
        if not hasattr(st, name):
            return
        current = getattr(st, name)
        # Skip if already wrapped to avoid stacking wrappers on repeated
        # Streamlit reruns, which would eventually cause a RecursionError.
        if getattr(current, "_mantis_wrapped", False):
            return
        wrapped = _wrap_widget(current, widget_type) if has_label else _wrap_widget_no_label(current, widget_type)
        setattr(st, name, wrapped)

    _maybe_wrap("button", "button")
    _maybe_wrap("text_input", "text_input")
    _maybe_wrap("text_area", "text_area")
    _maybe_wrap("selectbox", "selectbox")
    _maybe_wrap("radio", "radio")
    _maybe_wrap("checkbox", "checkbox")
    _maybe_wrap("number_input", "number_input")
    _maybe_wrap("slider", "slider")
    _maybe_wrap("multiselect", "multiselect")
    _maybe_wrap("file_uploader", "file_uploader")
    _maybe_wrap("download_button", "download_button")
    _maybe_wrap("form_submit_button", "form_submit_button")
    _maybe_wrap("toggle", "toggle")
    _maybe_wrap("feedback", "feedback")
    _maybe_wrap("date_input", "date_input")
    _maybe_wrap("time_input", "time_input")
    _maybe_wrap("color_picker", "color_picker")
    _maybe_wrap("camera_input", "camera_input")
    _maybe_wrap("audio_input", "audio_input")
    _maybe_wrap("chat_input", "chat_input", has_label=False)
    # NOTE: st.page_link does not take a "label" as its first positional argument.
    # Wrapping it with the generic label-first wrapper can break routing.
    # If we need auto-keys for page_link later, add a signature-aware wrapper.
    # _maybe_wrap("page_link", "page_link")

    def get_canon_health() -> tuple[str, str]:
        results = st.session_state.get("coherence_results", [])
        issue_count = len(results)
        if issue_count == 0:
            return "🟢", "Canon Stable"
        if issue_count <= 2:
            return "🟡", "Minor Canon Drift"
        return "🔴", "High Canon Risk"

    def detect_hard_canon_violation(project: Project, chapter_index: int, new_text: str) -> List[Dict[str, Any]]:
        hard_rules = (project.memory_hard or project.memory or "").strip()
        if not hard_rules or not (new_text or "").strip():
            return []
        active_provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
        active_key, _ = get_effective_key(active_provider, st.session_state.get("user_id"))
        if not active_key or not get_ai_model():
            return []
        compiled_world_bible = "\n".join(
            f"{e.name} ({e.category}): {e.description}"
            for e in project.world_db.values()
        )
        chapters_payload = [
            {
                "chapter_index": chapter_index,
                "summary": "",
                "excerpt": (new_text or "")[:800],
            }
        ]
        results = AnalysisEngine.coherence_check(
            memory=hard_rules,
            author_note="",
            style_guide="",
            outline=project.outline or "",
            world_bible=compiled_world_bible,
            chapters=chapters_payload,
            model=get_ai_model(),
        )
        return results or []

    def update_locked_chapters() -> None:
        """Refresh the set of chapter indices that are locked due to canon violations."""
        results = st.session_state.get("coherence_results", [])
        locked = set()
        for issue in results:
            try:
                idx = int(issue.get("chapter_index", -1))
                if idx >= 0:
                    locked.add(idx)
            except (TypeError, ValueError):
                pass
        st.session_state["locked_chapters"] = locked

    LEGAL_DIR = Path(__file__).resolve().parents[1] / "legal"

    def _read_legal_file(filename: str, fallback: str) -> str:
        path = LEGAL_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return fallback

    def render_privacy():
        content = _read_legal_file("privacy.md", "## Privacy Policy\n\nLocal-only storage. No analytics.")
        st.markdown(content)
        if st.button("← Back to All Policies", key=ui_key("privacy", "back")):
            st.session_state.page = "legal"
            st.rerun()

    def render_terms():
        content = _read_legal_file("terms.md", "## Terms of Service\n\nProvided as-is for creative use.")
        st.markdown(content)
        if st.button("← Back to All Policies", key=ui_key("terms", "back")):
            st.session_state.page = "legal"
            st.rerun()

    def render_copyright():
        content = _read_legal_file("copyright.md", "## Copyright\n\n© MANTIS Studio")
        st.markdown(content)
        if st.button("← Back to All Policies", key=ui_key("copyright", "back")):
            st.session_state.page = "legal"
            st.rerun()

    def render_cookie():
        content = _read_legal_file("cookie.md", "## Cookie Policy\n\nEssential cookies only.")
        st.markdown(content)
        if st.button("← Back to All Policies", key=ui_key("cookie", "back")):
            st.session_state.page = "legal"
            st.rerun()

    def render_help():
        content = _read_legal_file("help.md", "## Help\n\nVisit our GitHub for support.")
        st.markdown(content)
        if st.button("← Back to Dashboard", key=ui_key("help", "back")):
            st.session_state.page = "home"
            st.rerun()

    logger.info("Starting UI initialization...")
    logger.debug(f"Assets directory: {ASSETS_DIR}")
    
    icon_path = ASSETS_DIR / "mantis_logo_trans.png"
    page_icon = str(icon_path) if icon_path.exists() else "🪲"
    logger.debug(f"Icon path exists: {icon_path.exists()}, using: {page_icon}")
    
    try:
        st.set_page_config(page_title=AppConfig.APP_NAME, page_icon=page_icon, layout="wide")
        logger.info("Page config set successfully")
    except Exception as e:
        logger.error(f"Failed to set page config: {e}", exc_info=True)
        raise
    
    try:
        inject_theme()
        logger.info("Theme injected successfully")
    except Exception as e:
        logger.error(f"Failed to inject theme: {e}", exc_info=True)
        raise
    
    # Use centralized session initialization module
    from app.session_init import initialize_session_state
    try:
        initialize_session_state(st)
        logger.info("Session state initialized successfully via session_init module")
    except Exception as e:
        logger.error(f"Failed to initialize session state: {e}", exc_info=True)
        # Set absolute minimum state to prevent total failure
        st.session_state.setdefault("page", "home")
        st.session_state.setdefault("initialized", True)
        st.warning("⚠️ Failed to initialize application state. Some features may not work correctly.")

    apply_pending_widget_updates()

    theme = st.session_state.ui_theme if st.session_state.ui_theme in ("Dark", "Light") else "Dark"
    theme_tokens = {
        "Dark": {
            "bg": "#020617",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)",
            "text": "#ecfdf5",
            "muted": "#b6c3d1",
            "input_bg": "#0b1216",
            "input_border": "#166534",
            "button_bg": "linear-gradient(180deg, #0f1a15, #0b1411)",
            "button_border": "#163f2a",
            "button_hover_border": "#22c55e",
            "primary_bg": "linear-gradient(135deg, #15803d, #22c55e)",
            "primary_border": "rgba(34,197,94,0.55)",
            "primary_hover_border": "#4ade80",
            "card_bg": "linear-gradient(180deg, rgba(6,18,14,0.95), rgba(4,12,10,0.95))",
            "card_border": "#163523",
            "sidebar_bg": "linear-gradient(180deg, #020617, #07150f)",
            "sidebar_border": "#123123",
            "sidebar_title": "#7dd3a7",
            "divider": "#143023",
            "expander_border": "#1f3b2d",
            "header_gradient": "linear-gradient(135deg, #0b1216, #0f1a15)",
            "header_logo_bg": "rgba(34,197,94,0.2)",
            "header_sub": "#c7f2da",
            "shadow_strong": "0 18px 40px rgba(0,0,0,0.55)",
            "shadow_button": "0 10px 22px rgba(0,0,0,0.4)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(6,18,14,0.85), rgba(4,10,8,0.95))",
            "sidebar_brand_border": "rgba(34,197,94,0.25)",
            "sidebar_logo_bg": "rgba(34,197,94,0.12)",
            "accent": "#22c55e",
            "accent_soft": "rgba(34,197,94,0.18)",
            "accent_glow": "rgba(34,197,94,0.35)",
            "surface": "rgba(6,18,14,0.85)",
            "surface_alt": "rgba(5,14,11,0.9)",
            "success": "#22c55e",
            "warning": "#f59e0b",
        },
        "Light": {
            "bg": "#f4f6f5",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.08), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.06), transparent 40%)",
            "text": "#1a2e23",
            "muted": "#3d4f47",
            "input_bg": "#fafbfa",
            "input_border": "#6a8a7b",
            "button_bg": "linear-gradient(180deg, #fafbfa, #f0f5f2)",
            "button_border": "#6a8a7b",
            "button_hover_border": "#16a34a",
            "primary_bg": "linear-gradient(135deg, #16a34a, #15803d)",
            "primary_border": "rgba(22,163,74,0.5)",
            "primary_hover_border": "#15803d",
            "card_bg": "#fafbfa",
            "card_border": "#708a7e",
            "sidebar_bg": "linear-gradient(180deg, #eef1ef, #e4e9e6)",
            "sidebar_border": "#708378",
            "sidebar_title": "#15803d",
            "divider": "#7a8e82",
            "expander_border": "#708a7e",
            "header_gradient": "linear-gradient(135deg, #e2f3e8, #d0eddb)",
            "header_logo_bg": "#ddf0e4",
            "header_sub": "#276740",
            "shadow_strong": "0 12px 24px rgba(20,40,30,0.12)",
            "shadow_button": "0 6px 14px rgba(20,40,30,0.10)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(250,251,250,0.95), rgba(243,247,245,0.95))",
            "sidebar_brand_border": "rgba(20,40,30,0.18)",
            "sidebar_logo_bg": "rgba(22,163,74,0.10)",
            "accent": "#16a34a",
            "accent_soft": "rgba(22,163,74,0.12)",
            "accent_glow": "rgba(22,163,74,0.30)",
            "surface": "rgba(250,251,250,0.95)",
            "surface_alt": "rgba(243,247,245,0.95)",
            "success": "#15803d",
            "warning": "#b45309",
        },
    }
    tokens = theme_tokens[theme]

    st.html(
        f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400;600&family=Space+Grotesk:wght@500;700&display=swap');
    :root {{
        --mantis-bg: {tokens["bg"]};
        --mantis-bg-glow: {tokens["bg_glow"]};
        --mantis-text: {tokens["text"]};
        --mantis-muted: {tokens["muted"]};
        --mantis-input-bg: {tokens["input_bg"]};
        --mantis-input-border: {tokens["input_border"]};
        --mantis-button-bg: {tokens["button_bg"]};
        --mantis-button-border: {tokens["button_border"]};
        --mantis-button-hover-border: {tokens["button_hover_border"]};
        --mantis-primary-bg: {tokens["primary_bg"]};
        --mantis-primary-border: {tokens["primary_border"]};
        --mantis-primary-hover-border: {tokens["primary_hover_border"]};
        --mantis-card-bg: {tokens["card_bg"]};
        --mantis-card-border: {tokens["card_border"]};
        --mantis-sidebar-bg: {tokens["sidebar_bg"]};
        --mantis-sidebar-border: {tokens["sidebar_border"]};
        --mantis-sidebar-title: {tokens["sidebar_title"]};
        --mantis-divider: {tokens["divider"]};
        --mantis-expander-border: {tokens["expander_border"]};
        --mantis-header-gradient: {tokens["header_gradient"]};
        --mantis-header-logo-bg: {tokens["header_logo_bg"]};
        --mantis-header-sub: {tokens["header_sub"]};
        --mantis-shadow-strong: {tokens["shadow_strong"]};
        --mantis-shadow-button: {tokens["shadow_button"]};
        --mantis-sidebar-brand-bg: {tokens["sidebar_brand_bg"]};
        --mantis-sidebar-brand-border: {tokens["sidebar_brand_border"]};
        --mantis-sidebar-logo-bg: {tokens["sidebar_logo_bg"]};
        --mantis-accent: {tokens["accent"]};
        --mantis-accent-soft: {tokens["accent_soft"]};
        --mantis-accent-glow: {tokens["accent_glow"]};
        --mantis-surface: {tokens["surface"]};
        --mantis-surface-alt: {tokens["surface_alt"]};
        --mantis-success: {tokens["success"]};
        --mantis-warning: {tokens["warning"]};
        --mantis-space-1: 8px;
        --mantis-space-2: 16px;
        --mantis-space-3: 24px;
        --mantis-space-4: 32px;
    }}
    .stApp {{
        background-color: var(--mantis-bg);
        background-image: var(--mantis-bg-glow);
        color: var(--mantis-text);
        font-family: 'Inter', sans-serif;
    }}
    .block-container {{ padding-top: 2.6rem; padding-bottom: 2.6rem; max-width: 1380px; }}
    header[data-testid="stHeader"] {{ height: 2.6rem; }}
    h1, h2, h3 {{ letter-spacing: -0.02em; font-family: 'Space Grotesk', sans-serif; }}
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown div,
    .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label,
    .stNumberInput label, .stTextArea label {{
        color: var(--mantis-text) !important;
    }}
    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div {{
        background-color: var(--mantis-input-bg) !important;
        color: var(--mantis-text) !important;
        border: 1px solid var(--mantis-input-border) !important;
    }}
    div[data-baseweb="select"] input {{
        color: var(--mantis-text) !important;
    }}
    div[data-baseweb="select"] span {{
        color: var(--mantis-text) !important;
    }}
    div[data-baseweb="menu"] {{
        background: var(--mantis-card-bg) !important;
        border: 1px solid var(--mantis-card-border) !important;
    }}
    div[data-baseweb="option"] {{
        color: var(--mantis-text) !important;
        background: transparent !important;
    }}
    div[data-baseweb="option"]:hover {{
        background: var(--mantis-accent-soft) !important;
    }}
    .stTextArea textarea {{ background-color: var(--mantis-input-bg) !important; color: var(--mantis-text) !important; font-family: 'Crimson Pro', serif !important; font-size: 18px !important; line-height: 1.65 !important; border: 1px solid var(--mantis-input-border) !important; }}

    .mantis-muted {{ color: var(--mantis-muted); }}
    div[data-testid="stCaptionContainer"] {{ color: var(--mantis-muted); }}

    .mantis-header {{
        display:flex;
        align-items:center;
        justify-content: space-between;
        gap:14px;
        padding:18px 24px;
        border-radius:22px;
        background: var(--mantis-header-gradient);
        border: 1px solid var(--mantis-primary-border);
        margin-top: 18px;
        margin-bottom: 18px;
        box-shadow: var(--mantis-shadow-strong);
    }}
    .mantis-header-left {{
        display:flex;
        align-items:center;
        gap:14px;
    }}
    .mantis-header-right {{
        display:flex;
        gap:10px;
        align-items:center;
    }}
    .mantis-header-logo {{
        width:88px;
        height:88px;
        border-radius:18px;
        background: var(--mantis-header-logo-bg);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow:
            inset 0 0 0 1px rgba(0,0,0,0.06),
            0 0 18px var(--mantis-accent-glow);
    }}
    .mantis-header-logo img {{
        height:60px;
        width:auto;
        padding:0;
        border-radius:0;
    }}
    .mantis-header-title {{
        font-size:22px;
        font-weight:800;
        color: var(--mantis-text);
        letter-spacing: 0.01em;
    }}
    .mantis-header-sub {{
        color: var(--mantis-header-sub);
        font-size:12px;
    }}
    .mantis-header-meta {{
        display:flex;
        flex-direction:column;
        align-items:flex-end;
        gap:4px;
        font-size:12px;
        color: var(--mantis-muted);
    }}

    /* Button styles are defined centrally in assets/styles.css
       and injected via app/ui/theme.py — see the Unified Button System. */

    [data-testid="stVerticalBlock"] [data-testid="stContainer"] {{ border-radius: 16px !important; }}
    .stExpander {{ border: 1px solid var(--mantis-expander-border) !important; border-radius: 16px !important; }}
    hr {{ border-color: var(--mantis-divider) !important; }}
    section[data-testid="stSidebar"] {{ background: var(--mantis-sidebar-bg); border-right: 1px solid var(--mantis-sidebar-border); }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: var(--mantis-text); }}
    section[data-testid="stSidebar"] details summary {{
        color: var(--mantis-text) !important;
        font-weight: 600;
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-card-border);
        border-radius: 12px;
        padding: 6px 10px;
    }}
    section[data-testid="stSidebar"] details[open] {{
        margin-bottom: 8px;
    }}
    div[data-testid="stSidebarNav"] {{ display: none; }}
    div[data-testid="stToast"] {{ border-radius: 14px !important; }}

    /* --- CARD POLISH --- */
    div[data-testid="stContainer"] {{
        background: var(--mantis-card-bg);
        border-radius: 20px !important;
        padding: 22px !important;
        border: 1px solid var(--mantis-card-border) !important;
        box-shadow: var(--mantis-shadow-strong);
        margin-bottom: 18px;
    }}
    .mantis-pill {{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:6px 10px;
        border-radius:999px;
        font-size:12px;
        background: var(--mantis-accent-soft);
        border: 1px solid var(--mantis-accent-glow);
        color: var(--mantis-text);
        letter-spacing: 0.02em;
    }}
    .mantis-hero-caption {{
        font-size:12px;
        color: var(--mantis-muted);
        margin-top:4px;
    }}
    div[data-testid="stContainer"] h3 {{
        margin-top: 0;
        margin-bottom: 12px;
        color: var(--mantis-text);
    }}
    .mantis-hero {{
        background: var(--mantis-surface);
        border-radius: 22px;
        padding: 22px 24px;
        border: 1px solid var(--mantis-card-border);
        box-shadow: var(--mantis-shadow-strong);
    }}
    .mantis-hero-title {{
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 6px;
    }}
    .mantis-hero-sub {{
        color: var(--mantis-muted);
        font-size: 14px;
    }}
    .mantis-page-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
    }}
    .mantis-page-title {{
        font-size: 26px;
        font-weight: 700;
        margin: 0;
        color: var(--mantis-text);
    }}
    .mantis-page-sub {{
        color: var(--mantis-muted);
        margin-top: 4px;
        font-size: 14px;
    }}
    .mantis-tag {{
        display:inline-flex;
        align-items:center;
        gap:6px;
        padding:6px 12px;
        border-radius:999px;
        font-size:12px;
        font-weight:600;
        background: var(--mantis-accent-soft);
        color: var(--mantis-text);
        border: 1px solid var(--mantis-accent-glow);
    }}
    .mantis-kpi-grid {{
        display:grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap:12px;
        margin-top: 14px;
    }}
    .mantis-kpi-card {{
        padding: 12px 14px;
        border-radius: 16px;
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-kpi-label {{
        font-size:11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mantis-muted);
        margin-bottom: 6px;
    }}
    .mantis-kpi-value {{
        font-size:20px;
        font-weight:700;
    }}
    .mantis-section-title {{
        font-size:20px;
        font-weight:700;
        margin-bottom: 6px;
    }}
    .mantis-section-header {{
        display:flex;
        align-items:flex-end;
        justify-content:space-between;
        gap:16px;
        margin: 6px 0 14px;
    }}
    .mantis-section-caption {{
        color: var(--mantis-muted);
        font-size: 13px;
    }}
    .mantis-soft {{
        background: var(--mantis-surface-alt);
        border-radius: 16px;
        padding: 14px;
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-stat-tile {{
        display:flex;
        flex-direction:column;
        gap:6px;
        padding: 12px 14px;
        border-radius: 16px;
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-stat-icon {{
        width: 30px;
        height: 30px;
        border-radius: 10px;
        display:flex;
        align-items:center;
        justify-content:center;
        background: var(--mantis-accent-soft);
        border: 1px solid var(--mantis-accent-glow);
        font-size: 14px;
    }}
    .mantis-stat-label {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--mantis-muted);
    }}
    .mantis-stat-value {{
        font-size: 20px;
        font-weight: 700;
        color: var(--mantis-text);
    }}
    .mantis-stat-help {{
        font-size: 12px;
        color: var(--mantis-muted);
    }}

    /* --- SIDEBAR POLISH --- */
    section[data-testid="stSidebar"] {{
        background: var(--mantis-sidebar-bg);
        border-right: 1px solid var(--mantis-sidebar-border);
    }}
    section[data-testid="stSidebar"] h3 {{
        color: var(--mantis-sidebar-title);
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-size: 12px;
    }}
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {{
        color: var(--mantis-text);
    }}


    /* --- SIDEBAR BRAND --- */
    .mantis-sidebar-brand{{
        display:flex;
        gap:12px;
        align-items:center;
        padding:14px 12px 12px 12px;
        margin: 4px 8px 10px 8px;
        border-radius: 16px;
        background: var(--mantis-sidebar-brand-bg);
        border: 1px solid var(--mantis-sidebar-brand-border);
        box-shadow: var(--mantis-shadow-button);
    }}
    .mantis-sidebar-logo{{
        width:70px;
        height:70px;
        border-radius: 14px;
        background: var(--mantis-sidebar-logo-bg);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow: inset 0 0 0 1px rgba(0,0,0,0.05), 0 6px 16px rgba(0,0,0,0.2);
        flex: 0 0 auto;
    }}
    .mantis-sidebar-logo img{{
        height:48px;
        width:auto;
        display:block;
    }}
    .mantis-avatar {{
        height:44px;
        width:44px;
        border-radius:50%;
        background: var(--mantis-surface-alt);
        color: var(--mantis-text);
        display:flex;
        align-items:center;
        justify-content:center;
        font-weight:700;
        font-size:0.9rem;
        border: 1px solid var(--mantis-card-border);
    }}
    .mantis-logo-fallback {{
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--mantis-sidebar-title);
    }}
    .mantis-sidebar-title{{
        font-weight:800;
        font-size:14px;
        color: var(--mantis-text);
        line-height:1.1;
    }}
    .mantis-sidebar-sub{{
        font-size:12px;
        color: var(--mantis-muted);
        margin-top:2px;
        line-height:1.1;
    }}
    .mantis-banner img {{
        max-height: 180px;
        object-fit: contain;
    }}

    /* --- NAV RADIO STYLE --- */
    div[role="radiogroup"] > label {{
        background: var(--mantis-surface-alt);
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid var(--mantis-card-border);
        margin-bottom: 8px;
    }}
    div[role="radiogroup"] > label span {{
        color: var(--mantis-text);
    }}
    div[role="radiogroup"] > label:has(input:checked) {{
        border-color: var(--mantis-accent);
        box-shadow: 0 0 0 1px var(--mantis-accent-glow);
    }}
</style>
    """,
    )

    # --- BRAND HEADER (UI only) ---
    header_logo_b64 = asset_base64("mantis_logo_trans.png")
    header_logo_html = (
        f'<img src="data:image/png;base64,{header_logo_b64}" alt="MANTIS logo" />'
        if header_logo_b64
        else '<span class="mantis-logo-fallback">M</span>'
    )
    st.html(
        f"""
        <div class="mantis-header">
            <div class="mantis-header-left">
                <div class="mantis-header-logo">
                    {header_logo_html}
                </div>
                <div style="line-height:1.15;">
                    <div class="mantis-header-title">
                        MANTIS Studio — v{AppConfig.VERSION}
                    </div>
                    <div class="mantis-header-sub">
                        Modular AI Narrative Text Intelligence System
                    </div>
                </div>
            </div>
            <div class="mantis-header-right">
                <span class="mantis-pill">Workspace</span>
            </div>
        </div>
        """,
    )

    logger.info("Initializing session state...")
    
    # Load app configuration for session state initialization
    config_data = load_app_config()
    logger.debug(f"Loaded app config: {list(config_data.keys())}")
    
    init_state("user_id", None)
    init_state("projects_dir", None)
    init_state("project", None)
    init_state("page", "home")
    logger.debug(f"Default page set to: {st.session_state.page}")
    init_state("auto_save", True)
    init_state("ghost_text", "")
    init_state("pending_improvement_text", "")
    init_state("pending_improvement_meta", {})
    init_state("chapter_text_prev", {})
    init_state("chapter_drafts", [])
    init_state("chapters", [])
    init_state("chapters_project_id", None)
    init_state("active_chapter_id", None)
    init_state("editor_improve__copy_buffer", "")
    init_state("first_run", True)
    init_state("is_premium", True)
    init_state("pending_action", None)
    st.session_state.setdefault("ai_keys", {})
    logger.info("Session state initialization complete")

    def _resolve_api_key(provider: str, default_value: str) -> str:
        session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
        if session_key:
            return session_key
        config_key = config_data.get(f"{provider}_api_key", "")
        if config_key:
            return config_key
        return default_value or ""
    init_state(
        "openai_base_url",
        config_data.get("openai_base_url", AppConfig.OPENAI_API_URL),
    )
    init_state("ai_provider", config_data.get("ai_provider", "groq"))
    init_state("ai_session_keys", {
        "openai": config_data.get("openai_api_key", ""),
        "groq": config_data.get("groq_api_key", ""),
    })
    init_state("openai_key_input", "")
    init_state("openai_model", config_data.get("openai_model", AppConfig.OPENAI_MODEL))
    init_state("openai_model_list", [])
    init_state("openai_model_tests", {})
    init_state("ui_theme", config_data.get("ui_theme", "Dark"))
    init_state("groq_base_url", config_data.get("groq_base_url", AppConfig.GROQ_API_URL))
    init_state("groq_key_input", "")
    init_state("groq_model", config_data.get("groq_model", AppConfig.DEFAULT_MODEL))
    init_state("groq_model_list", [])
    init_state("groq_model_tests", {})
    init_state("_force_nav", False)

    AppConfig.GROQ_API_URL = st.session_state.groq_base_url
    AppConfig.DEFAULT_MODEL = st.session_state.groq_model
    AppConfig.OPENAI_API_URL = st.session_state.openai_base_url
    AppConfig.OPENAI_MODEL = st.session_state.openai_model

    def debug_enabled() -> bool:
        try:
            secrets = st.secrets
        except Exception:
            secrets = {}
        if isinstance(secrets, dict):
            return bool(secrets.get("DEBUG")) or bool(st.session_state.get("debug"))
        try:
            return bool(secrets["DEBUG"]) or bool(st.session_state.get("debug"))
        except Exception:
            return bool(st.session_state.get("debug"))

    def open_legal_page() -> None:
        st.session_state.page = "legal"
        st.rerun()

    def persist_project(project: "Project", *, action: str = "save") -> bool:
        """Save project to local storage."""
        path = project.save()
        if not path:
            logger.error("persist_project failed for '%s' (action=%s)", project.title, action)
            try:
                st.toast("⚠️ Save failed — check file permissions and disk space.", icon="⚠️")
            except Exception as e:
                st.error(f"Save failed for '{project.title}': {e}")
            return False
        # Remember the last active project so it can be restored after refresh
        config = load_app_config()
        config["last_project_path"] = path
        save_app_config(config)
        return True

    def check_and_show_whats_new() -> None:
        """Check if app version has changed and show What's New notification."""
        config = load_app_config()
        last_seen_version = config.get("last_seen_version", "")
        current_version = AppConfig.VERSION

        # Check if this is a new version
        if last_seen_version and last_seen_version != current_version:
            # Show What's New banner
            with st.container(border=True):
                st.markdown("### 🎉 What's New in Mantis Studio")
                st.markdown(f"""
                **Version {current_version} is now available!** (Updated from {last_seen_version})
                
                **What Changed:**
                - 🔔 **NEW**: You can now see what changed between versions!
                  - This notification system was added to address user feedback
                  - Version updates are now visible and transparent
                - 📝 **Improved**: Complete changelog documentation for all recent versions
                - 📊 **Enhanced**: Better version tracking and update notifications
                
                **Why This Matters:**
                - You previously reported: "merged 4 times now with no changed from users point of view"
                - This fix ensures you always know when the app updates and what's new
                - All future updates will show clear release notes
                
                👉 **See the [full changelog](https://github.com/bigmanjer/Mantis-Studio/blob/main/docs/CHANGELOG.md) for complete details**
                """)
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("✅ Got it, thanks!", use_container_width=True, type="primary"):
                        # Update last seen version
                        config["last_seen_version"] = current_version
                        save_app_config(config)
                        st.rerun()
                with col2:
                    if st.button("📖 View Full Changelog", use_container_width=True):
                        webbrowser.open("https://github.com/bigmanjer/Mantis-Studio/blob/main/docs/CHANGELOG.md")
                        config["last_seen_version"] = current_version
                        save_app_config(config)
                        st.rerun()
        elif not last_seen_version:
            # First time user - set version silently
            config["last_seen_version"] = current_version
            save_app_config(config)

    def render_welcome_banner(context: str) -> None:
        """Show helpful context-aware guidance for first-time users."""
        # Show What's New banner if version changed
        if context == "home":
            check_and_show_whats_new()

        if context == "home" and st.session_state.get("first_run", True):
            with st.container(border=True):
                st.markdown("### 👋 Welcome to Mantis Studio!")
                st.markdown(f"""
                **Your AI-powered writing environment is ready.**
                
                **Getting Started:**
                - 📁 Click **Projects** in the sidebar to create your first story
                - 📖 Check out the [Getting Started Guide]({AppConfig.GETTING_STARTED_URL}) for a complete walkthrough
                - 💡 Everything auto-saves locally
                
                **Quick Tips:**
                - Use **Outline** to plan your story structure
                - **Chapters** is your writing workspace  
                - **World Bible** keeps track of characters and lore
                - **Export** to get your work as a Word doc or PDF
                """)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 Create My First Project", use_container_width=True, type="primary"):
                        st.session_state.first_run = False
                        st.session_state.page = "projects"
                        st.rerun()
                with col2:
                    if st.button("✅ Got it, don't show again", use_container_width=True):
                        st.session_state.first_run = False
                        st.rerun()
        elif st.session_state.get("first_run", True) and context != "home":
            st.info(f"💡 **Tip**: Check out the [Getting Started Guide]({AppConfig.GETTING_STARTED_URL}) for help using this section.", icon="💡")

    def render_app_footer() -> None:
        render_footer(AppConfig.VERSION)

    def _render_header_bar(recent_projects: List[Dict[str, Any]]) -> None:
        logo_bytes = load_asset_bytes("mantis_logo_trans.png")
        left_col, mid_col, right_col = st.columns([1.6, 2.2, 1.2], vertical_alignment="center")
        with left_col:
            if logo_bytes:
                st.image(logo_bytes, width=42)
            st.markdown("### MANTIS Studio")
            st.caption("Modular AI Narrative Text Intelligence System")

        with mid_col:
            options = ["No project selected"]
            project_map = {"No project selected": None}
            for entry in recent_projects:
                meta = entry.get("meta", {})
                title = meta.get("title") or os.path.basename(entry.get("path", "Untitled"))
                label = f"{title}"
                options.append(label)
                project_map[label] = entry.get("path")
            current_label = "No project selected"
            if st.session_state.project:
                current_label = st.session_state.project.title or current_label
            selection = st.selectbox(
                "Current project",
                options,
                index=options.index(current_label) if current_label in options else 0,
                help="Quickly jump between recent projects.",
            )
            selected_path = project_map.get(selection)
            if selected_path and (not st.session_state.project or st.session_state.project.filepath != selected_path):
                loaded = load_project_safe(selected_path, context="project selector")
                if loaded:
                    st.session_state.project = loaded
                    st.session_state.page = "chapters"
                    st.rerun()

        with right_col:
            tags = []
            if st.session_state.project:
                tags.append("Project active")
            render_tag_list(tags)

    # Local-first: use the default projects directory
    if not st.session_state.get("projects_dir"):
        st.session_state.projects_dir = AppConfig.PROJECTS_DIR
        logger.info(f"Projects directory set to: {AppConfig.PROJECTS_DIR}")

    # Restore the last active project from config if none is loaded
    if not st.session_state.get("project"):
        last_path = config_data.get("last_project_path", "")
        if last_path and os.path.isfile(last_path):
            try:
                st.session_state.project = Project.load(last_path)
                logger.info(f"Restored last project: {st.session_state.project.title}")
            except Exception as e:
                logger.warning("Failed to restore last project: %s - %s", last_path, e, exc_info=True)
    
    # Startup diagnostics - run once per session
    if not st.session_state.get("_startup_diagnostics_run"):
        st.session_state._startup_diagnostics_run = True
        logger.info("=" * 60)
        logger.info("STARTUP DIAGNOSTICS")
        logger.info("=" * 60)
        logger.info(f"App Version: {AppConfig.VERSION}")
        logger.info(f"Python Version: {sys.version.split()[0]}")
        logger.info(f"Streamlit Version: {st.__version__}")
        logger.info(f"Projects Directory: {AppConfig.PROJECTS_DIR}")
        logger.info(f"Projects Dir Exists: {os.path.exists(AppConfig.PROJECTS_DIR)}")
        logger.info(f"Config Path: {AppConfig.CONFIG_PATH}")
        logger.info(f"Config Exists: {os.path.exists(AppConfig.CONFIG_PATH)}")
        logger.info(f"Assets Directory: {ASSETS_DIR}")
        logger.info(f"Assets Dir Exists: {ASSETS_DIR.exists()}")
        logger.info(f"Current Page: {st.session_state.page}")
        logger.info(f"Project Loaded: {st.session_state.project is not None}")
        if st.session_state.project:
            logger.info(f"  - Project Title: {st.session_state.project.title}")
            logger.info(f"  - Project Path: {st.session_state.project.filepath}")
        logger.info(f"Session State Keys: {len(st.session_state.keys())} total")
        logger.info(f"Debug Mode: {debug_enabled()}")
        logger.info("=" * 60)
        logger.info("STARTUP DIAGNOSTICS COMPLETE - App initialized successfully")
        logger.info("=" * 60)

    # Reliable navigation rerun (avoids Streamlit edge cases when returning early)
    if st.session_state.get("_force_nav"):
        st.session_state._force_nav = False
        st.rerun()

    def get_ai_model() -> str:
        provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
        if provider == "openai":
            return st.session_state.get("openai_model", AppConfig.OPENAI_MODEL)
        return st.session_state.get("groq_model", AppConfig.DEFAULT_MODEL)

    def get_active_key_status() -> tuple[str, str, str]:
        provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
        key, source = get_effective_key(provider, st.session_state.get("user_id"))
        return provider, key, source

    def save_p():
        if st.session_state.project and st.session_state.auto_save:
            persist_project(st.session_state.project)

    def get_active_projects_dir() -> Optional[str]:
        """Return the active projects directory (local-first, single user)."""
        return st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR

    def resume_pending_action() -> None:
        pending = st.session_state.get("pending_action")
        if not pending:
            return
        action = pending.get("action")
        payload = pending.get("payload") or {}
        return_to = pending.get("return_to") or "home"
        st.session_state.pending_action = None

        if action == "create_project":
            p = Project.create(
                payload.get("title") or "Untitled Project",
                author=payload.get("author", ""),
                genre=payload.get("genre", ""),
                storage_dir=get_active_projects_dir() or AppConfig.PROJECTS_DIR,
            )
            p.save()
            st.session_state.project = p
        elif action == "import_project":
            text = payload.get("text") or ""
            p = Project.create("Imported Project", storage_dir=get_active_projects_dir() or AppConfig.PROJECTS_DIR)
            p.import_text_file(text)
            active_provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
            active_key, _ = get_effective_key(active_provider, st.session_state.get("user_id"))
            if active_key and get_ai_model():
                p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
            p.save()
            st.session_state.project = p
        elif action == "save_project":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Project saved.")
        elif action == "save_outline":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Outline saved.")
        elif action == "save_chapter":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Chapter saved.")
        elif action == "export_project":
            if st.session_state.project:
                st.session_state.project.save()
                st.session_state.export_project_path = st.session_state.project.filepath
        elif action == "save_app_settings":
            save_app_settings()
        elif action == "delete_project":
            delete_path = payload.get("path")
            if delete_path:
                Project.delete_file(delete_path)
                _bump_projects_refresh()

        st.session_state.page = return_to
        st.rerun()

    if st.session_state.get("pending_action"):
        resume_pending_action()


    def load_project_safe(path: str, context: str = "project") -> Optional["Project"]:
        try:
            return Project.load(path)
        except Exception:
            logger.warning("Failed to load %s: %s", context, path, exc_info=True)
            st.error("We couldn't open that project file. It may be missing or corrupted.")
            return None

    def show_api_key_notice(action: str) -> None:
        """Display a notice that an API key is required for the specified action.
        
        Args:
            action: Description of what the user is trying to do (e.g., "scan entities", "generate outlines")
        """
        provider, _, _ = get_active_key_status()
        st.info(f"Add a {_provider_label(provider)} API key in AI Settings to {action}.")

    def get_ai_button_help(
        cooldown_seconds: int,
        has_api_key: bool,
        action_description: str,
    ) -> str:
        """Generate contextual help text for AI-powered buttons.
        
        Args:
            cooldown_seconds: Remaining cooldown time in seconds (0 if no cooldown)
            has_api_key: Whether the user has configured an API key
            action_description: What the button does (e.g., "generate a chapter outline")
        
        Returns:
            Appropriate help text explaining the button's state
        """
        if cooldown_seconds > 0:
            return f"Available in {cooldown_seconds} seconds to prevent API overuse"
        elif not has_api_key:
            provider, _, _ = get_active_key_status()
            return f"Configure {_provider_label(provider)} API key in AI Settings to use this feature"
        else:
            return f"AI will {action_description}"

    def render_page_header(
        title: str,
        subtitle: str,
        primary_label: Optional[str] = None,
        primary_action: Optional[Callable[[], None]] = None,
        primary_disabled: bool = False,
        primary_help: Optional[str] = None,
        secondary_label: Optional[str] = None,
        secondary_action: Optional[Callable[[], None]] = None,
        secondary_disabled: bool = False,
        secondary_help: Optional[str] = None,
        tag: Optional[str] = None,
        key_prefix: str = "page_header",
    ) -> None:
        header_bar(title, subtitle, pill=tag)
        action_cols = st.columns(2)
        with action_cols[0]:
            if primary_label and primary_action:
                if st.button(
                    primary_label,
                    type="primary",
                    use_container_width=True,
                    key=f"{key_prefix}__primary",
                    disabled=primary_disabled,
                    help=primary_help,
                ):
                    primary_action()
        with action_cols[1]:
            if secondary_label and secondary_action:
                if st.button(
                    secondary_label,
                    use_container_width=True,
                    key=f"{key_prefix}__secondary",
                    disabled=secondary_disabled,
                    help=secondary_help,
                ):
                    secondary_action()

    @st.cache_data(show_spinner=False)
    def _cached_models(base_url: str, api_key: str) -> List[str]:
        return AIEngine(base_url=base_url).probe_models(api_key)

    def refresh_models():
        groq_key, _ = get_effective_key("groq", st.session_state.get("user_id"))
        st.session_state.groq_model_list = _cached_models(
            st.session_state.groq_base_url,
            groq_key,
        ) or []

    def refresh_openai_models():
        openai_key, _ = get_effective_key("openai", st.session_state.get("user_id"))
        st.session_state.openai_model_list = _cached_models(
            st.session_state.openai_base_url,
            openai_key,
        ) or []

    def save_app_settings():
        # Merge with existing config to preserve saved API keys
        data = load_app_config()
        data.update({
            "ai_provider": st.session_state.ai_provider,
            "groq_base_url": st.session_state.groq_base_url,
            "groq_model": st.session_state.groq_model,
            "openai_base_url": st.session_state.openai_base_url,
            "openai_model": st.session_state.openai_model,
            "ui_theme": st.session_state.ui_theme,
            "daily_word_goal": int(st.session_state.daily_word_goal),
            "weekly_sessions_goal": int(st.session_state.weekly_sessions_goal),
            "focus_minutes": int(st.session_state.focus_minutes),
            "activity_log": list(st.session_state.activity_log),
        })
        save_app_config(data)
        st.toast("Settings saved.")

    def _today_str() -> str:
        return datetime.date.today().isoformat()

    def _parse_day(day: str) -> Optional[datetime.date]:
        try:
            return datetime.date.fromisoformat(day)
        except ValueError:
            return None

    def _log_activity():
        today = _today_str()
        log = set(st.session_state.activity_log)
        log.add(today)
        st.session_state.activity_log = sorted(log)
        save_app_settings()

    def _weekly_activity_count() -> int:
        today = datetime.date.today()
        cutoff = today - datetime.timedelta(days=6)
        count = 0
        for day in st.session_state.activity_log:
            parsed = _parse_day(day)
            if parsed and parsed >= cutoff:
                count += 1
        return count

    def _activity_streak() -> int:
        if not st.session_state.activity_log:
            return 0
        days = sorted(
            {d for d in (_parse_day(day) for day in st.session_state.activity_log) if d}
        )
        if not days:
            return 0
        streak = 0
        cursor = datetime.date.today()
        day_set = set(days)
        while cursor in day_set:
            streak += 1
            cursor -= datetime.timedelta(days=1)
        return streak

    def _activity_series() -> List[Dict[str, Any]]:
        today = datetime.date.today()
        labels = []
        counts = []
        log_set = set(st.session_state.activity_log)
        for offset in range(6, -1, -1):
            day = today - datetime.timedelta(days=offset)
            labels.append(day.strftime("%a"))
            counts.append(1 if day.isoformat() in log_set else 0)
        return [{"day": label, "sessions": count} for label, count in zip(labels, counts)]

    def _cooldown_remaining(action_key: str, cooldown_s: int = 8) -> int:
        cooldowns = st.session_state.setdefault("action_cooldowns", {})
        last_ts = cooldowns.get(action_key, 0)
        remaining = max(0, cooldown_s - (time.time() - last_ts))
        return int(round(remaining))

    def _mark_action(action_key: str) -> None:
        cooldowns = st.session_state.setdefault("action_cooldowns", {})
        cooldowns[action_key] = time.time()

    @st.cache_data(show_spinner=False)
    def _load_recent_projects(active_dir: Optional[str], refresh_token: int) -> List[Dict[str, Any]]:
        if not active_dir or not os.path.exists(active_dir):
            return []
        files = sorted(
            [f for f in os.listdir(active_dir) if f.endswith(".json")],
            key=lambda x: os.path.getmtime(os.path.join(active_dir, x)),
            reverse=True,
        )
        projects = []
        for filename in files:
            full_path = os.path.join(active_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                projects.append({"path": full_path, "meta": meta})
            except Exception:
                logger.warning("Failed to load project metadata: %s", full_path, exc_info=True)
        return projects

    def _bump_projects_refresh() -> None:
        st.session_state.projects_refresh_token += 1

    def _project_snapshot(meta: Dict[str, Any]) -> Dict[str, Any]:
        chapters = meta.get("chapters", {}) or {}
        chapter_list = list(chapters.values())
        word_count = sum(int(c.get("word_count") or 0) for c in chapter_list)
        return {
            "title": meta.get("title") or "Untitled Project",
            "genre": meta.get("genre") or "General Fiction",
            "chapters": len(chapter_list),
            "words": word_count,
            "modified_at": meta.get("last_modified") or meta.get("modified_at"),
        }

    FALLBACK_PROJECT_GENRES = ["Fantasy", "Adventure"]
    MAX_DRAFT_EXCERPT_LENGTH = 600
    AI_ERROR_MARKERS = (
        "not configured",
        "generation failed",
        "response empty",
        "error",
    )

    def _format_genre_list(genres: List[str]) -> str:
        return " · ".join(genres)

    def _parse_genre_list(raw: str) -> List[str]:
        cleaned = re.sub(r"(?i)^(genres?)[:\s-]*", "", (raw or "")).strip()
        if not cleaned:
            return []
        cleaned = cleaned.replace("|", ",")
        parts = re.split(r"[,\n·/]+", cleaned)
        return [part.strip() for part in parts if part.strip()]

    def _ai_generation_available() -> bool:
        provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
        key, _ = get_effective_key(provider, st.session_state.get("user_id"))
        model = get_ai_model()
        if not key or not model:
            return False
        base_url = _get_provider_base_url(provider)
        try:
            if provider == "openai":
                ok, _ = test_openai_model(base_url, key, model)
            else:
                ok, _ = test_groq_model(base_url, key, model)
            return ok
        except Exception:
            logger.warning(
                "AI availability check failed for provider=%s model=%s",
                provider,
                model,
                exc_info=True,
            )
            return False

    def _build_project_context(
        context: str,
        title: str,
        genre: str,
        author: str,
        draft_excerpt: str,
    ) -> str:
        parts = []
        if context:
            parts.append(context.strip())
        if title:
            parts.append(f"Title idea: {title}")
        if genre:
            parts.append(f"Genre hints: {genre}")
        if author:
            parts.append(f"Author: {author}")
        safe_excerpt = draft_excerpt.strip()
        if safe_excerpt:
            parts.append(f"Draft excerpt: {safe_excerpt[:MAX_DRAFT_EXCERPT_LENGTH]}")
        return "\n".join(parts) if parts else "A new creative writing project."

    def _ai_response_has_error(raw: str) -> bool:
        low = (raw or "").lower()
        return any(marker in low for marker in AI_ERROR_MARKERS)

    def _generate_project_title(context: str, genre_hint: str, model: str, provider: str) -> str:
        prompt = (
            "You are initializing a new creative writing project.\n"
            f"PROJECT CONTEXT:\n{context}\n\n"
            f"GENRE HINTS: {genre_hint or 'Open'}\n"
            "TASK: Generate a creative, relevant project title.\n"
            "RULES: Return ONLY the title. No quotes. No prefixes."
        )
        response = AIEngine(provider=provider).generate(prompt, model)
        raw = (response.get("text", "") or "").strip()
        if _ai_response_has_error(raw):
            return ""
        clean = re.sub(r"(?i)^(title|project title|suggested title)[:\s-]*", "", raw).strip()
        clean = clean.replace('"', "").replace("'", "").strip()
        return clean.splitlines()[0].strip() if clean else ""

    def _generate_project_genres(context: str, title: str, model: str, provider: str) -> List[str]:
        prompt = (
            "You are initializing a new creative writing project.\n"
            f"PROJECT CONTEXT:\n{context}\n\n"
            f"TITLE: {title or 'New Project'}\n"
            "TASK: Suggest 2-4 genres that fit this project.\n"
            "RULES: Return ONLY a comma-separated list of genres."
        )
        response = AIEngine(provider=provider).generate(prompt, model)
        raw = (response.get("text", "") or "").strip()
        if _ai_response_has_error(raw):
            return []
        raw = raw.replace('"', "").replace("'", "").strip()
        return _parse_genre_list(raw)

    def _resolve_project_seed(
        title: str,
        genre: str,
        author: str,
        context: str = "",
        draft_excerpt: str = "",
    ) -> tuple[str, str, List[str], bool]:
        final_title = (title or "").strip()
        final_genre = (genre or "").strip()
        ai_used = False

        needs_title = not final_title
        needs_genre = not final_genre
        if needs_title or needs_genre:
            ai_available = _ai_generation_available()
            if ai_available:
                provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
                model = get_ai_model()
                context_text = _build_project_context(
                    context,
                    final_title,
                    final_genre,
                    author,
                    draft_excerpt,
                )
                if needs_title:
                    generated_title = _generate_project_title(context_text, final_genre, model, provider)
                    if generated_title:
                        final_title = generated_title
                        ai_used = True
                if needs_genre:
                    generated_genres = _generate_project_genres(context_text, final_title, model, provider)
                    if generated_genres:
                        final_genre = _format_genre_list(generated_genres)
                        ai_used = True

        if not final_title:
            final_title = _random_project_title()
        if not final_genre:
            final_genre = _random_project_genres()

        genre_list = _parse_genre_list(final_genre) or list(FALLBACK_PROJECT_GENRES)
        return final_title, final_genre, genre_list, ai_used

    def _random_project_title() -> str:
        adjectives = [
            "Ashen",
            "Verdant",
            "Crimson",
            "Celestial",
            "Obsidian",
            "Luminous",
            "Forgotten",
            "Gilded",
            "Veiled",
            "Hollow",
            "Radiant",
            "Stormbound",
            "Ivory",
            "Eclipsed",
            "Thorned",
            "Mythic",
        ]
        nouns = [
            "Crown",
            "Archive",
            "Sanctum",
            "Labyrinth",
            "Harbor",
            "Citadel",
            "Oath",
            "Chronicle",
            "Constellation",
            "Axiom",
            "Ember",
            "Signal",
            "Throne",
            "Vesper",
            "Pulse",
            "Emissary",
        ]
        suffixes = [
            "of Hollowlight",
            "of the Verdant Sea",
            "of the Last Meridian",
            "of Emberglass",
            "of the Drowned Sky",
            "of Ironfall",
            "of the Crystal District",
            "of Midnight Bloom",
            "of the Sunken Choir",
            "of Starward",
        ]
        return f"The {random.choice(adjectives)} {random.choice(nouns)} {random.choice(suffixes)}"

    def _random_project_genres() -> str:
        genres = [
            "Solarpunk",
            "Mythic Fantasy",
            "Cosmic Horror",
            "Techno-Thriller",
            "Romantic Suspense",
            "Gaslamp Adventure",
            "Urban Fantasy",
            "Dark Academia",
            "Political Intrigue",
            "Epic Fantasy",
            "Noir Mystery",
            "Found Family",
            "Post-Apocalyptic",
            "Speculative Romance",
            "Spy Drama",
            "Weird Western",
        ]
        genre_count = min(4, len(genres))
        picks = random.sample(genres, k=genre_count)
        return " · ".join(picks)

    def test_groq_connection(base_url: str, api_key: str) -> bool:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def test_openai_connection(base_url: str, api_key: str) -> bool:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def fetch_groq_models(base_url: str, api_key: str) -> tuple[List[str], str]:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return models, ""
        except Exception as exc:
            return [], str(exc)

    def fetch_openai_models(base_url: str, api_key: str) -> tuple[List[str], str]:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return models, ""
        except Exception as exc:
            return [], str(exc)

    def test_groq_model(base_url: str, api_key: str, model: str) -> tuple[bool, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def test_openai_model(base_url: str, api_key: str, model: str) -> tuple[bool, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def _queue_world_bible_suggestion(item: Dict[str, Any]) -> None:
        from app.services.world_bible_merge import classify_suggestion
        queue = st.session_state.setdefault("world_bible_review", [])
        # Classify against the live project when available
        p = st.session_state.get("project")
        if p is not None:
            item = classify_suggestion(p, item)
            if item.get("type") == "duplicate":
                return
        aliases = item.get("novel_aliases") or item.get("aliases") or []
        if not isinstance(aliases, list):
            aliases = [str(aliases)]
        normalized_aliases = []
        for alias in aliases:
            clean = str(alias).strip()
            if not clean:
                continue
            normalized_aliases.append(Project._normalize_entity_name(clean))
        alias_key = ",".join(sorted({a for a in normalized_aliases if a}))
        key = (
            f"{Project._normalize_category(item.get('category'))}|"
            f"{Project._normalize_entity_name(item.get('name'))}|"
            f"{alias_key}|"
            f"{(item.get('description') or '').strip().lower()}|"
            f"{item.get('type', 'new')}"
        )
        existing_keys = {q.get("_key") for q in queue}
        if key in existing_keys:
            return
        item["_key"] = key
        queue.append(item)

    def extract_entities_ui(text: str, label: str):
        """Scan text for entities and update the World Bible.

        Uses Project.upsert_entity fuzzy matching so that abbreviations, nicknames,
        or slightly different spellings merge into existing entries instead of
        creating duplicates.
        """
        provider, active_key, _ = get_active_key_status()
        if not active_key:
            show_api_key_notice("scan entities")
            return
        last_scan = st.session_state.get("last_entity_scan")
        if last_scan and (time.time() - last_scan) < 15:
            st.warning("Please wait a few seconds before running another entity scan.")
            return
        model = get_ai_model()
        raw_text = text or ""
        p = st.session_state.project

        try:
            ents = AnalysisEngine.extract_entities(raw_text, model)
        except Exception:
            logger.warning("Entity extraction failed for %s", label, exc_info=True)
            st.error("Entity scan failed. Please check your AI settings and try again.")
            return
        total_detected = len(ents)
        added = 0
        matched = 0
        flagged = 0
        suggested = 0

        for e in ents:
            name = (e.get("name") or "").strip()
            category = (e.get("category") or "").strip()
            if not name or not category:
                continue

            desc = (e.get("description") or "").strip()
            aliases = e.get("aliases") or []
            try:
                confidence = float(e.get("confidence")) if e.get("confidence") is not None else 0.0
            except (TypeError, ValueError):
                confidence = 0.0

            if confidence < AppConfig.WORLD_BIBLE_CONFIDENCE:
                existing = p.find_entity_match(
                    name,
                    category,
                    aliases=aliases if isinstance(aliases, list) else None,
                )
                if existing and desc:
                    _queue_world_bible_suggestion(
                        {
                            "type": "update",
                            "entity_id": existing.id,
                            "name": existing.name,
                            "category": existing.category,
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        }
                    )
                else:
                    _queue_world_bible_suggestion(
                        {
                            "type": "new",
                            "name": name,
                            "category": Project._normalize_category(category),
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        }
                    )
                flagged += 1
                continue

            ent, status = p.upsert_entity(
                name,
                category,
                desc,
                aliases=aliases if isinstance(aliases, list) else None,
                allow_merge=False,
                allow_alias=True,
            )
            if ent is None:
                continue

            if status == "created":
                added += 1
            else:
                matched += 1
                if desc:
                    _queue_world_bible_suggestion(
                        {
                            "type": "update",
                            "entity_id": ent.id,
                            "name": ent.name,
                            "category": ent.category,
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        }
                    )
                    suggested += 1

        persist_project(p)
        st.session_state["last_entity_scan"] = time.time()

        if added > 0 or matched > 0 or flagged > 0:
            summary = [f"{added} new", f"{matched} existing", f"{flagged} flagged"]
            if suggested:
                summary.append(f"{suggested} suggested updates")
            st.toast(f"World Bible updated ✓ ({', '.join(summary)})", icon="🌍")
        else:
            if total_detected > 0:
                st.toast("Detected entities, but they all matched existing entries.", icon="🤷")
            else:
                st.toast("No entities detected in this text.", icon="🤷")

    query = st.query_params.get("page")
    if query in {
        "home", "projects", "outline", "chapters", "world", "export", "ai",
        "privacy", "terms", "copyright", "cookie", "legal", "help",
    }:
        st.session_state.page = query
        st.query_params.clear()
        st.rerun()
        return

    def render_ai_settings():
        # Enhanced page header
        enhanced_page_header(
            title="AI Configuration",
            subtitle="Configure AI providers and API keys for intelligent writing assistance",
            icon="🤖",
            breadcrumbs=["Home", "Settings", "AI Configuration"]
        )
        
        # Add helpful guidance
        help_tooltip(
            text="MANTIS Studio supports multiple AI providers. Configure at least one provider to unlock AI-assisted features like outline generation, chapter writing, and world-building.",
            title="Getting Started with AI"
        )
        
        def refresh_all_models() -> None:
            st.cache_data.clear()
            refresh_models()
            refresh_openai_models()
            st.toast("Model list refreshed")

        def save_settings_action() -> None:
            save_app_settings()

        header_bar(
            "AI Configuration",
            "Set up your AI providers and API keys. Start with one provider to begin writing.",
            pill="AI Tools",
        )
        
        if st.session_state.pop("ai_settings__flash", False):
            st.success("AI Settings opened. Configure a provider below to get started.")

        # Connection Status Overview
        groq_key, groq_source = get_effective_key("groq", st.session_state.get("user_id"))
        openai_key, openai_source = get_effective_key("openai", st.session_state.get("user_id"))
        
        with card_block("📊 Connection Status"):
            st.caption("Current status of your AI provider connections")
            status_cols = st.columns(3)
            with status_cols[0]:
                st.metric("Groq", "✓ Connected" if groq_key else "⚠ Not configured")
            with status_cols[1]:
                st.metric("OpenAI", "✓ Connected" if openai_key else "⚠ Not configured")
            with status_cols[2]:
                current_model = get_ai_model() or "None"
                st.metric("Active Model", current_model)

        # Provider Selection
        st.markdown("### Choose Your AI Provider")
        st.caption("Select which provider to use for AI-powered features like outlining, brainstorming, and text generation.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("**Groq** - Fast & Free\n\nGreat for getting started quickly with no cost.")
        with col2:
            st.info("**OpenAI** - Advanced Models\n\nIncludes GPT-4 and other powerful models (paid).")
        
        provider_choice = st.radio(
            "Which provider would you like to use?",
            ["Groq", "OpenAI"],
            horizontal=True,
            index=0 if st.session_state.ai_provider == "groq" else 1,
            key="ai_provider_choice",
        )
        provider_value = "groq" if provider_choice == "Groq" else "openai"
        if provider_value != st.session_state.ai_provider:
            st.session_state.ai_provider = provider_value

        # Provider Configuration Tabs
        st.markdown("### Configure Providers")
        tabs = st.tabs(["🤖 Groq", "✨ OpenAI"])

        def _status_label(source: str) -> str:
            return {
                "session": "Using session key",
                "saved": "Using saved key",
                "default": "Using server default",
                "none": "No key set",
            }.get(source, "No key set")

        def _render_key_controls(provider: str) -> None:
            provider_label = _provider_label(provider)
            key_input_state = f"{provider}_key_input"
            init_state(key_input_state, "")
            
            st.markdown("#### API Key")
            _, source = get_effective_key(provider)
            key_status = _status_label(source)
            if source in ["session", "saved"]:
                st.success(f"✓ {key_status}")
            else:
                st.info(f"ℹ {key_status}")
            
            key_value = st.text_input(
                f"Enter your {provider_label} API key",
                value=st.session_state.get(key_input_state, ""),
                type="password",
                placeholder="sk-...",
                help=f"Paste your API key here. It will only be stored for this session unless saved.",
                key=key_input_state,
                label_visibility="collapsed",
            )
            
            key_cols = st.columns(2)
            with key_cols[0]:
                if st.button(f"✓ Apply Key", use_container_width=True, key=f"{provider}_session_key", type="primary"):
                    if key_value.strip():
                        set_session_key(provider, key_value)
                        queue_widget_update(key_input_state, "")
                        # Auto-fetch models after applying key
                        base_url = st.session_state.get(f"{provider}_base_url", "")
                        fetch_fn = fetch_openai_models if provider == "openai" else fetch_groq_models
                        test_fn = test_openai_connection if provider == "openai" else test_groq_connection
                        models, _err = fetch_fn(base_url, key_value.strip())
                        if models:
                            st.session_state[f"{provider}_model_list"] = models
                            st.session_state[f"{provider}_model_tests"] = {}
                            st.toast(f"{provider_label} key activated — loaded {len(models)} models.")
                        else:
                            st.toast(f"{provider_label} key activated for this session.")
                        connection_ok = test_fn(base_url, key_value.strip())
                        st.session_state[f"{provider}_connection_tested"] = connection_ok
                        if not connection_ok:
                            st.toast(
                                f"{provider_label} connection test failed. Check your API key and base URL.",
                                icon="⚠️",
                            )
                        st.rerun()
                    else:
                        st.warning("Please enter an API key first.")
            with key_cols[1]:
                if st.button(f"✗ Clear Key", use_container_width=True, key=f"{provider}_clear_session"):
                    clear_session_key(provider)
                    st.toast(f"{provider_label} key cleared.")
                    st.rerun()

        with tabs[1]:
            with card_block("✨ OpenAI Configuration"):
                st.caption("OpenAI provides advanced models like GPT-4. Requires a paid API account.")
                
                _render_key_controls("openai")
                
                openai_key, _ = get_effective_key("openai", st.session_state.get("user_id"))
                if not openai_key:
                    st.info("💡 **Getting Started:** [Create an OpenAI account](https://platform.openai.com/api-keys) to get your API key.")
                
                st.markdown("#### Model Selection")
                if st.session_state.openai_model_list:
                    models = st.session_state.openai_model_list
                    idx = 0
                    if st.session_state.openai_model in models:
                        idx = models.index(st.session_state.openai_model)
                    openai_model = st.selectbox(
                        "Choose a model",
                        models,
                        index=idx,
                        help="Select which OpenAI model to use for AI features",
                        label_visibility="collapsed"
                    )
                else:
                    openai_model = st.text_input(
                        "Model name",
                        value=st.session_state.openai_model,
                        help="Enter the model name manually, or apply your key to auto-fetch available models",
                        label_visibility="collapsed"
                    )

                if openai_model != st.session_state.openai_model:
                    st.session_state.openai_model = openai_model
                    AppConfig.OPENAI_MODEL = openai_model
                    if openai_key:
                        st.session_state.openai_connection_tested = test_openai_connection(
                            st.session_state.openai_base_url,
                            openai_key,
                        )
                        if not st.session_state.openai_connection_tested:
                            st.toast("OpenAI connection test failed. Check your API key and base URL.", icon="⚠️")
                
                with st.expander("⚙️ Advanced Settings", expanded=False):
                    openai_url = st.text_input(
                        "API Base URL",
                        value=st.session_state.openai_base_url,
                        help="Change this only if using a custom OpenAI-compatible endpoint"
                    )
                    if openai_url != st.session_state.openai_base_url:
                        st.session_state.openai_base_url = openai_url
                        AppConfig.OPENAI_API_URL = openai_url

                if st.session_state.openai_model_list:
                    with st.expander("🧪 Advanced: Test All Models", expanded=False):
                        st.warning("⚠️ This will test each model individually. It may take time and consume API credits.")
                        openai_test_all_cooldown = _cooldown_remaining("openai_test_models", 20)
                        if st.button(
                            "Run Full Model Test",
                            use_container_width=True,
                            disabled=bool(openai_test_all_cooldown) or not openai_key,
                            key="openai_test_all_models_btn"
                        ):
                            _mark_action("openai_test_models")
                            results = {}
                            total = len(st.session_state.openai_model_list)
                            progress = st.progress(0)
                            for i, model_name in enumerate(st.session_state.openai_model_list, start=1):
                                ok, error_message = test_openai_model(
                                    st.session_state.openai_base_url,
                                    openai_key,
                                    model_name,
                                )
                                results[model_name] = "" if ok else error_message
                                progress.progress(i / total)
                            st.session_state.openai_model_tests = results
                            failures = [m for m, err in results.items() if err]
                            if failures:
                                st.warning(f"{len(failures)} models failed. Check details below.")
                            else:
                                st.success("✓ All models working correctly!")

                        if st.session_state.openai_model_tests:
                            st.markdown("**Test Results:**")
                            for model_name, error_message in sorted(
                                st.session_state.openai_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"✗ {model_name}: {error_message}")
                                else:
                                    st.success(f"✓ {model_name}")

        with tabs[0]:
            with card_block("🤖 Groq Configuration"):
                st.caption("Groq offers fast, free AI models. Great for getting started quickly.")
                
                _render_key_controls("groq")
                
                groq_key, _ = get_effective_key("groq", st.session_state.get("user_id"))
                if not groq_key:
                    st.info("💡 **Getting Started:** [Get a free Groq API key](https://console.groq.com/keys) to begin.")
                
                st.markdown("#### Model Selection")
                if st.session_state.groq_model_list:
                    models = st.session_state.groq_model_list
                    idx = 0
                    if st.session_state.groq_model in models:
                        idx = models.index(st.session_state.groq_model)
                    groq_model = st.selectbox(
                        "Choose a model",
                        models,
                        index=idx,
                        help="Select which Groq model to use for AI features",
                        label_visibility="collapsed"
                    )
                else:
                    groq_model = st.text_input(
                        "Model name",
                        value=st.session_state.groq_model,
                        help="Enter the model name manually, or apply your key to auto-fetch available models",
                        label_visibility="collapsed"
                    )

                if groq_model != st.session_state.groq_model:
                    st.session_state.groq_model = groq_model
                    AppConfig.DEFAULT_MODEL = groq_model
                    if groq_key:
                        st.session_state.groq_connection_tested = test_groq_connection(
                            st.session_state.groq_base_url,
                            groq_key,
                        )
                        if not st.session_state.groq_connection_tested:
                            st.toast("Groq connection test failed. Check your API key and base URL.", icon="⚠️")
                
                with st.expander("⚙️ Advanced Settings", expanded=False):
                    groq_url = st.text_input(
                        "API Base URL",
                        value=st.session_state.groq_base_url,
                        help="Change this only if using a custom Groq-compatible endpoint"
                    )
                    if groq_url != st.session_state.groq_base_url:
                        st.session_state.groq_base_url = groq_url
                        AppConfig.GROQ_API_URL = groq_url

                if st.session_state.groq_model_list:
                    with st.expander("🧪 Advanced: Test All Models", expanded=False):
                        st.warning("⚠️ This will test each model individually and may take some time.")
                        groq_test_all_cooldown = _cooldown_remaining("groq_test_models", 20)
                        if st.button(
                            "Run Full Model Test",
                            use_container_width=True,
                            disabled=bool(groq_test_all_cooldown) or not groq_key,
                            key="groq_test_all_models_btn"
                        ):
                            _mark_action("groq_test_models")
                            results = {}
                            total = len(st.session_state.groq_model_list)
                            progress = st.progress(0)
                            for i, model_name in enumerate(st.session_state.groq_model_list, start=1):
                                ok, error_message = test_groq_model(
                                    st.session_state.groq_base_url,
                                    groq_key,
                                    model_name,
                                )
                                results[model_name] = "" if ok else error_message
                                progress.progress(i / total)
                            st.session_state.groq_model_tests = results
                            failures = [m for m, err in results.items() if err]
                            if failures:
                                st.warning(f"{len(failures)} models failed. Check details below.")
                            else:
                                st.success("✓ All models working correctly!")

                        if st.session_state.groq_model_tests:
                            st.markdown("**Test Results:**")
                            for model_name, error_message in sorted(
                                st.session_state.groq_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"✗ {model_name}: {error_message}")
                                else:
                                    st.success(f"✓ {model_name}")

        # Save Settings Action
        st.markdown("---")
        save_cols = st.columns([2, 1])
        with save_cols[0]:
            st.markdown("### 💾 Save Your Configuration")
            st.caption("Save your provider settings and API keys for future sessions.")
        with save_cols[1]:
            if st.button(
                "Save Settings",
                type="primary",
                use_container_width=True,
                help="Save your AI provider configuration"
            ):
                save_settings_action()

    def render_legal_redirect():
        render_page_header(
            "All Policies",
            "Review policies, IP guidance, and acceptable use.",
            tag="Policies",
            key_prefix="legal_header",
        )

        legal_pages = [
            ("Terms of Service", "terms", "terms.md"),
            ("Privacy Policy", "privacy", "privacy.md"),
            ("Copyright", "copyright", "copyright.md"),
            ("Cookie Policy", "cookie", "cookie.md"),
            ("Brand & IP Clarity", "brand_ip", "Brand_ip_Clarity.md"),
            ("Trademark Path", "trademark", "Trademark_Path.md"),
            ("Contact", "contact_legal", "contact.md"),
        ]

        cols = st.columns(2)
        for idx, (label, key_suffix, filename) in enumerate(legal_pages):
            with cols[idx % 2]:
                path = LEGAL_DIR / filename
                if path.exists():
                    with st.expander(label):
                        st.markdown(path.read_text(encoding="utf-8"))
                else:
                    st.caption(f"{label} — not available")

    with st.sidebar:
        with key_scope("sidebar"):
            st.markdown("### MANTIS Studio")
            st.caption(f"Version {AppConfig.VERSION}")
            st.html("<div class='mantis-nav-section'>Appearance</div>")
            st.selectbox("Theme", ["Dark", "Light"], key="ui_theme")
            
            # Debug mode toggle for troubleshooting
            with st.expander("🔧 Advanced", expanded=False):
                st.checkbox(
                    "Enable Debug Mode",
                    key="debug",
                    help="Show detailed debugging information and logs"
                )
                if st.session_state.debug:
                    st.caption("✓ Debug mode active")
                    st.caption("Check terminal for detailed logs")
            
            st.divider()

            if st.session_state.project:
                p = st.session_state.project
                st.html("<div class='mantis-nav-section'>Current Project</div>")
                st.caption(p.title)
                st.caption(f"📚 {p.get_total_word_count()} words")
            else:
                st.info("No project loaded.")

            st.divider()
            st.html("<div class='mantis-nav-section'>Navigation</div>")

            from app.utils.navigation import get_nav_sections

            nav_sections = get_nav_sections()
            current_page = st.session_state.get("page", "home")
            world_focus = st.session_state.get("world_focus_tab", "")
            for section_idx, (section_name, nav_items) in enumerate(nav_sections):
                with st.expander(section_name, expanded=section_idx < 2):
                    for label, target, icon in nav_items:
                        if target == "memory":
                            is_active = current_page == "world" and world_focus == "Memory"
                        elif target == "insights":
                            is_active = current_page == "world" and world_focus == "Insights"
                        elif target == "legal":
                            is_active = current_page in {
                                "legal",
                                "terms",
                                "privacy",
                                "copyright",
                                "cookie",
                                "help",
                            }
                        else:
                            is_active = current_page == target
                        if st.button(
                            f"{icon} {label}",
                            key=f"nav_{target}_{_slugify(label)}",
                            use_container_width=True,
                            disabled=is_active,
                        ):
                            if target == "memory":
                                st.session_state.world_focus_tab = "Memory"
                                st.session_state.page = "world"
                            elif target == "insights":
                                st.session_state.world_focus_tab = "Insights"
                                st.session_state.page = "world"
                            else:
                                st.session_state.page = target
                            st.rerun()

            if st.session_state.project:
                st.divider()
                action_cols = st.columns(2)
                with action_cols[0]:
                    if st.button(
                        "💾 Save Project",
                        key="sidebar_save_project",
                        type="primary",
                        use_container_width=True,
                        help="Save all changes to this project"
                    ):
                        if persist_project(p, action="save"):
                            st.toast("Project saved successfully")
                with action_cols[1]:
                    if st.button(
                        "✖ Close Project",
                        key="sidebar_close_project",
                        use_container_width=True,
                        help="Save and close the current project"
                    ):
                        save_p()
                        # Clear the last_project_path from config to prevent auto-reload
                        config = load_app_config()
                        config.pop("last_project_path", None)
                        save_app_config(config)
                        st.session_state.project = None
                        st.session_state.page = "home"
                        st.rerun()

            # Debug panel - enhanced for troubleshooting black screen issues
            if debug_enabled():
                st.divider()
                st.markdown("### 🛠 Debug Panel")
                
                with st.expander("📊 Session State", expanded=False):
                    st.caption(f"**Current Page:** {st.session_state.get('page', 'unknown')}")
                    st.caption(f"**Initialized:** {st.session_state.get('initialized', False)}")
                    st.caption(f"**Project Loaded:** {st.session_state.project is not None}")
                    if st.session_state.project:
                        st.caption(f"  - Title: {st.session_state.project.title}")
                        st.caption(f"  - Path: {st.session_state.project.filepath}")
                    
                    last_action = st.session_state.get("last_action") or "—"
                    last_action_ts = st.session_state.get("last_action_ts")
                    if last_action_ts:
                        st.caption(f"**Last Action:** {last_action} ({time.strftime('%H:%M:%S', time.localtime(last_action_ts))})")
                    else:
                        st.caption(f"**Last Action:** {last_action}")
                    
                    last_exception = st.session_state.get("last_exception") or "—"
                    st.caption(f"**Last Exception:** {last_exception}")
                
                with st.expander("🔧 System Info", expanded=False):
                    st.caption(f"**Python:** {sys.version.split()[0]}")
                    st.caption(f"**Streamlit:** {st.__version__}")
                    st.caption(f"**App Version:** {AppConfig.VERSION}")
                    st.caption(f"**Projects Dir:** {AppConfig.PROJECTS_DIR}")
                    st.caption(f"**Config Path:** {AppConfig.CONFIG_PATH}")
                
                with st.expander("📝 Session State Keys", expanded=False):
                    keys = sorted([k for k in st.session_state.keys() if not k.startswith("_")])
                    st.caption(f"Total: {len(keys)} keys")
                    for key in keys[:20]:  # Show first 20 keys
                        value = st.session_state.get(key)
                        value_str = str(value)[:50] if value is not None else "None"
                        st.caption(f"- {key}: {value_str}")
                    if len(keys) > 20:
                        st.caption(f"... and {len(keys) - 20} more")
                
                if st.button("🔄 Force Rerun", use_container_width=True):
                    st.rerun()
                
                if st.button("🗑️ Clear Session State", use_container_width=True):
                    # Clear only user-defined keys, preserve Streamlit internal state
                    keys_to_clear = [k for k in st.session_state.keys() if not k.startswith("_")]
                    for key in keys_to_clear:
                        del st.session_state[key]
                    st.toast(f"Cleared {len(keys_to_clear)} session state keys")
                    st.rerun()

    def render_home():
        # Import new dashboard components
        from app.ui.dashboard_components import (
            render_hero_header,
            render_metrics_row,
            render_workspace_hub_section,
            render_feature_group,
            render_dashboard_section_header,
            add_divider_with_spacing,
        )
        
        render_welcome_banner("home")
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)

        has_outline = any((p["meta"].get("outline") or "").strip() for p in recent_projects)
        has_chapter = any(
            (c.get("word_count") or 0) > 0
            for p in recent_projects
            for c in (p["meta"].get("chapters") or {}).values()
        )

        active_project = st.session_state.project
        recent_snapshot = _project_snapshot(recent_projects[0]["meta"]) if recent_projects else None

        project_title = (
            (active_project.title if active_project else None)
            or (recent_snapshot or {}).get("title")
            or "Your next story"
        )
        milestone_label = "🚀 Create/Advance Next Narrative Milestone"
        weekly_goal = max(1, int(st.session_state.weekly_sessions_goal))
        weekly_count = _weekly_activity_count()
        canon_icon, canon_label = get_canon_health()
        groq_key, _ = get_effective_key("groq", st.session_state.get("user_id"))
        openai_key, _ = get_effective_key("openai", st.session_state.get("user_id"))
        project_health_completed = sum(
            [bool(recent_projects), bool(has_outline), bool(has_chapter), canon_icon != "🔴"]
        )
        project_health_percent = int((project_health_completed / 4) * 100)
        latest_chapter_label = "You last worked on Chapter — · recently"
        latest_chapter_index = None
        latest_chapter_id = None

        if active_project and getattr(active_project, "chapters", None):
            ch = max(
                active_project.chapters.values(),
                key=lambda c: (c.modified_at or c.created_at or 0),
            )
            latest_chapter_index = ch.index
            latest_chapter_id = ch.id
            latest_chapter_label = f"Latest: Chapter {ch.index} — {ch.title}"

        primary_label = milestone_label
        primary_target = "projects"
        if canon_icon == "🔴":
            primary_label = "🛠 Fix story issues"
            primary_target = "world"
        elif has_chapter and latest_chapter_index:
            primary_label = f"▶ Continue Chapter {latest_chapter_index}"
            primary_target = "chapters"
        elif has_outline:
            primary_label = "📝 Build your outline"
            primary_target = "outline"

        def open_recent_project(target: str, focus_tab: Optional[str] = None) -> None:
            if not recent_projects and not st.session_state.project:
                st.session_state.page = "projects"
                st.toast("Create or import a project to unlock this module.")
                st.rerun()
            if recent_projects and not st.session_state.project:
                loaded = load_project_safe(recent_projects[0]["path"], context="recent project")
                if not loaded:
                    st.session_state.page = "projects"
                    st.toast("Select a project to continue.")
                    st.rerun()
                st.session_state.project = loaded
            if focus_tab:
                st.session_state.world_focus_tab = focus_tab
            st.session_state.page = target
            st.rerun()

        def open_export() -> None:
            export_path = None
            if st.session_state.project and st.session_state.project.filepath:
                export_path = st.session_state.project.filepath
            elif recent_projects:
                export_path = recent_projects[0]["path"]
            if export_path:
                st.session_state.export_project_path = export_path
                st.session_state.page = "export"
                st.rerun()
            else:
                st.session_state.page = "export"
                st.toast("Select a project to export.")
                st.rerun()

        def open_ai_settings() -> None:
            st.session_state.ai_settings__flash = True
            st.session_state.page = "ai"
            st.rerun()

        def open_primary_cta() -> None:
            if primary_target == "chapters" and latest_chapter_id:
                st.session_state.curr_chap_id = latest_chapter_id
                st.session_state.active_chapter_id = latest_chapter_id
            open_recent_project(primary_target)

        def open_new_project() -> None:
            st.session_state.page = "projects"
            st.rerun()

        today = datetime.date.today()
        last_action_ts = st.session_state.get("last_action_ts")
        last_action_day = (
            datetime.date.fromtimestamp(last_action_ts) if last_action_ts else None
        )
        last_action_label = (st.session_state.get("last_action") or "").lower()
        ai_action_tokens = ("analysis", "insights", "memory", "semantic", "entity", "ai")
        ai_ops_today = (
            1
            if last_action_day == today and any(token in last_action_label for token in ai_action_tokens)
            else 0
        )
        system_mode = "Cloud" if (groq_key or openai_key) else "Local"
        autosave_status = "Auto-saving" if st.session_state.get("auto_save", True) else "Saved"

        def _open_project(project_path: str, target: str = "chapters") -> None:
            loaded = load_project_safe(project_path, context="project")
            if loaded:
                st.session_state.project = loaded
                st.session_state.page = target
                st.rerun()

        # =====================================================================
        # 1️⃣ HERO HEADER — Full Width Top Section
        # =====================================================================
        def hero_new_project() -> None:
            with st.spinner("Opening project setup..."):
                open_new_project()
        
        def hero_open_workspace() -> None:
            with st.spinner("Opening workspace..."):
                open_recent_project("chapters")
        
        def hero_run_analysis() -> None:
            with st.spinner("Preparing analysis workspace..."):
                open_recent_project("world", focus_tab="Insights")
        
        render_hero_header(
            status_label="🟢 Operational",
            status_caption=f"💾 {autosave_status}",
            primary_action=hero_new_project,
            secondary_action=hero_open_workspace,
            tertiary_action=hero_run_analysis,
        )

        add_divider_with_spacing(top=3, bottom=3)

        # =====================================================================
        # 2️⃣ METRICS OVERVIEW ROW
        # =====================================================================
        render_dashboard_section_header("Metrics Overview")
        
        metrics = [
            ("Total Projects", str(len(recent_projects))),
            ("Active Workspace", active_project.title if active_project else "None"),
            ("AI Operations Today", str(ai_ops_today)),
            ("System Mode", system_mode),
        ]
        render_metrics_row(metrics)

        add_divider_with_spacing(top=3, bottom=3)

        # =====================================================================
        # 3️⃣ WORKSPACE HUB SECTION
        # =====================================================================
        render_dashboard_section_header(
            "Workspace Hub",
            "Open recent projects or create a new workspace."
        )
        
        hub_cols = st.columns([2, 1])
        
        # Left: Recent Projects
        with hub_cols[0]:
            def _recent_projects_content() -> None:
                if not recent_projects:
                    st.info("📭 No projects yet — create your first workspace.")
                    return
                for project_entry in recent_projects[:5]:
                    meta = project_entry.get("meta", {})
                    title = meta.get("title") or os.path.basename(project_entry.get("path", "Untitled"))
                    modified = time.strftime(
                        "%Y-%m-%d %H:%M",
                        time.localtime(os.path.getmtime(project_entry["path"])),
                    )
                    row = st.columns([2.4, 1.2, 0.8])
                    with row[0]:
                        st.markdown(f"**{title}**")
                    with row[1]:
                        st.caption(f"Modified {modified}")
                    with row[2]:
                        if st.button("Open Workspace", use_container_width=True, key=f"dash_hub_open_{project_entry['path']}"):
                            _open_project(project_entry["path"])
            
            render_workspace_hub_section("Recent Projects", _recent_projects_content)

        # Right: Create New Project
        with hub_cols[1]:
            def _new_project_content() -> None:
                st.html(
                    """
                    <div style="text-align: center; padding: 16px 0;">
                        <div style="font-size: 48px; margin-bottom: 12px;">📝</div>
                        <div style="font-size: 14px; color: var(--mantis-muted); margin-bottom: 16px;">
                            Start a fresh narrative workspace with guided setup.
                        </div>
                    </div>
                    """
                )
                if st.button("✨ Create New Project", type="primary", use_container_width=True, key="hub_create_new"):
                    open_new_project()
                st.html("<div style='height: 8px;'></div>")
                st.caption(f"💡 Next: {primary_label}")
            
            render_workspace_hub_section("Create Workspace", _new_project_content)

        add_divider_with_spacing(top=3, bottom=3)

        # =====================================================================
        # 4️⃣ FEATURE ACCESS — GROUPED, NOT LISTED
        # =====================================================================
        render_dashboard_section_header(
            "Feature Access",
            "Grouped tools for intelligence, writing, insights, and system controls."
        )
        
        feature_groups = [
            (
                "🧠 Intelligence",
                [
                    ("Narrative Analysis", "Analyze structure and milestones.", lambda: open_recent_project("outline")),
                    ("Semantic Tools", "Review memory and semantic coherence.", lambda: open_recent_project("world", focus_tab="Memory")),
                    ("Entity Extraction", "Manage entities from the World Bible.", lambda: open_recent_project("world")),
                ],
            ),
            (
                "✍ Writing",
                [
                    ("Editor", "Draft and revise scenes.", lambda: open_recent_project("chapters")),
                    ("Rewrite", "Open editor tools for rewrites.", lambda: open_recent_project("chapters")),
                    ("Tone Modulation", "Refine voice and tone from editor workflows.", lambda: open_recent_project("chapters")),
                ],
            ),
            (
                "📊 Insights",
                [
                    ("Reports", "Prepare export-ready story reports.", open_export),
                    ("Analytics", "Open canon analytics and health.", lambda: open_recent_project("world", focus_tab="Insights")),
                    ("Data Viewer", "Inspect project metadata and structure.", lambda: open_recent_project("projects")),
                ],
            ),
            (
                "⚙ System",
                [
                    ("Settings", "Manage AI providers and keys.", open_ai_settings),
                    ("Configuration", "Adjust themes and workspace preferences.", open_ai_settings),
                ],
            ),
        ]

        for group_idx, (group_name, features) in enumerate(feature_groups):
            render_feature_group(
                group_name,
                features,
                expanded=(group_idx == 0),
                key_prefix="dashboard"
            )

        # =====================================================================
        # AI PROVIDER CONNECTION STATUS
        # =====================================================================
        st.html("<div style='height: 24px;'></div>")
        
        if not groq_key or not openai_key:
            with card_block("🔑 Connect your AI providers", "Unlock generation, summaries, and entity tools with API access."):
                cta_left, cta_right = st.columns(2)
                with cta_left:
                    st.link_button("Create Groq Account", "https://console.groq.com/keys", use_container_width=True)
                with cta_right:
                    st.link_button(
                        "Create OpenAI Account",
                        "https://platform.openai.com/api-keys",
                        use_container_width=True,
                    )
        else:
            with card_block("✅ AI providers connected", "Your AI providers are configured and ready to use."):
                cta_left, cta_right = st.columns(2)
                with cta_left:
                    if st.button("⚙️ Manage AI Settings", use_container_width=True, key="dashboard__ai_connected_settings"):
                        open_ai_settings()
                with cta_right:
                    st.caption("Groq and OpenAI are active.")


    def render_projects():
        # Enhanced page header with breadcrumbs
        enhanced_page_header(
            title="Projects",
            subtitle="Create, import, and manage your story worlds",
            icon="📁",
            breadcrumbs=["Home", "Projects"]
        )
        
        render_welcome_banner("projects")
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)

        def open_latest_project() -> None:
            if not recent_projects:
                st.toast("Complete the form below to create your first project.")
                return
            loaded = load_project_safe(recent_projects[0]["path"], context="recent project")
            if not loaded:
                return
            st.session_state.project = loaded
            st.session_state.page = "chapters"
            st.session_state.first_run = False
            st.rerun()

        primary_label = "Open latest project" if recent_projects else "Create your first project"
        render_page_header(
            "Projects",
            "Create, import, and manage your story worlds.",
            primary_label=primary_label,
            primary_action=open_latest_project,
            secondary_label="⬇️ Import draft",
            secondary_action=lambda: st.toast("Use the importer below to bring in .txt or .md files."),
            tag="Workspace",
            key_prefix="projects_header",
        )

        from app.utils.helpers import ai_connection_warning
        ai_connection_warning(st)

        section_header(
            "Start a new project",
            "Set a title, genre, and author details to build your base.",
        )
        with st.container(border=True):
            with st.form("new_project_form", clear_on_submit=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    t = st.text_input(
                        "Project Title",
                        placeholder="e.g., The Chronicle of Ash",
                        help="Give your story a title. Leave blank for a randomly generated name."
                    )
                with c2:
                    g = st.text_input(
                        "Genre",
                        placeholder="e.g., Dark Fantasy, Sci-Fi Noir",
                        help="Specify the genre(s) to help guide AI suggestions and tone."
                    )
                a = st.text_input(
                    "Author Name (Optional)",
                    placeholder="Your name",
                    help="Add your name or pen name for attribution. Leave blank if you prefer."
                )
                submitted = st.form_submit_button("🚀 Create Project", type="primary", use_container_width=True)
                if submitted:
                    title, genre, genre_list, ai_used = _resolve_project_seed(t, g, a)
                    st.session_state["project_seed_output"] = {
                        "title": title,
                        "genres": genre_list,
                        "ai_used": ai_used,
                    }
                    p = Project.create(
                        title,
                        author=a,
                        genre=genre,
                        storage_dir=get_active_projects_dir(),
                    )
                    persist_project(p, action="create_project")
                    _bump_projects_refresh()
                    st.session_state.project = p
                    st.session_state.page = "outline"
                    st.session_state.first_run = False
                    st.rerun()

        section_header(
            "Import an existing draft",
            "Upload a .txt or .md file to split into chapters.",
        )
        with st.container(border=True):
            uf = st.file_uploader("Upload file", type=["txt", "md"])
            if uf:
                max_bytes = AppConfig.MAX_UPLOAD_MB * 1024 * 1024
                uf_size = getattr(uf, "size", None)
                if uf_size and uf_size > max_bytes:
                    st.error(
                        f"File too large. Max size is {AppConfig.MAX_UPLOAD_MB} MB."
                    )
                else:
                    txt = uf.read().decode("utf-8", errors="replace")
                    if st.button("Import & Analyze", use_container_width=True, type="primary"):
                        try:
                            # Show step indicator for import process
                            step_indicator(
                                steps=["Upload File", "Create Project", "Analyze Content", "Generate Outline"],
                                current_step=1
                            )
                            
                            p = Project.create("Imported Project", storage_dir=get_active_projects_dir())
                            p.import_text_file(txt)
                            
                            # Update step indicator
                            step_indicator(
                                steps=["Upload File", "Create Project", "Analyze Content", "Generate Outline"],
                                current_step=2,
                                completed_steps=[0, 1]
                            )
                            
                            active_provider = _normalize_provider(st.session_state.get("ai_provider", "groq"))
                            active_key, _ = get_effective_key(active_provider, st.session_state.get("user_id"))
                            if active_key and get_ai_model():
                                # Enhanced loading state
                                loading_state(
                                    message="Analyzing your document...",
                                    subtext="This may take 10-30 seconds depending on length",
                                    show_spinner=True
                                )
                                p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
                                
                                # Show success feedback
                                feedback_message(
                                    "Document imported and outline generated successfully!",
                                    type="success"
                                )
                            else:
                                st.warning(
                                    f"Add a {_provider_label(active_provider)} API key and model to auto-generate an outline."
                                )
                            persist_project(p, action="create_project")
                        except Exception:
                            logger.warning("Import failed for uploaded draft", exc_info=True)
                            st.error("Import failed. Please check the file and try again.")
                            return
                        _bump_projects_refresh()
                        st.session_state.project = p
                        st.session_state.page = "outline"
                        st.session_state.first_run = False
                        st.rerun()

        section_header(
            "Your projects",
            "Open, export, or clean up older drafts.",
        )
        with st.container(border=True):
            if not recent_projects:
                st.info("📭 No projects yet. Start a new project above to get going.")
            else:
                for project_entry in recent_projects[:30]:
                    full = project_entry["path"]
                    try:
                        meta = project_entry["meta"]
                        filename = os.path.basename(full)
                        title = meta.get("title") or filename
                        genre = meta.get("genre") or ""
                        row1, row2, row3, row4 = st.columns([5, 2, 1.5, 1])
                        with row1:
                            if st.button(f"📂 {title}", key=f"open_{full}", use_container_width=True):
                                loaded = load_project_safe(full, context="project")
                                if loaded:
                                    st.session_state.project = loaded
                                    st.session_state.page = "chapters"
                                    st.session_state.first_run = False
                                    st.rerun()
                        with row2:
                            st.caption(genre)
                        with row3:
                            if st.button("⬇️ Export", key=f"export_{full}", use_container_width=True):
                                st.session_state.export_project_path = full
                                st.rerun()
                        with row4:
                            if st.button("🗑", key=f"del_{full}", use_container_width=True):
                                st.session_state.delete_project_path = full
                                st.session_state.delete_project_title = title
                                st.rerun()
                    except Exception:
                        logger.warning("Failed to load project metadata: %s", full, exc_info=True)

        if st.session_state.delete_project_path:
            with st.container(border=True):
                title = st.session_state.delete_project_title or "this project"
                st.warning(f"Delete **{title}**? This cannot be undone.")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("🗑 Confirm delete", type="primary", use_container_width=True):
                        Project.delete_file(st.session_state.delete_project_path)
                        if (
                            st.session_state.project
                            and st.session_state.project.filepath == st.session_state.delete_project_path
                        ):
                            st.session_state.project = None
                            st.session_state.page = "projects"
                        st.session_state.delete_project_path = None
                        st.session_state.delete_project_title = None
                        _bump_projects_refresh()
                        st.toast("Project deleted.")
                        st.rerun()
                with d2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.delete_project_path = None
                        st.session_state.delete_project_title = None
                        st.rerun()

        export_path = st.session_state.get("export_project_path")
        if export_path:
            with st.container(border=True):
                try:
                    export_project = Project.load(export_path)
                except Exception:
                    st.error("Export failed. Unable to load project.")
                    st.session_state.export_project_path = None
                else:
                    st.markdown("### Export Project")
                    st.caption("Download a single markdown file containing outline, world bible, and chapters.")
                    st.download_button(
                        "⬇️ Download .md",
                        project_to_markdown(export_project),
                        file_name=f"{export_project.title}.md",
                        use_container_width=True,
                    )
                    if st.button("Close export", use_container_width=True):
                        st.session_state.export_project_path = None
                        st.rerun()


    def render_export():
        render_page_header(
            "Export",
            "Export your project as markdown for editors or collaborators.",
            tag="Export",
            key_prefix="export_header",
        )

        export_project = None
        export_path = st.session_state.get("export_project_path")
        if export_path:
            try:
                export_project = Project.load(export_path)
            except Exception:
                st.error("Export failed. Unable to load project.")
                st.session_state.export_project_path = None
                return
        elif st.session_state.project:
            export_project = st.session_state.project
            if not export_project.filepath:
                export_project.save()

        if not export_project:
            st.info("No project selected for export yet.")
            return

        with st.container(border=True):
            st.markdown(f"### {export_project.title}")
            st.caption("Download your complete manuscript with outline, world bible, and chapters.")
            st.download_button(
                "⬇️ Download Manuscript (.md)",
                project_to_markdown(export_project),
                file_name=f"{export_project.title}.md",
                use_container_width=True,
                help="Download your complete project as a single markdown file for sharing or publishing",
            )

    def render_outline():
        p = st.session_state.project
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Create or open a project to edit an outline.")
                if st.button(
                    "📁 Go to Projects",
                    use_container_width=True,
                    help="Open or create a project to start planning your story"
                ):
                    st.session_state.page = "projects"
                    st.rerun()
            return
        def save_outline_action() -> None:
            if persist_project(p, action="save"):
                st.toast("Outline saved.")

        def scan_outline_action() -> None:
            extract_entities_ui(p.outline or "", "Outline")

        provider, active_key, _ = get_active_key_status()
        render_page_header(
            "Outline",
            "Your blueprint. Generate structure, scan entities, and keep the story plan here.",
            primary_label="💾 Save outline",
            primary_action=save_outline_action,
            secondary_label="🔍 Scan entities",
            secondary_action=scan_outline_action,
            secondary_disabled=not active_key,
            tag="Project",
            key_prefix="outline_header",
        )
        if not active_key:
            st.info(
                f"Add a {_provider_label(provider)} API key in AI Settings to scan entities or generate outlines."
            )

        # Keep the outline editor widget in sync when switching projects/pages
        if st.session_state.get("out_txt_project_id") != p.id:
            st.session_state["out_txt_project_id"] = p.id
            st.session_state["_outline_sync"] = p.outline or ""  # apply on next rerun before widget renders

        # If AI updated the outline this run, apply it BEFORE the text_area is created.
        if st.session_state.get("_outline_sync") is not None:
            st.session_state["out_txt"] = st.session_state.pop("_outline_sync")

        with st.container(border=True):
            top1, top2, top3 = st.columns([2.2, 1.1, 1])
            with top1:
                new_title = st.text_input("Project Title", p.title)
                if new_title != p.title:
                    p.title = new_title
                    save_p()
            with top2:
                new_genre = st.text_input("Genre", p.genre, placeholder="e.g., Dark Fantasy")
                if new_genre != p.genre:
                    p.genre = new_genre
                    save_p()
            with top3:
                if st.button("💾 Save Project", key="outline_save_project", type="primary", use_container_width=True):
                    if persist_project(p, action="save"):
                        st.toast("Saved")
                        st.rerun()

        left, right = st.columns([2.1, 1])

        # Placeholder for streaming AI-generated outline; lives below the editor, like chapters.
        outline_stream_ph = st.empty()

        with left:
            with st.container(border=True):
                st.markdown("### 🧩 Blueprint")
                val = st.text_area(
                    "Plot Outline",
                    p.outline,
                    height=560,
                    key="out_txt",
                    label_visibility="collapsed",
                    help="Write your story's plot outline here. Changes are auto-saved."
                )
                if val != p.outline:
                    p.outline = val
                    save_p()

                if st.button(
                    "💾 Save Outline",
                    use_container_width=True,
                    help="Save and automatically scan for characters, locations, and other entities"
                ):
                    if persist_project(p, action="save"):
                        # Automatically scan entities on save so World Bible stays in sync.
                        extract_entities_ui(p.outline or "", "Outline")
                        st.toast("Outline Saved & Entities Scanned")
                        st.rerun()

        with right:
            with st.container(border=True):
                st.markdown("### 🏗️ Architect (AI)")
                st.caption("Generate a chapter-by-chapter outline and append it to your blueprint.")

                chaps = st.number_input(
                    "Number of Chapters",
                    min_value=1,
                    max_value=50,
                    value=12,
                    help="Specify how many chapters to generate in the AI outline"
                )
                provider, active_key, _ = get_active_key_status()
                outline_cooldown = _cooldown_remaining("outline_generate", 12)
                outline_label = (
                    f"✨ Generate Structure ({outline_cooldown}s)" if outline_cooldown else "✨ Generate Structure"
                )
                
                # Determine help text based on disabled state
                button_help = get_ai_button_help(
                    outline_cooldown,
                    active_key,
                    "generate a detailed chapter-by-chapter outline for your story"
                )
                
                if not active_key:
                    show_api_key_notice("generate outlines")
                if st.button(
                    outline_label,
                    type="primary",
                    use_container_width=True,
                    disabled=bool(outline_cooldown) or not active_key,
                    help=button_help,
                ):
                    _mark_action("outline_generate")
                    # use outline_stream_ph defined above
                    full = ""
                    prompt = (
                        f"Write a detailed {chaps}-chapter outline for a {p.genre} novel: {p.title}. "
                        "Use structure: Chapter X: [Title] - [Summary]."
                    )
                    # Show loading indicator before streaming starts
                    with outline_stream_ph.container():
                        st.markdown("🔄 **Generating chapter outline...**")
                    
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        outline_stream_ph.markdown(full)

                    if full.strip():
                        new_outline = (((p.outline or "").rstrip() + "\n\n" + full.strip()).strip())
                        p.outline = new_outline
                        st.session_state["_outline_sync"] = new_outline  # apply on next rerun before widget renders
                        save_p()
                        st.rerun()

    def build_expander_label(base: str, suffix: Optional[str] = None) -> str:
        if suffix:
            return f"{base} · {suffix}"
        return base

    def render_world():
        p = st.session_state.project
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Open or create a project to access the World Bible.")
                if st.button(
                    "📁 Go to Projects",
                    use_container_width=True,
                    help="Open or create a project to manage your story world"
                ):
                    st.session_state.page = "projects"
                    st.rerun()
            return
        def open_add_entity() -> None:
            tab_label = st.session_state.get("world_tabs") or "Characters"
            category_map = {
                "Characters": "Character",
                "Locations": "Location",
                "Factions": "Faction",
                "Lore": "Lore",
            }
            category = category_map.get(tab_label, "Character")
            st.session_state[f"add_open_{category}"] = True
            st.rerun()

        render_page_header(
            "World Bible",
            "Your story's encyclopedia: Track characters, locations, factions, and lore. Mantis uses this to keep your writing consistent.",
            tag="Canon",
            key_prefix="world_header",
        )
        if not get_active_key_status()[1]:
            show_api_key_notice("run scans")

        st.html(
            """
            <style>
            .world-overview-card {
                padding: 14px 18px;
                border-radius: 18px;
                background: var(--mantis-surface);
                border: 1px solid var(--mantis-card-border);
            }
            .world-pill {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 600;
                border: 1px solid var(--mantis-primary-border);
                background: var(--mantis-accent-soft);
            }
            .world-pill.good {
                border-color: rgba(34,197,94,0.45);
                background: rgba(34,197,94,0.16);
            }
            .world-pill.warn {
                border-color: rgba(245,158,11,0.4);
                background: rgba(245,158,11,0.16);
            }
            .world-pill.risk {
                border-color: rgba(239,68,68,0.45);
                background: rgba(239,68,68,0.16);
            }
            .world-card {
                padding: 14px 18px;
                border-radius: 18px;
                background: var(--mantis-surface);
                border: 1px solid var(--mantis-card-border);
                box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
            }
            .world-card.highlight {
                border-color: rgba(245,158,11,0.6);
                box-shadow: 0 12px 24px rgba(245,158,11,0.18);
            }
            .world-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
            }
            .world-card-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 1.05rem;
                font-weight: 600;
            }
            .world-card-meta {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.85rem;
                color: var(--mantis-muted);
            }
            .world-badge {
                padding: 4px 10px;
                border-radius: 999px;
                background: var(--mantis-accent-soft);
                border: 1px solid var(--mantis-primary-border);
                color: var(--mantis-text);
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-size: 0.65rem;
            }
            .world-card-actions {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .world-card-metric {
                font-weight: 600;
                color: var(--mantis-text);
            }
            </style>
            """,
        )

        entries = list(p.world_db.values())
        chapters = p.get_ordered_chapters()
        chapter_texts = [(c, (c.content or "")) for c in chapters]
        chapter_texts_lower = [(c, text.lower()) for c, text in chapter_texts]

        def _count_mentions(aliases: List[str], text: str) -> int:
            total = 0
            for alias in aliases:
                alias_clean = (alias or "").strip()
                if not alias_clean:
                    continue
                pattern = rf"\\b{re.escape(alias_clean.lower())}\\b"
                total += len(re.findall(pattern, text))
            return total

        mention_counts: Dict[str, int] = {}
        mention_refs: Dict[str, List[Chapter]] = {}
        for ent in entries:
            aliases = [ent.name] + (ent.aliases or [])
            total_hits = 0
            hit_chapters = []
            for chap, lower_text in chapter_texts_lower:
                hits = _count_mentions(aliases, lower_text)
                if hits:
                    hit_chapters.append(chap)
                total_hits += hits
            mention_counts[ent.id] = total_hits
            mention_refs[ent.id] = hit_chapters

        orphaned_ids = {eid for eid, count in mention_counts.items() if count == 0}
        under_described_ids = {
            e.id for e in entries if len((e.description or "").strip()) < 30
        }
        normalized_name_map: Dict[str, List[str]] = {}
        for ent in entries:
            normalized = Project._normalize_entity_name(ent.name)
            if not normalized:
                continue
            normalized_name_map.setdefault(normalized, []).append(ent.id)
        collision_ids = {
            ent_id
            for ent_ids in normalized_name_map.values()
            if len(ent_ids) > 1
            for ent_id in ent_ids
        }
        flagged_entity_ids = orphaned_ids | under_described_ids | collision_ids

        locked_entities = [
            e for e in entries if "locked" in (e.tags or "").lower()
        ]
        last_scan_ts = st.session_state.get("last_entity_scan") or p.last_modified
        canon_icon, canon_label = get_canon_health()
        canon_class = "good"
        if canon_icon == "🟡":
            canon_class = "warn"
        elif canon_icon == "🔴":
            canon_class = "risk"

        with card("World overview", "Live status of your canon database."):
            top_cols = st.columns([1, 1, 1, 1, 1.2])
            with top_cols[0]:
                stat_tile("Total entities", str(len(entries)), icon="📘")
            with top_cols[1]:
                stat_tile("Orphaned", str(len(orphaned_ids)), icon="🛰️")
            with top_cols[2]:
                stat_tile("Locked", str(len(locked_entities)), icon="🔒")
            with top_cols[3]:
                stat_tile(
                    "Last scan",
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(last_scan_ts)),
                    icon="🕒",
                )
            with top_cols[4]:
                stat_tile("Canon health", f"{canon_icon} {canon_label}", icon="✅")

        with card("Search & filters", "Refine by status, recency, or canon risk."):
            f1, f2, f3, f4 = st.columns([2.2, 1, 1, 1])
            with f1:
                if st.session_state.get("world_search_pending"):
                    st.session_state["world_search"] = st.session_state.pop("world_search_pending")
                query = st.text_input(
                    "Search",
                    placeholder="Type a name or alias to filter...",
                    key="world_search",
                )
            with f2:
                show_orphaned = st.checkbox("Orphaned only", key="world_filter_orphaned")
            with f3:
                show_canon_risk = st.checkbox("Canon risk only", key="world_filter_risk")
            with f4:
                show_recent = st.checkbox("Recently added", key="world_filter_recent")

        tab_options = ["Characters", "Locations", "Factions", "Lore", "Memory", "Insights"]
        focus_tab = st.session_state.pop("world_focus_tab", None)
        if focus_tab not in tab_options:
            focus_tab = None
        default_tab = focus_tab or st.session_state.get("world_tabs", tab_options[0])
        if default_tab not in tab_options:
            default_tab = tab_options[0]
        selected_tab = st.radio(
            "World Bible sections",
            tab_options,
            index=tab_options.index(default_tab),
            horizontal=True,
            key="world_tabs",
        )

        review_queue = st.session_state.get("world_bible_review", [])
        if review_queue:
            with card("🔍 Review AI Suggestions", "AI suggestions are queued for review. Apply to update canon."):
                for idx, item in enumerate(list(review_queue)):
                    stype = item.get("type", "new")
                    label = f"{item.get('name', 'Unnamed')} • {item.get('category', 'Lore')}"
                    if stype == "update":
                        label = f"🔄 {label}"
                    elif stype == "alias_only":
                        label = f"🏷️ {label}"
                    else:
                        label = f"🆕 {label}"
                    expander_label = build_expander_label(label, str(idx))
                    with st.expander(expander_label):
                        type_labels = {"update": "Update Existing", "alias_only": "Add Aliases", "new": "New Entry"}
                        st.markdown(f"**Action:** {type_labels.get(stype, stype.title())}")
                        if item.get("match_name"):
                            st.markdown(f"**Matches:** {item['match_name']}")
                        confidence = item.get("confidence")
                        if confidence is not None:
                            st.markdown(f"**Confidence:** {confidence:.2f}")
                        source = item.get("source")
                        if source:
                            st.markdown(f"**Source:** {source}")
                        if item.get("reason"):
                            st.info(item["reason"])
                        novel_bullets = item.get("novel_bullets") or []
                        if novel_bullets:
                            st.markdown("**New details to add:**")
                            for b in novel_bullets:
                                st.markdown(f"- {b}")
                        elif item.get("description"):
                            st.markdown("**Suggested Notes**")
                            st.write(item.get("description"))
                        novel_aliases = item.get("novel_aliases") or []
                        if novel_aliases:
                            st.markdown(f"**New aliases:** {', '.join(novel_aliases)}")
                        elif item.get("aliases"):
                            st.markdown(f"**Aliases:** {', '.join(item.get('aliases') or [])}")

                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Apply", key=f"apply_suggestion_{idx}", use_container_width=True):
                                from app.services.world_bible_merge import apply_suggestion as _apply_suggestion
                                applied_ent, _action = _apply_suggestion(p, item)
                                # Clear cached widget values so the UI
                                # reflects the updated description/aliases
                                # on the next rerun.
                                if applied_ent is not None:
                                    st.session_state.pop(f"desc_{applied_ent.id}", None)
                                    st.session_state.pop(f"aliases_{applied_ent.id}", None)
                                review_queue.pop(idx)
                                st.session_state["world_bible_review"] = review_queue
                                persist_project(p)
                                if _action == "duplicate":
                                    st.toast("No new World Bible changes to apply.")
                                else:
                                    st.toast("World Bible updated.")
                                st.rerun()
                        with c2:
                            if st.button("🗑 Ignore", key=f"ignore_suggestion_{idx}", use_container_width=True):
                                review_queue.pop(idx)
                                st.session_state["world_bible_review"] = review_queue
                                st.toast("Suggestion removed.")
                                st.rerun()

        focus_entity = st.session_state.get("world_focus_entity")
        recent_cutoff = time.time() - (7 * 86400)

        def render_cat(category: str):
            with card():
                top = st.columns([1, 1.2, 1])
                with top[0]:
                    st.markdown(f"### {category}")
                with top[2]:
                    if st.button(f"➕ Add {category}", use_container_width=True):
                        st.session_state[f"add_open_{category}"] = True
                        st.rerun()

                if st.session_state.get(f"add_open_{category}", False):
                    with st.form(f"add_{category}"):
                        cat_slug = re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_")
                        n = st.text_input("Name", key=f"add_{cat_slug}_name")
                        d = st.text_area("Description", key=f"add_{cat_slug}_desc")
                        a = st.text_input("Aliases (comma-separated)", key=f"add_{cat_slug}_aliases")
                        s1, s2 = st.columns(2)
                        with s1:
                            ok = st.form_submit_button("Save", type="primary", use_container_width=True)
                        with s2:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                        if ok:
                            aliases = [alias.strip() for alias in (a or "").split(",") if alias.strip()]
                            p.upsert_entity(n, category, d, aliases=aliases, allow_merge=True, allow_alias=True)
                            persist_project(p)
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()
                        if cancel:
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()

                ents = [
                    e
                    for e in p.world_db.values()
                    if Project._normalize_category(e.category)
                    == Project._normalize_category(category)
                ]
                if query:
                    q = query.lower()
                    ents = [
                        e
                        for e in ents
                        if q in (e.name or "").lower()
                        or any(q in alias.lower() for alias in (e.aliases or []))
                    ]
                if show_orphaned:
                    ents = [e for e in ents if e.id in orphaned_ids]
                if show_canon_risk:
                    ents = [e for e in ents if e.id in flagged_entity_ids]
                if show_recent:
                    ents = [e for e in ents if e.created_at >= recent_cutoff]

                if not ents:
                    st.info(f"📭 No {category} entries yet. Add one above or scan entities from your outline/chapters.")
                    return

                ents = sorted(ents, key=lambda ent: (ent.name or "").lower())

                for idx, e in enumerate(ents):
                    mention_count = mention_counts.get(e.id, 0)
                    is_orphaned = e.id in orphaned_ids
                    is_under_described = e.id in under_described_ids
                    is_collision = e.id in collision_ids
                    if is_orphaned:
                        status_icon = "💤"
                    elif is_collision:
                        status_icon = "🔴"
                    elif is_under_described:
                        status_icon = "🟡"
                    else:
                        status_icon = "🟢"

                    highlight = "highlight" if e.id in flagged_entity_ids or e.id == focus_entity else ""

                    with st.container(border=True):
                        st.html(
                            f"""
                            <div class="world-card {highlight}">
                                <div class="world-card-header">
                                    <div class="world-card-title">{status_icon} {e.name}</div>
                                    <div class="world-card-meta">
                                        <span class="world-badge">{e.category}</span>
                                        <span class="world-card-metric">📌 {mention_count} mentions</span>
                                    </div>
                                </div>
                            </div>
                            """,
                        )

                        issues = []
                        if is_orphaned:
                            issues.append("Orphaned")
                        if is_under_described:
                            issues.append("Needs detail")
                        if is_collision:
                            issues.append("Name collision")
                        if issues:
                            st.caption(f"⚠️ {' • '.join(issues)}")

                        detail_suffix = f"{e.name} ({e.id})" if e.id else e.name
                        detail_label = build_expander_label("Details", detail_suffix)
                        with st.expander(detail_label, expanded=e.id == focus_entity):
                            new_desc = st.text_area("Notes", e.description, key=f"desc_{e.id}", height=140)
                            if new_desc != e.description:
                                e.description = new_desc
                                persist_project(p)

                            alias_text = st.text_input(
                                "Aliases (comma-separated)",
                                value=", ".join(e.aliases or []),
                                key=f"aliases_{e.id}",
                            )
                            if alias_text != ", ".join(e.aliases or []):
                                e.aliases = [a.strip() for a in alias_text.split(",") if a.strip()]
                                persist_project(p)

                            st.caption("Enrichment is currently unavailable.")

                            refs = mention_refs.get(e.id, [])
                            if refs:
                                options = {
                                    f"Chapter {chap.index}: {chap.title}": chap.id for chap in refs
                                }
                                sel = st.selectbox(
                                    "Jump to chapter",
                                    list(options.keys()),
                                    key=f"jump_select_{e.id}",
                                )
                                if st.button("📖 Jump to Chapter", key=f"jump_{e.id}", use_container_width=True):
                                    st.session_state.page = "chapters"
                                    st.session_state.curr_chap_id = options[sel]
                                    st.session_state.active_chapter_id = options[sel]
                                    st.session_state._force_nav = True
                                    st.rerun()
                            else:
                                st.caption("No chapter references yet.")

                            d1, d2 = st.columns([1, 1])
                            with d1:
                                if st.session_state.delete_entity_id == e.id:
                                    st.warning(f"Delete **{st.session_state.delete_entity_name or e.name}**?")
                                    cdel1, cdel2 = st.columns(2)
                                    with cdel1:
                                        if st.button("Confirm", type="primary", use_container_width=True):
                                            p.delete_entity(e.id)
                                            persist_project(p)
                                            st.session_state.delete_entity_id = None
                                            st.session_state.delete_entity_name = None
                                            st.toast("Entity deleted.")
                                            st.rerun()
                                    with cdel2:
                                        if st.button("Cancel", use_container_width=True):
                                            st.session_state.delete_entity_id = None
                                            st.session_state.delete_entity_name = None
                                            st.rerun()
                                elif st.button("🗑 Delete", key=f"del_{e.id}", use_container_width=True):
                                    st.session_state.delete_entity_id = e.id
                                    st.session_state.delete_entity_name = e.name
                                    st.rerun()
                            with d2:
                                st.caption(f"Created: {time.strftime('%Y-%m-%d', time.localtime(e.created_at))}")

        if selected_tab == "Characters":
            render_cat("Character")
        elif selected_tab == "Locations":
            render_cat("Location")
        elif selected_tab == "Factions":
            render_cat("Faction")
        elif selected_tab == "Lore":
            render_cat("Lore")
        elif selected_tab == "Memory":
            st.markdown("### 🧠 World Memory")
            st.caption("Keep canon notes, timelines, and facts the AI should always know.")
            st.markdown("#### 🔒 Hard Canon Rules")
            hard_key = f"world_memory_hard_{p.id}"
            hard_default = p.memory_hard or p.memory
            hard_val = st.text_area("Hard Canon Rules", hard_default, height=160, key=hard_key)
            if hard_val != p.memory_hard:
                p.memory_hard = hard_val
                save_p()

            st.markdown("#### 🧭 Soft Guidelines")
            soft_key = f"world_memory_soft_{p.id}"
            soft_val = st.text_area("Soft Guidelines", p.memory_soft, height=160, key=soft_key)
            if soft_val != p.memory_soft:
                p.memory_soft = soft_val
                save_p()

            st.markdown("#### 🧠 Project Memory")
            memory_key = f"world_memory_{p.id}"
            memory_val = st.text_area("Memory", p.memory, height=320, key=memory_key)
            if memory_val != p.memory:
                p.memory = memory_val
                save_p()
            if st.button("💾 Save Memory", use_container_width=True):
                if persist_project(p, action="save"):
                    st.toast("Memory saved")
                    st.rerun()

            st.divider()
            st.markdown("#### 🔍 Coherence Check")
            scope_cols = st.columns(3)
            with scope_cols[0]:
                scope_outline = st.checkbox("Outline", value=True, key=f"coh_outline_{p.id}")
            with scope_cols[1]:
                scope_world = st.checkbox("World Bible", value=True, key=f"coh_world_{p.id}")
            with scope_cols[2]:
                scope_chapters = st.checkbox("Chapters", value=True, key=f"coh_chapters_{p.id}")

            provider, active_key, _ = get_active_key_status()
            coherence_cooldown = _cooldown_remaining(f"coherence_{p.id}", 15)
            coherence_label = (
                f"🔍 Run Coherence Check ({coherence_cooldown}s)"
                if coherence_cooldown
                else "🔍 Run Coherence Check"
            )
            if not active_key:
                st.info(
                    f"Add a {_provider_label(provider)} API key in AI Settings to run coherence checks."
                )
            if st.button(
                coherence_label,
                use_container_width=True,
                disabled=bool(coherence_cooldown) or not active_key,
            ):
                _mark_action(f"coherence_{p.id}")
                compiled_world_bible = "\n".join(
                    f"{e.name} ({e.category}): {e.description}"
                    for e in p.world_db.values()
                )
                chapter_payload = [
                    {
                        "chapter_index": c.index,
                        "summary": c.summary,
                        "excerpt": (c.content or "")[:800],
                    }
                    for c in p.get_ordered_chapters()
                ]
                outline_payload = p.outline if scope_outline else ""
                world_payload = compiled_world_bible if scope_world else ""
                chapters_payload = chapter_payload if scope_chapters else []
                with st.spinner("Running coherence check..."):
                    results = AnalysisEngine.coherence_check(
                        memory=p.memory,
                        author_note=p.author_note,
                        style_guide=p.style_guide,
                        outline=outline_payload,
                        world_bible=world_payload,
                        chapters=chapters_payload,
                        model=get_ai_model(),
                    )
                st.session_state["coherence_results"] = results or []
                canon_icon, canon_label = get_canon_health()
                st.session_state.setdefault("canon_health_log", [])
                st.session_state["canon_health_log"].append(
                    {
                        "timestamp": time.time(),
                        "status": canon_icon,
                        "issue_count": len(st.session_state.get("coherence_results", [])),
                    }
                )
                st.session_state["canon_health_log"] = st.session_state["canon_health_log"][-30:]
                if results:
                    st.toast("Coherence issues found.")
                else:
                    st.toast("No coherence issues detected.")

            results = st.session_state.get("coherence_results", [])
            if results:
                st.markdown("#### 🧩 Coherence Issues")
                for idx, issue in enumerate(list(results)):
                    with st.container(border=True):
                        chapter_idx = issue.get("chapter_index", "?")
                        st.markdown(f"**Chapter #{chapter_idx}**")
                        st.markdown(f"**Issue:** {issue.get('issue', 'Unspecified issue')}")
                        st.markdown(f"**Confidence:** {issue.get('confidence', 'unknown')}")
                        st.markdown("**Suggested Rewrite:**")
                        st.write(issue.get("suggested_rewrite", ""))

                        a1, a2 = st.columns(2)
                        with a1:
                            if st.button("✅ Apply Fix", key=f"coh_apply_{idx}", use_container_width=True):
                                target_excerpt = issue.get("target_excerpt", "")
                                try:
                                    chapter_num = int(chapter_idx)
                                except (TypeError, ValueError):
                                    chapter_num = None
                                target_chapter = None
                                if chapter_num is not None:
                                    for c in p.get_ordered_chapters():
                                        if c.index == chapter_num:
                                            target_chapter = c
                                            break
                                if not target_chapter:
                                    st.warning("Chapter not found for this issue.")
                                elif target_excerpt and target_excerpt in (target_chapter.content or ""):
                                    updated = (target_chapter.content or "").replace(
                                        target_excerpt,
                                        issue.get("suggested_rewrite", ""),
                                        1,
                                    )
                                    target_chapter.update_content(updated, "Coherence Fix")
                                    persist_project(p)
                                    results.pop(idx)
                                    st.session_state["coherence_results"] = results
                                    update_locked_chapters()
                                    st.toast("Applied fix.")
                                    st.rerun()
                                elif issue.get("suggested_rewrite"):
                                    insertion = issue.get("suggested_rewrite", "").strip()
                                    if insertion:
                                        spacer = "\n\n" if (target_chapter.content or "").strip() else ""
                                        updated = f"{(target_chapter.content or '').rstrip()}{spacer}{insertion}"
                                        target_chapter.update_content(updated, "Coherence Fix (Appended)")
                                        persist_project(p)
                                        results.pop(idx)
                                        st.session_state["coherence_results"] = results
                                        update_locked_chapters()
                                        st.toast("Applied fix (appended).")
                                        st.rerun()
                                else:
                                    st.warning("Target excerpt not found in chapter content.")
                        with a2:
                            if st.button("🗑 Ignore", key=f"coh_ignore_{idx}", use_container_width=True):
                                results.pop(idx)
                                st.session_state["coherence_results"] = results
                                update_locked_chapters()
                                st.toast("Issue ignored.")
                                st.rerun()
        elif selected_tab == "Insights":
            st.markdown("### 📊 World Bible Insights")
            st.caption("Quick stats on your current canon database.")
            entries = list(p.world_db.values())
            total_entries = len(entries)
            counts = {"Character": 0, "Location": 0, "Faction": 0, "Lore": 0}
            for ent in entries:
                category = Project._normalize_category(ent.category)
                counts[category] = counts.get(category, 0) + 1

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Entries", total_entries)
            c2.metric("Characters", counts.get("Character", 0))
            c3.metric("Locations", counts.get("Location", 0))
            c4.metric("Factions", counts.get("Faction", 0))

            c5, c6 = st.columns(2)
            c5.metric("Lore", counts.get("Lore", 0))
            c6.metric(
                "Last Updated",
                time.strftime("%Y-%m-%d", time.localtime(p.last_modified)),
            )

            st.divider()
            if not st.session_state.get("is_premium", False):
                st.info("🔒 Canon history is a Premium feature.")
            else:
                st.markdown("### 🧠 Canon Health History")
                for entry in st.session_state.get("canon_health_log", []):
                    st.caption(
                        f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(entry['timestamp']))} "
                        f"{entry['status']} ({entry['issue_count']} issues)"
                    )

            st.divider()
            st.markdown("### ⏱ Timeline Heatmap")
            for chap in p.get_ordered_chapters():
                intensity = min(1.0, chap.word_count / 2000)
                st.progress(intensity, text=f"Chapter {chap.index}: {chap.word_count} words")

            st.divider()
            st.markdown("#### 📌 Entity Utilization")
            utilization_rows = []
            for ent in entries:
                aliases = [ent.name] + (ent.aliases or [])
                total_hits = mention_counts.get(ent.id, 0)
                utilization_rows.append(
                    {
                        "Name": ent.name,
                        "Category": ent.category,
                        "Appearances": total_hits,
                        "Orphaned": ent.id in orphaned_ids,
                        "Under-described": ent.id in under_described_ids,
                    }
                )
            if utilization_rows:
                st.dataframe(utilization_rows, use_container_width=True, hide_index=True)
            else:
                st.info("No entities yet to analyze.")

            st.divider()
            st.markdown("#### 🚩 Flagged Entities")
            flagged_entities = [ent for ent in entries if ent.id in flagged_entity_ids]
            if flagged_entities:
                for ent in flagged_entities:
                    reasons = []
                    if ent.id in orphaned_ids:
                        reasons.append("Orphaned")
                    if ent.id in under_described_ids:
                        reasons.append("Needs detail")
                    if ent.id in collision_ids:
                        reasons.append("Name collision")
                    with st.container(border=True):
                        r1, r2 = st.columns([3, 1])
                        with r1:
                            st.markdown(f"**{ent.name}** • {ent.category}")
                            st.caption(" • ".join(reasons))
                        with r2:
                            if st.button("Jump to Entity", key=f"jump_entity_{ent.id}", use_container_width=True):
                                st.session_state["world_focus_entity"] = ent.id
                                st.session_state["world_search_pending"] = ent.name
                                st.toast("Entity highlighted in World Bible.")
                                st.rerun()
            else:
                st.success("No flagged entities right now.")

            st.divider()
            st.markdown("#### ⚠️ Canon Risk Flags")
            coherence_results = st.session_state.get("coherence_results", [])
            high_canon_drift = len(coherence_results) > 0
            alias_collision = any(len(names) > 1 for names in normalized_name_map.values())

            timeline_dense = False
            dense_chapters = []
            for chap in chapters:
                summary_text = (chap.summary or "").strip()
                base_text = summary_text if summary_text else (chap.content or "")[:800]
                sentence_count = len([s for s in re.split(r"[.!?]+", base_text) if s.strip()])
                if sentence_count > 3:
                    timeline_dense = True
                    dense_chapters.append(chap.index)

            if high_canon_drift:
                st.warning("High Canon Drift: coherence issues detected.")
            if alias_collision:
                st.warning("Alias Collision: multiple entities share normalized names.")
            if timeline_dense:
                chap_list = ", ".join(str(idx) for idx in dense_chapters)
                st.warning(f"Timeline Density: >3 major events in chapters {chap_list}.")
            if not any([high_canon_drift, alias_collision, timeline_dense]):
                st.success("No canon risk flags detected.")

            st.divider()
            st.markdown("#### ✅ AI Readiness Score")
            readiness = 0
            if (p.memory or "").strip():
                readiness += 20
            if len(entries) > 10:
                readiness += 20
            if (p.outline or "").strip():
                readiness += 20
            if chapters:
                readiness += 20
            if not coherence_results:
                readiness += 20
            st.metric("AI Readiness", f"{readiness}%")

    def render_chapters():
        # Get project first
        p = st.session_state.project
        
        # Enhanced page header (only if project exists)
        if p:
            enhanced_page_header(
                title="Editor",
                subtitle="Write chapters, update summaries, and apply AI improvements",
                icon="✍️",
                breadcrumbs=["Home", p.title, "Editor"]
            )
        
        # Single welcome banner for the editor page (avoid duplicate widgets / duplicate keys).
        render_welcome_banner("editor")
        
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Create or open a project to start writing.")
                if st.button(
                    "📁 Go to Projects",
                    use_container_width=True,
                    help="Open or create a project to start writing your story",
                    key="editor_no_project_go_projects"
                ):
                    st.session_state.page = "projects"
                    st.rerun()
            return

        def _persist_chapter_update() -> None:
            st.session_state.project = p
            persist_project(p)
            _bump_projects_refresh()
            st.rerun()

        def _serialize_chapter(chapter: Chapter) -> Dict[str, Any]:
            return {
                "id": chapter.id,
                "index": chapter.index,
                "title": chapter.title,
                "content": chapter.content,
                "summary": chapter.summary,
                "word_count": chapter.word_count,
                "target_words": chapter.target_words,
                "created_at": chapter.created_at,
                "modified_at": chapter.modified_at,
            }

        def _set_active_chapter(chapter_id: Optional[str]) -> None:
            st.session_state.active_chapter_id = chapter_id
            st.session_state.curr_chap_id = chapter_id

        def _sync_session_chapters(force: bool = False) -> None:
            if (
                force
                or st.session_state.get("chapters_project_id") != p.id
                or not isinstance(st.session_state.get("chapters"), list)
            ):
                st.session_state.chapters = [_serialize_chapter(c) for c in p.get_ordered_chapters()]
                st.session_state.chapters_project_id = p.id
            chapter_ids = [c.get("id") for c in st.session_state.get("chapters", []) if c.get("id")]
            if st.session_state.get("active_chapter_id") not in chapter_ids:
                _set_active_chapter(chapter_ids[0] if chapter_ids else None)
            elif st.session_state.get("active_chapter_id"):
                st.session_state.curr_chap_id = st.session_state.active_chapter_id

        def _update_session_chapter(chapter: Chapter) -> None:
            chapters = st.session_state.get("chapters", [])
            for idx, item in enumerate(chapters):
                if item.get("id") == chapter.id:
                    chapters[idx] = {**item, **_serialize_chapter(chapter)}
                    st.session_state.chapters = chapters
                    return

        def _append_session_chapter(chapter: Chapter) -> None:
            chapters = st.session_state.get("chapters", [])
            chapters.append(_serialize_chapter(chapter))
            st.session_state.chapters = chapters

        _sync_session_chapters()
        chapters = st.session_state.get("chapters", [])

        def create_next_chapter() -> None:
            next_idx = len(chapters) + 1 if chapters else 1
            title = f"Chapter {next_idx}"
            if p.outline:
                pat = re.compile(rf"Chapter {next_idx}[:\\s]+(.*?)(?=\\n|$)", re.IGNORECASE)
                match = pat.search(p.outline or "")
                if match:
                    raw = match.group(1).strip()
                    title = sanitize_chapter_title(re.split(r" [-–:] ", raw, 1)[0].strip()) or title
            new_chapter = p.add_chapter(title)
            _append_session_chapter(new_chapter)
            _set_active_chapter(new_chapter.id)
            _persist_chapter_update()

        render_page_header(
            "Editor",
            "Write chapters, update summaries, and apply AI improvements.",
            tag="Drafting",
            key_prefix="editor_header",
        )

        if not chapters:
            with st.container(border=True):
                st.info("📭 No chapters yet.\n\nCreate your first chapter — or let MANTIS write one from your outline.")
                if st.button(
                    "➕ Create Chapter 1",
                    type="primary",
                    use_container_width=True,
                    help="Start your story by creating the first chapter",
                    key="editor_create_chapter_1"
                ):
                    create_next_chapter()
            return

        chapter_map = {c["id"]: c for c in chapters if c.get("id")}
        active_id = st.session_state.get("active_chapter_id")
        if active_id not in chapter_map:
            _set_active_chapter(chapters[0]["id"] if chapters else None)
            active_id = st.session_state.get("active_chapter_id")

        curr = p.chapters.get(active_id) if active_id else None
        if curr is None and active_id:
            _sync_session_chapters(force=True)
            chapters = st.session_state.get("chapters", [])
            chapter_map = {c["id"]: c for c in chapters if c.get("id")}
            active_id = st.session_state.get("active_chapter_id")
            curr = p.chapters.get(active_id) if active_id else None
        if curr is None:
            st.warning("Select a chapter to begin editing.")
            return
        curr_entry = chapter_map.get(curr.id, _serialize_chapter(curr))
        locked_chapters = st.session_state.get("locked_chapters", set())
        # --- SAFELY sync programmatic chapter updates into the editor widget (before widget exists)
        ed_key = f"ed_{curr.id}"
        if (
            st.session_state.get("_chapter_sync_id") == curr.id
            and ed_key in st.session_state
        ):
            st.session_state[ed_key] = st.session_state.get("_chapter_sync_text", "") or ""
            st.session_state._chapter_sync_id = None
            st.session_state._chapter_sync_text = None

        if p.outline and "Untitled" in (curr.title or ""):
            pat = re.compile(rf"Chapter {curr.index}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
            match = pat.search(p.outline or "")
            if match:
                raw = match.group(1).strip()
                clean = re.split(r" [-–:] ", raw, 1)[0].strip()
                if len(clean) > 2:
                    curr.title = sanitize_chapter_title(clean)
                    _update_session_chapter(curr)
                    persist_project(p)

        col_nav, col_editor, col_ai = st.columns([1.05, 3.2, 1.25])

        with col_nav:
            with st.container(border=True):
                st.markdown("### 📍 Chapters")
                for c in chapters:
                    chapter_id = c.get("id")
                    lbl = f"{c.get('index', 0)}. {(c.get('title') or 'Untitled')[:18]}"
                    if st.button(
                        lbl,
                        key=f"n_{chapter_id}",
                        type="primary" if chapter_id == curr.id else "secondary",
                        use_container_width=True,
                    ):
                        _set_active_chapter(chapter_id)
                        st.rerun()

                st.divider()
                if st.button(
                    "➕ New Chapter",
                    use_container_width=True,
                    help="Create a new chapter in this project.",
                    key="editor_new_chapter"
                ):
                    create_next_chapter()

                if chapters:
                    if st.session_state.get("delete_chapter_id") == curr.id:
                        st.warning(f"Delete **{st.session_state.get('delete_chapter_title') or curr.title}**?")
                        cdel1, cdel2 = st.columns(2)
                        with cdel1:
                            if st.button("Yes", type="primary", use_container_width=True, key="editor_del_ch_confirm"):
                                p.delete_chapter(curr.id)
                                _sync_session_chapters(force=True)
                                chapters = st.session_state.get("chapters", [])
                                _set_active_chapter(chapters[0]["id"] if chapters else None)
                                st.session_state.delete_chapter_id = None
                                st.session_state.delete_chapter_title = None
                                persist_project(p)
                                st.toast("Chapter deleted.")
                                st.rerun()
                        with cdel2:
                            if st.button("No", use_container_width=True, key="editor_del_ch_cancel"):
                                st.session_state.delete_chapter_id = None
                                st.session_state.delete_chapter_title = None
                                st.rerun()
                    elif st.button("🗑 Delete Chapter", use_container_width=True, key=f"editor_del_{curr.id}"):
                        st.session_state.delete_chapter_id = curr.id
                        st.session_state.delete_chapter_title = curr.title
                        st.rerun()

        stream_ph = st.empty()
        provider, active_key, _ = get_active_key_status()

        with col_editor:
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    title_key = f"editor_title_{curr.id}"
                    title_val = st.text_input(
                        "Chapter Title",
                        curr_entry.get("title", curr.title),
                        label_visibility="collapsed",
                        help="Edit the title of this chapter",
                        key=title_key,
                    )
                    if title_val != curr.title:
                        curr.title = title_val
                        _update_session_chapter(curr)
                        save_p()
                with h2:
                    target_key = f"editor_target_{curr.id}"
                    target_val = st.number_input(
                        "Target Word Count",
                        min_value=100,
                        max_value=10000,
                        value=int(curr_entry.get("target_words", curr.target_words)),
                        label_visibility="collapsed",
                        help="Set a target word count goal for this chapter",
                        key=target_key,
                    )
                    if int(target_val) != int(curr.target_words):
                        curr.target_words = int(target_val)
                        _update_session_chapter(curr)
                        save_p()

                val = st.text_area(
                    "Chapter Content",
                    curr_entry.get("content", curr.content),
                    height=680,
                    label_visibility="collapsed",
                    key=f"ed_{curr.id}",
                    help="Write your chapter content here. Changes are auto-saved."
                )
                if val != curr.content:
                    curr.update_content(val, "manual")
                    _update_session_chapter(curr)
                    save_p()

                st.caption(f"📝 Chapter: {curr.word_count} words • 📚 Total: {p.get_total_word_count()} words")

                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button(
                        "💾 Save Chapter",
                        type="primary",
                        use_container_width=True,
                        key=f"editor_save_{curr.id}",
                    ):
                        curr.update_content(val, "manual")
                        _update_session_chapter(curr)
                        if persist_project(p, action="save"):
                            # Automatically scan entities from this chapter when the user explicitly saves it.
                            extract_entities_ui(curr.content or "", f"Ch {curr.index}")
                            st.toast("Chapter Saved & Entities Scanned")
                            st.rerun()
                with c2:
                    summary_cooldown = _cooldown_remaining(f"summary_{curr.id}", 10)
                    summary_label = (
                        f"📝 Update Summary ({summary_cooldown}s)"
                        if summary_cooldown
                        else "📝 Update Summary"
                    )
                    if not active_key:
                        st.info(
                            f"Add a {_provider_label(provider)} API key in AI Settings to update summaries."
                        )
                    if st.button(
                        summary_label,
                        use_container_width=True,
                        disabled=bool(summary_cooldown) or not active_key,
                        key=f"editor_summary_{curr.id}",
                    ):
                        _mark_action(f"summary_{curr.id}")
                        summary = StoryEngine.summarize(curr.content or "", get_ai_model())
                        if summary.strip().startswith("ERROR: Canon violation detected."):
                            st.error("Canon violation detected. Resolve issues before generating AI content.")
                        else:
                            curr.summary = summary
                            _update_session_chapter(curr)
                            persist_project(p)
                            st.rerun()

                def generate_improvement(style_choice, custom_instructions):
                    prompt = rewrite_prompt(curr.content or "", style_choice, custom_instructions)
                    full = ""
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        stream_ph.markdown(f"**IMPROVING:**\n\n{full}")
                    if full.strip().startswith("ERROR: Canon violation detected."):
                        st.error("Canon violation detected. Resolve issues before generating AI content.")
                        return ""
                    violations = detect_hard_canon_violation(p, curr.index, full)
                    if violations:
                        results = st.session_state.get("coherence_results", [])
                        results.extend(violations)
                        st.session_state["coherence_results"] = results
                        update_locked_chapters()
                        st.warning("Hard Canon conflict detected. AI output was not applied.")
                        return ""
                    return full

                with st.expander("✨ Modify / Improve Text"):
                    rewrite_locked = curr.index in locked_chapters
                    style = st.selectbox(
                        "How to improve?",
                        list(REWRITE_PRESETS.keys()),
                        disabled=rewrite_locked,
                        key=f"editor_improve__style_{curr.id}",
                    )
                    cust = ""
                    if style == "Custom":
                        cust = st.text_input(
                            "Instructions",
                            disabled=rewrite_locked,
                            key=f"editor_improve__instructions_{curr.id}",
                        )
                    if rewrite_locked:
                        st.caption("🔒 Rewrite tools are disabled for locked chapters.")
                    if not active_key:
                        st.info(
                            f"Add a {_provider_label(provider)} API key in AI Settings to generate improvements."
                        )
                    improve_cooldown = _cooldown_remaining(f"improve_{curr.id}", 12)
                    improve_label = (
                        f"Generate Improvement ({improve_cooldown}s)"
                        if improve_cooldown
                        else "Generate Improvement"
                    )
                    if st.button(
                        improve_label,
                        use_container_width=True,
                        disabled=rewrite_locked or bool(improve_cooldown) or not active_key,
                        key=f"editor_improve__generate_{curr.id}",
                    ):
                        _mark_action(f"improve_{curr.id}")
                        full = generate_improvement(style, cust)
                        if full:
                            st.session_state.pending_improvement_text = full
                            st.session_state.pending_improvement_meta = {
                                "mode": style,
                                "custom": cust,
                                "timestamp": time.time(),
                                "chapter_id": curr.id,
                            }
                            st.rerun()

                if st.button(
                    "↩️ Undo last apply",
                    use_container_width=True,
                    key=f"editor_improve__undo_{curr.id}",
                    help="Restore the previous chapter text, if available.",
                ):
                    prev = st.session_state.get("chapter_text_prev", {})
                    if prev.get("chapter_id") == curr.id and prev.get("text") is not None:
                        curr.update_content(prev.get("text") or "", "Undo Apply")
                        _update_session_chapter(curr)
                        persist_project(p)
                        st.session_state._chapter_sync_id = curr.id
                        st.session_state._chapter_sync_text = prev.get("text") or ""
                        st.toast("Previous chapter text restored.")
                        st.rerun()
                    else:
                        st.info("No previous chapter text available to restore.")

                chapter_drafts = [
                    draft for draft in st.session_state.get("chapter_drafts", [])
                    if draft.get("chapter_id") == curr.id
                ]
                if chapter_drafts:
                    st.markdown("#### Draft Versions")
                    for idx, draft in enumerate(chapter_drafts, start=1):
                        label = f"Draft {idx} • {draft.get('mode', 'Improved')} • {time.strftime('%Y-%m-%d %H:%M', time.localtime(draft.get('timestamp', 0)))}"
                        with st.expander(label):
                            st.text_area(
                                "Draft Text",
                                draft.get("text", ""),
                                height=200,
                                disabled=True,
                                key=f"editor_improve__draft_text_{curr.id}_{idx}",
                            )
                            if st.button(
                                "Set as active",
                                type="primary",
                                use_container_width=True,
                                key=f"editor_improve__set_active_{curr.id}_{idx}",
                            ):
                                st.session_state.chapter_text_prev = {
                                    "chapter_id": curr.id,
                                    "text": curr.content or "",
                                }
                                curr.update_content(draft.get("text", ""), "Draft Applied")
                                _update_session_chapter(curr)
                                persist_project(p)
                                st.session_state._chapter_sync_id = curr.id
                                st.session_state._chapter_sync_text = draft.get("text", "")
                                st.toast("Draft set as active.")
                                st.rerun()

        with col_ai:
            with st.container(border=True):
                st.markdown("### 🤖 Assistant")
                st.caption("Generate new prose from your outline + previous context.")

                canon_icon, canon_label = get_canon_health()
                canon_blocked = canon_icon == "🔴"
                if canon_blocked:
                    st.button(
                        "🚫 Auto-Write Disabled (Canon Risk)",
                        disabled=True,
                        use_container_width=True,
                        help="Resolve canon issues in World Bible → Memory before generating.",
                        key=f"editor_autowrite_blocked_{curr.id}",
                    )
                else:
                    if not active_key:
                        st.info(
                            f"Add a {_provider_label(provider)} API key in AI Settings to auto-write chapters."
                        )
                    auto_cooldown = _cooldown_remaining(f"auto_write_{curr.id}", 12)
                    auto_label = (
                        f"✨ Auto-Write Chapter ({auto_cooldown}s)"
                        if auto_cooldown
                        else "✨ Auto-Write Chapter"
                    )
                    if st.button(
                        auto_label,
                        type="primary",
                        use_container_width=True,
                        disabled=bool(auto_cooldown) or not active_key,
                        key=f"editor_autowrite_{curr.id}",
                    ):
                        _mark_action(f"auto_write_{curr.id}")
                        prompt = StoryEngine.generate_chapter_prompt(p, curr.index, int(curr.target_words))
                        full = ""
                        for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                            full += chunk
                            stream_ph.markdown(f"**GENERATING:**\n\n{full}")

                        if full.strip():
                            if full.strip().startswith("ERROR: Canon violation detected."):
                                st.error("Canon violation detected. Resolve issues before generating AI content.")
                                return
                            violations = detect_hard_canon_violation(p, curr.index, full)
                            if violations:
                                results = st.session_state.get("coherence_results", [])
                                results.extend(violations)
                                st.session_state["coherence_results"] = results
                                update_locked_chapters()
                                st.warning("Hard Canon conflict detected. AI output was not applied.")
                                return
                            new_text = ((curr.content or "") + "\n" + full.strip()).strip()
                            curr.update_content(new_text, "AI Auto-Write")
                            _update_session_chapter(curr)
                            persist_project(p)

                            # Queue sync into editor widget on next run (do NOT set ed_key here!)
                            st.session_state._chapter_sync_id = curr.id
                            st.session_state._chapter_sync_text = new_text

                            st.toast("Chapter Updated")
                            time.sleep(0.3)
                            st.rerun()

                st.divider()
                st.markdown("#### Summary")
                if curr.summary:
                    st.info(curr.summary)
                else:
                    st.info("No summary yet. Click **Update Summary** to generate one.")

        pending_text = st.session_state.get("pending_improvement_text") or ""
        pending_meta = st.session_state.get("pending_improvement_meta") or {}
        pending_for_chapter = pending_text and pending_meta.get("chapter_id") == curr.id
        if pending_for_chapter:
            with st.container(border=True):
                st.markdown("### ✨ Review Changes")
                diff_toggle = st.toggle(
                    "Diff view",
                    value=False,
                    key=f"editor_improve__diff_toggle_{curr.id}",
                    help="Show a unified diff instead of the full texts.",
                )
                col_left, col_right = st.columns(2)
                if diff_toggle:
                    diff_lines = difflib.unified_diff(
                        (curr.content or "").splitlines(),
                        (pending_text or "").splitlines(),
                        fromfile="Original",
                        tofile="Improved",
                        lineterm="",
                    )
                    diff_text = "\n".join(diff_lines).strip() or "No differences found."
                    with col_left:
                        st.text_area(
                            "Original",
                            curr.content or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__original_{curr.id}",
                        )
                    with col_right:
                        st.code(diff_text, language="diff")
                else:
                    with col_left:
                        st.text_area(
                            "Original",
                            curr.content or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__original_{curr.id}",
                        )
                    with col_right:
                        st.text_area(
                            "Improved",
                            pending_text or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__improved_{curr.id}",
                        )

                apply_mode = st.selectbox(
                    "Apply result as",
                    [
                        "Replace chapter",
                        "Save as new draft/version",
                        "Append to end (advanced)",
                    ],
                    key=f"editor_improve__apply_mode_{curr.id}",
                )

                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                with b1:
                    if st.button(
                        "Apply Changes",
                        type="primary",
                        use_container_width=True,
                        key=f"editor_improve__apply_{curr.id}",
                    ):
                        if apply_mode == "Replace chapter":
                            st.session_state.chapter_text_prev = {
                                "chapter_id": curr.id,
                                "text": curr.content or "",
                            }
                            new_text = pending_text or ""
                            curr.update_content(new_text, "AI Improve")
                            _update_session_chapter(curr)
                            persist_project(p)
                            st.session_state._chapter_sync_id = curr.id
                            st.session_state._chapter_sync_text = new_text
                            st.toast("Chapter replaced with improved text.")
                        elif apply_mode == "Save as new draft/version":
                            draft_entry = {
                                "chapter_id": curr.id,
                                "text": pending_text or "",
                                "mode": pending_meta.get("mode", "Improve"),
                                "timestamp": time.time(),
                            }
                            st.session_state.chapter_drafts = (
                                st.session_state.get("chapter_drafts", []) + [draft_entry]
                            )
                            st.toast("Saved as a new draft version.")
                        else:
                            st.session_state.chapter_text_prev = {
                                "chapter_id": curr.id,
                                "text": curr.content or "",
                            }
                            new_text = ((curr.content or "") + "\n" + (pending_text or "")).strip()
                            curr.update_content(new_text, "AI Improve Append")
                            _update_session_chapter(curr)
                            persist_project(p)
                            st.session_state._chapter_sync_id = curr.id
                            st.session_state._chapter_sync_text = new_text
                            st.toast("Improved text appended to chapter.")

                        st.session_state.pending_improvement_text = ""
                        st.session_state.pending_improvement_meta = {}
                        st.rerun()
                with b2:
                    if st.button(
                        "Copy Improved",
                        use_container_width=True,
                        key=f"editor_improve__copy_{curr.id}",
                    ):
                        st.session_state.editor_improve__copy_buffer = pending_text or ""
                        st.toast("Improved text ready to copy (Ctrl/Cmd+C).")
                with b3:
                    regen_cooldown = _cooldown_remaining(f"improve_regen_{curr.id}", 12)
                    regen_label = (
                        f"Regenerate ({regen_cooldown}s)" if regen_cooldown else "Regenerate"
                    )
                    if st.button(
                        regen_label,
                        use_container_width=True,
                        disabled=bool(regen_cooldown) or not active_key,
                        key=f"editor_improve__regenerate_{curr.id}",
                    ):
                        _mark_action(f"improve_regen_{curr.id}")
                        regen_style = pending_meta.get("mode", "Improve Flow")
                        regen_custom = pending_meta.get("custom", "")
                        full = generate_improvement(regen_style, regen_custom)
                        if full:
                            st.session_state.pending_improvement_text = full
                            st.session_state.pending_improvement_meta = {
                                "mode": regen_style,
                                "custom": regen_custom,
                                "timestamp": time.time(),
                                "chapter_id": curr.id,
                            }
                            st.rerun()
                with b4:
                    if st.button(
                        "Discard",
                        use_container_width=True,
                        key=f"editor_improve__discard_{curr.id}",
                    ):
                        st.session_state.pending_improvement_text = ""
                        st.session_state.pending_improvement_meta = {}
                        st.rerun()

    def _render_current_page() -> None:
        rendered_page = False
        current_page = st.session_state.get("page")
        logger.info(f"Rendering page: {current_page}")
        
        if st.session_state.page == "home":
            logger.debug("Rendering home/dashboard page")
            with key_scope("dashboard"):
                render_home()
            rendered_page = True
        elif st.session_state.page == "projects":
            logger.debug("Rendering projects page")
            with key_scope("projects"):
                render_projects()
            rendered_page = True
        elif st.session_state.page == "ai":
            logger.debug("Rendering AI settings page")
            with key_scope("settings"):
                render_ai_settings()
            rendered_page = True
        elif st.session_state.page == "legal":
            logger.debug("Rendering legal page")
            with key_scope("legal"):
                render_legal_redirect()
            rendered_page = True
        elif st.session_state.page == "privacy":
            logger.debug("Rendering privacy page")
            with key_scope("privacy"):
                render_privacy()
            rendered_page = True
        elif st.session_state.page == "terms":
            logger.debug("Rendering terms page")
            with key_scope("terms"):
                render_terms()
            rendered_page = True
        elif st.session_state.page == "copyright":
            logger.debug("Rendering copyright page")
            with key_scope("copyright"):
                render_copyright()
            rendered_page = True
        elif st.session_state.page == "cookie":
            logger.debug("Rendering cookie page")
            with key_scope("cookie"):
                render_cookie()
            rendered_page = True
        elif st.session_state.page == "help":
            logger.debug("Rendering help page")
            with key_scope("help"):
                render_help()
            rendered_page = True
        elif st.session_state.page == "export":
            logger.debug("Rendering export page")
            with key_scope("export"):
                render_export()
            rendered_page = True
        else:
            pg = st.session_state.page
            if pg == "outline":
                logger.debug("Rendering outline page")
                with key_scope("outline"):
                    render_outline()
                rendered_page = True
            elif pg == "world":
                logger.debug("Rendering world bible page")
                with key_scope("world"):
                    render_world()
                rendered_page = True
            elif pg == "chapters":
                logger.debug("Rendering chapters/editor page")
                with key_scope("editor"):
                    render_chapters()
                rendered_page = True
            else:
                logger.warning(f"Unknown page '{pg}', redirecting to home")
                st.session_state.page = "home"
                st.rerun()
        if rendered_page:
            logger.debug("Rendering footer")
            render_app_footer()
            logger.info(f"Page '{current_page}' rendered successfully")

    # Render with comprehensive error handling and fallback UI
    try:
        logger.info("=" * 60)
        logger.info("Starting page render cycle")
        logger.info("=" * 60)
        _render_current_page()
        logger.info("Page render cycle completed successfully")
    except Exception as exc:
        # Comprehensive error handling with fallback UI to ensure app never shows blank page
        error_msg = f"{type(exc).__name__}: {exc}"
        st.session_state["last_exception"] = error_msg
        logger.error("=" * 60)
        logger.error("UNHANDLED UI EXCEPTION")
        logger.error("=" * 60)
        logger.error(f"Page: {st.session_state.get('page', 'unknown')}")
        logger.error(f"Error: {error_msg}")
        logger.exception("Exception details:", exc_info=True)
        logger.error("=" * 60)
        
        # Render fallback error UI
        try:
            st.error("⚠️ **Something went wrong while rendering this page.**")
            st.markdown("""
            ### Troubleshooting Steps:
            1. Try reloading the app (F5 or Ctrl+R)
            2. Return to the dashboard using the sidebar or button below
            3. Check the terminal/logs for detailed error messages
            4. If the issue persists, please report it on GitHub with the error details below
            """)
            
            with st.expander("🔍 Error Details (Click to expand)", expanded=False):
                st.code(error_msg, language="text")
                if debug_enabled():
                    st.write("**Debug Mode Active - Full Stack Trace:**")
                    st.exception(exc)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏠 Return to Dashboard", use_container_width=True, type="primary", key="main_error_fallback_home"):
                    st.session_state.page = "home"
                    st.rerun()
            with col2:
                if st.button("🔄 Reload App", use_container_width=True, key="main_error_fallback_reload"):
                    st.rerun()
        except Exception as fallback_exc:
            # Last resort: even the error UI failed
            logger.critical(f"Error fallback UI failed: {fallback_exc}", exc_info=True)
            try:
                st.text("Critical error - please refresh the page")
                if st.button("Refresh", key="main_error_critical_refresh"):
                    st.rerun()
            except Exception:
                # Nothing we can do at this point
                pass


# Execute the UI when running under Streamlit (not when imported by tests/other modules)
# This is the main entry point when `streamlit run app/main.py` is executed
try:
    import streamlit as st
    from streamlit import runtime
    
    # Only run UI if we're already inside a Streamlit runtime
    # (which happens when `streamlit run app/main.py` is executed)
    if runtime.exists():
        _run_ui()
except ImportError:
    # Streamlit not available - don't run UI
    # This allows imports in tests and other contexts where Streamlit is not installed
    pass


def run_selftest() -> int:
    """
    Quick non-UI integrity test. Intended to be called by the launcher.
    Creates a temporary project, exercises save/load, chapters/entities/export, then cleans up.
    """
    print("[MANTIS SELFTEST]")
    try:
        os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
        # Local-first architecture: all projects stored in default directory
        user_projects_dir = AppConfig.PROJECTS_DIR

        p = Project.create("SELFTEST_PROJECT", author="MANTIS", genre="Test", storage_dir=user_projects_dir)
        p.outline = "Chapter 1: Test - This is a test outline."
        path = p.save()
        if not os.path.exists(path):
            raise RuntimeError("Save failed: project file not found on disk.")

        p2 = Project.load(path)
        if p2.title != "SELFTEST_PROJECT":
            raise RuntimeError("Load failed: project title mismatch.")

        ch = p2.add_chapter("Test Chapter", "Hello world")
        if ch.word_count != 2:
            raise RuntimeError(f"Chapter word_count incorrect: expected 2, got {ch.word_count}")

        ent = p2.add_entity("Tester", "Character", "A test entity.")
        if ent is None:
            raise RuntimeError("Entity add failed: returned None.")

        md = project_to_markdown(p2)
        if "# SELFTEST_PROJECT" not in md:
            raise RuntimeError("Export markdown failed: missing title header.")

        # Cleanup
        try:
            os.remove(path)
        except OSError:
            logger.warning("Selftest cleanup failed for %s", path, exc_info=True)
        try:
            if os.path.isdir(user_projects_dir):
                shutil.rmtree(user_projects_dir)
        except OSError:
            logger.warning("Selftest cleanup failed for %s", user_projects_dir, exc_info=True)
        print("SELFTEST RESULT: PASS")
        return 0
    except Exception as e:
        logger.error("Selftest failed", exc_info=True)
        print("SELFTEST RESULT: FAIL")
        print(str(e))
        return 1



def run_repair() -> int:
    """
    Repairs/normalizes project JSON files in the projects folder.
    - Creates a timestamped backup copy into projects/.backups
    - Attempts to load via Project.load (validates schema)
    - Rewrites JSON in a normalized format (indent=2, ensure_ascii=False)
    Returns 0 on success, 1 if any file failed.
    """
    projects_dir = AppConfig.PROJECTS_DIR
    backups_dir = AppConfig.BACKUPS_DIR
    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(backups_dir, exist_ok=True)

    files = [f for f in os.listdir(projects_dir) if f.lower().endswith(".json")]
    if not files:
        print("[REPAIR] No project files found.")
        return 0

    stamp = time.strftime("%Y%m%d_%H%M%S")
    failures = 0

    def _atomic_write(path: str, data: dict) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    print(f"[REPAIR] Found {len(files)} project file(s). Backups -> {backups_dir}")
    for fn in files:
        full = os.path.join(projects_dir, fn)
        try:
            # Backup first
            backup_name = f"{stamp}__{fn}"
            backup_path = os.path.join(backups_dir, backup_name)
            try:
                with open(full, "rb") as src, open(backup_path, "wb") as dst:
                    dst.write(src.read())
            except Exception:
                # Backup failure shouldn't block repair attempt, but count it
                print(f"[REPAIR][WARN] Could not backup: {fn}")
                logger.warning("Repair backup failed for %s", full, exc_info=True)

            # Validate/normalize via Project model
            proj = Project.load(full)
            data = proj.to_dict()
            _atomic_write(full, data)
            print(f"[REPAIR][OK] {fn}")
        except Exception as e:
            failures += 1
            print(f"[REPAIR][FAIL] {fn} :: {e}")
            logger.error("Repair failed for %s", full, exc_info=True)

    if failures:
        print(f"[REPAIR] Completed with failures: {failures}")
        return 1

    print("[REPAIR] Completed successfully.")
    return 0


# If launched directly by Python (e.g., from the .bat launcher), support utility flags.
# Only execute when run as main script, not when imported by tests or other modules.
if __name__ == "__main__":
    if SELFTEST_MODE:
        raise SystemExit(run_selftest())

    if REPAIR_MODE:
        raise SystemExit(run_repair())

    # Default: run the Streamlit UI (Streamlit will execute this script).
    # Check if we're already running inside Streamlit to avoid double-initialization
    should_launch = True
    try:
        from streamlit import runtime
        if runtime.exists():
            # Already running in Streamlit, don't launch again
            should_launch = False
    except ImportError:
        # streamlit.runtime doesn't exist in older versions, try to launch anyway
        pass

    if should_launch:
        import streamlit.web.cli as stcli
        sys.argv = ["streamlit", "run", __file__]
        sys.exit(stcli.main())
