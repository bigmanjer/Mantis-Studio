from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

import streamlit as st


def _entity_aliases(entity: Any) -> List[str]:
    aliases = [entity.name] + list(entity.aliases or [])
    return [a.strip() for a in aliases if (a or "").strip()]


def _mention_count(aliases: List[str], text: str) -> int:
    hits = 0
    source = (text or "").lower()
    for alias in aliases:
        pattern = rf"\b{re.escape(alias.lower())}\b"
        hits += len(re.findall(pattern, source))
    return hits


def _parse_links(tags: str) -> List[Tuple[str, str]]:
    links: List[Tuple[str, str]] = []
    for token in re.findall(r"\[link:([^\]|]+)\|([^\]]+)\]", tags or ""):
        target_id, rel_type = token
        links.append((target_id.strip(), rel_type.strip()))
    return links


def _upsert_link_tags(tags: str, target_id: str, rel_type: str) -> str:
    current = _parse_links(tags)
    filtered = [(tid, rtype) for tid, rtype in current if tid != target_id]
    filtered.append((target_id, rel_type))
    clean = re.sub(r"\s*\[link:[^\]]+\]\s*", " ", tags or "").strip()
    encoded = " ".join(f"[link:{tid}|{rtype}]" for tid, rtype in filtered)
    merged = " ".join(x for x in [clean, encoded] if x).strip()
    return re.sub(r"\s{2,}", " ", merged)


def _remove_link_tags(tags: str, target_id: str) -> str:
    current = _parse_links(tags)
    filtered = [(tid, rtype) for tid, rtype in current if tid != target_id]
    clean = re.sub(r"\s*\[link:[^\]]+\]\s*", " ", tags or "").strip()
    encoded = " ".join(f"[link:{tid}|{rtype}]" for tid, rtype in filtered)
    merged = " ".join(x for x in [clean, encoded] if x).strip()
    return re.sub(r"\s{2,}", " ", merged)


