#!/usr/bin/env python3
# Mantis_Studio.py — MANTIS Studio
#
# Run:
#   python -m streamlit run Mantis_Studio.py
#
# Requirements:
#   streamlit>=1.42.0
#   requests
#   Authlib>=1.3.2
#   python-dotenv (optional)
#   pandas
#   plotly
#
# Notes:
# - This preserves ALL current features from your v47 generator build:
#   Projects (create/load/delete), Outline generation/title generation/reverse engineer,
#   Entity scanning & enrich, World Bible categories, Chapters w/ AI autowrite,
#   Summaries, Rewrite presets, Export markdown, Import story text, Auto-save, Ghost text flow.
#
# - This is a UI/first-time appearance upgrade:
#   First-run welcome, clearer home, cleaner sidebar, better empty states, safer buttons/layout.

import os
import re
import json
import random
import time
import datetime
import uuid
import difflib
import logging
import shutil
from dataclasses import dataclass, field, asdict, fields
from typing import Dict, List, Optional, Any, Generator, Callable

import requests
# (UI-only imports are loaded inside _run_ui() so selftests can run without Streamlit installed.)

import sys
from app.utils.navigation import get_nav_config
from app.utils import auth


# ===== v45 BRANDING (SAFE, ORIGINAL TEMPLATE) =====
import base64
# ==================================================

SELFTEST_MODE = "--selftest" in sys.argv
REPAIR_MODE = "--repair" in sys.argv


# ============================================================
# 1) CONFIG
# ============================================================

def get_app_version() -> str:
    return os.getenv("MANTIS_APP_VERSION", "47 (Chronicle • One-File)")


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


