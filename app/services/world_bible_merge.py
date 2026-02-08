"""Intelligent merge engine for World Bible AI suggestions.

Decides whether a suggestion should update an existing entity, add aliases,
expand a description, or create a new entry.  Uses semantic similarity
(``difflib.SequenceMatcher``) — no external ML dependencies required.

Decision flow
-------------
1. Normalize the incoming suggestion (name, category, aliases).
2. Search the project's ``world_db`` for a matching entity using
   ``Project.find_entity_match`` (fuzzy name + alias matching).
3. Compute a *similarity score* between the existing and incoming
   descriptions to decide whether the new text is truly additive.
4. Classify the suggestion as one of:
   - ``"update"``      – merge description + aliases into an existing entry
   - ``"alias_only"``  – only attach new aliases, description is redundant
   - ``"new"``         – create a brand-new entity
5. Attach a *confidence* rating and a human-readable *reason* string so the
   review UI can explain what will happen.

All helpers are pure functions that operate on ``Project`` / ``Entity``
objects and never touch Streamlit session state.
"""
from __future__ import annotations

import difflib
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.projects import Entity, Project


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HIGH_CONFIDENCE_THRESHOLD = 0.80   # auto-classify as update
DESCRIPTION_OVERLAP_THRESHOLD = 0.85  # descriptions are "same enough"


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

def _bullet_points(text: str) -> List[str]:
    """Split a description into individual bullet points / sentences."""
    if not text:
        return []
    lines = text.strip().splitlines()
    points: List[str] = []
    for line in lines:
        cleaned = re.sub(r"^[-•*]\s*", "", line).strip()
        if not cleaned:
            continue
        # If the line looks like a single bullet / short phrase, keep it whole
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", cleaned) if s.strip()]
        if len(sentences) > 1:
            points.extend(sentences)
        elif cleaned:
            points.append(cleaned)
    if not points:
        # Fall back to sentence splitting
        points = [s.strip() for s in re.split(r"[.!?\n]", text) if s.strip()]
    return points


def _normalize_bullet(text: str) -> str:
    """Lower-case, collapse whitespace, strip punctuation for comparison."""
    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()


def _description_similarity(existing: str, incoming: str) -> float:
    """Semantic similarity between two descriptions (0.0 – 1.0)."""
    if not existing or not incoming:
        return 0.0
    return difflib.SequenceMatcher(
        None,
        _normalize_bullet(existing),
        _normalize_bullet(incoming),
    ).ratio()


def _novel_bullets(existing_desc: str, incoming_desc: str) -> List[str]:
    """Return bullet-point strings from *incoming* that are not already
    covered by *existing* (using fuzzy matching)."""
    existing_bullets = _bullet_points(existing_desc)
    incoming_bullets = _bullet_points(incoming_desc)

    existing_normalized = {_normalize_bullet(b) for b in existing_bullets}

    novel: List[str] = []
    for bullet in incoming_bullets:
        norm = _normalize_bullet(bullet)
        if not norm:
            continue
        # Check for exact or near-duplicate
        is_dup = False
        for en in existing_normalized:
            if en == norm:
                is_dup = True
                break
            if difflib.SequenceMatcher(None, en, norm).ratio() >= DESCRIPTION_OVERLAP_THRESHOLD:
                is_dup = True
                break
        if not is_dup:
            novel.append(bullet)
    return novel


def _normalize_alias(alias: str) -> str:
    """Normalize an alias for dedup comparison."""
    return Project._normalize_entity_name(alias)


