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
    "role": "role",
    "occupation": "role",
    "location": "location",
    "place": "location",
    "goal": "goal",
    "knowledge": "knowledge",
    "appearance": "appearance",
    "item": "item",
    "emotion": "emotional_state",
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
    "meets": "meets",
    "helps": "helps",
    "attacks": "attacks",
    "warns": "warns",
    "confronts": "confronts",
    "chases": "chases",
    "pursues": "pursues",
    "searches for": "searches_for",
    "looks for": "searches_for",
}

TRANSIENT_BODY_ACTIONS: set[str] = {
    "blinked",
    "closed",
    "darted",
    "fluttered",
    "fluttered open",
    "narrowed",
    "opened",
    "shifted",
    "widened",
}

EVENT_TRIGGERS: set[str] = {
    "arrived",
    "asked",
    "attacked",
    "battle",
    "began",
    "betrayal",
    "betrayed",
    "chased",
    "collapsed",
    "confronted",
    "coronation",
    "death",
    "decided",
    "destroyed",
    "discovered",
    "entered",
    "escaped",
    "fell",
    "fled",
    "found",
    "heard",
    "hid",
    "killed",
    "left",
    "learned",
    "met",
    "opened",
    "pursued",
    "realized",
    "reached",
    "revealed",
    "saw",
    "searched",
    "stumbled",
    "took",
    "turned",
    "war",
    "warned",
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
    entity_names = _known_entity_names(project)

    for sentence in sentences:
        evidence = CanonEvidence(
            source_type="chapter",
            source_id=chapter_id,
            source_label=chapter_title,
            quote=sentence,
        )
        facts = _extract_facts(sentence, evidence, entity_names=entity_names)
        relationships = _extract_relationships(sentence, evidence, entity_names=entity_names)
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


def _extract_facts(
    sentence: str,
    evidence: CanonEvidence,
    *,
    entity_names: Optional[List[str]] = None,
) -> List[CanonFact]:
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
            _append_fact(
                facts,
                subject=match.group("subject").strip(),
                attribute=attr,
                value=value,
                confidence=0.78,
                evidence=evidence,
            )

    subject_pattern = _subject_pattern(entity_names)
    sentence_patterns = [
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern}),\s+(?:a|an|the)\s+"
                r"(?P<value>[A-Za-z][A-Za-z0-9 '\-]{2,80}?)(?:,|\.|;| who\b| with\b| and\b)",
                re.IGNORECASE,
            ),
            "role",
            0.72,
        ),
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern})\s+(?:is|was|remains|became|becomes)\s+"
                r"(?P<value>(?:a|an|the)?\s*[A-Za-z][A-Za-z0-9 '\-]{2,80}?)(?:,|\.|;| who\b| with\b| and\b)",
                re.IGNORECASE,
            ),
            "role",
            0.7,
        ),
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern})\s+(?:carried|carries|held|holds|gripped|grips|wielded|wields)\s+"
                r"(?P<value>(?:a|an|the)?\s*[A-Za-z][A-Za-z0-9 '\-]{2,60}?)(?:,|\.|;| as\b| while\b| and\b)",
                re.IGNORECASE,
            ),
            "item",
            0.68,
        ),
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern})(?:,\s+[^,.;!?]{{2,80}},)?\s+"
                r"(?:entered|reached|arrived at|arrived in|returned to|went to|moved through|stood in|hid in|slipped inside)\s+"
                r"(?P<value>(?:the\s+)?[A-Z][A-Za-z0-9 '\-]{1,60}|(?:the|a|an)\s+[a-z][A-Za-z0-9 '\-]{2,60})(?:,|\.|;| as\b| while\b| and\b)",
                re.IGNORECASE,
            ),
            "location",
            0.68,
        ),
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern})\s+(?:knew|realized|remembered|learned|discovered|suspected|noticed)\s+"
                r"(?P<value>that\s+)?(?P<detail>[A-Za-z0-9][^.;!?]{8,120})",
                re.IGNORECASE,
            ),
            "knowledge",
            0.62,
        ),
        (
            re.compile(
                rf"\b(?P<subject>{subject_pattern})\s+(?:felt|looked|seemed|appeared)\s+"
                r"(?P<value>[A-Za-z][A-Za-z0-9 '\-]{2,50}?)(?:,|\.|;| as\b| while\b| and\b)",
                re.IGNORECASE,
            ),
            "emotional_state",
            0.58,
        ),
    ]
    for pattern, attribute, confidence in sentence_patterns:
        for match in pattern.finditer(sentence):
            value = match.groupdict().get("detail") or match.groupdict().get("value") or ""
            _append_fact(
                facts,
                subject=match.group("subject").strip(),
                attribute=attribute,
                value=_clean_value(value),
                confidence=confidence,
                evidence=evidence,
            )
    return _dedupe_facts(facts)


