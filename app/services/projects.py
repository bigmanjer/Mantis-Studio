"""Project models and logic for Mantis Studio.

Note: This module is part of the new app/ structure.
      Current implementation still uses mantis.core.models for backward compatibility.
      These imports will be updated when the migration is complete.
"""
from __future__ import annotations

import difflib
import json
import os
import re
import shutil
import time
import uuid
from dataclasses import asdict, dataclass, field, fields
from typing import Any, Dict, List, Optional

from app.config.settings import AppConfig, logger
from app.services.storage import _acquire_lock, _release_lock, resolve_storage_dir


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
            # Use list building and join for efficient string assembly
            desc_parts = []
            if self.description:
                if not self.description.startswith("-"):
                    desc_parts.append(f"- {self.description.strip()}")
                else:
                    desc_parts.append(self.description)
            
            for item in to_add:
                desc_parts.append(f"- {item}")
            
            self.description = "\n".join(desc_parts)


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
        """Update chapter content and track in revision history.
        
        Args:
            new_text: The new chapter content
            source: Source of the update (e.g., "manual", "ai", "import")
        """
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


def sanitize_chapter_title(title: str) -> str:
    """Clean and normalize a chapter title.
    
    Removes quotes, asterisks, extra whitespace, and other formatting artifacts.
    
    Args:
        title: Raw chapter title
        
    Returns:
        Cleaned chapter title string
    """
    raw = (title or "").strip()
    if not raw:
        return ""
    clean = raw.replace("“", "").replace("”", "").replace("’", "")
    clean = clean.replace('"', "").replace("'", "")
    clean = re.sub(r"^\*+|\*+$", "", clean).strip()
    clean = re.sub(r"\s{2,}", " ", clean).strip()
    return clean


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
        storage_dir = resolve_storage_dir(storage_dir)
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
