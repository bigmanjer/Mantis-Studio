"""Deterministic canon intelligence for World Bible, Memory, and Insights.

This module is the offline, testable foundation for smarter canon behavior.
It turns chapter text into reviewable facts, events, relationships, memory
suggestions, and contradiction flags without mutating project state.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from app.services.projects import Entity, Project


ATTRIBUTE_ALIASES: Dict[str, str] = {
    "eye": "eyes",
    "eyes": "eyes",
    "hair": "hair",
    "age": "age",
    "home": "home",
    "hometown": "home",
    "origin": "origin",
    "species": "species",
    "rank": "rank",
    "title": "title",
    "weapon": "weapon",
}

RELATIONSHIP_VERBS: Dict[str, str] = {
    "hates": "enemy",
    "despises": "enemy",
    "fears": "fears",
    "loves": "loves",
    "trusts": "trusts",
    "betrays": "betrays",
    "protects": "protects",
    "serves": "serves",
    "follows": "follows",
    "leads": "leads",
}

CONFLICTING_RELATIONS: Dict[str, set[str]] = {
    "enemy": {"loves", "trusts", "protects"},
    "loves": {"enemy", "betrays"},
    "trusts": {"enemy", "betrays"},
    "protects": {"enemy", "betrays"},
    "betrays": {"trusts", "loves", "protects"},
}


@dataclass
class CanonEvidence:
    source_type: str
    source_id: str
    source_label: str
    quote: str


@dataclass
class CanonFact:
    subject: str
    attribute: str
    value: str
    confidence: float
    evidence: CanonEvidence

    def as_review_item(self) -> Dict[str, Any]:
        return {
            "kind": "canon_fact",
            "subject": self.subject,
            "attribute": self.attribute,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": asdict(self.evidence),
        }


@dataclass
class TimelineEvent:
    name: str
    summary: str
    order_hint: Optional[int]
    confidence: float
    evidence: CanonEvidence

    def as_review_item(self) -> Dict[str, Any]:
        return {
            "kind": "timeline_event",
            "name": self.name,
            "summary": self.summary,
            "order_hint": self.order_hint,
            "confidence": self.confidence,
            "evidence": asdict(self.evidence),
        }


@dataclass
class RelationshipSignal:
    source: str
    target: str
    relation: str
    confidence: float
    evidence: CanonEvidence

    def as_review_item(self) -> Dict[str, Any]:
        return {
            "kind": "relationship",
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
            "confidence": self.confidence,
            "evidence": asdict(self.evidence),
        }


@dataclass
class MemorySuggestion:
    tier: str
    text: str
    confidence: float
    evidence: CanonEvidence

    def as_review_item(self) -> Dict[str, Any]:
        return {
            "kind": "memory_suggestion",
            "tier": self.tier,
            "text": self.text,
            "confidence": self.confidence,
            "evidence": asdict(self.evidence),
        }


@dataclass
class CanonConflict:
    severity: str
    subject: str
    issue: str
    existing: str
    incoming: str
    evidence: CanonEvidence

    def as_review_item(self) -> Dict[str, Any]:
        return {
            "kind": "canon_conflict",
            "severity": self.severity,
            "subject": self.subject,
            "issue": self.issue,
            "existing": self.existing,
            "incoming": self.incoming,
            "evidence": asdict(self.evidence),
        }


@dataclass
class CanonIntelligenceReport:
    facts: List[CanonFact] = field(default_factory=list)
    events: List[TimelineEvent] = field(default_factory=list)
    relationships: List[RelationshipSignal] = field(default_factory=list)
    memory_suggestions: List[MemorySuggestion] = field(default_factory=list)
    conflicts: List[CanonConflict] = field(default_factory=list)

    @property
    def risk_score(self) -> int:
        score = 0
        for conflict in self.conflicts:
            score += 35 if conflict.severity == "high" else 18
        score += min(20, len(self.relationships) * 2)
        return min(100, score)

    def review_items(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for collection in (
            self.conflicts,
            self.facts,
            self.events,
            self.relationships,
            self.memory_suggestions,
        ):
            items.extend(item.as_review_item() for item in collection)
        return items


def analyze_chapter_canon(
    project: Project,
    chapter_text: str,
    *,
    chapter_id: str = "",
    chapter_title: str = "Current chapter",
) -> CanonIntelligenceReport:
    """Analyze chapter text against project canon without mutating state."""
    sentences = _split_sentences(chapter_text)
    report = CanonIntelligenceReport()

    for sentence in sentences:
        evidence = CanonEvidence(
            source_type="chapter",
            source_id=chapter_id,
            source_label=chapter_title,
            quote=sentence,
        )
        facts = _extract_facts(sentence, evidence)
        relationships = _extract_relationships(sentence, evidence)
        events = _extract_events(sentence, evidence)

        report.facts.extend(facts)
        report.relationships.extend(relationships)
        report.events.extend(events)

    report.conflicts.extend(_detect_fact_conflicts(project, report.facts))
    report.conflicts.extend(_detect_relationship_conflicts(project, report.relationships))
    report.memory_suggestions.extend(_build_memory_suggestions(report))
    return report


def build_context_packet(
    project: Project,
    chapter_text: str,
    *,
    max_entities: int = 8,
) -> Dict[str, Any]:
    """Return relevant canon context for AI prompts or Insights."""
    text_lower = chapter_text.lower()
    matched: List[Entity] = []
    for entity in project.world_db.values():
        names = [entity.name] + list(entity.aliases or [])
        if any(_contains_name(text_lower, name) for name in names if name):
            matched.append(entity)
    if not matched:
        matched = list(project.world_db.values())[:max_entities]

    return {
        "project_id": project.id,
        "hard_canon": project.memory_hard or project.memory,
        "soft_guidelines": project.memory_soft,
        "entities": [
            {
                "id": entity.id,
                "name": entity.name,
                "category": entity.category,
                "description": entity.description,
                "aliases": list(entity.aliases or []),
            }
            for entity in matched[:max_entities]
        ],
    }


def _split_sentences(text: str) -> List[str]:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return []
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", cleaned)
        if part.strip()
    ]


def _extract_facts(sentence: str, evidence: CanonEvidence) -> List[CanonFact]:
    facts: List[CanonFact] = []
    patterns = [
        re.compile(
            r"\b(?P<subject>[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)"
            r"(?:'s| has| have) (?P<attribute>eyes?|hair|age|home|hometown|origin|species|rank|title|weapon)"
            r"(?: is| are|:)? (?P<value>[A-Za-z][A-Za-z0-9 '-]{1,40})",
        ),
        re.compile(
            r"\b(?P<subject>[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*) is "
            r"(?P<value>[A-Za-z][A-Za-z0-9 '-]{1,40})"
            r" (?P<attribute>years old|old|dead|alive)",
        ),
    ]
    for pattern in patterns:
        for match in pattern.finditer(sentence):
            raw_attr = match.group("attribute").lower().strip()
            attr = "status" if raw_attr in {"dead", "alive"} else ATTRIBUTE_ALIASES.get(raw_attr, raw_attr)
            value = _clean_value(match.group("value"))
            if raw_attr in {"dead", "alive"}:
                value = raw_attr
            if raw_attr == "years old":
                attr = "age"
            if value:
                facts.append(
                    CanonFact(
                        subject=match.group("subject").strip(),
                        attribute=attr,
                        value=value,
                        confidence=0.78,
                        evidence=evidence,
                    )
                )
    return _dedupe_facts(facts)


def _extract_relationships(sentence: str, evidence: CanonEvidence) -> List[RelationshipSignal]:
    relationships: List[RelationshipSignal] = []
    verb_pattern = "|".join(re.escape(v) for v in RELATIONSHIP_VERBS)
    pattern = re.compile(
        r"\b(?P<source>[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*) "
        rf"(?P<verb>{verb_pattern}) "
        r"(?P<target>[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\b"
    )
    for match in pattern.finditer(sentence):
        relationships.append(
            RelationshipSignal(
                source=match.group("source").strip(),
                target=match.group("target").strip(),
                relation=RELATIONSHIP_VERBS[match.group("verb").lower()],
                confidence=0.74,
                evidence=evidence,
            )
        )
    return relationships


def _extract_events(sentence: str, evidence: CanonEvidence) -> List[TimelineEvent]:
    lowered = sentence.lower()
    if not any(token in lowered for token in ("battle", "death", "coronation", "arrival", "war", "betrayal")):
        return []
    order_hint = None
    year_match = re.search(r"\b(?:year|yr)\s*(?P<year>-?\d{1,5})\b", lowered)
    if year_match:
        order_hint = int(year_match.group("year"))
    name = _clean_value(sentence[:60]) or "Timeline event"
    return [
        TimelineEvent(
            name=name,
            summary=sentence,
            order_hint=order_hint,
            confidence=0.66,
            evidence=evidence,
        )
    ]


def _detect_fact_conflicts(project: Project, facts: Iterable[CanonFact]) -> List[CanonConflict]:
    conflicts: List[CanonConflict] = []
    for fact in facts:
        entity = project.find_entity_match(fact.subject, "Character")
        if entity is None:
            entity = project.find_entity_match(fact.subject, "")
        if entity is None:
            continue
        existing_value = _find_existing_attribute(entity.description, fact.attribute)
        if existing_value and _normalize_value(existing_value) != _normalize_value(fact.value):
            conflicts.append(
                CanonConflict(
                    severity="high",
                    subject=entity.name,
                    issue=f"Conflicting {fact.attribute}",
                    existing=existing_value,
                    incoming=fact.value,
                    evidence=fact.evidence,
                )
            )
    return conflicts


def _detect_relationship_conflicts(
    project: Project,
    relationships: Iterable[RelationshipSignal],
) -> List[CanonConflict]:
    conflicts: List[CanonConflict] = []
    for rel in relationships:
        source = project.find_entity_match(rel.source, "Character")
        target = project.find_entity_match(rel.target, "Character")
        if source is None or target is None:
            continue
        existing_text = f"{source.description}\n{target.description}".lower()
        for relation, conflicting in CONFLICTING_RELATIONS.items():
            if rel.relation in conflicting and _mentions_relation(existing_text, source.name, target.name, relation):
                conflicts.append(
                    CanonConflict(
                        severity="medium",
                        subject=f"{source.name} / {target.name}",
                        issue="Relationship drift",
                        existing=relation,
                        incoming=rel.relation,
                        evidence=rel.evidence,
                    )
                )
    return conflicts


def _build_memory_suggestions(report: CanonIntelligenceReport) -> List[MemorySuggestion]:
    suggestions: List[MemorySuggestion] = []
    for fact in report.facts:
        tier = "hard" if fact.confidence >= 0.8 else "soft"
        suggestions.append(
            MemorySuggestion(
                tier=tier,
                text=f"{fact.subject}: {fact.attribute} = {fact.value}",
                confidence=fact.confidence,
                evidence=fact.evidence,
            )
        )
    for rel in report.relationships:
        suggestions.append(
            MemorySuggestion(
                tier="soft",
                text=f"{rel.source} {rel.relation} {rel.target}",
                confidence=rel.confidence,
                evidence=rel.evidence,
            )
        )
    return suggestions


def _find_existing_attribute(description: str, attribute: str) -> str:
    if not description:
        return ""
    attr = re.escape(attribute.lower())
    patterns = [
        re.compile(rf"\b{attr}\s*[:=]\s*(?P<value>[A-Za-z0-9 '-]+)", re.IGNORECASE),
        re.compile(rf"\b{attr}\s+(?:is|are)\s+(?P<value>[A-Za-z0-9 '-]+)", re.IGNORECASE),
    ]
    for pattern in patterns:
        match = pattern.search(description)
        if match:
            return _clean_value(match.group("value"))
    return ""


def _mentions_relation(text: str, source: str, target: str, relation: str) -> bool:
    del source
    return relation.lower() in text and target.lower() in text


def _contains_name(text_lower: str, name: str) -> bool:
    needle = re.escape(name.strip().lower())
    return bool(re.search(rf"\b{needle}\b", text_lower))


def _clean_value(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"[.,;:!?]+$", "", value).strip()
    return value


def _normalize_value(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _dedupe_facts(facts: List[CanonFact]) -> List[CanonFact]:
    seen: set[tuple[str, str, str]] = set()
    deduped: List[CanonFact] = []
    for fact in facts:
        key = (
            _normalize_value(fact.subject),
            fact.attribute,
            _normalize_value(fact.value),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(fact)
    return deduped