def render_world_relationships(
    *,
    project: Any,
    entries: List[Any],
    chapters: List[Any],
    mention_refs: Dict[str, List[Any]],
    mention_counts: Dict[str, int],
) -> None:
    if not entries:
        return

    with st.container(border=True):
        st.markdown("### Relationship graph")
        st.caption("Entity links are inferred from chapter co-occurrence and mention density.")

        pair_weights: Dict[Tuple[str, str], int] = defaultdict(int)
        entity_by_id = {e.id: e for e in entries}
        chapter_link_map: Dict[Tuple[str, str], List[int]] = defaultdict(list)

        chapter_mentions: Dict[str, List[str]] = defaultdict(list)
        for chapter in chapters:
            text = (chapter.content or "")
            for entity in entries:
                aliases = _entity_aliases(entity)
                if _mention_count(aliases, text) > 0:
                    chapter_mentions[chapter.id].append(entity.id)

        for chapter in chapters:
            ids = sorted(set(chapter_mentions.get(chapter.id, [])))
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    pair = (ids[i], ids[j])
                    pair_weights[pair] += 1
                    chapter_link_map[pair].append(chapter.index)

        # Manual link editor
        with st.expander("Manual relationship links", expanded=False):
            source_options = {f"{e.name} ({e.category})": e.id for e in entries}
            if source_options:
                col_a, col_b, col_c = st.columns([1.2, 1.2, 1.0])
                with col_a:
                    source_label = st.selectbox(
                        "Source entity",
                        list(source_options.keys()),
                        key="world_rel_source",
                    )
                source_id = source_options[source_label]
                source_entity = entity_by_id.get(source_id)
                target_options = {
                    f"{e.name} ({e.category})": e.id for e in entries if e.id != source_id
                }
                with col_b:
                    if target_options:
                        target_label = st.selectbox(
                            "Target entity",
                            list(target_options.keys()),
                            key="world_rel_target",
                        )
                        target_id = target_options[target_label]
                    else:
                        target_id = None
                        st.caption("Add another entity to define a relationship.")
                with col_c:
                    rel_type = st.selectbox(
                        "Relation",
                        ["ally", "rival", "family", "mentor", "mystery", "conflict"],
                        key="world_rel_type",
                    )
                b1, b2 = st.columns(2)
                with b1:
                    if st.button(
                        "Save link",
                        use_container_width=True,
                        key="world_rel_save",
                        disabled=target_id is None,
                    ):
                        if source_entity and target_id:
                            source_entity.tags = _upsert_link_tags(
                                source_entity.tags or "",
                                target_id,
                                rel_type,
                            )
                            project.save()
                            st.toast("Relationship link saved.")
                            st.rerun()
                with b2:
                    if st.button(
                        "Remove link",
                        use_container_width=True,
                        key="world_rel_remove",
                        disabled=target_id is None,
                    ):
                        if source_entity and target_id:
                            source_entity.tags = _remove_link_tags(
                                source_entity.tags or "",
                                target_id,
                            )
                            project.save()
                            st.toast("Relationship link removed.")
                            st.rerun()
            else:
                st.caption("No entities yet.")

            st.markdown("**Current manual links**")
            manual_rows = []
            for entity in entries:
                for target_id, rel_type in _parse_links(entity.tags or ""):
                    target = entity_by_id.get(target_id)
                    if not target:
                        continue
                    manual_rows.append(
                        {
                            "Source": entity.name,
                            "Relation": rel_type,
                            "Target": target.name,
                        }
                    )
            if manual_rows:
                st.dataframe(manual_rows, use_container_width=True, hide_index=True)
            else:
                st.caption("No manual links configured.")

        top_pairs = sorted(pair_weights.items(), key=lambda x: x[1], reverse=True)[:15]
        if top_pairs:
            rows = []
            for (left_id, right_id), strength in top_pairs:
                left = entity_by_id.get(left_id)
                right = entity_by_id.get(right_id)
                if not left or not right:
                    continue
                chapter_list = chapter_link_map.get((left_id, right_id), [])
                rows.append(
                    {
                        "Entity A": left.name,
                        "Entity B": right.name,
                        "Link strength": strength,
                        "Shared chapters": ", ".join(f"Ch {c}" for c in chapter_list[:6]),
                        "A mentions": mention_counts.get(left.id, 0),
                        "B mentions": mention_counts.get(right.id, 0),
                    }
                )
            if rows:
                st.dataframe(rows, hide_index=True, use_container_width=True)
        else:
            st.info("Add chapter text referencing multiple entities to build relationship links.")

    with st.container(border=True):
        st.markdown("### Conflict timeline")
        st.caption("Chronological canon-risk timeline from coherence checks and entity change pressure.")

        results = st.session_state.get("coherence_results", []) or []
        chapter_conflicts: Dict[int, List[str]] = defaultdict(list)
        for item in results:
            try:
                chap_idx = int(item.get("chapter_index"))
            except (TypeError, ValueError):
                continue
            issue = (item.get("issue") or "Canon inconsistency").strip()
            chapter_conflicts[chap_idx].append(issue)

        for entity in entries:
            refs = mention_refs.get(entity.id, [])
            if len(refs) >= 3 and len((entity.description or "").strip()) < 30:
                for ref in refs[:4]:
                    chapter_conflicts[ref.index].append(
                        f"{entity.name}: high reuse with low detail (expand description)"
                    )

        if not chapter_conflicts:
            st.success("No active canon conflicts detected. Timeline is stable.")
            return

        ordered = sorted(chapter_conflicts.items(), key=lambda x: x[0])
        severity_filter = st.selectbox(
            "Timeline filter",
            ["All", "Coherence only", "Entity pressure only"],
            key="world_conflict_timeline_filter",
        )
        for chapter_idx, issues in ordered:
            if severity_filter == "Coherence only":
                issues = [i for i in issues if "low detail" not in i.lower()]
            elif severity_filter == "Entity pressure only":
                issues = [i for i in issues if "low detail" in i.lower()]
            if not issues:
                continue
            with st.expander(f"Chapter {chapter_idx} · {len(issues)} conflict(s)"):
                for issue in issues[:8]:
                    st.markdown(f"- {issue}")
                if len(issues) > 8:
                    st.caption(f"+ {len(issues) - 8} more")