def _extract_relationships(
    sentence: str,
    evidence: CanonEvidence,
    *,
    entity_names: Optional[List[str]] = None,
) -> List[RelationshipSignal]:
    relationships: List[RelationshipSignal] = []
    verb_pattern = "|".join(re.escape(v) for v in RELATIONSHIP_VERBS)
    subject_pattern = _subject_pattern(entity_names)
    pattern = re.compile(
        rf"\b(?P<source>{subject_pattern}) "
        rf"(?P<verb>{verb_pattern}) "
        rf"(?P<target>{subject_pattern})\b",
        re.IGNORECASE,
    )
    for match in pattern.finditer(sentence):
        source = _canonical_name(match.group("source"), entity_names)
        target = _canonical_name(match.group("target"), entity_names)
        if not source or not target or source == target:
            continue
        relationships.append(
            RelationshipSignal(
                source=source,
                target=target,
                relation=RELATIONSHIP_VERBS[match.group("verb").lower()],
                confidence=0.74,
                evidence=evidence,
            )
        )
    interaction_patterns = [
        (r"with", "with"),
        (r"against", "opposes"),
        (r"from", "separated_from"),
        (r"toward|towards", "approaches"),
    ]
    for prep, relation in interaction_patterns:
        interaction = re.compile(
            rf"\b(?P<source>{subject_pattern})\b[^.!?]{{0,80}}\b(?:{prep})\s+(?:the\s+)?(?P<target>{subject_pattern})\b",
            re.IGNORECASE,
        )
        for match in interaction.finditer(sentence):
            source = _canonical_name(match.group("source"), entity_names)
            target = _canonical_name(match.group("target"), entity_names)
            if not source or not target or source == target:
                continue
            relationships.append(
                RelationshipSignal(
                    source=source,
                    target=target,
                    relation=relation,
                    confidence=0.56,
                    evidence=evidence,
                )
            )
    return relationships


def _extract_events(sentence: str, evidence: CanonEvidence) -> List[TimelineEvent]:
    lowered = sentence.lower()
    if not any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in EVENT_TRIGGERS):
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


def _known_entity_names(project: Project) -> List[str]:
    names: List[str] = []
    for entity in project.world_db.values():
        names.append(entity.name)
        names.extend(entity.aliases or [])
    cleaned = [_clean_value(name) for name in names if _clean_value(name)]
    return sorted(set(cleaned), key=len, reverse=True)


def _subject_pattern(entity_names: Optional[List[str]] = None) -> str:
    names = [name for name in (entity_names or []) if name]
    if names:
        return "|".join(re.escape(name) for name in names)
    return r"[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*"


def _canonical_name(raw_name: str, entity_names: Optional[List[str]] = None) -> str:
    name = _clean_value(raw_name)
    if not name or _normalize_value(name) in {"he", "she", "they", "it", "his", "her", "their"}:
        return ""
    for candidate in entity_names or []:
        if _normalize_value(candidate) == _normalize_value(name):
            return candidate
    return name


def _append_fact(
    facts: List[CanonFact],
    *,
    subject: str,
    attribute: str,
    value: str,
    confidence: float,
    evidence: CanonEvidence,
) -> None:
    clean_subject = _canonical_name(subject)
    clean_value = _clean_value(value)
    if not clean_subject or not clean_value:
        return
    if attribute == "location":
        clean_value = _clean_location_value(clean_value)
    elif attribute in {"item", "weapon"}:
        clean_value = re.sub(r"^(?:a|an|the)\s+", "", clean_value, flags=re.IGNORECASE)
    if _is_transient_fact(attribute, clean_value):
        return
    if len(clean_value.split()) > 14:
        clean_value = " ".join(clean_value.split()[:14])
    facts.append(
        CanonFact(
            subject=clean_subject,
            attribute=ATTRIBUTE_ALIASES.get(attribute, attribute),
            value=clean_value,
            confidence=confidence,
            evidence=evidence,
        )
    )


def _is_transient_fact(attribute: str, value: str) -> bool:
    normalized = _normalize_value(value)
    if attribute in {"eyes", "hair"} and normalized in {_normalize_value(action) for action in TRANSIENT_BODY_ACTIONS}:
        return True
    if attribute in {"eyes", "hair"} and any(
        normalized.startswith(_normalize_value(action)) for action in TRANSIENT_BODY_ACTIONS
    ):
        return True
    return False


def _clean_location_value(value: str) -> str:
    value = _clean_value(value)
    value = re.split(
        r"\b(?:with|without|on|under|before|after|while|as|because|when)\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return re.sub(r"^(?:a|an|the)\s+", "", _clean_value(value), flags=re.IGNORECASE)


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
