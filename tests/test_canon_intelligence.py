from __future__ import annotations

from app.services.canon_intelligence import analyze_chapter_canon, build_context_packet
from app.services.projects import Entity, Project


def _project() -> Project:
    project = Project.create("Canon Test")
    project.world_db["aria"] = Entity(
        id="aria",
        name="Aria",
        category="Character",
        description="eyes: green\nAria trusts Marcus.",
        aliases=["Princess Aria"],
    )
    project.world_db["marcus"] = Entity(
        id="marcus",
        name="Marcus",
        category="Character",
        description="Marcus protects Aria.",
    )
    project.world_db["ironforge"] = Entity(
        id="ironforge",
        name="Ironforge",
        category="Location",
        description="A mountain city.",
    )
    project.memory_hard = "Aria's eyes are green."
    project.memory_soft = "Keep political betrayals tense."
    return project


def test_analyze_chapter_detects_attribute_conflict_with_evidence():
    project = _project()
    report = analyze_chapter_canon(
        project,
        "Aria's eyes are blue. Marcus betrays Aria during the coronation in year 12.",
        chapter_id="ch1",
        chapter_title="Chapter 1",
    )

    assert any(f.subject == "Aria" and f.attribute == "eyes" and f.value == "blue" for f in report.facts)
    conflict = next(c for c in report.conflicts if c.issue == "Conflicting eyes")
    assert conflict.subject == "Aria"
    assert conflict.existing == "green"
    assert conflict.incoming == "blue"
    assert conflict.evidence.source_label == "Chapter 1"
    assert "Aria's eyes are blue" in conflict.evidence.quote


def test_analyze_chapter_extracts_relationships_events_and_memory_suggestions():
    project = _project()
    report = analyze_chapter_canon(
        project,
        "Marcus betrays Aria during the coronation in year 12.",
        chapter_id="ch2",
        chapter_title="Chapter 2",
    )

    assert any(r.source == "Marcus" and r.target == "Aria" and r.relation == "betrays" for r in report.relationships)
    assert any(event.order_hint == 12 and "coronation" in event.summary.lower() for event in report.events)
    assert any("Marcus betrays Aria" in item.text for item in report.memory_suggestions)
    assert report.review_items()


def test_context_packet_retrieves_relevant_entities():
    project = _project()
    packet = build_context_packet(project, "Aria returns to Ironforge.")

    names = {entity["name"] for entity in packet["entities"]}
    assert {"Aria", "Ironforge"}.issubset(names)
    assert packet["hard_canon"] == "Aria's eyes are green."
    assert packet["soft_guidelines"] == "Keep political betrayals tense."

