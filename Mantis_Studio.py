#!/usr/bin/env python3
# Mantis_Studio.py — MANTIS Studio v47 (Chronicle) — SINGLE FILE EDITION
#
# Run:
#   python -m streamlit run Mantis_Studio.py
#
# Requirements:
#   streamlit>=1.30.0
#   requests
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
import time
import datetime
import uuid
import difflib
import logging
import hashlib
import hmac
import shutil
from dataclasses import dataclass, field, asdict, fields
from typing import Dict, List, Optional, Any, Generator

import requests
# (UI-only imports are loaded inside _run_ui() so selftests can run without Streamlit installed.)

import sys


# ===== v45 BRANDING (SAFE, ORIGINAL TEMPLATE) =====
import base64

_MANTIS_LOGO_PATH = "mantis_logo_trans.png"

def _mantis_logo_b64() -> str:
    try:
        with open(_MANTIS_LOGO_PATH, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        logging.getLogger("MANTIS").warning(
            "Failed to load logo asset from %s",
            _MANTIS_LOGO_PATH,
            exc_info=True,
        )
        return ""

_MANTIS_LOGO_B64 = _mantis_logo_b64()
# ==================================================

SELFTEST_MODE = "--selftest" in sys.argv
REPAIR_MODE = "--repair" in sys.argv


# ============================================================
# 1) CONFIG
# ============================================================

class AppConfig:
    APP_NAME = "MANTIS Studio"
    VERSION = "47 (Chronicle • One-File)"
    PROJECTS_DIR = os.getenv("MANTIS_PROJECTS_DIR", "projects")
    BACKUPS_DIR = os.path.join(PROJECTS_DIR, ".backups")
    USERS_DB_PATH = os.getenv(
        "MANTIS_USERS_DB_PATH",
        os.path.join(PROJECTS_DIR, ".mantis_users.json"),
    )
    USERS_DIR = os.getenv("MANTIS_USERS_DIR", os.path.join(PROJECTS_DIR, "users"))
    GUESTS_DIR = os.getenv("MANTIS_GUESTS_DIR", os.path.join(PROJECTS_DIR, "guests"))
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


os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
os.makedirs(AppConfig.BACKUPS_DIR, exist_ok=True)
os.makedirs(AppConfig.USERS_DIR, exist_ok=True)
os.makedirs(AppConfig.GUESTS_DIR, exist_ok=True)

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


def _normalize_username(username: str) -> str:
    return re.sub(r"\s+", "", (username or "").strip()).lower()


def load_users_db() -> Dict[str, Dict[str, Any]]:
    try:
        with open(AppConfig.USERS_DB_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict) and isinstance(data.get("users"), dict):
                return data
    except FileNotFoundError:
        return {"users": {}}
    except Exception:
        logger.warning("Failed to load users database", exc_info=True)
    return {"users": {}}


def save_users_db(data: Dict[str, Dict[str, Any]]) -> None:
    try:
        with open(AppConfig.USERS_DB_PATH, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        logger.warning("Failed to save users database", exc_info=True)


def _truncate_prompt(prompt: str, limit: int) -> str:
    if not prompt:
        return prompt
    if len(prompt) <= limit:
        return prompt
    logger.warning("Prompt length %s exceeded limit %s; truncating", len(prompt), limit)
    return prompt[:limit]


def _password_policy_error(password: str) -> Optional[str]:
    if len(password or "") < 10:
        return "Password must be at least 10 characters."
    if not re.search(r"[A-Za-z]", password or "") or not re.search(r"\d", password or ""):
        return "Password must include at least one letter and one number."
    return None


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


def hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
    if salt is None:
        salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return {"salt": salt.hex(), "hash": pw_hash.hex()}


def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except ValueError:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return hmac.compare_digest(candidate, expected)


def create_user(username: str, display_name: str, password: str) -> Dict[str, Any]:
    clean_username = _normalize_username(username)
    display_name = (display_name or "").strip()
    if not clean_username or not display_name or not password:
        return {"ok": False, "error": "All fields are required."}
    policy_error = _password_policy_error(password)
    if policy_error:
        return {"ok": False, "error": policy_error}

    data = load_users_db()
    if clean_username in data["users"]:
        return {"ok": False, "error": "That username is already taken."}

    creds = hash_password(password)
    user_id = str(uuid.uuid4())
    data["users"][clean_username] = {
        "id": user_id,
        "username": clean_username,
        "display_name": display_name,
        "password_hash": creds["hash"],
        "password_salt": creds["salt"],
        "created_at": time.time(),
    }
    save_users_db(data)
    return {"ok": True, "user": data["users"][clean_username]}


def authenticate_user(username: str, password: str) -> Dict[str, Any]:
    clean_username = _normalize_username(username)
    data = load_users_db()
    user = data.get("users", {}).get(clean_username)
    if not user:
        return {"ok": False, "error": "Username or password is incorrect."}

    if not verify_password(password, user.get("password_salt", ""), user.get("password_hash", "")):
        return {"ok": False, "error": "Username or password is incorrect."}

    return {"ok": True, "user": user}


def get_user_projects_dir(user_id: str) -> str:
    user_dir = os.path.join(AppConfig.USERS_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    return user_dir


def get_guest_projects_dir(guest_id: str) -> str:
    guest_dir = os.path.join(AppConfig.GUESTS_DIR, guest_id)
    os.makedirs(guest_dir, exist_ok=True)
    return guest_dir


# ============================================================
# 2) MODELS
# ============================================================

@dataclass
class Entity:
    id: str
    name: str
    category: str
    description: str = ""
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
    def _normalize_entity_name(name: str) -> str:
        base = (name or "").strip().lower()
        if not base:
            return ""
        base = re.sub(r"[\"'`]", "", base)
        base = re.sub(r"\((.*?)\)", r" \1 ", base)
        base = re.sub(r"\b(mr|mrs|ms|dr|prof|sir|madam)\.?\b", "", base)
        base = re.sub(r"[^\w\s/-]", " ", base)
        base = re.sub(r"\s+", " ", base).strip()
        return base

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

        similarity = difflib.SequenceMatcher(None, left_norm, right_norm).ratio()
        return similarity >= 0.75

    def add_entity(self, name: str, category: str, desc: str = "") -> Optional[Entity]:
        """Smart Add with Fuzzy Matching."""
        clean_name = (name or "").strip()
        if not clean_name:
            return None

        for ent in self.world_db.values():
            if ent.category == category:
                candidates = self._entity_aliases(ent.name)
                incoming_aliases = self._entity_aliases(clean_name)
                if not candidates:
                    candidates = [ent.name]
                if not incoming_aliases:
                    incoming_aliases = [clean_name]
                matched = any(
                    self._names_match(candidate, incoming)
                    for candidate in candidates
                    for incoming in incoming_aliases
                )
                if matched:
                    ent.merge(desc)
                    self.last_modified = time.time()
                    return ent

        e = Entity(
            id=str(uuid.uuid4()),
            name=clean_name,
            category=category,
            description=(desc or "").strip(),
        )
        self.world_db[e.id] = e
        self.last_modified = time.time()
        return e

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
                final_title = split_text[0].strip()
                if len(final_title) > 2:
                    title = final_title

        c = Chapter(
            id=str(uuid.uuid4()),
            index=index,
            title=(title or "").strip(),
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

        proj = cls(id=data.get("id"), title=data.get("title"))
        proj.author = data.get("author", "")
        proj.genre = data.get("genre", "")
        proj.outline = data.get("outline", "")
        proj.memory = data.get("memory", data.get("memory_notes", ""))
        proj.author_note = data.get("author_note", data.get("authors_note", ""))
        proj.style_guide = data.get("style_guide", data.get("style_note", ""))
        proj.default_word_count = data.get("default_word_count", 1000)
        proj.created_at = data.get("created_at", time.time())
        proj.last_modified = data.get("last_modified", time.time())

        ent_fields = {f.name for f in fields(Entity)}
        for k, v in (data.get("world_db") or data.get("characters") or {}).items():
            if "category" not in v:
                v["category"] = "Character"
            clean = {key: val for key, val in v.items() if key in ent_fields}
            proj.world_db[k] = Entity(**clean)

        chap_fields = {f.name for f in fields(Chapter)}
        for k, v in (data.get("chapters") or {}).items():
            clean = {key: val for key, val in v.items() if key in chap_fields}
            proj.chapters[k] = Chapter(**clean)

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
            "Analyze text. Identify Characters, Locations, Factions, and important Items/Lore.\n"
            "Return JSON List: [{'name': 'X', 'category': 'Character|Location|Item|Lore|Faction', 'description': 'Z'}]\n"
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


# ============================================================
# 5) STREAMLIT UI (Appearance + First-time Onboarding)
# ============================================================



def _run_ui():
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    from pages.legal import render_copyright, render_privacy, render_terms
    from ui.layout import render_footer

    st.set_page_config(page_title=AppConfig.APP_NAME, layout="wide")

    config_data = load_app_config()

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
    if "remember_me" not in st.session_state:
        st.session_state.remember_me = bool(config_data.get("remember_me", False))

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
            "header_gradient": "radial-gradient(circle at top left, rgba(34,197,94,0.35), rgba(2,6,23,0.6)), linear-gradient(135deg, #0b1216, #0f1a15)",
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
            "sidebar_bg": "linear-gradient(180deg, #f1f7f3, #e7f4ed)",
            "sidebar_border": "#dbeee2",
            "sidebar_title": "#1f7a4f",
            "divider": "#deeee3",
            "expander_border": "#d7e9df",
            "header_gradient": "linear-gradient(135deg, #e6f9ef, #c7f4dc)",
            "header_logo_bg": "#e7fdf1",
            "header_sub": "#2f6f43",
            "shadow_strong": "0 12px 24px rgba(12,26,18,0.08)",
            "shadow_button": "0 8px 16px rgba(12,26,18,0.12)",
            "sidebar_brand_bg": "linear-gradient(180deg, rgba(241,251,245,0.95), rgba(226,245,236,0.95))",
            "sidebar_brand_border": "rgba(21,128,61,0.18)",
            "sidebar_logo_bg": "rgba(15,23,42,0.06)",
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
        width:52px;
        height:52px;
        border-radius:16px;
        background: var(--mantis-header-logo-bg);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.2), 0 8px 20px rgba(0,0,0,0.25);
    }}
    .mantis-header-logo img {{
        height:32px;
        width:auto;
        padding:6px;
        border-radius:12px;
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
    .mantis-soft {{
        background: var(--mantis-surface-alt);
        border-radius: 16px;
        padding: 14px;
        border: 1px solid var(--mantis-card-border);
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
        width:56px;
        height:56px;
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
        height:38px;
        width:auto;
        display:block;
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

    /* --- NAV RADIO STYLE --- */
    div[role="radiogroup"] > label {{
        background: var(--mantis-surface-alt);
        padding: 10px 12px;
        border-radius: 12px;
        border: 1px solid var(--mantis-card-border);
        margin-bottom: 8px;
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
    st.markdown(f"""
        <div class="mantis-header">
            <div class="mantis-header-left">
                <div class="mantis-header-logo">
                    <img src="data:image/png;base64,{_MANTIS_LOGO_B64}" />
                </div>
                <div style="line-height:1.15;">
                    <div class="mantis-header-title">
                        MANTIS Studio
                    </div>
                    <div class="mantis-header-sub">
                        Modular AI Narrative Text Intelligence System
                    </div>
                </div>
            </div>
            <div class="mantis-header-right">
                <span class="mantis-pill">Workspace</span>
                <span class="mantis-pill">v{AppConfig.VERSION}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if "auth_user" not in st.session_state:
        st.session_state.auth_user = None
    if "auth_user_id" not in st.session_state:
        st.session_state.auth_user_id = None
    if "auth_username" not in st.session_state:
        st.session_state.auth_username = None
    if "auth_is_guest" not in st.session_state:
        st.session_state.auth_is_guest = False
    if "projects_dir" not in st.session_state:
        st.session_state.projects_dir = None
    if "project" not in st.session_state:
        st.session_state.project = None
    if "page" not in st.session_state:
        st.session_state.page = "home"
    if "auto_save" not in st.session_state:
        st.session_state.auto_save = True
    if "ghost_text" not in st.session_state:
        st.session_state.ghost_text = ""
    if "first_run" not in st.session_state:
        st.session_state.first_run = True
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

    if st.session_state.auth_user and not st.session_state.projects_dir:
        if st.session_state.auth_is_guest:
            guest_id = st.session_state.get("guest_id") or st.session_state.auth_user_id or str(uuid.uuid4())
            st.session_state.guest_id = guest_id
            st.session_state.projects_dir = get_guest_projects_dir(guest_id)
        elif st.session_state.auth_user_id:
            st.session_state.projects_dir = get_user_projects_dir(st.session_state.auth_user_id)

    # Reliable navigation rerun (avoids Streamlit edge cases when returning early)
    if st.session_state.get("_force_nav"):
        st.session_state._force_nav = False
        st.rerun()

    def get_ai_model() -> str:
        return st.session_state.get("groq_model", AppConfig.DEFAULT_MODEL)

    def save_p():
        if st.session_state.project and st.session_state.auto_save:
            st.session_state.project.save()

    def get_active_projects_dir() -> str:
        return st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR

    @st.cache_data(show_spinner=False)
    def _cached_models(base_url: str, api_key: str) -> List[str]:
        return AIEngine(base_url=base_url).probe_models(api_key)

    def refresh_models():
        st.session_state.groq_model_list = _cached_models(
            st.session_state.groq_base_url,
            st.session_state.groq_api_key,
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
            "remember_me": bool(st.session_state.remember_me),
        }
        save_app_config(data)
        st.toast("Settings saved.")

    def save_auth_remember(user: Optional[Dict[str, Any]], is_guest: bool, remember: bool, guest_id: str = ""):
        data = dict(config_data)
        if remember and user:
            data.update(
                {
                    "remember_me": True,
                    "remembered_username": user.get("username", ""),
                    "remembered_user_id": user.get("id", ""),
                    "remembered_display_name": user.get("display_name", ""),
                    "remembered_is_guest": bool(is_guest),
                    "remembered_guest_id": guest_id or "",
                }
            )
        else:
            data.update(
                {
                    "remember_me": False,
                    "remembered_username": "",
                    "remembered_user_id": "",
                    "remembered_display_name": "",
                    "remembered_is_guest": False,
                    "remembered_guest_id": "",
                }
            )
        config_data.clear()
        config_data.update(data)
        if "remember_me" not in st.session_state:
            st.session_state.remember_me = bool(data.get("remember_me", False))
        save_app_config(data)

    def _restore_remembered_session() -> None:
        if st.session_state.auth_user or not config_data.get("remember_me"):
            return
        if config_data.get("remembered_is_guest"):
            guest_id = config_data.get("remembered_guest_id") or str(uuid.uuid4())
            st.session_state.guest_id = guest_id
            st.session_state.auth_user = config_data.get("remembered_display_name") or "Guest"
            st.session_state.auth_user_id = guest_id
            st.session_state.auth_username = "guest"
            st.session_state.auth_is_guest = True
            st.session_state.projects_dir = get_guest_projects_dir(guest_id)
            return

        username = config_data.get("remembered_username", "")
        user_id = config_data.get("remembered_user_id", "")
        if not username or not user_id:
            save_auth_remember(None, False, False)
            return

        data = load_users_db()
        user = data.get("users", {}).get(username)
        if not user or user.get("id") != user_id:
            save_auth_remember(None, False, False)
            return

        st.session_state.auth_user = user.get("display_name") or username
        st.session_state.auth_user_id = user.get("id")
        st.session_state.auth_username = user.get("username")
        st.session_state.auth_is_guest = False
        st.session_state.projects_dir = get_user_projects_dir(user.get("id", ""))

    def render_auth():
        saved_username = config_data.get("last_username", "")
        hero_left, hero_right = st.columns([1.1, 1.3])
        with hero_left:
            st.markdown(
                """
                <div class="mantis-hero">
                    <div class="mantis-tag">Welcome</div>
                    <div class="mantis-hero-title">Enter your story studio</div>
                    <div class="mantis-hero-sub">
                        Start writing instantly. Sign in later to save and sync.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="mantis-soft">
                    <div class="mantis-section-title">What you can do</div>
                    <ul style="margin:0; padding-left:18px;">
                        <li>Draft chapters with AI assist</li>
                        <li>Build and maintain your World Bible</li>
                        <li>Track goals and writing momentum</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with hero_right:
            st.markdown(
                """
                <div class="mantis-section-title">Account access</div>
                <p class="mantis-muted" style="margin-top:0;">
                    Choose how you want to start writing.
                </p>
                """,
                unsafe_allow_html=True,
            )
            tabs = st.tabs(["Start Writing (Guest)", "Sign In", "Create Account"])

            with tabs[0]:
                st.caption("Guest mode lets you write immediately. Projects are not saved.")
                if st.button("✍️ Start Writing (Guest)", type="primary", use_container_width=True):
                    guest_id = st.session_state.get("guest_id") or str(uuid.uuid4())
                    st.session_state.guest_id = guest_id
                    st.session_state.auth_user = "Guest"
                    st.session_state.auth_user_id = guest_id
                    st.session_state.auth_username = "guest"
                    st.session_state.auth_is_guest = True
                    st.session_state.projects_dir = get_guest_projects_dir(guest_id)
                    save_auth_remember(
                        {
                            "id": guest_id,
                            "username": "guest",
                            "display_name": "Guest",
                        },
                        True,
                        st.session_state.remember_me,
                        guest_id=guest_id,
                    )
                    st.session_state._force_nav = True
                    st.rerun()

            with tabs[1]:
                username = st.text_input(
                    "Username",
                    value=saved_username,
                    key="auth_login_username",
                    placeholder="e.g. alex",
                )
                password = st.text_input("Password", type="password", key="auth_login_password")
                if st.button("Sign In", use_container_width=True):
                    result = authenticate_user(username, password)
                    if not result.get("ok"):
                        st.error(result.get("error", "Sign in failed."))
                    else:
                        user = result["user"]
                        st.session_state.auth_user = user["display_name"]
                        st.session_state.auth_user_id = user["id"]
                        st.session_state.auth_username = user["username"]
                        st.session_state.auth_is_guest = False
                        st.session_state.projects_dir = get_user_projects_dir(user["id"])
                        save_auth_remember(user, False, st.session_state.remember_me)
                        st.session_state._force_nav = True
                        st.rerun()

            with tabs[2]:
                display_name = st.text_input(
                    "Display name",
                    key="auth_create_display_name",
                    placeholder="e.g. Alex Writer",
                )
                new_username = st.text_input("Username", key="auth_create_username", placeholder="e.g. alex")
                new_password = st.text_input("Password", type="password", key="auth_create_password")
                confirm_password = st.text_input("Confirm password", type="password", key="auth_create_confirm")
                if st.button("Create Account", type="primary", use_container_width=True):
                    if new_password != confirm_password:
                        st.error("Passwords do not match.")
                    else:
                        policy_error = _password_policy_error(new_password or "")
                        if policy_error:
                            st.error(policy_error)
                        else:
                            result = create_user(new_username, display_name, new_password)
                            if not result.get("ok"):
                                st.error(result.get("error", "Could not create account."))
                            else:
                                user = result["user"]
                                st.session_state.auth_user = user["display_name"]
                                st.session_state.auth_user_id = user["id"]
                                st.session_state.auth_username = user["username"]
                                st.session_state.auth_is_guest = False
                                st.session_state.projects_dir = get_user_projects_dir(user["id"])
                            save_auth_remember(user, False, st.session_state.remember_me)
                            st.session_state._force_nav = True
                            st.rerun()

    def _today_str() -> str:
        return datetime.date.today().isoformat()

    def _parse_day(day: str) -> Optional[datetime.date]:
        try:
            return datetime.date.fromisoformat(day)
        except ValueError:
            return None

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

    def _load_recent_projects(active_dir: str) -> List[Dict[str, Any]]:
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

    def extract_entities_ui(text: str, label: str):
        """Scan text for entities and update the World Bible.

        Uses Project.add_entity's fuzzy matching so that abbreviations, nicknames,
        or slightly different spellings merge into existing entries instead of
        creating duplicates.
        """
        model = get_ai_model()
        raw_text = text or ""
        p = st.session_state.project

        ents = AnalysisEngine.extract_entities(raw_text, model)
        total_detected = len(ents)
        added = 0
        merged = 0

        for e in ents:
            name = (e.get("name") or "").strip()
            category = (e.get("category") or "").strip()
            if not name or not category:
                continue

            desc = (e.get("description") or "").strip()

            before = len(p.world_db)
            ent = p.add_entity(name, category, desc)
            after = len(p.world_db)

            if ent is None:
                continue

            if after > before:
                added += 1
            else:
                merged += 1

        p.save()

        if added > 0 and merged > 0:
            st.toast(f"Entities: {added} new, {merged} merged into existing.", icon="🌍")
        elif added > 0:
            st.toast(f"Added {added} new entities to World Bible.", icon="🌍")
        elif merged > 0:
            st.toast(f"Merged details into {merged} existing entities.", icon="🌍")
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

    if not st.session_state.auth_user:
        _restore_remembered_session()
    if not st.session_state.auth_user:
        render_auth()
        render_footer()
        return

    def render_ai_settings():
        st.markdown("## 🧠 AI Settings")
        st.caption("Configure your AI providers and models.")

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

        st.divider()
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

        openai_model = st.text_input("OpenAI Model", value=st.session_state.openai_model)
        if openai_model != st.session_state.openai_model:
            st.session_state.openai_model = openai_model
            AppConfig.OPENAI_MODEL = openai_model

        st.markdown(
            "[Create an OpenAI account](https://platform.openai.com/api-keys) to get an API key."
        )

        colm1, colm2 = st.columns([1, 1])
        with colm1:
            st.checkbox("Auto-save", key="auto_save")
        with colm2:
            if st.button("↻ Refresh Groq Models", use_container_width=True):
                st.cache_data.clear()
                refresh_models()
                st.toast("Model list refreshed")

        if st.button("💾 Save AI Settings", use_container_width=True):
            save_app_settings()

    with st.sidebar:
        st.markdown(f"""
        <div class="mantis-sidebar-brand">
            <div class="mantis-sidebar-logo">
                <img src="data:image/png;base64,{_MANTIS_LOGO_B64}" />
            </div>
            <div>
                <div class="mantis-sidebar-title">MANTIS Studio</div>
                <div class="mantis-sidebar-sub">v{AppConfig.VERSION}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 👤 Account")
        st.caption(f"Signed in as **{st.session_state.auth_user}**")
        if st.session_state.auth_username and not st.session_state.auth_is_guest:
            st.caption(f"@{st.session_state.auth_username}")
        if st.button("💾 Save Account", use_container_width=True):
            save_app_settings()
        if st.button("Sign out", use_container_width=True):
            st.session_state.auth_user = None
            st.session_state.auth_user_id = None
            st.session_state.auth_username = None
            st.session_state.auth_is_guest = False
            st.session_state.projects_dir = None
            st.session_state.project = None
            st.session_state.page = "home"
            save_auth_remember(None, False, False)
            st.session_state._force_nav = True
            st.rerun()

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

        nav_labels = ["Dashboard", "Projects", "AI Tools"]
        pmap = {
            "Dashboard": "home",
            "Projects": "projects",
            "AI Tools": "ai",
        }
        if st.session_state.project:
            nav_labels = [
                "Dashboard",
                "Projects",
                "Editor",
                "Outline",
                "World Bible",
                "Export",
                "AI Tools",
            ]
            pmap = {
                "Dashboard": "home",
                "Projects": "projects",
                "Editor": "chapters",
                "Outline": "outline",
                "World Bible": "world",
                "Export": "export",
                "AI Tools": "ai",
            }
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
                    p.save()
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
        recent_projects = _load_recent_projects(active_dir)
        recent_snapshot = _project_snapshot(recent_projects[0]["meta"]) if recent_projects else None
        streak = _activity_streak()
        weekly_count = _weekly_activity_count()
        weekly_goal = max(int(st.session_state.weekly_sessions_goal), 1)
        weekly_progress = min(weekly_count / weekly_goal, 1.0)
        has_project = bool(recent_projects)
        has_outline = any((p["meta"].get("outline") or "").strip() for p in recent_projects)
        has_chapter = any(
            (c.get("word_count") or 0) > 0
            for p in recent_projects
            for c in (p["meta"].get("chapters") or {}).values()
        )

        with st.container(border=True):
            st.markdown(
                f"""
                <div class="mantis-hero">
                    <div class="mantis-tag">Dashboard</div>
                    <div class="mantis-hero-title">Welcome back, {st.session_state.auth_user}</div>
                    <div class="mantis-hero-sub">
                        Build worlds, draft chapters, and keep your narrative canon in sync.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            hero_left, hero_right = st.columns([1.6, 1])
            with hero_left:
                st.markdown("#### Quick actions")
                action_cols = st.columns(3)
                with action_cols[0]:
                    if st.button(
                        "📂 Resume",
                        type="primary",
                        use_container_width=True,
                        disabled=not recent_projects,
                    ):
                        if recent_projects:
                            st.session_state.project = Project.load(recent_projects[0]["path"])
                            st.session_state.page = "chapters"
                            st.rerun()
                with action_cols[1]:
                    if st.button("🧭 New project", use_container_width=True):
                        st.session_state.page = "projects"
                        st.rerun()
                with action_cols[2]:
                    if st.button(
                        "🧩 Open outline",
                        use_container_width=True,
                        disabled=not recent_projects,
                    ):
                        if recent_projects:
                            st.session_state.project = Project.load(recent_projects[0]["path"])
                            st.session_state.page = "outline"
                            st.rerun()

                st.markdown("#### Workspace snapshot")
                st.markdown(
                    f"""
                    <div class="mantis-kpi-grid">
                        <div class="mantis-kpi-card">
                            <div class="mantis-kpi-label">Active projects</div>
                            <div class="mantis-kpi-value">{len(recent_projects)}</div>
                        </div>
                        <div class="mantis-kpi-card">
                            <div class="mantis-kpi-label">Latest genre</div>
                            <div class="mantis-kpi-value">{(recent_snapshot or {}).get("genre", "—")}</div>
                        </div>
                        <div class="mantis-kpi-card">
                            <div class="mantis-kpi-label">Writing streak</div>
                            <div class="mantis-kpi-value">{streak} days</div>
                        </div>
                        <div class="mantis-kpi-card">
                            <div class="mantis-kpi-label">Weekly sessions</div>
                            <div class="mantis-kpi-value">{weekly_count}/{weekly_goal}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with hero_right:
                st.markdown("#### Studio signals")
                st.caption("Model, storage, and AI readiness at a glance.")
                status_card = st.container(border=True)
                with status_card:
                    groq_status = "Connected" if st.session_state.groq_api_key else "Add key"
                    openai_status = "Connected" if st.session_state.openai_api_key else "Add key"
                    st.metric("Groq", groq_status)
                    st.metric("OpenAI", openai_status)
                    st.metric("Model", st.session_state.groq_model or AppConfig.DEFAULT_MODEL)
                    st.caption(f"Projects dir: `{active_dir}`")

                st.markdown("#### Next milestones")
                st.caption("Keep the studio healthy with these quick checks.")
                milestone_col = st.container(border=True)
                with milestone_col:
                    st.checkbox(
                        "Create a project",
                        value=has_project,
                        disabled=True,
                        key="milestone_create_project",
                    )
                    st.checkbox(
                        "Draft an outline",
                        value=has_outline,
                        disabled=True,
                        key="milestone_draft_outline",
                    )
                    st.checkbox(
                        "Write a chapter",
                        value=has_chapter,
                        disabled=True,
                        key="milestone_write_chapter",
                    )

        with st.container(border=True):
            st.markdown("### 🧭 Guided first session")
            st.caption("Complete these steps to unlock the full studio workflow.")
            progress = sum([has_project, has_outline, has_chapter]) / 3
            st.progress(progress, text=f"{sum([has_project, has_outline, has_chapter])}/3 steps complete")
            s1, s2, s3 = st.columns([1.2, 1.2, 1.4])
            with s1:
                st.checkbox(
                    "Create a project",
                    value=has_project,
                    disabled=True,
                    key="guided_create_project",
                )
                if not has_project:
                    if st.button("Start here", type="primary", use_container_width=True):
                        st.session_state.page = "projects"
                        st.rerun()
            with s2:
                st.checkbox(
                    "Draft an outline",
                    value=has_outline,
                    disabled=True,
                    key="guided_draft_outline",
                )
                if has_project and not has_outline:
                    if st.button("Open outline", use_container_width=True):
                        st.session_state.project = Project.load(recent_projects[0]["path"])
                        st.session_state.page = "outline"
                        st.rerun()
            with s3:
                st.checkbox(
                    "Write a chapter",
                    value=has_chapter,
                    disabled=True,
                    key="guided_write_chapter",
                )
                if has_project and not has_chapter:
                    if st.button("Start writing", use_container_width=True):
                        st.session_state.project = Project.load(recent_projects[0]["path"])
                        st.session_state.page = "chapters"
                        st.rerun()

        onboarding_left, onboarding_right = st.columns([1.4, 1])
        with onboarding_left:
            if st.session_state.get("first_run", True):
                with st.container(border=True):
                    st.markdown("### 👋 First time here?")
                    st.markdown(
                        """
**MANTIS** mirrors a focused NovelAI-style studio: a clean writing surface, memory tools,
and quick start modules so you can draft fast and refine later.

**Quick path**
1) Create a project  
2) Build a structured outline or lore entries  
3) Draft chapters with AI assists on demand
"""
                    )
                    c1, c2, c3 = st.columns([1, 1, 2])
                    with c1:
                        if st.button("✅ Got it", type="primary", use_container_width=True):
                            st.session_state.first_run = False
                            st.rerun()
                    with c2:
                        if st.button("📌 Keep showing", use_container_width=True):
                            st.toast("Welcome panel will keep showing.")
                    with c3:
                        st.caption("Tip: If the AI model shows Offline, confirm your Groq API key and model access.")

        with onboarding_right:
            if not st.session_state.groq_api_key or not st.session_state.openai_api_key:
                with st.container(border=True):
                    st.markdown("### 🔑 Connect your AI providers")
                    st.caption("Unlock generation, summaries, and entity tools with API access.")
                    cta_left, cta_right = st.columns(2)
                    with cta_left:
                        st.link_button("Create Groq Account", "https://console.groq.com/keys", use_container_width=True)
                    with cta_right:
                        st.link_button(
                            "Create OpenAI Account",
                            "https://platform.openai.com/api-keys",
                            use_container_width=True,
                        )

        with st.container(border=True):
            st.markdown("### 🚀 Creator Momentum")
            st.caption("Track your writing rhythm and jump back in with a single click.")

            if recent_snapshot:
                headline = f"**Resume:** {recent_snapshot['title']} · {recent_snapshot['genre']}"
                st.markdown(headline)
                metrics = st.columns(4)
                metrics[0].metric("Words written", f"{recent_snapshot['words']:,}")
                metrics[1].metric("Chapters", recent_snapshot["chapters"])
                metrics[2].metric("Streak", f"{streak} day(s)")
                metrics[3].metric("Sessions this week", f"{weekly_count}/{weekly_goal}")
            else:
                st.info("Create a project to unlock your momentum stats and quick actions.")

            goal_cols = st.columns(3)
            with goal_cols[0]:
                st.number_input("Daily word goal", min_value=100, max_value=5000, step=50, key="daily_word_goal")
            with goal_cols[1]:
                st.number_input(
                    "Weekly sessions goal",
                    min_value=1,
                    max_value=14,
                    step=1,
                    key="weekly_sessions_goal",
                )
            with goal_cols[2]:
                st.number_input(
                    "Focus sprint (minutes)",
                    min_value=10,
                    max_value=90,
                    step=5,
                    key="focus_minutes",
                )

            progress_cols = st.columns([2, 1])
            with progress_cols[0]:
                st.progress(weekly_progress, text="Weekly writing progress")
                if st.button("✅ Log a writing session", use_container_width=True):
                    _log_activity()
                    st.toast("Session logged. Keep the streak going!")
                    st.rerun()
            with progress_cols[1]:
                if st.button("💾 Save studio goals", use_container_width=True):
                    save_app_settings()

            if st.session_state.activity_log:
                activity_df = pd.DataFrame(_activity_series())
                activity_chart = px.bar(
                    activity_df,
                    x="day",
                    y="sessions",
                    title="Last 7 days",
                    text_auto=True,
                )
                activity_chart.update_layout(
                    height=240,
                    margin=dict(l=10, r=10, t=50, b=10),
                    yaxis=dict(range=[0, 1], tickmode="array", tickvals=[0, 1]),
                )
                st.plotly_chart(activity_chart, use_container_width=True)

    def render_projects():
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir)

        st.markdown("## Projects")
        st.caption("Create, import, and manage your story worlds.")

        st.markdown(
            """
            <div class="mantis-section-header">
                <div>
                    <div class="mantis-section-title">Start a new project</div>
                    <div class="mantis-hero-caption">Set a title, genre, and author details to build your base.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
                    # If title or genre are missing, try to use AI to fill them in.
                    if not t or not g:
                        try:
                            with st.spinner("Generating missing title/genre using AI..."):
                                outline_hint = "A new story project with mystery and character development."
                                model = get_ai_model()
                                if not t:
                                    t = AnalysisEngine.generate_title(outline_hint, g or "General Fiction", model)
                                if not g:
                                    detected = AnalysisEngine.detect_genre(outline_hint, model) or ""
                                    g = detected or (g or "General Fiction")
                                st.toast("AI filled missing fields")
                        except Exception as e:
                            logger.warning("AI title/genre helper failed", exc_info=True)
                            st.warning(f"AI title/genre helper failed: {e}")
                    # Fall back to defaults if still empty
                    p = Project.create(
                        t,
                        author=a,
                        genre=g or "General Fiction",
                        storage_dir=get_active_projects_dir(),
                    )
                    p.save()
                    st.session_state.project = p
                    st.session_state.page = "outline"
                    st.session_state.first_run = False
                    st.rerun()

        st.markdown(
            """
            <div class="mantis-section-header">
                <div>
                    <div class="mantis-section-title">Import an existing draft</div>
                    <div class="mantis-hero-caption">Upload a .txt or .md file to split into chapters.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
                        p = Project.create("Imported Project", storage_dir=get_active_projects_dir())
                        p.import_text_file(txt)
                        p.save()
                        st.session_state.project = p
                        st.session_state.page = "chapters"
                        st.session_state.first_run = False
                        st.rerun()

        st.markdown(
            """
            <div class="mantis-section-header">
                <div>
                    <div class="mantis-section-title">Your projects</div>
                    <div class="mantis-hero-caption">Open, export, or clean up older drafts.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
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
                                st.session_state.project = Project.load(full)
                                st.session_state.page = "chapters"
                                st.session_state.first_run = False
                                st.rerun()
                        with row2:
                            st.caption(genre)
                        with row3:
                            if st.button("⬇️ Export", key=f"export_{full}", use_container_width=True):
                                st.session_state.project = Project.load(full)
                                st.session_state.page = "export"
                                st.rerun()
                        with row4:
                            if st.button("🗑", key=f"del_{full}", use_container_width=True):
                                Project.delete_file(full)
                                st.rerun()
                    except Exception:
                        logger.warning("Failed to load project metadata: %s", full, exc_info=True)


    def render_outline():
        p = st.session_state.project
        st.markdown("## Outline")
        st.caption("Your blueprint. Generate structure, scan entities, and keep the story plan here.")

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
                    p.save()
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

                b1, b2, b3 = st.columns([1, 1, 1])
                with b1:
                    if st.button("💾 Save Outline", use_container_width=True):
                        p.save()
                        # Automatically scan entities on save so World Bible stays in sync.
                        extract_entities_ui(p.outline or "", "Outline")
                        st.toast("Outline Saved & Entities Scanned")
                with b2:
                    if st.button("🌍 Scan Entities", use_container_width=True):
                        # Manual re-scan option if user wants to refresh entities after major edits.
                        extract_entities_ui(p.outline or "", "Outline")
                with b3:
                    if st.button("🔄 Reverse Outline", use_container_width=True):
                        p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
                        st.session_state["_outline_sync"] = p.outline or ""  # apply on next rerun before widget renders
                        save_p()
                        st.rerun()

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

                st.divider()

                if st.button("🏷️ Generate Title", use_container_width=True):
                    with st.spinner("Analyzing outline..."):
                        # Auto-detect genre if empty
                        if not (p.genre or "").strip() and (p.outline or "").strip():
                            g_guess = AnalysisEngine.detect_genre(p.outline, get_ai_model())
                            if g_guess:
                                p.genre = g_guess
                                save_p()
                                st.toast(f"Genre detected: {g_guess}", icon="🧭")

                        # Generate title using outline + genre
                        t = AnalysisEngine.generate_title(p.outline, p.genre, get_ai_model())
                        if t and "Untitled" not in t:
                            p.title = t
                            save_p()
                            st.toast("Title Updated")
                            st.rerun()
            

    def render_world():
        p = st.session_state.project
        st.markdown("## World Bible")
        st.caption("Track characters, locations, factions, items, and lore.")

        query = st.text_input("Search", placeholder="Type a name to filter...")
        t1, t2, t3, t4, t5, t6, t7 = st.tabs(["Characters", "Locations", "Items", "Lore", "Factions", "Analytics", "Memory"])

        def render_cat(category: str):
            with st.container(border=True):
                top = st.columns([1, 1.2, 1])
                with top[0]:
                    st.markdown(f"### {category}")
                with top[2]:
                    if st.button(f"➕ Add {category}", use_container_width=True):
                        st.session_state[f"add_open_{category}"] = True

                if st.session_state.get(f"add_open_{category}", False):
                    with st.form(f"add_{category}"):
                        n = st.text_input("Name")
                        d = st.text_area("Description")
                        s1, s2 = st.columns(2)
                        with s1:
                            ok = st.form_submit_button("Save", type="primary", use_container_width=True)
                        with s2:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                        if ok:
                            p.add_entity(n, category, d)
                            p.save()
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()
                        if cancel:
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()

                ents = [e for e in p.world_db.values() if e.category == category]
                if query:
                    ents = [e for e in ents if query.lower() in (e.name or "").lower()]

                if not ents:
                    st.info(f"📭 No {category} entries yet. Add one above or scan entities from your outline/chapters.")
                    return

                for e in ents:
                    with st.expander(f"{e.name}"):
                        c1, c2 = st.columns([4, 1])
                        new_desc = c1.text_area("Notes", e.description, key=f"desc_{e.id}", height=140)
                        if new_desc != e.description:
                            e.description = new_desc
                            p.save()

                        if c2.button("✨ Enrich", key=f"en_{e.id}", use_container_width=True):
                            new_info = AnalysisEngine.enrich_entity(e.name, e.category, e.description, get_ai_model())
                            if new_info:
                                e.merge(new_info)
                                p.save()
                                st.rerun()

                        d1, d2 = st.columns([1, 1])
                        with d1:
                            if st.button("🗑 Delete", key=f"del_{e.id}", use_container_width=True):
                                p.delete_entity(e.id)
                                p.save()
                                st.rerun()
                        with d2:
                            st.caption(f"Created: {time.strftime('%Y-%m-%d', time.localtime(e.created_at))}")

        def render_analytics():
            with st.container(border=True):
                st.markdown("### Analytics")
                chaps = p.get_ordered_chapters()
                total_words = p.get_total_word_count()
                total_chapters = len(chaps)
                avg_words = int(total_words / total_chapters) if total_chapters else 0
                total_target = sum(c.target_words for c in chaps)

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Words", f"{total_words:,}")
                m2.metric("Chapters", total_chapters)
                m3.metric("Avg Words / Chapter", f"{avg_words:,}")
                m4.metric("Target Words", f"{total_target:,}")

                if chaps:
                    df = pd.DataFrame(
                        [
                            {
                                "Chapter": f"{c.index}. {c.title}",
                                "Words": c.word_count,
                                "Target": c.target_words,
                            }
                            for c in chaps
                        ]
                    )
                    fig = px.bar(
                        df,
                        x="Chapter",
                        y=["Words", "Target"],
                        barmode="group",
                        title="Chapter Word Counts vs Targets",
                    )
                    fig.update_layout(xaxis_title="", yaxis_title="Words", height=360, legend_title_text="")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("📭 No chapters yet. Create chapters to unlock word count analytics.")

                cat_counts: Dict[str, int] = {}
                for ent in p.world_db.values():
                    cat_counts[ent.category] = cat_counts.get(ent.category, 0) + 1

                if cat_counts:
                    st.markdown("#### World Bible Coverage")
                    cat_df = pd.DataFrame(
                        [{"Category": k, "Entries": v} for k, v in sorted(cat_counts.items())]
                    )
                    fig2 = px.bar(cat_df, x="Category", y="Entries", title="World Bible Entries by Category")
                    fig2.update_layout(xaxis_title="", yaxis_title="Entries", height=300)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("No World Bible entries yet. Add or scan entities to see coverage.")

        def render_memory():
            with st.container(border=True):
                st.markdown("### Memory")
                st.caption("Store canon, tone, and guardrails the AI should always respect.")
                mem_txt = st.text_area("Story Memory", p.memory, height=180, key="mem_txt")
                if mem_txt != p.memory:
                    p.memory = mem_txt
                    save_p()

                note_cols = st.columns(2)
                with note_cols[0]:
                    author_txt = st.text_area(
                        "Author Note",
                        p.author_note,
                        height=150,
                        key="author_note_txt",
                        placeholder="E.g., 'Keep POV close and intimate. Avoid modern slang.'",
                    )
                    if author_txt != p.author_note:
                        p.author_note = author_txt
                        save_p()
                with note_cols[1]:
                    style_txt = st.text_area(
                        "Style Guide",
                        p.style_guide,
                        height=150,
                        key="style_guide_txt",
                        placeholder="E.g., 'Short sentences, cinematic beats, vivid sensory detail.'",
                    )
                    if style_txt != p.style_guide:
                        p.style_guide = style_txt
                        save_p()

                st.divider()
                st.markdown("#### Coherence Check")
                st.caption("Run a focused continuity sweep. Suggestions can replace exact passages in chapters.")

                chaps = p.get_ordered_chapters()

                def build_world_bible_text() -> str:
                    grouped: Dict[str, List[Entity]] = {}
                    for ent in p.world_db.values():
                        grouped.setdefault(ent.category, []).append(ent)

                    chunks = []
                    for category in sorted(grouped.keys()):
                        chunks.append(f"{category}s:")
                        for ent in sorted(grouped[category], key=lambda e: e.name.lower()):
                            desc = (ent.description or "").strip()
                            line = f"- {ent.name}"
                            if desc:
                                line += f": {desc}"
                            chunks.append(line)
                        chunks.append("")
                    return "\n".join(chunks).strip()

                if st.button("🧭 Run Coherence Check", type="primary", use_container_width=True):
                    if not chaps:
                        st.warning("Add chapters before running a coherence check.")
                    else:
                        with st.spinner("Checking continuity across memory, world bible, and chapters..."):
                            chapter_payload = []
                            for c in chaps:
                                excerpt = (c.content or "").strip()
                                excerpt = excerpt[:1200]
                                chapter_payload.append(
                                    {
                                        "chapter_index": c.index,
                                        "title": c.title,
                                        "summary": c.summary,
                                        "excerpt": excerpt,
                                    }
                                )
                            results = AnalysisEngine.coherence_check(
                                p.memory or "",
                                p.author_note or "",
                                p.style_guide or "",
                                p.outline or "",
                                build_world_bible_text(),
                                chapter_payload,
                                get_ai_model(),
                            )
                            st.session_state["coherence_results"] = results

                results = st.session_state.get("coherence_results", [])
                if results:
                    for idx, item in enumerate(results, start=1):
                        chap_index = item.get("chapter_index")
                        chapter = next((c for c in chaps if c.index == chap_index), None)
                        label = f"Issue {idx}"
                        if chapter:
                            label = f"Issue {idx} • Ch {chapter.index}: {chapter.title or 'Untitled'}"
                        with st.expander(label):
                            st.markdown(f"**Issue:** {item.get('issue', 'Unspecified')}")
                            st.markdown(f"**Confidence:** {item.get('confidence', 'medium')}")
                            target_excerpt = (item.get("target_excerpt") or "").strip()
                            suggested = (item.get("suggested_rewrite") or "").strip()
                            if target_excerpt:
                                st.markdown("**Target Excerpt**")
                                st.code(target_excerpt)
                            if suggested:
                                st.markdown("**Suggested Rewrite**")
                                st.code(suggested)

                            if chapter and target_excerpt and suggested:
                                if target_excerpt not in (chapter.content or ""):
                                    st.warning("Target excerpt not found in the chapter text.")
                                elif st.button(
                                    "✅ Replace in Chapter",
                                    key=f"apply_fix_{idx}",
                                    use_container_width=True,
                                ):
                                    updated = (chapter.content or "").replace(target_excerpt, suggested, 1)
                                    chapter.update_content(updated, "Coherence Fix")
                                    p.save()
                                    st.toast("Chapter updated.")
                else:
                    st.info("Run a coherence check to see continuity fixes and replacement suggestions.")

                st.divider()
                st.markdown("#### World Bible Sync")
                st.caption("Merge canon details from memory, outline, and summaries into the World Bible.")
                if st.button("🔄 Merge World Bible Info", use_container_width=True):
                    sync_text = "\n\n".join(
                        [
                            p.memory or "",
                            p.outline or "",
                            "\n".join([c.summary or "" for c in chaps]),
                        ]
                    ).strip()
                    if sync_text:
                        extract_entities_ui(sync_text[:8000], "Memory + Outline + Summaries")
                        st.toast("World Bible merged from current canon.")
                    else:
                        st.warning("Add memory, outline, or summaries to sync the World Bible.")

                st.divider()
                st.markdown("#### Chapter Summaries")
                if not chaps:
                    st.info("📭 No chapters yet. Add chapters to start building a timeline.")
                else:
                    for c in chaps:
                        label = f"{c.index}. {c.title or 'Untitled'}"
                        with st.expander(label):
                            if c.summary:
                                st.write(c.summary)
                            else:
                                st.info("No summary yet. Generate one from the chapter editor.")

        with t1: render_cat("Character")
        with t2: render_cat("Location")
        with t3: render_cat("Item")
        with t4: render_cat("Lore")
        with t5: render_cat("Faction")
        with t6: render_analytics()
        with t7: render_memory()

    def render_chapters():
        p = st.session_state.project
        chaps = p.get_ordered_chapters()

        if not chaps:
            with st.container(border=True):
                st.markdown("## Chapters")
                st.info("📭 No chapters yet.\n\nCreate your first chapter — or let MANTIS write one from your outline.")
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("➕ Create Chapter 1", type="primary", use_container_width=True):
                        p.add_chapter("Chapter 1")
                        p.save()
                        st.rerun()
                with c2:
                    if st.button("🧩 Go to Outline", use_container_width=True):
                        st.session_state.page = "outline"
                        st.session_state._force_nav = True
            return

        if "curr_chap_id" not in st.session_state or st.session_state.curr_chap_id not in p.chapters:
            st.session_state.curr_chap_id = chaps[0].id

        curr = p.chapters[st.session_state.curr_chap_id]
        # --- SAFELY sync programmatic chapter updates into the editor widget (before widget exists)
        ed_key = f"ed_{curr.id}"
        if st.session_state.get("_chapter_sync_id") == curr.id:
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
                    curr.title = clean
                    p.save()

        st.markdown("## Chapters")
        st.caption("Navigate on the left, write in the center, and use AI tools on the right.")

        col_nav, col_editor, col_ai = st.columns([1.05, 3.2, 1.25])

        with col_nav:
            with st.container(border=True):
                st.markdown("### 📍 Navigation")
                for c in chaps:
                    lbl = f"{c.index}. {(c.title or 'Untitled')[:18]}"
                    if st.button(lbl, key=f"n_{c.id}", type="primary" if c.id == curr.id else "secondary", use_container_width=True):
                        st.session_state.curr_chap_id = c.id
                        st.rerun()

                st.divider()
                if st.button("➕ New Chapter", use_container_width=True):
                    next_idx = len(chaps) + 1
                    pat = re.compile(rf"Chapter {next_idx}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
                    match = pat.search(p.outline or "")
                    if match:
                        raw = match.group(1).strip()
                        title = re.split(r" [-–:] ", raw, 1)[0].strip()
                    else:
                        title = f"Chapter {next_idx}"
                    p.add_chapter(title)
                    p.save()
                    st.rerun()

        stream_ph = st.empty()

        with col_editor:
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])
                with h1:
                    curr.title = st.text_input("Title", curr.title, label_visibility="collapsed")
                with h2:
                    curr.target_words = st.number_input("Target", 100, 10000, int(curr.target_words), label_visibility="collapsed")

                val = st.text_area("Manuscript", curr.content, height=680, label_visibility="collapsed", key=f"ed_{curr.id}")
                if val != curr.content:
                    curr.update_content(val, "manual")
                    save_p()

                st.caption(f"📝 Chapter: {curr.word_count} words • 📚 Total: {p.get_total_word_count()} words")

                c1, c2, c3 = st.columns([1, 1, 1])
                with c1:
                    if st.button("💾 Save Chapter", type="primary", use_container_width=True):
                        curr.update_content(val, "manual")
                        p.save()
                        # Automatically scan entities from this chapter when the user explicitly saves it.
                        extract_entities_ui(curr.content or "", f"Ch {curr.index}")
                        st.toast("Chapter Saved & Entities Scanned")
                with c2:
                    if st.button("🔍 Scan Entities", use_container_width=True):
                        # Manual re-scan option for this chapter.
                        extract_entities_ui(curr.content or "", f"Ch {curr.index}")
                with c3:
                    if st.button("📝 Update Summary", use_container_width=True):
                        curr.summary = StoryEngine.summarize(curr.content or "", get_ai_model())
                        p.save()
                        st.rerun()

                with st.expander("✨ Modify / Improve Text"):
                    style = st.selectbox("How to improve?", list(REWRITE_PRESETS.keys()))
                    cust = st.text_input("Instructions") if style == "Custom" else ""
                    if st.button("Apply Changes", use_container_width=True):
                        prompt = rewrite_prompt(curr.content or "", style, cust)
                        st.session_state.ghost_text = ""
                        full = ""
                        for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                            full += chunk
                            stream_ph.markdown(f"**IMPROVING:**\n\n{full}")
                        st.session_state.ghost_text = full

        with col_ai:
            with st.container(border=True):
                st.markdown("### 🤖 Assistant")
                st.caption("Generate new prose from your outline + previous context.")

                if st.button("✨ Auto-Write Chapter", type="primary", use_container_width=True):
                    prompt = StoryEngine.generate_chapter_prompt(p, curr.index, int(curr.target_words))
                    full = ""
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        stream_ph.markdown(f"**GENERATING:**\n\n{full}")

                    if full.strip():
                        new_text = ((curr.content or "") + "\n" + full.strip()).strip()
                        curr.update_content(new_text, "AI Auto-Write")
                        p.save()

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

        if st.session_state.ghost_text:
            with st.container(border=True):
                st.warning("⚠️ Pending AI Text generated (not inserted yet).")
                g1, g2 = st.columns([1, 1])
                with g1:
                    if st.button("✅ Insert into Editor", type="primary", use_container_width=True):
                        new_text = ((curr.content or "") + "\n" + (st.session_state.ghost_text or "")).strip()
                        curr.update_content(new_text, "AI Insert")
                        st.session_state.ghost_text = ""
                        p.save()

                        st.session_state._chapter_sync_id = curr.id
                        st.session_state._chapter_sync_text = new_text

                        st.rerun()
                with g2:
                    if st.button("🗑 Discard", use_container_width=True):
                        st.session_state.ghost_text = ""
                        st.rerun()

    def render_export():
        p = st.session_state.project
        st.markdown("## Export")
        st.caption("Download a single markdown file containing outline, world bible, and chapters.")
        with st.container(border=True):
            st.download_button("⬇️ Download .md", project_to_markdown(p), file_name=f"{p.title}.md", use_container_width=True)
            st.caption("Tip: You can convert .md to .docx/.pdf with many tools if needed.")

    rendered_page = False
    if st.session_state.page == "home":
        render_home()
        rendered_page = True
    elif st.session_state.page == "projects":
        render_projects()
        rendered_page = True
    elif st.session_state.page == "ai":
        render_ai_settings()
        rendered_page = True
    elif st.session_state.project:
        pg = st.session_state.page
        if pg == "outline":
            render_outline()
            rendered_page = True
        elif pg == "world":
            render_world()
            rendered_page = True
        elif pg == "chapters":
            render_chapters()
            rendered_page = True
        elif pg == "export":
            render_export()
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
        original_users_db = json.loads(json.dumps(load_users_db()))
        test_username = f"selftest_{uuid.uuid4().hex[:8]}"
        test_password = "Testpass1234"
        user_result = create_user(test_username, "Self Test", test_password)
        if not user_result.get("ok"):
            raise RuntimeError(f"User create failed: {user_result.get('error', 'unknown')}")
        auth_result = authenticate_user(test_username, test_password)
        if not auth_result.get("ok"):
            raise RuntimeError(f"User auth failed: {auth_result.get('error', 'unknown')}")
        user_id = auth_result["user"]["id"]
        user_projects_dir = get_user_projects_dir(user_id)

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
        try:
            save_users_db(original_users_db)
        except Exception:
            logger.warning("Selftest cleanup failed for users DB", exc_info=True)

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
