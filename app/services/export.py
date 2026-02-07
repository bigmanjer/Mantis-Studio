"""Export functionality for Mantis Studio.

Note: This module is part of the new app/ structure.
      Current implementation still uses mantis.core.models for backward compatibility.
      These imports will be updated when the migration is complete.
"""
from __future__ import annotations

from app.services.projects import Project


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
