#!/usr/bin/env python3
# mantis_onefile_v44.py — MANTIS Studio v44 (Chronicle) — SINGLE FILE EDITION
#
# Run:
#   python -m streamlit run mantis_onefile_v44.py
#
# Requirements:
#   streamlit>=1.30.0
#   requests
#   python-dotenv (optional)
#   pandas
#   plotly
#
# Notes:
# - This preserves ALL current features from your v44 generator build:
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
import uuid
import difflib
import logging
import hashlib
import hmac
from dataclasses import dataclass, field, asdict, fields
from typing import Dict, List, Optional, Any, Generator

import requests
# (UI-only imports are loaded inside _run_ui() so selftests can run without Streamlit installed.)

import sys


# ===== v45 BRANDING (SAFE, ORIGINAL TEMPLATE) =====
import base64
from urllib.parse import urlparse

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
    OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))
    DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
    OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    CONFIG_PATH = os.getenv(
        "MANTIS_CONFIG_PATH",
        os.path.join(PROJECTS_DIR, ".mantis_config.json"),
    )
    MAX_PROMPT_CHARS = 16000
    SUMMARY_CONTEXT_CHARS = 4000


def normalize_ollama_base_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return AppConfig.OLLAMA_API_URL.rstrip("/")
    if "://" not in raw:
        raw = f"http://{raw}"
    parsed = urlparse(raw)
    path = parsed.path.rstrip("/")
    if path.endswith("/api/v1"):
        path = path[: -len("/api/v1")]
    elif path.endswith("/api"):
        path = path[: -len("/api")]
    normalized = parsed._replace(path=path, params="", query="", fragment="").geturl()
    return normalized.rstrip("/")


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

    def add_entity(self, name: str, category: str, desc: str = "") -> Optional[Entity]:
        """Smart Add with Fuzzy Matching."""
        clean_name = (name or "").strip()
        if not clean_name:
            return None

        for ent in self.world_db.values():
            if ent.category == category:
                similarity = difflib.SequenceMatcher(None, ent.name.lower(), clean_name.lower()).ratio()
                if similarity > 0.80:
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
        tmp = path + ".tmp"
        last_error: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
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
    def __init__(self, timeout: int = AppConfig.OLLAMA_TIMEOUT, base_url: Optional[str] = None):
        resolved_base = normalize_ollama_base_url(base_url or AppConfig.OLLAMA_API_URL)
        self.base_url = resolved_base
        self.timeout = timeout
        self.session = requests.Session()

    def probe_models(self) -> List[str]:
        try:
            r = self.session.get(f"{self.base_url}/api/tags", timeout=3)
            r.raise_for_status()
            data = r.json()
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            logger.warning("Model probe failed for %s", self.base_url, exc_info=True)
            return []

    def generate_stream(self, prompt: str, model: str) -> Generator[str, None, None]:
        if not model or "Offline" in model:
            yield "AI is offline."
            return

        if model.startswith("openai:"):
            openai_model = model.split("openai:", 1)[1].strip()
            if not openai_model:
                yield "OpenAI model not configured."
                return
            api_key = (AppConfig.OPENAI_API_KEY or "").strip()
            openai_base = AppConfig.OPENAI_API_URL.rstrip("/")
            if not api_key and "api.openai.com" in openai_base:
                yield "OpenAI API key not configured."
                return

            payload = {
                "model": openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            }
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            try:
                with self.session.post(
                    f"{openai_base}/chat/completions",
                    json=payload,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
                ) as r:
                    r.raise_for_status()
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
                            yield content
                return
            except Exception:
                logger.warning("OpenAI generation failed", exc_info=True)
                yield "OpenAI generation failed."
                return

        payload = {
            "model": model,
            "prompt": (prompt or "")[-AppConfig.MAX_PROMPT_CHARS:],
            "stream": True,
            "options": {"num_ctx": 8192},
        }

        try:
            with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout,
            ) as r:
                r.raise_for_status()
                buffer = ""
                is_start = True

                for line in r.iter_lines():
                    if not line:
                        continue

                    try:
                        json_obj = json.loads(line.decode("utf-8"))
                        chunk = json_obj.get("response", "")
                        done = json_obj.get("done", False)

                        if is_start:
                            if not chunk.strip() and not done:
                                continue
                            buffer += chunk
                            if len(buffer) < 40 and not done:
                                continue
                            clean = buffer
                            clean = re.sub(r"(?i)^(sure|here|certainly|okay).*?:\s*", "", clean)
                            clean = re.sub(r"(?i)^\*\*.*?\*\*\s*", "", clean)
                            yield clean
                            is_start = False
                            buffer = ""
                        else:
                            if chunk:
                                yield chunk

                        if done and buffer:
                            yield buffer
                    except Exception:
                        logger.debug("Stream chunk parse failed from %s", self.base_url, exc_info=True)

        except Exception as e:
            logger.error("Stream generation failed for %s", self.base_url, exc_info=True)
            yield f"\n[Error: {str(e)}]"

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

    st.set_page_config(page_title=AppConfig.APP_NAME, layout="wide")

    config_data = load_app_config()

    # --- BRAND HEADER (UI only) ---
    st.markdown(f"""
        <div style="
            display:flex;
            align-items:center;
            gap:14px;
            padding:14px 20px;
            border-radius:18px;
            background: linear-gradient(135deg, #43a047, #1b5e20);
            margin-top: 18px;
            margin-bottom: 18px;
            box-shadow: 0 8px 22px rgba(0,0,0,0.32);
        ">
            <div style="
                width:46px;
                height:46px;
                border-radius:14px;
                background:#0b3d1f;
                display:flex;
                align-items:center;
                justify-content:center;
                overflow:hidden;
                box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
            ">
                <img src="data:image/png;base64,{_MANTIS_LOGO_B64}" style="height:28px; width:auto; padding:6px; border-radius:10px;" />
            </div>
            <div style="line-height:1.15;">
                <div style="font-size:24px;font-weight:800;color:white;">
                    MANTIS Studio
                </div>
                <div style="color:#c8e6c9;font-size:13px;">
                    Plan • Write • Grow your story with AI
                </div>
            </div>
        </div>
        """ , unsafe_allow_html=True)



    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600&family=Inter:wght@400;600&display=swap');
    .stApp { background-color: #0e1117; color: #e6edf3; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 0.6rem; padding-bottom: 2rem; }
    h1, h2, h3 { letter-spacing: -0.02em; }
    .stTextInput input, .stSelectbox div, .stNumberInput input { background-color: #0f1521 !important; color: #e6edf3 !important; border: 1px solid #253041 !important; }
    .stTextArea textarea { background-color: #0f1521 !important; color: #e6edf3 !important; font-family: 'Crimson Pro', serif !important; font-size: 18px !important; line-height: 1.65 !important; border: 1px solid #253041 !important; }
    
    .stButton>button {
        border-radius: 16px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.1rem !important;
        transition: all 0.15s ease-in-out;
        border: 1px solid #2a3750 !important;
        background: linear-gradient(180deg, #1e293b, #0f172a) !important;
        color: #e6edf3 !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        border-color: #4caf50 !important;
        box-shadow: 0 8px 18px rgba(0,0,0,0.35);
    }
    .stButton>button:active { transform: translateY(0); }
    .stButton>button:focus { outline: none !important; box-shadow: none !important; }

    /* --- BUTTON HIERARCHY --- */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #43a047, #1b5e20) !important;
        border-color: rgba(255,255,255,0.14) !important;
        box-shadow: 0 10px 22px rgba(0,0,0,0.35);
    }
    .stButton>button[kind="primary"]:hover {
        border-color: #81c784 !important;
        box-shadow: 0 12px 26px rgba(0,0,0,0.45);
    }
    .stButton>button[kind="secondary"] {
        background: linear-gradient(180deg, #1e293b, #0f172a) !important;
    }


    [data-testid="stVerticalBlock"] [data-testid="stContainer"] { border-radius: 16px !important; }
    .stExpander { border: 1px solid #253041 !important; border-radius: 16px !important; }
    hr { border-color: #1e2636 !important; }
    section[data-testid="stSidebar"] { background-color: #0b1019; border-right: 1px solid #1e2636; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 { color: #e6edf3; }
    div[data-testid="stToast"] { border-radius: 14px !important; }
    
    /* --- CARD POLISH --- */
    div[data-testid="stContainer"] {
        background: linear-gradient(180deg, #111827, #0b1220);
        border-radius: 20px !important;
        padding: 22px !important;
        border: 1px solid #1f2937 !important;
        box-shadow: 0 12px 28px rgba(0,0,0,0.45);
        margin-bottom: 18px;
    }
    div[data-testid="stContainer"] h3 {
        margin-top: 0;
        margin-bottom: 12px;
        color: #e5e7eb;
    }

    /* --- SIDEBAR POLISH --- */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617, #020617);
        border-right: 1px solid #1e2936;
    }
    section[data-testid="stSidebar"] h3 {
        color: #4caf50;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-size: 12px;
    }

    
    /* --- SIDEBAR BRAND --- */
    .mantis-sidebar-brand{
        display:flex;
        gap:12px;
        align-items:center;
        padding:14px 12px 12px 12px;
        margin: 4px 8px 10px 8px;
        border-radius: 16px;
        background: linear-gradient(180deg, rgba(17,24,39,0.75), rgba(2,6,23,0.9));
        border: 1px solid rgba(76,175,80,0.18);
        box-shadow: 0 10px 22px rgba(0,0,0,0.35);
    }
    .mantis-sidebar-logo{
        width:38px;
        height:38px;
        border-radius: 12px;
        background: rgba(0,0,0,0.20);
        display:flex;
        align-items:center;
        justify-content:center;
        overflow:hidden;
        box-shadow: inset 0 0 0 1px rgba(255,255,255,0.08);
        flex: 0 0 auto;
    }
    .mantis-sidebar-logo img{
        height:22px;
        width:auto;
        display:block;
    }
    .mantis-sidebar-title{
        font-weight:800;
        font-size:14px;
        color:#e6edf3;
        line-height:1.1;
    }
    .mantis-sidebar-sub{
        font-size:12px;
        color:#9aa4b2;
        margin-top:2px;
        line-height:1.1;
    }
</style>
    """,
        unsafe_allow_html=True,
    )

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
    if "model_list" not in st.session_state:
        st.session_state.model_list = []
    if "ai_provider" not in st.session_state:
        st.session_state.ai_provider = config_data.get("ai_provider", "Ollama")
    if "ollama_base_url" not in st.session_state:
        st.session_state.ollama_base_url = normalize_ollama_base_url(
            config_data.get("ollama_base_url", AppConfig.OLLAMA_API_URL)
        )
    if "openai_base_url" not in st.session_state:
        st.session_state.openai_base_url = config_data.get("openai_base_url", AppConfig.OPENAI_API_URL)
    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = config_data.get("openai_api_key", AppConfig.OPENAI_API_KEY)
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = config_data.get("openai_model", AppConfig.OPENAI_MODEL)

    if "_force_nav" not in st.session_state:
        st.session_state._force_nav = False

    AppConfig.OLLAMA_API_URL = normalize_ollama_base_url(st.session_state.ollama_base_url)
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
        provider = st.session_state.get("ai_provider", "Ollama")
        if provider == "OpenAI":
            return f"openai:{st.session_state.get('openai_model', AppConfig.OPENAI_MODEL)}"
        return st.session_state.get("selected_model", AppConfig.DEFAULT_MODEL)

    def save_p():
        if st.session_state.project and st.session_state.auto_save:
            st.session_state.project.save()

    def get_active_projects_dir() -> str:
        return st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR

    def render_auth():
        st.markdown(
            """
            <div style="max-width:480px;margin:0 auto;padding:24px 12px;">
                <h2 style="margin-bottom:8px;">Welcome to MANTIS Studio</h2>
                <p style="margin-top:0;color:#9aa4b2;">
                    Sign in or create an account to keep your projects saved.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        tabs = st.tabs(["Sign In", "Create Account", "Guest"])

        with tabs[0]:
            username = st.text_input("Username", key="auth_login_username", placeholder="e.g. alex")
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
                    st.session_state._force_nav = True
                    st.rerun()

        with tabs[1]:
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
                elif len(new_password or "") < 6:
                    st.error("Password must be at least 6 characters.")
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
                        st.session_state._force_nav = True
                        st.rerun()

        with tabs[2]:
            st.caption("Guest sessions store projects separately and may be cleared by the host.")
            if st.button("Continue as Guest", use_container_width=True):
                guest_id = st.session_state.get("guest_id") or str(uuid.uuid4())
                st.session_state.guest_id = guest_id
                st.session_state.auth_user = "Guest"
                st.session_state.auth_user_id = guest_id
                st.session_state.auth_username = "guest"
                st.session_state.auth_is_guest = True
                st.session_state.projects_dir = get_guest_projects_dir(guest_id)
                st.session_state._force_nav = True
                st.rerun()

    @st.cache_data(show_spinner=False)
    def _cached_models(base_url: str) -> List[str]:
        return AIEngine(base_url=base_url).probe_models()

    def refresh_models():
        st.session_state.model_list = _cached_models(AppConfig.OLLAMA_API_URL) or []

    def save_provider_settings():
        data = {
            "ai_provider": st.session_state.ai_provider,
            "ollama_base_url": st.session_state.ollama_base_url,
            "openai_base_url": st.session_state.openai_base_url,
            "openai_api_key": st.session_state.openai_api_key,
            "openai_model": st.session_state.openai_model,
        }
        save_app_config(data)
        st.toast("Provider settings saved.")

    def test_ollama_connection(base_url: str) -> tuple[bool, str]:
        try:
            normalized = normalize_ollama_base_url(base_url)
            r = requests.get(f"{normalized}/api/tags", timeout=5)
            r.raise_for_status()
            return True, ""
        except Exception as exc:
            return False, str(exc)

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

    if not st.session_state.auth_user:
        render_auth()
        return

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
        st.markdown("### 🧠 AI Engine")
        st.caption(f"Signed in as **{st.session_state.auth_user}**")
        if st.session_state.auth_username and not st.session_state.auth_is_guest:
            st.caption(f"@{st.session_state.auth_username}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.auth_user = None
            st.session_state.auth_user_id = None
            st.session_state.auth_username = None
            st.session_state.auth_is_guest = False
            st.session_state.projects_dir = None
            st.session_state.project = None
            st.session_state.page = "home"
            st.session_state._force_nav = True
            st.rerun()

        provider = st.selectbox("Provider", ["Ollama", "OpenAI"], key="ai_provider")

        if provider == "Ollama":
            ollama_url = st.text_input("Ollama Base URL", value=st.session_state.ollama_base_url)
            normalized_ollama_url = normalize_ollama_base_url(ollama_url)
            if normalized_ollama_url != st.session_state.ollama_base_url:
                st.session_state.ollama_base_url = normalized_ollama_url
                AppConfig.OLLAMA_API_URL = normalized_ollama_url
                st.cache_data.clear()
                refresh_models()
            st.caption("Ollama must be reachable from the server hosting MANTIS Studio.")

            if not st.session_state.model_list:
                refresh_models()
            models = st.session_state.model_list or ["Offline"]

            idx = 0
            if AppConfig.DEFAULT_MODEL in models:
                idx = models.index(AppConfig.DEFAULT_MODEL)

            st.selectbox("🧠 AI Model", models, index=idx, key="selected_model")

            if st.button("🔌 Test Ollama Connection", use_container_width=True):
                ok, error_message = test_ollama_connection(st.session_state.ollama_base_url)
                if ok:
                    st.success("Ollama connection OK.")
                else:
                    st.error(f"Could not reach Ollama. {error_message or 'Check the base URL and server.'}")
        else:
            openai_url = st.text_input("OpenAI Base URL", value=st.session_state.openai_base_url)
            if openai_url != st.session_state.openai_base_url:
                st.session_state.openai_base_url = openai_url
                AppConfig.OPENAI_API_URL = openai_url

            openai_key = st.text_input(
                "OpenAI API Key (optional for local servers)",
                value=st.session_state.openai_api_key,
                type="password",
                help="Leave blank for local OpenAI-compatible servers (LM Studio, llama.cpp).",
            )
            if openai_key != st.session_state.openai_api_key:
                st.session_state.openai_api_key = openai_key
                AppConfig.OPENAI_API_KEY = openai_key

            openai_model = st.text_input("OpenAI Model", value=st.session_state.openai_model)
            if openai_model != st.session_state.openai_model:
                st.session_state.openai_model = openai_model
                AppConfig.OPENAI_MODEL = openai_model

            st.markdown(
                "[Create an OpenAI account](https://platform.openai.com/signup) to get an API key, "
                "or point the base URL to a local OpenAI-compatible server for free models."
            )
            if st.button("🔌 Test OpenAI Connection", use_container_width=True):
                ok = test_openai_connection(
                    st.session_state.openai_base_url,
                    st.session_state.openai_api_key,
                )
                if ok:
                    st.success("OpenAI connection OK.")
                else:
                    st.error("OpenAI connection failed. Check your base URL and key if required.")

        colm1, colm2 = st.columns([1, 1])
        with colm1:
            st.checkbox("Auto-save", key="auto_save")
        with colm2:
            if provider == "Ollama" and st.button("↻ Refresh", use_container_width=True):
                st.cache_data.clear()
                refresh_models()
                st.toast("Model list refreshed")

        if st.button("💾 Save Provider Settings", use_container_width=True):
            save_provider_settings()
        st.divider()

        if st.session_state.project:
            p = st.session_state.project
            st.markdown("### 📖 Project")
            st.caption(p.title)
            st.caption(f"🗂 Projects folder: `{get_active_projects_dir()}`")
            st.caption(f"📚 Total words: {p.get_total_word_count()}")

            st.divider()
            st.markdown("### 🧭 Navigation")

            nav_labels = ["Dashboard", "Outline", "Chapters", "World Bible", "Export"]
            pmap = {"Dashboard": "home", "Outline": "outline", "World Bible": "world", "Chapters": "chapters", "Export": "export"}
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
        if st.session_state.get("first_run", True):
            with st.container(border=True):
                st.markdown("### 👋 Welcome")
                st.markdown(
                    """
**MANTIS** helps you plan, write, and grow a story with AI — without losing control.

**Quick path**
1) Create a project  
2) Add or generate an outline  
3) Write chapters (use AI only when you want)
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
                    st.caption("Tip: If the AI model shows Offline, start Ollama or your local provider first.")
            st.write("")

        st.markdown("## Studio Dashboard")
        st.caption("Create a project, load a recent one, or import a story to start building.")

        colA, colB = st.columns([1.1, 1.3])

        with colA:
            with st.container(border=True):
                st.markdown("### ✨ New Project")
                with st.form("new_project_form", clear_on_submit=False):
                    t = st.text_input("Title", placeholder="e.g., The Chronicle of Ash")
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

                st.divider()
                st.markdown("### 📥 Import Story")
                st.caption("Upload a .txt or .md and MANTIS will split it into chapters when possible.")
                uf = st.file_uploader("Upload file", type=["txt", "md"])
                if uf:
                    txt = uf.read().decode("utf-8", errors="replace")
                    if st.button("Import & Analyze", use_container_width=True):
                        p = Project.create("Imported Project", storage_dir=get_active_projects_dir())
                        p.import_text_file(txt)
                        p.save()
                        st.session_state.project = p
                        st.session_state.page = "chapters"
                        st.session_state.first_run = False
                        st.rerun()

        with colB:
            with st.container(border=True):
                st.markdown("### 🕘 Recent Projects")
                st.caption("Click to open. Use 🗑 to delete the file from disk.")

                files = []
                active_dir = get_active_projects_dir()
                if os.path.exists(active_dir):
                    files = sorted(
                        [f for f in os.listdir(active_dir) if f.endswith(".json")],
                        key=lambda x: os.path.getmtime(os.path.join(active_dir, x)),
                        reverse=True,
                    )

                if not files:
                    st.info("📭 No projects yet. Create one on the left to get started.")
                else:
                    for f in files[:30]:
                        full = os.path.join(active_dir, f)
                        try:
                            with open(full, "r", encoding="utf-8") as fh:
                                meta = json.load(fh)
                            title = meta.get("title") or f
                            genre = meta.get("genre") or ""
                            row1, row2, row3 = st.columns([6, 2, 1])
                            with row1:
                                if st.button(f"📂 {title}", key=f"open_{f}", use_container_width=True):
                                    st.session_state.project = Project.load(full)
                                    st.session_state.page = "chapters"
                                    st.session_state.first_run = False
                                    st.rerun()
                            with row2:
                                st.caption(genre)
                            with row3:
                                if st.button("🗑", key=f"del_{f}", use_container_width=True):
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
                st.caption("Store high-level canon details you want the AI to remember.")
                mem_txt = st.text_area("Story Memory", p.memory, height=220, key="mem_txt")
                if mem_txt != p.memory:
                    p.memory = mem_txt
                    save_p()

                st.divider()
                st.markdown("#### Chapter Summaries")
                chaps = p.get_ordered_chapters()
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

    if st.session_state.page == "home":
        render_home()
    elif st.session_state.project:
        pg = st.session_state.page
        if pg == "outline": render_outline()
        elif pg == "world": render_world()
        elif pg == "chapters": render_chapters()
        elif pg == "export": render_export()
        else:
            st.session_state.page = "home"
            st.rerun()
    else:
        st.session_state.page = "home"
        st.rerun()


def run_selftest() -> int:
    """
    Quick non-UI integrity test. Intended to be called by the launcher.
    Creates a temporary project, exercises save/load, chapters/entities/export, then cleans up.
    """
    print("[MANTIS SELFTEST]")
    try:
        os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)

        p = Project.create("SELFTEST_PROJECT", author="MANTIS", genre="Test")
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