os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)
os.makedirs(AppConfig.USERS_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MANTIS")


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


def _truncate_prompt(prompt: str, limit: int) -> str:
    if not prompt:
        return prompt
    if len(prompt) <= limit:
        return prompt
    logger.warning("Prompt length %s exceeded limit %s; truncating", len(prompt), limit)
    return prompt[:limit]


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


def get_user_projects_dir(user_id: str) -> str:
    user_dir = os.path.join(AppConfig.USERS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


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
        os.makedirs(storage_dir, exist_ok=True)
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
            return path
        try:
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
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning("Save attempt %s failed for %s", attempt, path, exc_info=True)
                    time.sleep(0.1)
            else:
                logger.error("Save failed after retries for %s: %s", path, last_error)
        finally:
            _release_lock(lock_path)

        self.filepath = path
        self.storage_dir = storage_dir
        self.last_modified = time.time()
        return path

    @classmethod
    def load(cls, path: str) -> "Project":
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

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
    def __init__(self, timeout: int = AppConfig.GROQ_TIMEOUT, base_url: Optional[str] = None):
        self.base_url = (base_url or AppConfig.GROQ_API_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

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
            yield "Groq model not configured."
            return

        api_key = (AppConfig.GROQ_API_KEY or "").strip()
        if not api_key:
            yield "Groq API key not configured."
            return

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
                    yield "Groq response empty."
            except Exception:
                logger.warning("Groq non-stream generation failed", exc_info=True)
                yield "Groq generation failed."

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
            logger.warning("Groq streaming generation failed, retrying non-stream", exc_info=True)
            yield from _groq_non_stream()

    def generate(self, prompt: str, model: str) -> Dict[str, str]:
        full_text = ""
        for chunk in self.generate_stream(prompt, model):
            full_text += chunk
        return {"text": full_text}

    def generate_json(self, prompt: str, model: str) -> Optional[List[Dict[str, Any]]]:
        res = self.generate(f"Return ONLY valid JSON. List of objects. No markdown.\n\n{prompt}", model)
        txt = (res.get("text", "") or "").strip()
        txt = re.sub(r"```json\s*", "", txt)
        txt = re.sub(r"```\s*", "", txt).strip()
        try:
            d = json.loads(txt)
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                return [d]
            return None
        except Exception:
            logger.warning("JSON parse failed for AI response", exc_info=True)
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

    widget_counters: Dict[tuple, int] = {}
    key_prefix_stack: List[str] = []

    ASSETS_DIR = Path(__file__).parent / "assets"

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

    def _maybe_wrap(name: str, widget_type: str, has_label: bool = True) -> None:
        if not hasattr(st, name):
            return
        original = getattr(st, name)
        wrapped = _wrap_widget(original, widget_type) if has_label else _wrap_widget_no_label(original, widget_type)
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
    _maybe_wrap("page_link", "page_link")

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
        if not AppConfig.GROQ_API_KEY or not get_ai_model():
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

    def render_privacy():
        st.markdown("## Privacy Policy\n\nLocal-only storage. No analytics.")

    def render_terms():
        st.markdown("## Terms of Service\n\nProvided as-is for creative use.")

    def render_copyright():
        st.markdown("## Copyright\n\n© MANTIS Studio")

    icon_path = ASSETS_DIR / "mantis_logo_trans.png"
    page_icon = str(icon_path) if icon_path.exists() else "🪲"
    st.set_page_config(page_title=AppConfig.APP_NAME, page_icon=page_icon, layout="wide")

    raw_user = st.user
    config_data = load_app_config()

    raw_user_id = auth.get_user_id(raw_user) if raw_user else ""
    has_auth_identity = bool(raw_user and raw_user_id)
    user = raw_user if has_auth_identity else None
    is_guest = not has_auth_identity
    st.session_state["guest_mode"] = is_guest
    if is_guest:
        st.session_state.setdefault("guest_session_id", uuid.uuid4().hex[:8])

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
            "bg": "#f8fafc",
            "bg_glow": "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)",
            "text": "#0f172a",
            "muted": "#6b7280",
            "input_bg": "#ffffff",
            "input_border": "#cce5d6",
            "button_bg": "linear-gradient(180deg, #ffffff, #ecfdf3)",
            "button_border": "#cdebd9",
            "button_hover_border": "#22c55e",
            "primary_bg": "linear-gradient(135deg, #34d399, #22c55e)",
            "primary_border": "rgba(34,197,94,0.25)",
            "primary_hover_border": "#16a34a",
            "card_bg": "#ffffff",
            "card_border": "#e1efe6",
            "sidebar_bg": "linear-gradient(180deg, #f3f4f6, #e5e7eb)",
            "sidebar_border": "#d1d5db",
            "sidebar_title": "#166534",
            "divider": "#deeee3",
            "expander_border": "#d7e9df",
            "header_gradient": "linear-gradient(135deg, #e6f9ef, #c7f4dc)",
            "header_logo_bg": "#e7fdf1",
            "header_sub": "#2f6f43",
            "shadow_strong": "0 12px 24px rgba(12,26,18,0.08)",
            "shadow_button": "0 8px 16px rgba(12,26,18,0.12)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(255,255,255,0.9), rgba(243,244,246,0.95))",
            "sidebar_brand_border": "rgba(15,23,42,0.08)",
            "sidebar_logo_bg": "rgba(15,23,42,0.08)",
            "accent": "#22c55e",
            "accent_soft": "rgba(34,197,94,0.18)",
            "accent_glow": "rgba(34,197,94,0.35)",
            "surface": "rgba(255,255,255,0.9)",
            "surface_alt": "rgba(241,245,249,0.95)",
            "success": "#16a34a",
            "warning": "#d97706",
        },
    }
    tokens = theme_tokens[theme]

    st.markdown(
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
        background: rgba(0,0,0,0.35);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow:
            inset 0 0 0 1px rgba(255,255,255,0.15),
            0 0 18px rgba(34,197,94,0.45);
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

    .stButton>button {{
        border-radius: 16px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.1rem !important;
        transition: all 0.15s ease-in-out;
        border: 1px solid var(--mantis-button-border) !important;
        background: var(--mantis-button-bg) !important;
        color: var(--mantis-text) !important;
    }}
    .stButton>button:hover {{
        transform: translateY(-1px);
        border-color: var(--mantis-button-hover-border) !important;
        box-shadow: var(--mantis-shadow-button);
    }}
    .stButton>button:active {{ transform: translateY(0); }}
    .stButton>button:focus {{ outline: none !important; box-shadow: none !important; }}

    /* --- BUTTON HIERARCHY --- */
    .stButton>button[kind="primary"] {{
        background: var(--mantis-primary-bg) !important;
        border-color: var(--mantis-primary-border) !important;
        box-shadow: var(--mantis-shadow-button);
        color: #ffffff !important;
    }}
    .stButton>button[kind="primary"]:hover {{
        border-color: var(--mantis-primary-hover-border) !important;
        box-shadow: var(--mantis-shadow-strong);
    }}
    .stButton>button[kind="secondary"] {{
        background: var(--mantis-button-bg) !important;
    }}


    [data-testid="stVerticalBlock"] [data-testid="stContainer"] {{ border-radius: 16px !important; }}
    .stExpander {{ border: 1px solid var(--mantis-expander-border) !important; border-radius: 16px !important; }}
    hr {{ border-color: var(--mantis-divider) !important; }}
    section[data-testid="stSidebar"] {{ background: var(--mantis-sidebar-bg); border-right: 1px solid var(--mantis-sidebar-border); }}
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {{ color: var(--mantis-text); }}
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
        unsafe_allow_html=True,
    )

    # --- BRAND HEADER (UI only) ---
    header_logo_b64 = asset_base64("mantis_logo_trans.png")
    header_logo_html = (
        f'<img src="data:image/png;base64,{header_logo_b64}" alt="MANTIS logo" />'
        if header_logo_b64
        else '<span class="mantis-logo-fallback">M</span>'
    )
    st.markdown(
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
                        Modular narrative workspace
                    </div>
                </div>
            </div>
            <div class="mantis-header-right">
                <span class="mantis-pill">Workspace</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
    if "openai_base_url" not in st.session_state:
        st.session_state.openai_base_url = config_data.get(
            "openai_base_url",
            AppConfig.OPENAI_API_URL,
        )
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = config_data.get(
            "openai_api_key",
            AppConfig.OPENAI_API_KEY,
        )
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = config_data.get(
            "openai_model",
            AppConfig.OPENAI_MODEL,
        )
    if "openai_model_list" not in st.session_state:
        st.session_state.openai_model_list = []
    if "openai_model_tests" not in st.session_state:
        st.session_state.openai_model_tests = {}
    if "ui_theme" not in st.session_state:
        st.session_state.ui_theme = config_data.get("ui_theme", "Dark")
    if "groq_base_url" not in st.session_state:
        st.session_state.groq_base_url = config_data.get("groq_base_url", AppConfig.GROQ_API_URL)
    if "groq_api_key" not in st.session_state:
        st.session_state.groq_api_key = config_data.get("groq_api_key", AppConfig.GROQ_API_KEY)
    if "groq_model" not in st.session_state:
        st.session_state.groq_model = config_data.get("groq_model", AppConfig.DEFAULT_MODEL)
    if "groq_model_list" not in st.session_state:
        st.session_state.groq_model_list = []
    if "groq_model_tests" not in st.session_state:
        st.session_state.groq_model_tests = {}
    if "_force_nav" not in st.session_state:
        st.session_state._force_nav = False

    AppConfig.GROQ_API_URL = st.session_state.groq_base_url
    AppConfig.GROQ_API_KEY = st.session_state.groq_api_key
    AppConfig.DEFAULT_MODEL = st.session_state.groq_model
    AppConfig.OPENAI_API_URL = st.session_state.openai_base_url
    AppConfig.OPENAI_API_KEY = st.session_state.openai_api_key
    AppConfig.OPENAI_MODEL = st.session_state.openai_model

    def open_legal_page() -> None:
        if hasattr(st, "switch_page"):
            st.switch_page("pages/legal.py")
            return
        st.toast("Open the Legal page from the sidebar menu if it did not open.")

    GUEST_BANNER_TEXT = (
        "Guest mode: creations are not saved. Create an account to save projects across devices."
    )

    def open_account_access(action: str, reason: str) -> None:
        st.session_state["auth_redirect_action"] = action
        st.session_state["auth_redirect_reason"] = reason
        st.session_state["auth_redirect_return_page"] = st.session_state.get("page", "home")
        if hasattr(st, "switch_page"):
            st.switch_page("pages/account.py")
        else:
            st.info("Account access is available from the sidebar.")

    def persist_project(
        project: "Project",
        *,
        prompt_on_guest: bool = False,
        action: str = "save",
    ) -> bool:
        if not is_guest:
            project.save()
            return True
        if prompt_on_guest:
            open_account_access(action, GUEST_BANNER_TEXT)
        else:
            project.last_modified = time.time()
        return False

    def render_guest_banner(context: str) -> None:
        if not is_guest:
            return
        with st.container(border=True):
            st.markdown("#### 👋 Guest mode")
            st.caption(GUEST_BANNER_TEXT)
            banner_cols = st.columns([1, 1])
            with banner_cols[0]:
                if st.button(
                    "Create account to save",
                    type="primary",
                    use_container_width=True,
                    key=f"guest_banner_create_{context}",
                ):
                    open_account_access("signup", GUEST_BANNER_TEXT)
            with banner_cols[1]:
                if st.button(
                    "Enable cloud save",
                    use_container_width=True,
                    key=f"guest_banner_cloud_{context}",
                ):
                    open_account_access("enable_cloud_save", GUEST_BANNER_TEXT)

    def render_footer() -> None:
        st.markdown("---")
        f1, f2, f3 = st.columns([1.2, 1, 1])
        with f1:
            if st.button("Legal & Privacy", use_container_width=True, key="footer_legal"):
                open_legal_page()
        with f2:
            st.caption(f"Version {AppConfig.VERSION}")
        with f3:
            st.caption("Built with Streamlit • MANTIS Studio")

    if is_guest:
        user_id = f"guest_{st.session_state['guest_session_id']}"
        if raw_user and not raw_user_id:
            st.warning(
                "We couldn't read a user identifier from your login, so you're in Guest mode. "
                "Sign out and sign back in to enable cloud saving."
            )
            auth.logout_button(key="auth_missing_user_id_logout")
    else:
        if not auth.is_user_allowed(user):
            st.error("Your account is not authorized to access this workspace.")
            auth.logout_button(label="Sign out", key="auth_denied_logout")
            st.stop()
        user_id = raw_user_id

    if st.session_state.user_id != user_id:
        st.session_state.user_id = user_id
        st.session_state.projects_dir = get_user_projects_dir(user_id)
        st.session_state.project = None
        st.session_state.page = "home"
    elif not st.session_state.projects_dir:
        st.session_state.projects_dir = get_user_projects_dir(user_id)

    if is_guest:
        st.session_state.auto_save = False

    guest_continue_action = st.session_state.get("guest_continue_action")
    if guest_continue_action and guest_continue_action != "create_project":
        st.session_state["guest_continue_action"] = None
        st.toast("You're still in Guest mode. Saving stays disabled until you create an account.")

    # Reliable navigation rerun (avoids Streamlit edge cases when returning early)
    if st.session_state.get("_force_nav"):
        st.session_state._force_nav = False
        st.rerun()

    def get_ai_model() -> str:
        return st.session_state.get("groq_model", AppConfig.DEFAULT_MODEL)

    def save_p():
        if st.session_state.project and st.session_state.auto_save:
            persist_project(st.session_state.project)

    def get_active_projects_dir() -> str:
        return st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR

    def load_project_safe(path: str, context: str = "project") -> Optional["Project"]:
        try:
            return Project.load(path)
        except Exception:
            logger.warning("Failed to load %s: %s", context, path, exc_info=True)
            st.error("We couldn't open that project file. It may be missing or corrupted.")
            return None

    def render_page_header(
        title: str,
        subtitle: str,
        primary_label: Optional[str] = None,
        primary_action: Optional[Callable[[], None]] = None,
        secondary_label: Optional[str] = None,
        secondary_action: Optional[Callable[[], None]] = None,
        tag: Optional[str] = None,
        key_prefix: str = "page_header",
    ) -> None:
        with st.container(border=True):
            left, right = st.columns([2.4, 1])
            with left:
                tag_html = f"<span class='mantis-tag'>{tag}</span>" if tag else ""
                st.markdown(
                    f"""
                    <div class="mantis-page-header">
                        <div>
                            <div class="mantis-page-title">{title} {tag_html}</div>
                            <div class="mantis-page-sub">{subtitle}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with right:
                if primary_label and primary_action:
                    if st.button(primary_label, type="primary", use_container_width=True, key=f"{key_prefix}__primary"):
                        primary_action()
                if secondary_label and secondary_action:
                    if st.button(secondary_label, use_container_width=True, key=f"{key_prefix}__secondary"):
                        secondary_action()

    @st.cache_data(show_spinner=False)
    def _cached_models(base_url: str, api_key: str) -> List[str]:
        return AIEngine(base_url=base_url).probe_models(api_key)

    def refresh_models():
        st.session_state.groq_model_list = _cached_models(
            st.session_state.groq_base_url,
            st.session_state.groq_api_key,
        ) or []

    def refresh_openai_models():
        st.session_state.openai_model_list = _cached_models(
            st.session_state.openai_base_url,
            st.session_state.openai_api_key,
        ) or []

    def save_app_settings():
        data = {
            "groq_base_url": st.session_state.groq_base_url,
            "groq_api_key": st.session_state.groq_api_key,
            "groq_model": st.session_state.groq_model,
            "openai_base_url": st.session_state.openai_base_url,
            "openai_api_key": st.session_state.openai_api_key,
            "openai_model": st.session_state.openai_model,
            "ui_theme": st.session_state.ui_theme,
            "daily_word_goal": int(st.session_state.daily_word_goal),
            "weekly_sessions_goal": int(st.session_state.weekly_sessions_goal),
            "focus_minutes": int(st.session_state.focus_minutes),
            "activity_log": list(st.session_state.activity_log),
        }
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

    @st.cache_data(show_spinner=False)
    def _load_recent_projects(active_dir: str, refresh_token: int) -> List[Dict[str, Any]]:
        if not os.path.exists(active_dir):
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
        queue = st.session_state.setdefault("world_bible_review", [])
        key = (
            f"{Project._normalize_category(item.get('category'))}|"
            f"{Project._normalize_entity_name(item.get('name'))}|"
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
    if query == "privacy":
        render_privacy()
        render_footer()
        return
    if query == "terms":
        render_terms()
        render_footer()
        return
    if query == "copyright":
        render_copyright()
        render_footer()
        return

    def render_ai_settings():
        def refresh_all_models() -> None:
            st.cache_data.clear()
            refresh_models()
            refresh_openai_models()
            st.toast("Model list refreshed")

        render_page_header(
            "AI Tools",
            "Connect providers, choose models, and validate access.",
            primary_label="💾 Save settings",
            primary_action=save_app_settings,
            secondary_label="↻ Refresh models",
            secondary_action=refresh_all_models,
            tag="Settings",
            key_prefix="ai_header",
        )
        if st.session_state.pop("ai_settings__flash", False):
            st.success("AI Settings opened. Update providers and models below.")

        status_cols = st.columns(3)
        with status_cols[0]:
            st.metric("Groq", "Connected" if st.session_state.groq_api_key else "Missing key")
        with status_cols[1]:
            st.metric("OpenAI", "Connected" if st.session_state.openai_api_key else "Missing key")
        with status_cols[2]:
            st.metric("Active model", st.session_state.groq_model or "Not set")

        provider_cols = st.columns(2)
        with provider_cols[0]:
            with st.container(border=True):
                st.markdown("### 🤖 Groq")
                groq_url = st.text_input("Groq Base URL", value=st.session_state.groq_base_url)
                if groq_url != st.session_state.groq_base_url:
                    st.session_state.groq_base_url = groq_url
                    AppConfig.GROQ_API_URL = groq_url

                groq_key = st.text_input(
                    "Groq API Key",
                    value=st.session_state.groq_api_key,
                    type="password",
                    help="Required for Groq cloud models.",
                )
                if groq_key != st.session_state.groq_api_key:
                    st.session_state.groq_api_key = groq_key
                    AppConfig.GROQ_API_KEY = groq_key

                if st.button("↻ Fetch Groq Models", use_container_width=True):
                    models, error_message = fetch_groq_models(
                        st.session_state.groq_base_url,
                        st.session_state.groq_api_key,
                    )
                    if models:
                        st.session_state.groq_model_list = models
                        st.session_state.groq_model_tests = {}
                        st.toast(f"Loaded {len(models)} models.")
                    else:
                        st.session_state.groq_model_list = []
                        st.session_state.groq_model_tests = {}
                        st.error(f"Model fetch failed. {error_message or 'Check the base URL and key.'}")

                if st.session_state.groq_model_list:
                    models = st.session_state.groq_model_list
                    idx = 0
                    if st.session_state.groq_model in models:
                        idx = models.index(st.session_state.groq_model)
                    groq_model = st.selectbox("Groq Model", models, index=idx)

                    if st.button("🧪 Test All Groq Models", use_container_width=True):
                        results = {}
                        total = len(models)
                        progress = st.progress(0)
                        for i, model_name in enumerate(models, start=1):
                            ok, error_message = test_groq_model(
                                st.session_state.groq_base_url,
                                st.session_state.groq_api_key,
                                model_name,
                            )
                            results[model_name] = "" if ok else error_message
                            progress.progress(i / total)
                        st.session_state.groq_model_tests = results
                        failures = [m for m, err in results.items() if err]
                        if failures:
                            st.warning(f"{len(failures)} models failed. Expand results for details.")
                        else:
                            st.success("All models responded successfully.")

                    if st.session_state.groq_model_tests:
                        with st.expander("Groq model test results", expanded=False):
                            for model_name, error_message in sorted(
                                st.session_state.groq_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"{model_name}: {error_message}")
                                else:
                                    st.success(f"{model_name}: OK")
                else:
                    groq_model = st.text_input("Groq Model", value=st.session_state.groq_model)

                if groq_model != st.session_state.groq_model:
                    st.session_state.groq_model = groq_model
                    AppConfig.DEFAULT_MODEL = groq_model

                st.markdown(
                    "[Get a free Groq API key](https://console.groq.com/keys) to enable cloud models."
                )
                if not st.session_state.groq_api_key:
                    st.info("No Groq API key yet. Create one above and paste it here to unlock Groq models.")
                if st.button("🔌 Test Groq Connection", use_container_width=True):
                    ok = test_groq_connection(
                        st.session_state.groq_base_url,
                        st.session_state.groq_api_key,
                    )
                    if ok:
                        st.success("Groq connection OK.")
                    else:
                        st.error("Groq connection failed. Check your base URL and key.")

        with provider_cols[1]:
            with st.container(border=True):
                st.markdown("### ✨ OpenAI")
                openai_url = st.text_input("OpenAI Base URL", value=st.session_state.openai_base_url)
                if openai_url != st.session_state.openai_base_url:
                    st.session_state.openai_base_url = openai_url
                    AppConfig.OPENAI_API_URL = openai_url

                openai_key = st.text_input(
                    "OpenAI API Key",
                    value=st.session_state.openai_api_key,
                    type="password",
                    help="Required for OpenAI cloud models.",
                )
                if openai_key != st.session_state.openai_api_key:
                    st.session_state.openai_api_key = openai_key
                    AppConfig.OPENAI_API_KEY = openai_key
                if not st.session_state.openai_api_key:
                    st.info("No OpenAI API key yet. Create one and paste it here to unlock OpenAI models.")

                if st.button("↻ Fetch OpenAI Models", use_container_width=True):
                    models, error_message = fetch_openai_models(
                        st.session_state.openai_base_url,
                        st.session_state.openai_api_key,
                    )
                    if models:
                        st.session_state.openai_model_list = models
                        st.session_state.openai_model_tests = {}
                        st.toast(f"Loaded {len(models)} models.")
                    else:
                        st.session_state.openai_model_list = []
                        st.session_state.openai_model_tests = {}
                        st.error(f"Model fetch failed. {error_message or 'Check the base URL and key.'}")

                if st.session_state.openai_model_list:
                    models = st.session_state.openai_model_list
                    idx = 0
                    if st.session_state.openai_model in models:
                        idx = models.index(st.session_state.openai_model)
                    openai_model = st.selectbox("OpenAI Model", models, index=idx)

                    if st.button("🧪 Test All OpenAI Models", use_container_width=True):
                        results = {}
                        total = len(models)
                        progress = st.progress(0)
                        for i, model_name in enumerate(models, start=1):
                            ok, error_message = test_openai_model(
                                st.session_state.openai_base_url,
                                st.session_state.openai_api_key,
                                model_name,
                            )
                            results[model_name] = "" if ok else error_message
                            progress.progress(i / total)
                        st.session_state.openai_model_tests = results
                        failures = [m for m, err in results.items() if err]
                        if failures:
                            st.warning(f"{len(failures)} models failed. Expand results for details.")
                        else:
                            st.success("All models responded successfully.")

                    if st.session_state.openai_model_tests:
                        with st.expander("OpenAI model test results", expanded=False):
                            for model_name, error_message in sorted(
                                st.session_state.openai_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"{model_name}: {error_message}")
                                else:
                                    st.success(f"{model_name}: OK")
                else:
                    openai_model = st.text_input("OpenAI Model", value=st.session_state.openai_model)

                if openai_model != st.session_state.openai_model:
                    st.session_state.openai_model = openai_model
                    AppConfig.OPENAI_MODEL = openai_model

                st.markdown(
                    "[Create an OpenAI account](https://platform.openai.com/api-keys) to get an API key."
                )
                if st.button("🔌 Test OpenAI Connection", use_container_width=True):
                    ok = test_openai_connection(
                        st.session_state.openai_base_url,
                        st.session_state.openai_api_key,
                    )
                    if ok:
                        st.success("OpenAI connection OK.")
                    else:
                        st.error("OpenAI connection failed. Check your base URL and key.")

        with st.container(border=True):
            st.markdown("### ✅ Actions")
            action_cols = st.columns(4)
            with action_cols[0]:
                if is_guest:
                    st.checkbox("Auto-save (cloud)", key="auto_save", disabled=True)
                    if st.button("Enable cloud save", use_container_width=True, key="guest_enable_cloud_save"):
                        open_account_access("enable_cloud_save", GUEST_BANNER_TEXT)
                else:
                    st.checkbox("Auto-save", key="auto_save")
            with action_cols[1]:
                if st.button("↻ Refresh Groq Models", use_container_width=True):
                    st.cache_data.clear()
                    refresh_models()
                    st.toast("Model list refreshed")
            with action_cols[2]:
                if st.button("↻ Refresh OpenAI Models", use_container_width=True):
                    st.cache_data.clear()
                    refresh_openai_models()
                    st.toast("OpenAI model list refreshed")
            with action_cols[3]:
                if st.button("💾 Save AI Settings", use_container_width=True):
                    save_app_settings()

    with st.sidebar:
        with key_scope("sidebar"):
            sidebar_logo_b64 = asset_base64("mantis_logo_trans.png")
            sidebar_logo_html = (
                f'<img src="data:image/png;base64,{sidebar_logo_b64}" alt="MANTIS logo" />'
                if sidebar_logo_b64
                else '<span class="mantis-logo-fallback">MANTIS</span>'
            )
            st.markdown(
                f"""
            <div class="mantis-sidebar-brand">
                <div class="mantis-sidebar-logo">
                    {sidebar_logo_html}
                </div>
                <div>
                    <div class="mantis-sidebar-title">MANTIS Studio — v{AppConfig.VERSION}</div>
                    <div class="mantis-sidebar-sub">Modular narrative workspace</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.markdown("### 👤 Account")
            if is_guest:
                st.markdown("**Guest mode**")
                st.caption("Projects and edits are not saved across devices.")
                if st.button(
                    "Create account to save",
                    type="primary",
                    use_container_width=True,
                    key="sidebar_guest_create_account",
                ):
                    open_account_access("signup", GUEST_BANNER_TEXT)
                if st.button(
                    "Enable cloud save",
                    use_container_width=True,
                    key="sidebar_guest_cloud_save",
                ):
                    open_account_access("enable_cloud_save", GUEST_BANNER_TEXT)
            else:
                account_cols = st.columns([1, 2.6])
                display_name = auth.get_user_display_name(user)
                email = auth.get_user_email(user)
                avatar_url = auth.get_user_avatar_url(user)
                with account_cols[0]:
                    if avatar_url:
                        st.image(avatar_url, width=44)
                    else:
                        st.markdown(
                            f"<div class='mantis-avatar'>{auth.get_user_initials(user)}</div>",
                            unsafe_allow_html=True,
                        )
                with account_cols[1]:
                    st.markdown(f"**{display_name}**")
                    if email:
                        st.caption(email)
                    if auth.user_is_admin(user):
                        st.caption("Admin")

                manage_url = auth.get_manage_account_url(user)
                if manage_url:
                    st.link_button("Manage account", manage_url, use_container_width=True)
                auth.logout_button(
                    key="sidebar_logout",
                    extra_state_keys=["projects_dir", "project", "page", "_force_nav"],
                )

            st.markdown("### 🎨 Appearance")
            st.selectbox("Theme", ["Dark", "Light"], key="ui_theme")
            st.divider()

            if st.session_state.project:
                p = st.session_state.project
                st.markdown("### 📖 Project")
                st.caption(p.title)
                st.caption(f"🗂 Projects folder: `{get_active_projects_dir()}`")
                st.caption(f"📚 Total words: {p.get_total_word_count()}")

            st.divider()
            st.markdown("### 🧭 Navigation")
            st.caption("Write • World Bible • Memory • Insights • Export • Settings")

            nav_labels, pmap = get_nav_config(bool(st.session_state.project))
            current_page = st.session_state.page
            reverse_map = {v: k for k, v in pmap.items()}
            current_label = reverse_map.get(current_page, "Dashboard")
            try:
                current_index = nav_labels.index(current_label)
            except ValueError:
                current_index = 0
            nav = st.radio(
                "Navigation",
                nav_labels,
                index=current_index,
                label_visibility="collapsed",
            )
            if pmap[nav] != st.session_state.page:
                st.session_state.page = pmap[nav]
                st.rerun()

            if st.session_state.project:
                st.divider()

                cA, cB = st.columns(2)
                with cA:
                    if st.button("💾 Save", type="primary", use_container_width=True):
                        if persist_project(p, prompt_on_guest=True, action="save"):
                            st.toast("Saved")
                with cB:
                    if st.button("✖ Close", use_container_width=True):
                        save_p()
                        st.session_state.project = None
                        st.session_state.page = "home"
                        st.rerun()
            else:
                st.info("No project loaded.")

    def render_home():
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)
        has_project = bool(recent_projects)

        render_guest_banner("dashboard")

        banner_bytes = load_asset_bytes("mantis_banner_dark.png")
        st.markdown('<div class="mantis-banner">', unsafe_allow_html=True)
        if banner_bytes:
            st.image(banner_bytes, use_container_width=True)
        else:
            st.markdown("## MANTIS Studio")
        st.markdown("</div>", unsafe_allow_html=True)

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
        weekly_goal = max(1, int(st.session_state.weekly_sessions_goal))
        weekly_count = _weekly_activity_count()
        canon_icon, canon_label = get_canon_health()
        latest_chapter_label = "You last worked on Chapter — · recently"
        latest_chapter_index = None
        latest_chapter_id = None
        latest_ts = None

        if active_project and getattr(active_project, "chapters", None):
            ch = max(
                active_project.chapters.values(),
                key=lambda c: (c.modified_at or c.created_at or 0),
            )
            latest_ts = ch.modified_at or ch.created_at
            latest_chapter_index = ch.index
            latest_chapter_id = ch.id
            latest_chapter_label = f"Latest: Chapter {ch.index} — {ch.title}"

        primary_label = "✨ Start your story"
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
                    return
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
                st.session_state.page = "projects"
                st.rerun()
            else:
                st.session_state.page = "projects"
                st.toast("Select a project to export.")
                st.rerun()

        def open_ai_settings() -> None:
            st.session_state.ai_settings__flash = True
            st.session_state.page = "ai"
            st.rerun()

        def open_primary_cta() -> None:
            if primary_target == "chapters" and latest_chapter_id:
                st.session_state.curr_chap_id = latest_chapter_id
            open_recent_project(primary_target)

        def open_new_project() -> None:
            st.session_state.page = "projects"
            st.rerun()

        render_page_header(
            "Dashboard",
            "Your studio cockpit for progress, projects, and next steps.",
            primary_label=primary_label,
            primary_action=open_primary_cta,
            secondary_label="➕ New project",
            secondary_action=open_new_project,
            tag="Workspace",
            key_prefix="dashboard_header",
        )

        hero_logo_bytes = load_asset_bytes("mantis_logo_trans.png")
        with st.container(border=True):
            hero_cols = st.columns([2.4, 1])
            with hero_cols[0]:
                logo_col, text_col = st.columns([0.18, 0.82])
                with logo_col:
                    if hero_logo_bytes:
                        st.image(hero_logo_bytes, width=64)
                    else:
                        st.markdown("### M")
                with text_col:
                    st.markdown("### MANTIS Studio")
                    st.markdown("#### About MANTIS")
                    st.markdown("**A premium command deck for storytellers.**")
                    st.markdown(
                        """
                        - AI-assisted drafting, summaries, and rewrite presets
                        - World Bible to keep canon, characters, and lore aligned
                        - Memory + insights to track momentum and continuity
                        - Clean markdown exports for editors and collaborators
                        """
                    )
                    st.caption("Built for writers who want clarity, speed, and control.")
                    if st.button("Learn more", key="dashboard__about_learn_more"):
                        open_legal_page()
            with hero_cols[1]:
                st.markdown(
                    f"""
                    <div style="display:flex; gap:8px; justify-content:flex-end; flex-wrap:wrap;">
                        <span class="mantis-pill">Workspace</span>
                        <span class="mantis-pill">v{AppConfig.VERSION}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        header_cols = st.columns([2.2, 1])
        with header_cols[0]:
            with card("Current focus", "Suggested next step based on your latest activity."):
                st.markdown(f"## {project_title}")
                st.caption(latest_chapter_label)
                if st.button(primary_label, type="primary", use_container_width=True):
                    if primary_target == "chapters" and latest_chapter_id:
                        st.session_state.curr_chap_id = latest_chapter_id
                    open_recent_project(primary_target)
                action_row = st.columns(2)
                with action_row[0]:
                    if st.button("📂 Resume project", use_container_width=True, disabled=not recent_projects):
                        open_recent_project("chapters")
                with action_row[1]:
                    if st.button("🧭 New project", use_container_width=True):
                        st.session_state.page = "projects"
                        st.rerun()

        with header_cols[1]:
            with card("Workspace snapshot"):
                st.markdown("#### Project status")
                k1, k2 = st.columns(2)
                with k1:
                    stat_tile("Active projects", str(len(recent_projects)), icon="📁")
                with k2:
                    stat_tile("Latest genre", (recent_snapshot or {}).get("genre", "—"), icon="🏷️")
                k3, k4 = st.columns(2)
                with k3:
                    stat_tile("Weekly sessions", f"{weekly_count}/{weekly_goal}", icon="🗓️")
                with k4:
                    stat_tile("Writing streak", f"{_activity_streak()} days", icon="🔥")
                st.caption(f"Canon health: {canon_icon} {canon_label}.")

        section_header("Quick actions", "Jump straight into your most-used tools.")
        quick_row_one = st.columns(3)
        with quick_row_one[0]:
            if action_card("✍️ Editor", "Draft chapters and summaries.", help_text="Open the chapter editor."):
                open_recent_project("chapters")
        with quick_row_one[1]:
            if action_card("📝 Outline", "Plan beats, arcs, and chapter flow."):
                open_recent_project("outline")
        with quick_row_one[2]:
            if action_card("🌍 World Bible", "Characters, places, factions, lore."):
                open_recent_project("world")

        quick_row_two = st.columns(3)
        with quick_row_two[0]:
            if action_card("🧠 Memory", "Hard canon rules and guidelines."):
                open_recent_project("world", focus_tab="Memory")
        with quick_row_two[1]:
            if action_card("📊 Insights", "Canon health and analytics."):
                open_recent_project("world", focus_tab="Insights")
        with quick_row_two[2]:
            if action_card("⬇️ Export", "Download your project as markdown.", button_label="Export"):
                open_export()

        with st.container(border=True):
            st.markdown("#### My projects")
            st.caption("Select a project to open and pick up where you left off.")
            if not recent_projects:
                st.info("📭 No projects yet. Create one to get started.")
            else:
                for project_entry in recent_projects[:5]:
                    meta = project_entry.get("meta", {})
                    title = meta.get("title") or os.path.basename(project_entry.get("path", "Untitled"))
                    genre = meta.get("genre") or "—"
                    row = st.columns([2.2, 1, 1])
                    with row[0]:
                        if st.button(f"📂 {title}", use_container_width=True):
                            loaded = load_project_safe(project_entry["path"], context="project")
                            if loaded:
                                st.session_state.project = loaded
                                st.session_state.page = "chapters"
                                st.rerun()
                    with row[1]:
                        st.caption(genre)
                    with row[2]:
                        if st.button("Open", use_container_width=True):
                            loaded = load_project_safe(project_entry["path"], context="project")
                            if loaded:
                                st.session_state.project = loaded
                                st.session_state.page = "chapters"
                                st.rerun()

        with st.container(border=True):
            st.markdown("#### Utilities")
            st.caption("Compact shortcuts to settings, docs, and policies.")
            s1, s2, s3 = st.columns(3)
            with s1:
                st.markdown("**AI Settings**")
                st.caption("Manage providers, models, and API access.")
                if st.button(
                    "⚙️ AI Settings",
                    key="dashboard__utilities_ai_settings",
                    use_container_width=True,
                    help="Jump to AI Tools to configure Groq/OpenAI.",
                ):
                    open_ai_settings()
            with s2:
                st.markdown("**Help Docs**")
                st.caption("Guides, README notes, and updates.")
                st.link_button(
                    "📖 Help Docs",
                    "https://github.com/bigmanjer/Mantis-Studio",
                    use_container_width=True,
                    help="Open the project documentation in a new tab.",
                )
            with s3:
                st.markdown("**Legal**")
                st.caption("Terms, privacy, and IP clarity.")
                if st.button(
                    "⚖️ Legal",
                    key="dashboard__utilities_legal",
                    use_container_width=True,
                    help="Review policies and legal details.",
                ):
                    open_legal_page()

        if not st.session_state.groq_api_key or not st.session_state.openai_api_key:
            with card("🔑 Connect your AI providers", "Unlock generation, summaries, and entity tools with API access."):
                cta_left, cta_right = st.columns(2)
                with cta_left:
                    st.link_button("Create Groq Account", "https://console.groq.com/keys", use_container_width=True)
                with cta_right:
                    st.link_button(
                        "Create OpenAI Account",
                        "https://platform.openai.com/api-keys",
                        use_container_width=True,
                    )


    def render_projects():
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)

        render_guest_banner("projects")

        if is_guest and st.session_state.get("guest_continue_action") == "create_project":
            pending_project = st.session_state.pop("guest_pending_project", None)
            pending_import = st.session_state.pop("guest_pending_import", None)
            if pending_project or pending_import:
                st.session_state["guest_continue_action"] = None
                title = (pending_project or {}).get("title") or _random_project_title()
                genre = (pending_project or {}).get("genre") or _random_project_genres()
                author = (pending_project or {}).get("author") or ""
                p = Project.create(title, author=author, genre=genre, storage_dir=get_active_projects_dir())
                if pending_import:
                    p.import_text_file(pending_import)
                    if AppConfig.GROQ_API_KEY and get_ai_model():
                        with st.spinner("Reviewing document and generating outline..."):
                            p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
                    else:
                        st.warning("Add a Groq API key and model to auto-generate an outline.")
                st.session_state.project = p
                st.session_state.page = "outline"
                st.session_state.first_run = False
                st.toast("Guest project ready. Remember: it won't be saved.")
                st.rerun()

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

        section_header(
            "Start a new project",
            "Set a title, genre, and author details to build your base.",
        )
        with st.container(border=True):
            with st.form("new_project_form", clear_on_submit=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    t = st.text_input("Title", placeholder="e.g., The Chronicle of Ash")
                with c2:
                    g = st.text_input("Genre", placeholder="e.g., Dark Fantasy, Sci-Fi Noir")
                a = st.text_input("Author (optional)", placeholder="Your name")
                submitted = st.form_submit_button("🚀 Initialize Project", type="primary", use_container_width=True)
                if submitted:
                    if is_guest:
                        st.session_state["guest_pending_project"] = {"title": t, "genre": g, "author": a}
                        open_account_access("create_project", GUEST_BANNER_TEXT)
                        return
                    if not t:
                        t = _random_project_title()
                    if not g:
                        g = _random_project_genres()
                    p = Project.create(
                        t,
                        author=a,
                        genre=g,
                        storage_dir=get_active_projects_dir(),
                    )
                    persist_project(p, prompt_on_guest=True, action="create_project")
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
                    if st.button("Import & Analyze", use_container_width=True):
                        if is_guest:
                            st.session_state["guest_pending_import"] = txt
                            open_account_access("create_project", GUEST_BANNER_TEXT)
                            return
                        try:
                            p = Project.create("Imported Project", storage_dir=get_active_projects_dir())
                            p.import_text_file(txt)
                            if AppConfig.GROQ_API_KEY and get_ai_model():
                                with st.spinner("Reviewing document and generating outline..."):
                                    p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
                            else:
                                st.warning("Add a Groq API key and model to auto-generate an outline.")
                            persist_project(p, prompt_on_guest=True, action="create_project")
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


    def render_outline():
        p = st.session_state.project
        def save_outline_action() -> None:
            if persist_project(p, prompt_on_guest=True, action="save"):
                st.toast("Outline saved.")

        def scan_outline_action() -> None:
            extract_entities_ui(p.outline or "", "Outline")

        render_page_header(
            "Outline",
            "Your blueprint. Generate structure, scan entities, and keep the story plan here.",
            primary_label="💾 Save outline",
            primary_action=save_outline_action,
            secondary_label="🔍 Scan entities",
            secondary_action=scan_outline_action,
            tag="Project",
            key_prefix="outline_header",
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
                if st.button("💾 Save Project", type="primary", use_container_width=True):
                    if persist_project(p, prompt_on_guest=True, action="save"):
                        st.toast("Saved")

        left, right = st.columns([2.1, 1])

        # Placeholder for streaming AI-generated outline; lives below the editor, like chapters.
        outline_stream_ph = st.empty()

        with left:
            with st.container(border=True):
                st.markdown("### 🧩 Blueprint")
                val = st.text_area("Plot Outline", p.outline, height=560, key="out_txt", label_visibility="collapsed")
                if val != p.outline:
                    p.outline = val
                    save_p()

                if st.button("💾 Save Outline", use_container_width=True):
                    if persist_project(p, prompt_on_guest=True, action="save"):
                        # Automatically scan entities on save so World Bible stays in sync.
                        extract_entities_ui(p.outline or "", "Outline")
                        st.toast("Outline Saved & Entities Scanned")

        with right:
            with st.container(border=True):
                st.markdown("### 🏗️ Architect (AI)")
                st.caption("Generate a chapter-by-chapter outline and append it to your blueprint.")

                chaps = st.number_input("Chapters", 1, 50, 12)
                if st.button("✨ Generate Structure", type="primary", use_container_width=True):
                    # use outline_stream_ph defined above
                    full = ""
                    prompt = (
                        f"Write a detailed {chaps}-chapter outline for a {p.genre} novel: {p.title}. "
                        "Use structure: Chapter X: [Title] - [Summary]."
                    )
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
            "Track canonical characters, locations, factions, and lore.",
            primary_label="➕ Add entity",
            primary_action=open_add_entity,
            secondary_label="🔍 Run scan",
            secondary_action=lambda: extract_entities_ui(p.outline or "", "Outline"),
            tag="Canon",
            key_prefix="world_header",
        )

        st.markdown(
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
            unsafe_allow_html=True,
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
                    label = f"{item.get('name', 'Unnamed')} • {item.get('category', 'Lore')}"
                    expander_label = build_expander_label(label, str(idx))
                    with st.expander(expander_label):
                        st.markdown(f"**Type:** {item.get('type', 'new').title()}")
                        confidence = item.get("confidence")
                        if confidence is not None:
                            st.markdown(f"**Confidence:** {confidence:.2f}")
                        if item.get("description"):
                            st.markdown("**Suggested Notes**")
                            st.write(item.get("description"))
                        if item.get("aliases"):
                            st.markdown("**Aliases**")
                            st.write(", ".join(item.get("aliases") or []))

                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Apply", key=f"apply_suggestion_{idx}", use_container_width=True):
                                if item.get("type") == "update" and item.get("entity_id"):
                                    ent = p.world_db.get(item.get("entity_id"))
                                    if ent:
                                        ent.merge(item.get("description", ""))
                                        incoming_aliases = item.get("aliases") or []
                                        p._merge_aliases(ent, incoming_aliases, ent.name)
                                else:
                                    p.upsert_entity(
                                        item.get("name", ""),
                                        item.get("category", "Lore"),
                                        item.get("description", ""),
                                        aliases=item.get("aliases") or [],
                                        allow_merge=True,
                                        allow_alias=True,
                                    )
                                review_queue.pop(idx)
                                st.session_state["world_bible_review"] = review_queue
                                persist_project(p)
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
                        st.markdown(
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
                            unsafe_allow_html=True,
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
                if persist_project(p, prompt_on_guest=True, action="save"):
                    st.toast("Memory saved")

            st.divider()
            st.markdown("#### 🔍 Coherence Check")
            scope_cols = st.columns(3)
            with scope_cols[0]:
                scope_outline = st.checkbox("Outline", value=True, key=f"coh_outline_{p.id}")
            with scope_cols[1]:
                scope_world = st.checkbox("World Bible", value=True, key=f"coh_world_{p.id}")
            with scope_cols[2]:
                scope_chapters = st.checkbox("Chapters", value=True, key=f"coh_chapters_{p.id}")

            if st.button("🔍 Run Coherence Check", use_container_width=True):
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
        p = st.session_state.project
        chaps = p.get_ordered_chapters()

        def create_next_chapter() -> None:
            next_idx = len(chaps) + 1 if chaps else 1
            title = f"Chapter {next_idx}"
            if p.outline:
                pat = re.compile(rf"Chapter {next_idx}[:\\s]+(.*?)(?=\\n|$)", re.IGNORECASE)
                match = pat.search(p.outline or "")
                if match:
                    raw = match.group(1).strip()
                    title = sanitize_chapter_title(re.split(r" [-–:] ", raw, 1)[0].strip()) or title
            p.add_chapter(title)
            persist_project(p)
            st.rerun()

        def go_to_outline() -> None:
            st.session_state.page = "outline"
            st.session_state._force_nav = True
            st.rerun()

        render_guest_banner("editor")

        render_page_header(
            "Editor",
            "Write chapters, update summaries, and apply AI improvements.",
            primary_label="➕ New chapter",
            primary_action=create_next_chapter,
            secondary_label="🧩 Go to outline",
            secondary_action=go_to_outline,
            tag="Drafting",
            key_prefix="editor_header",
        )

        if not chaps:
            with st.container(border=True):
                st.info("📭 No chapters yet.\n\nCreate your first chapter — or let MANTIS write one from your outline.")
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("➕ Create Chapter 1", type="primary", use_container_width=True):
                        p.add_chapter("Chapter 1")
                        persist_project(p)
                        st.rerun()
                with c2:
                    if st.button("🧩 Go to Outline", use_container_width=True):
                        st.session_state.page = "outline"
                        st.session_state._force_nav = True
                        st.rerun()
            return

        if "curr_chap_id" not in st.session_state or st.session_state.curr_chap_id not in p.chapters:
            st.session_state.curr_chap_id = chaps[0].id

        curr = p.chapters[st.session_state.curr_chap_id]
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
                    persist_project(p)

        col_nav, col_editor, col_ai = st.columns([1.05, 3.2, 1.25])

        with col_nav:
            with st.container(border=True):
                st.markdown("### 📍 Chapters")
                for c in chaps:
                    lbl = f"{c.index}. {(c.title or 'Untitled')[:18]}"
                    if st.button(lbl, key=f"n_{c.id}", type="primary" if c.id == curr.id else "secondary", use_container_width=True):
                        st.session_state.curr_chap_id = c.id
                        st.rerun()

                st.divider()
                if st.button("➕ New Chapter", use_container_width=True, help="Create a new chapter in this project."):
                    next_idx = len(chaps) + 1
                    pat = re.compile(rf"Chapter {next_idx}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
                    match = pat.search(p.outline or "")
                    if match:
                        raw = match.group(1).strip()
                        title = sanitize_chapter_title(re.split(r" [-–:] ", raw, 1)[0].strip())
                    else:
                        title = f"Chapter {next_idx}"
                    p.add_chapter(sanitize_chapter_title(title))
                    persist_project(p)
                    st.rerun()

        stream_ph = st.empty()

        with col_editor:
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    curr.title = st.text_input("Title", curr.title, label_visibility="collapsed", help="Rename this chapter.")
                with h2:
                    curr.target_words = st.number_input(
                        "Target",
                        100,
                        10000,
                        int(curr.target_words),
                        label_visibility="collapsed",
                        help="Target word count for this chapter.",
                    )

                val = st.text_area("Manuscript", curr.content, height=680, label_visibility="collapsed", key=f"ed_{curr.id}")
                if val != curr.content:
                    curr.update_content(val, "manual")
                    save_p()

                st.caption(f"📝 Chapter: {curr.word_count} words • 📚 Total: {p.get_total_word_count()} words")

                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("💾 Save Chapter", type="primary", use_container_width=True):
                        curr.update_content(val, "manual")
                        if persist_project(p, prompt_on_guest=True, action="save"):
                            # Automatically scan entities from this chapter when the user explicitly saves it.
                            extract_entities_ui(curr.content or "", f"Ch {curr.index}")
                            st.toast("Chapter Saved & Entities Scanned")
                with c2:
                    if st.button("📝 Update Summary", use_container_width=True):
                        summary = StoryEngine.summarize(curr.content or "", get_ai_model())
                        if summary.strip().startswith("ERROR: Canon violation detected."):
                            st.error("Canon violation detected. Resolve issues before generating AI content.")
                        else:
                            curr.summary = summary
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
                    if st.button(
                        "Generate Improvement",
                        use_container_width=True,
                        disabled=rewrite_locked,
                        key=f"editor_improve__generate_{curr.id}",
                    ):
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
                    )
                elif st.button("✨ Auto-Write Chapter", type="primary", use_container_width=True):
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
                    if st.button(
                        "Regenerate",
                        use_container_width=True,
                        key=f"editor_improve__regenerate_{curr.id}",
                    ):
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

    rendered_page = False
    if st.session_state.page == "home":
        with key_scope("dashboard"):
            render_home()
        rendered_page = True
    elif st.session_state.page == "projects":
        with key_scope("projects"):
            render_projects()
        rendered_page = True
    elif st.session_state.page == "ai":
        with key_scope("settings"):
            render_ai_settings()
        rendered_page = True
    elif st.session_state.project:
        pg = st.session_state.page
        if pg == "outline":
            with key_scope("outline"):
                render_outline()
            rendered_page = True
        elif pg == "world":
            with key_scope("world"):
                render_world()
            rendered_page = True
        elif pg == "chapters":
            with key_scope("editor"):
                render_chapters()
            rendered_page = True
        else:
            st.session_state.page = "home"
            st.rerun()
    else:
        st.session_state.page = "home"
        st.rerun()

    if rendered_page:
        render_footer()


def run_selftest() -> int:
    """
    Quick non-UI integrity test. Intended to be called by the launcher.
    Creates a temporary project, exercises save/load, chapters/entities/export, then cleans up.
    """
    print("[MANTIS SELFTEST]")
    try:
        os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
        user_projects_dir = get_user_projects_dir(f"selftest_{uuid.uuid4().hex[:8]}")

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
if SELFTEST_MODE:
    raise SystemExit(run_selftest())

if REPAIR_MODE:
    raise SystemExit(run_repair())

# Default: run the Streamlit UI (Streamlit will execute this script).
_run_ui()
