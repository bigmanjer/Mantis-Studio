"""World Bible database layer for MANTIS Studio.

Provides a structured "mini database" for world-building entities with
CRUD helpers, search, tagging, consistency checking, and canon conflict
detection.  All data lives in ``st.session_state["world_bible_db"]`` so
it persists across Streamlit reruns without external storage.

Usage (inside a Streamlit app)::

    from app.services.world_bible_db import (
        ensure_world_bible_db,
        add_entry,
        search_world_bible,
        validate_world_bible_db,
    )

    ensure_world_bible_db()          # safe to call every rerun
    add_entry("characters", {"name": "Alice", "description": "Hero"})
"""
from __future__ import annotations

import copy
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Schema constants
# ---------------------------------------------------------------------------

CATEGORIES: Tuple[str, ...] = (
    "characters",
    "locations",
    "factions",
    "history",
    "rules",
)

REQUIRED_ENTRY_FIELDS: Tuple[str, ...] = ("name", "description", "tags", "created_at")


# ---------------------------------------------------------------------------
# Initialisation helpers
# ---------------------------------------------------------------------------

def _empty_db() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Return a fresh, empty world-bible database dict."""
    return {cat: {} for cat in CATEGORIES}


def ensure_world_bible_db(session_state: Any) -> Dict[str, Any]:
    """Guarantee ``session_state["world_bible_db"]`` exists and is valid.

    Safe to call on every rerun — uses ``setdefault`` so existing data
    is never overwritten.
    """
    db = session_state.setdefault("world_bible_db", _empty_db())
    # Ensure every required category key exists
    for cat in CATEGORIES:
        if cat not in db or not isinstance(db[cat], dict):
            db[cat] = {}
    session_state.setdefault("world_bible_versions", [])
    session_state.setdefault("world_bible_last_saved", False)
    return db


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _generate_id(prefix: str = "wb") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_db(session_state: Any) -> Dict[str, Any]:
    """Return the world-bible DB from *session_state*, creating it if needed."""
    return ensure_world_bible_db(session_state)


def _normalise_category(category: str) -> str:
    """Map a category string to its canonical lower-case plural form."""
    cat = (category or "").strip().lower()
    mapping = {
        "character": "characters",
        "characters": "characters",
        "location": "locations",
        "locations": "locations",
        "faction": "factions",
        "factions": "factions",
        "history": "history",
        "rule": "rules",
        "rules": "rules",
    }
    return mapping.get(cat, cat if cat in CATEGORIES else "rules")


# ---------------------------------------------------------------------------
# CRUD functions
# ---------------------------------------------------------------------------

def add_entry(
    category: str,
    entry: Dict[str, Any],
    *,
    session_state: Any,
) -> Tuple[str, Dict[str, Any]]:
    """Add a new entry to *category* and return ``(entry_id, entry)``."""
    db = _resolve_db(session_state)
    cat = _normalise_category(category)

    entry_id = _generate_id(cat[:4])
    now = _now_iso()
    record: Dict[str, Any] = {
        "id": entry_id,
        "name": (entry.get("name") or "").strip() or "Unnamed",
        "description": (entry.get("description") or "").strip(),
        "tags": list(entry.get("tags") or []),
        "created_at": entry.get("created_at") or now,
        "updated_at": now,
    }
    # Preserve any extra keys the caller supplies
    for k, v in entry.items():
        if k not in record:
            record[k] = v

    db[cat][entry_id] = record
    _mark_saved(session_state)
    _snapshot_version(session_state)
    return entry_id, record


def update_entry(
    category: str,
    entry_id: str,
    updates: Dict[str, Any],
    *,
    session_state: Any,
) -> Optional[Dict[str, Any]]:
    """Update fields on an existing entry.  Returns the updated record or ``None``."""
    db = _resolve_db(session_state)
    cat = _normalise_category(category)
    bucket = db.get(cat)
    if not bucket or entry_id not in bucket:
        return None
    record = bucket[entry_id]
    for k, v in updates.items():
        record[k] = v
    record["updated_at"] = _now_iso()
    _mark_saved(session_state)
    _snapshot_version(session_state)
    return record


def delete_entry(
    category: str,
    entry_id: str,
    *,
    session_state: Any,
) -> bool:
    """Remove an entry.  Returns ``True`` if something was deleted."""
    db = _resolve_db(session_state)
    cat = _normalise_category(category)
    bucket = db.get(cat)
    if not bucket or entry_id not in bucket:
        return False
    del bucket[entry_id]
    _mark_saved(session_state)
    _snapshot_version(session_state)
    return True


def get_entry(
    category: str,
    entry_id: str,
    *,
    session_state: Any,
) -> Optional[Dict[str, Any]]:
    """Return a single entry or ``None``."""
    db = _resolve_db(session_state)
    cat = _normalise_category(category)
    return db.get(cat, {}).get(entry_id)


def list_entries(
    category: str,
    *,
    session_state: Any,
) -> Dict[str, Dict[str, Any]]:
    """Return all entries in *category* as ``{entry_id: entry}``."""
    db = _resolve_db(session_state)
    cat = _normalise_category(category)
    return dict(db.get(cat, {}))


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search_world_bible(
    query: str,
    *,
    session_state: Any,
) -> List[Dict[str, Any]]:
    """Case-insensitive search across name, description, and tags.

    Returns a list of dicts each containing ``category``, ``entry_id``,
    and the full ``entry`` data.
    """
    db = _resolve_db(session_state)
    q = (query or "").strip().lower()
    if not q:
        return []

    results: List[Dict[str, Any]] = []
    for cat, bucket in db.items():
        for eid, entry in bucket.items():
            name_match = q in (entry.get("name") or "").lower()
            desc_match = q in (entry.get("description") or "").lower()
            tag_match = any(q in (t or "").lower() for t in (entry.get("tags") or []))
            if name_match or desc_match or tag_match:
                results.append({
                    "category": cat,
                    "entry_id": eid,
                    "entry": entry,
                })
    return results


# ---------------------------------------------------------------------------
# Tagging
# ---------------------------------------------------------------------------

def get_entries_by_tag(
    tag: str,
    *,
    session_state: Any,
) -> List[Dict[str, Any]]:
    """Return all entries whose ``tags`` list contains *tag* (case-insensitive)."""
    db = _resolve_db(session_state)
    tag_lower = (tag or "").strip().lower()
    if not tag_lower:
        return []

    results: List[Dict[str, Any]] = []
    for cat, bucket in db.items():
        for eid, entry in bucket.items():
            if any(tag_lower == (t or "").strip().lower() for t in (entry.get("tags") or [])):
                results.append({
                    "category": cat,
                    "entry_id": eid,
                    "entry": entry,
                })
    return results


# ---------------------------------------------------------------------------
# Consistency checking (local — no API key required)
# ---------------------------------------------------------------------------

def check_world_bible_consistency(
    entry_text: str,
    *,
    session_state: Any,
) -> List[str]:
    """Scan *entry_text* for references to known world-bible entries.

    Returns a list of human-readable warnings such as::

        "Character referenced but not in World Bible: Marcus"

    This function works entirely offline — it uses world-bible data
    stored in *session_state* and never calls an external API.
    """
    db = _resolve_db(session_state)
    if not entry_text:
        return []

    text_lower = entry_text.lower()
    warnings: List[str] = []

    known_names: Dict[str, str] = {}  # lower-name -> category
    for cat, bucket in db.items():
        for entry in bucket.values():
            name = (entry.get("name") or "").strip()
            if name:
                known_names[name.lower()] = cat

    # Check for names that appear in text but *aren't* in the world bible.
    # We extract capitalised multi-word phrases as candidates.
    candidate_pattern = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b")
    candidates = set(candidate_pattern.findall(entry_text))

    for candidate in candidates:
        candidate_lower = candidate.lower()
        if candidate_lower not in known_names:
            # Only warn if the candidate looks like a proper noun
            if len(candidate) > 1:
                warnings.append(
                    f"Referenced but not in World Bible: {candidate}"
                )

    return warnings


# ---------------------------------------------------------------------------
# Canon conflict detection
# ---------------------------------------------------------------------------

def detect_canon_conflicts(
    entry: Dict[str, Any],
    *,
    session_state: Any,
) -> List[str]:
    """Detect conflicts between *entry* and existing world-bible data.

    Checks for:
    - duplicate character names
    - duplicate locations
    - entries with identical names across any category
    - conflicting rule definitions

    Returns a list of human-readable conflict descriptions.
    """
    db = _resolve_db(session_state)
    conflicts: List[str] = []
    entry_name = (entry.get("name") or "").strip().lower()
    if not entry_name:
        return conflicts

    for cat, bucket in db.items():
        for eid, existing in bucket.items():
            existing_name = (existing.get("name") or "").strip().lower()
            if existing_name == entry_name:
                conflicts.append(
                    f"Duplicate name '{entry.get('name')}' found in {cat} "
                    f"(entry {eid})"
                )

    return conflicts


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_world_bible_db(*, session_state: Any) -> Dict[str, Any]:
    """Validate and repair the world-bible database.

    Ensures:
    - all categories exist
    - every entry has required fields (``name``, ``description``, ``tags``,
      ``created_at``)
    - ``tags`` is always a list
    - ``None`` values in required fields are replaced with safe defaults

    Returns the cleaned database dict.
    """
    db = _resolve_db(session_state)

    for cat in CATEGORIES:
        if cat not in db or not isinstance(db[cat], dict):
            db[cat] = {}

    now = _now_iso()
    for cat in CATEGORIES:
        to_delete: List[str] = []
        for eid, entry in db[cat].items():
            if not isinstance(entry, dict):
                to_delete.append(eid)
                continue

            # Ensure required fields
            if not entry.get("id"):
                entry["id"] = eid
            if not entry.get("name"):
                entry["name"] = "Unnamed"
            if entry.get("description") is None:
                entry["description"] = ""
            if not isinstance(entry.get("tags"), list):
                entry["tags"] = []
            if not entry.get("created_at"):
                entry["created_at"] = now
            if not entry.get("updated_at"):
                entry["updated_at"] = now

        for eid in to_delete:
            del db[cat][eid]

    return db


# ---------------------------------------------------------------------------
# Editor integration – world-bible-aware scanning
# ---------------------------------------------------------------------------

def scan_editor_for_world_bible_references(
    text: str,
    *,
    session_state: Any,
) -> List[Dict[str, Any]]:
    """Scan *text* for mentions of known world-bible entries.

    Checks character, location, and faction names (case-insensitive).
    Returns a list of dicts each containing ``category``, ``entry_id``,
    ``name``, and the matched ``entry``.
    """
    db = _resolve_db(session_state)
    if not text:
        return []

    text_lower = text.lower()
    refs: List[Dict[str, Any]] = []
    seen: set = set()

    for cat in ("characters", "locations", "factions"):
        bucket = db.get(cat, {})
        for eid, entry in bucket.items():
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            if name.lower() in text_lower and eid not in seen:
                refs.append({
                    "category": cat,
                    "entry_id": eid,
                    "name": name,
                    "entry": entry,
                })
                seen.add(eid)

    return refs


# ---------------------------------------------------------------------------
# Global canon conflict detection
# ---------------------------------------------------------------------------

def detect_canon_conflicts_global(
    *,
    session_state: Any,
) -> List[str]:
    """Detect conflicts across the entire world-bible database.

    Checks for:
    - duplicate names across categories
    - duplicate entries in the same category
    - entries missing descriptions
    - entries missing tags
    - conflicting rules (rules with identical names)

    Returns a list of human-readable conflict descriptions.
    """
    db = _resolve_db(session_state)
    conflicts: List[str] = []

    # Collect all names to find cross-category duplicates
    name_registry: Dict[str, List[Tuple[str, str, str]]] = {}  # lower_name -> [(cat, eid, name)]
    for cat, bucket in db.items():
        for eid, entry in bucket.items():
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            key = name.lower()
            name_registry.setdefault(key, []).append((cat, eid, name))

    # Duplicate names across or within categories
    for lower_name, occurrences in name_registry.items():
        if len(occurrences) > 1:
            locs = ", ".join(f"{cat}({eid})" for cat, eid, _name in occurrences)
            conflicts.append(
                f"Duplicate name '{occurrences[0][2]}' "
                f"found in: {locs}"
            )

    # Missing descriptions / tags
    for cat, bucket in db.items():
        for eid, entry in bucket.items():
            name = (entry.get("name") or "").strip() or eid
            if not (entry.get("description") or "").strip():
                conflicts.append(f"Entry '{name}' in {cat} is missing a description")
            tags = entry.get("tags")
            if not isinstance(tags, list) or len(tags) == 0:
                conflicts.append(f"Entry '{name}' in {cat} is missing tags")

    return conflicts


# ---------------------------------------------------------------------------
# Relationship graph data
# ---------------------------------------------------------------------------

def build_world_bible_relationships(
    *,
    session_state: Any,
) -> Dict[str, List[Dict[str, Any]]]:
    """Build a graph-like structure of world-bible relationships.

    Returns ``{"nodes": [...], "edges": [...]}``.

    Edges are created when:
    - entries share tags
    - entries reference each other by name in their description
    """
    db = _resolve_db(session_state)
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    edge_set: set = set()

    # Collect all entries as nodes
    all_entries: List[Tuple[str, str, Dict[str, Any]]] = []
    for cat, bucket in db.items():
        for eid, entry in bucket.items():
            nodes.append({
                "id": eid,
                "name": entry.get("name", ""),
                "category": cat,
            })
            all_entries.append((cat, eid, entry))

    # Tag-based edges
    tag_index: Dict[str, List[str]] = {}  # lower_tag -> [eid]
    for _cat, eid, entry in all_entries:
        for tag in (entry.get("tags") or []):
            tag_lower = (tag or "").strip().lower()
            if tag_lower:
                tag_index.setdefault(tag_lower, []).append(eid)

    for _tag, eids in tag_index.items():
        for i in range(len(eids)):
            for j in range(i + 1, len(eids)):
                pair = tuple(sorted((eids[i], eids[j])))
                if pair not in edge_set:
                    edge_set.add(pair)
                    edges.append({
                        "source": pair[0],
                        "target": pair[1],
                        "relation": "shared_tag",
                    })

    # Description-reference edges
    for _cat_a, eid_a, entry_a in all_entries:
        desc_a = (entry_a.get("description") or "").lower()
        if not desc_a:
            continue
        for _cat_b, eid_b, entry_b in all_entries:
            if eid_a == eid_b:
                continue
            name_b = (entry_b.get("name") or "").strip()
            if name_b and name_b.lower() in desc_a:
                pair = tuple(sorted((eid_a, eid_b)))
                if pair not in edge_set:
                    edge_set.add(pair)
                    edges.append({
                        "source": eid_a,
                        "target": eid_b,
                        "relation": "description_reference",
                    })

    return {"nodes": nodes, "edges": edges}


# ---------------------------------------------------------------------------
# Timeline validation
# ---------------------------------------------------------------------------

def validate_world_timeline(
    *,
    session_state: Any,
) -> List[str]:
    """Validate ``history`` entries that have an optional ``year`` field.

    Checks:
    - events are sorted correctly (chronologically)
    - no duplicate years
    - no missing year fields among history entries that use years

    Returns a list of human-readable warnings.
    """
    db = _resolve_db(session_state)
    history = db.get("history", {})
    if not history:
        return []

    warnings: List[str] = []
    entries_with_year: List[Tuple[str, str, int]] = []  # (eid, name, year)
    entries_without_year: List[Tuple[str, str]] = []

    for eid, entry in history.items():
        name = (entry.get("name") or "").strip() or eid
        year = entry.get("year")
        if year is not None:
            if not isinstance(year, int):
                warnings.append(f"History entry '{name}' has non-integer year: {year!r}")
                continue
            entries_with_year.append((eid, name, year))
        else:
            entries_without_year.append((eid, name))

    # Missing years
    for eid, name in entries_without_year:
        warnings.append(f"History entry '{name}' is missing a year field")

    # Duplicate years
    year_counts: Dict[int, List[str]] = {}
    for eid, name, year in entries_with_year:
        year_counts.setdefault(year, []).append(name)

    for year, names in year_counts.items():
        if len(names) > 1:
            warnings.append(
                f"Duplicate year {year} found in history entries: "
                + ", ".join(names)
            )

    # Check chronological ordering (compare insertion order vs sorted)
    original_years = [e[2] for e in entries_with_year]
    sorted_years = sorted(original_years)
    if original_years != sorted_years:
        warnings.append("History events are not in chronological order")

    return warnings


# ---------------------------------------------------------------------------
# Auto-save / persistence helpers
# ---------------------------------------------------------------------------

def _mark_saved(session_state: Any) -> None:
    """Mark that the world bible was recently modified."""
    session_state["world_bible_last_saved"] = True


def save_world_bible(*, session_state: Any) -> None:
    """Explicitly mark the world bible as saved (call after add/edit/delete)."""
    _mark_saved(session_state)


def _snapshot_version(session_state: Any, max_versions: int = 20) -> None:
    """Append a deep copy of the current world-bible DB to the version list."""
    db = session_state.get("world_bible_db")
    if db is None:
        return
    versions = session_state.setdefault("world_bible_versions", [])
    snapshot = {
        "timestamp": _now_iso(),
        "data": copy.deepcopy(db),
    }
    versions.append(snapshot)
    # Keep only the most recent snapshots
    if len(versions) > max_versions:
        session_state["world_bible_versions"] = versions[-max_versions:]