def _novel_aliases(
    entity: Entity,
    incoming_aliases: List[str],
    primary_name: str,
) -> List[str]:
    """Return aliases from *incoming* that are truly new."""
    existing_normalized = {_normalize_alias(entity.name)}
    for a in entity.aliases:
        existing_normalized.add(_normalize_alias(a))
    primary_norm = _normalize_alias(primary_name)

    novel: List[str] = []
    seen: set = set()
    for alias in incoming_aliases:
        clean = (alias or "").strip()
        if not clean:
            continue
        norm = _normalize_alias(clean)
        if not norm or norm in existing_normalized or norm == primary_norm or norm in seen:
            continue
        novel.append(clean)
        seen.add(norm)
    return novel


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_suggestion(
    project: Project,
    suggestion: Dict[str, Any],
) -> Dict[str, Any]:
    """Classify an incoming AI suggestion and enrich it with merge metadata.

    Returns a *new* dict (does not mutate the input) with these extra keys:

    - ``type``       — ``"update"`` | ``"alias_only"`` | ``"new"`` | ``"duplicate"``
    - ``entity_id``  — the matched entity's id (if any)
    - ``match_name`` — the matched entity's canonical name (if any)
    - ``reason``     — human-readable explanation
    - ``novel_bullets``  — list of genuinely new description bullet points
    - ``novel_aliases``  — list of genuinely new aliases
    - ``confidence``     — a float 0–1
    """
    name = (suggestion.get("name") or "").strip()
    category = (suggestion.get("category") or "").strip()
    description = (suggestion.get("description") or "").strip()
    aliases = suggestion.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = [str(aliases)]
    raw_confidence = suggestion.get("confidence")
    try:
        confidence = float(raw_confidence) if raw_confidence is not None else 0.0
    except (TypeError, ValueError):
        confidence = 0.0

    result = dict(suggestion)  # shallow copy
    result["name"] = name
    result["category"] = Project._normalize_category(category)
    result["aliases"] = aliases
    result["confidence"] = confidence

    if not name:
        result["type"] = "new"
        result["reason"] = "No name provided — manual review required."
        result["novel_bullets"] = _bullet_points(description)
        result["novel_aliases"] = aliases
        return result

    # --- Try to find an existing match ---
    match = project.find_entity_match(name, category, aliases=aliases)

    if match is None:
        result["type"] = "new"
        result["entity_id"] = None
        result["match_name"] = None
        result["reason"] = f"No existing entry matches '{name}'. Will create new {result['category']}."
        result["novel_bullets"] = _bullet_points(description)
        result["novel_aliases"] = aliases
        return result

    # --- Existing match found — decide update vs alias-only ---
    result["entity_id"] = match.id
    result["match_name"] = match.name

    novel_b = _novel_bullets(match.description, description)
    novel_a = _novel_aliases(match, aliases, match.name)

    result["novel_bullets"] = novel_b
    result["novel_aliases"] = novel_a

    if novel_b:
        result["type"] = "update"
        parts = [f"Matches existing entry '{match.name}'."]
        parts.append(f"{len(novel_b)} new detail(s) to add.")
        if novel_a:
            parts.append(f"{len(novel_a)} new alias(es).")
        result["reason"] = " ".join(parts)
    elif novel_a:
        result["type"] = "alias_only"
        result["reason"] = (
            f"Matches existing entry '{match.name}'. "
            f"Description is already covered. {len(novel_a)} new alias(es) to add."
        )
    else:
        # Everything is already present — this is a duplicate
        result["type"] = "duplicate"
        result["reason"] = (
            f"Matches existing entry '{match.name}'. "
            "All information is already present — nothing to add."
        )

    # Boost confidence when match is strong
    name_sim = difflib.SequenceMatcher(
        None,
        Project._normalize_entity_name(name),
        Project._normalize_entity_name(match.name),
    ).ratio()
    if name_sim >= 0.95:
        result["confidence"] = max(confidence, 0.90)
    elif name_sim >= 0.80:
        result["confidence"] = max(confidence, 0.75)

    return result


# ---------------------------------------------------------------------------
# Apply helpers
# ---------------------------------------------------------------------------

def merge_description_bullets(entity: Entity, novel_bullets: List[str]) -> None:
    """Append *novel_bullets* to the entity's description as bullet points.

    Existing user-written content is never removed or overwritten.
    """
    if not novel_bullets:
        return

    desc = (entity.description or "").strip()

    # Convert existing plain text to bullet format if needed
    if desc and not desc.startswith("-") and not desc.startswith("•"):
        desc = f"- {desc}"

    for bullet in novel_bullets:
        clean = bullet.strip()
        if not clean:
            continue
        if desc:
            desc += f"\n- {clean}"
        else:
            desc = f"- {clean}"

    entity.description = desc


def apply_suggestion(project: Project, classified: Dict[str, Any]) -> Tuple[Optional[Entity], str]:
    """Apply a classified suggestion to the project.

    Returns ``(entity, action)`` where *action* is one of:
    ``"updated"``, ``"alias_added"``, ``"created"``, ``"duplicate"``, ``"skipped"``.
    """
    stype = classified.get("type", "new")

    if stype == "duplicate":
        eid = classified.get("entity_id")
        ent = project.world_db.get(eid) if eid else None
        return ent, "duplicate"

    if stype in ("update", "alias_only"):
        eid = classified.get("entity_id")
        if not eid:
            # Fallback: try to find the entity by name/category
            match = project.find_entity_match(
                classified.get("name", ""),
                classified.get("category", ""),
                aliases=classified.get("aliases") or [],
            )
            if match:
                eid = match.id
            else:
                return _create_new(project, classified)

        ent = project.world_db.get(eid)
        if not ent:
            return _create_new(project, classified)

        # Compute novel bullets/aliases on the fly when not pre-classified
        novel_bullets = classified.get("novel_bullets")
        if novel_bullets is None:
            incoming_desc = (classified.get("description") or "").strip()
            novel_bullets = _novel_bullets(ent.description, incoming_desc) if incoming_desc else []

        novel_aliases_list = classified.get("novel_aliases")
        if novel_aliases_list is None:
            incoming_aliases = classified.get("aliases") or []
            novel_aliases_list = _novel_aliases(ent, incoming_aliases, ent.name) if incoming_aliases else []

        raw_desc = (classified.get("description") or "").strip()

        # Merge novel description bullets
        if novel_bullets:
            merge_description_bullets(ent, novel_bullets)
        elif raw_desc:
            # Even when pre-classified as "alias_only", merge the raw
            # description so that user-visible "Suggested Notes" are applied.
            # Entity.merge() handles its own dedup to avoid duplicates.
            ent.merge(raw_desc)

        # Merge novel aliases
        if novel_aliases_list:
            Project._merge_aliases(ent, novel_aliases_list, ent.name)

        action = "updated" if novel_bullets or raw_desc else "alias_added"
        return ent, action

    # type == "new"
    return _create_new(project, classified)


def _create_new(project: Project, classified: Dict[str, Any]) -> Tuple[Optional[Entity], str]:
    """Create a new entity from a classified suggestion, using upsert to
    leverage built-in fuzzy dedup one more time."""
    ent, status = project.upsert_entity(
        classified.get("name", ""),
        classified.get("category", "Lore"),
        classified.get("description", ""),
        aliases=classified.get("aliases") or [],
        allow_merge=True,
        allow_alias=True,
    )
    return ent, status  # "created" or "matched"
