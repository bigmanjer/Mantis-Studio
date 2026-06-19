from __future__ import annotations

import hashlib
import json
import re
import time
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


KB_VERSION = 1
DEFAULT_KB_DIRNAME = ".knowledge_base"
DEFAULT_CHUNK_CHARS = 1100
MAX_IMPORT_CHARS = 500_000
BUILTIN_KB_FILENAME = "MANTIS Literary Master Knowledge Base.md"
BUILTIN_KB_SOURCE_PATH = Path(__file__).resolve().parents[1] / "data" / "knowledge_base" / "mantis_literary_master_knowledge_base.md"


@dataclass
class KnowledgeChunk:
    id: str
    document_id: str
    title: str
    category: str
    tags: List[str]
    text: str
    source: str
    created_at: float


def _now() -> float:
    return time.time()


def normalize_whitespace(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text_from_docx(payload: bytes) -> str:
    """Extract paragraphs from a DOCX without external dependencies."""
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(BytesIO(payload)) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    paragraphs: List[str] = []
    for para in root.findall(".//w:p", ns):
        texts = [node.text or "" for node in para.findall(".//w:t", ns)]
        line = "".join(texts).strip()
        if line:
            paragraphs.append(line)
    return normalize_whitespace("\n".join(paragraphs))


def extract_text_from_upload(filename: str, payload: bytes) -> str:
    name = (filename or "").lower()
    if name.endswith(".docx"):
        return extract_text_from_docx(payload)
    if name.endswith(".txt") or name.endswith(".md"):
        return normalize_whitespace(payload.decode("utf-8", errors="replace"))
    raise ValueError("Knowledge Base import supports DOCX, TXT, and Markdown files.")


def _hash_text(*parts: str) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").encode("utf-8", errors="ignore"))
        h.update(b"\0")
    return h.hexdigest()[:16]


def classify_text(text: str) -> Tuple[str, List[str]]:
    low = (text or "").lower()
    category = "reference"
    rules = [
        ("copyright", ("copyright", "public-domain", "public domain", "permission", "quotation")),
        ("author", ("author biography", "birth-death", "known for", "literary period")),
        ("work", ("publication year", "genre/form", "major works", "summary:")),
        ("style", ("style notes", "sentence structure", "dialogue", "pacing", "imagery", "tone")),
        ("theme", ("theme", "symbol", "motif", "ambition", "revenge", "memory", "identity")),
        ("workflow", ("workflow", "checklist", "recommended format", "dataset fields", "json record")),
    ]
    for candidate, needles in rules:
        if any(needle in low for needle in needles):
            category = candidate
            break
    tag_map = {
        "gothic": "gothic",
        "tragedy": "tragedy",
        "detective": "detective",
        "dystopia": "dystopian",
        "science fiction": "science-fiction",
        "fantasy": "fantasy",
        "horror": "horror",
        "satire": "satire",
        "realism": "realism",
        "modernism": "modernism",
        "stream of consciousness": "stream-of-consciousness",
        "free indirect discourse": "free-indirect-discourse",
        "irony": "irony",
        "symbolism": "symbolism",
        "unreliable narrator": "unreliable-narrator",
        "frame narrative": "frame-narrative",
    }
    tags = [tag for needle, tag in tag_map.items() if needle in low]
    return category, sorted(set(tags))


def chunk_text(text: str, *, max_chars: int = DEFAULT_CHUNK_CHARS) -> List[str]:
    clean = normalize_whitespace(text)[:MAX_IMPORT_CHARS]
    if not clean:
        return []
    paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]
    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        if current and len(paragraph) >= 45:
            chunks.append(current.strip())
            current = paragraph
            continue
        if current and len(current) + len(paragraph) + 2 > max_chars:
            chunks.append(current.strip())
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph
    if current:
        chunks.append(current.strip())
    expanded: List[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars * 1.35:
            expanded.append(chunk)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", chunk)
        current = ""
        for sentence in sentences:
            if current and len(current) + len(sentence) + 1 > max_chars:
                expanded.append(current.strip())
                current = sentence
            else:
                current = f"{current} {sentence}".strip() if current else sentence
        if current:
            expanded.append(current.strip())
    return expanded


def knowledge_base_path(projects_dir: str) -> Path:
    return Path(projects_dir) / DEFAULT_KB_DIRNAME / "knowledge_base.json"


def load_knowledge_base(projects_dir: str) -> Dict[str, Any]:
    path = knowledge_base_path(projects_dir)
    if not path.exists():
        return {"version": KB_VERSION, "documents": [], "chunks": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": KB_VERSION, "documents": [], "chunks": []}
    if not isinstance(data, dict):
        return {"version": KB_VERSION, "documents": [], "chunks": []}
    data.setdefault("version", KB_VERSION)
    data.setdefault("documents", [])
    data.setdefault("chunks", [])
    return data


def save_knowledge_base(projects_dir: str, data: Dict[str, Any]) -> None:
    path = knowledge_base_path(projects_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def import_knowledge_document(projects_dir: str, filename: str, text: str) -> Dict[str, Any]:
    return import_knowledge_document_with_metadata(projects_dir, filename, text)


def import_knowledge_document_with_metadata(
    projects_dir: str,
    filename: str,
    text: str,
    *,
    source_type: str = "upload",
    protected: bool = False,
) -> Dict[str, Any]:
    clean = normalize_whitespace(text)
    if not clean:
        raise ValueError("The uploaded document did not contain readable text.")
    clean = clean[:MAX_IMPORT_CHARS]
    doc_id = _hash_text(filename, clean)
    data = load_knowledge_base(projects_dir)
    existing_chunks = [c for c in data.get("chunks", []) if c.get("document_id") != doc_id]
    documents = [d for d in data.get("documents", []) if d.get("id") != doc_id]
    created_at = _now()
    chunks: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunk_text(clean), start=1):
        category, tags = classify_text(chunk)
        chunks.append(
            {
                "id": _hash_text(doc_id, str(idx), chunk),
                "document_id": doc_id,
                "title": f"{filename} #{idx}",
                "category": category,
                "tags": tags,
                "text": chunk,
                "source": filename,
                "source_type": source_type,
                "created_at": created_at,
            }
        )
    category_counts: Dict[str, int] = {}
    for chunk in chunks:
        category_counts[chunk["category"]] = category_counts.get(chunk["category"], 0) + 1
    documents.append(
        {
            "id": doc_id,
            "filename": filename,
            "chars": len(clean),
            "chunks": len(chunks),
            "category_counts": category_counts,
            "source_type": source_type,
            "protected": protected,
            "content_hash": _hash_text(clean),
            "created_at": created_at,
        }
    )
    data["documents"] = sorted(documents, key=lambda d: d.get("created_at", 0), reverse=True)
    data["chunks"] = existing_chunks + chunks
    save_knowledge_base(projects_dir, data)
    return {"document_id": doc_id, "chunks": len(chunks), "chars": len(clean), "category_counts": category_counts}


def builtin_knowledge_text() -> str:
    if not BUILTIN_KB_SOURCE_PATH.exists():
        return ""
    return normalize_whitespace(BUILTIN_KB_SOURCE_PATH.read_text(encoding="utf-8"))


def builtin_knowledge_status(projects_dir: str) -> Dict[str, Any]:
    text = builtin_knowledge_text()
    if not text:
        return {
            "available": False,
            "installed": False,
            "current": False,
            "document_id": "",
            "filename": BUILTIN_KB_FILENAME,
            "chunks": 0,
            "content_hash": "",
        }
    content_hash = _hash_text(text)
    data = load_knowledge_base(projects_dir)
    for doc in data.get("documents", []) or []:
        if str(doc.get("source_type") or "") == "builtin" and str(doc.get("filename") or "") == BUILTIN_KB_FILENAME:
            return {
                "available": True,
                "installed": True,
                "current": str(doc.get("content_hash") or "") == content_hash,
                "document_id": str(doc.get("id") or ""),
                "filename": BUILTIN_KB_FILENAME,
                "chunks": int(doc.get("chunks", 0) or 0),
                "content_hash": content_hash,
            }
    return {
        "available": True,
        "installed": False,
        "current": False,
        "document_id": "",
        "filename": BUILTIN_KB_FILENAME,
        "chunks": 0,
        "content_hash": content_hash,
    }


def install_builtin_knowledge_base(projects_dir: str) -> Dict[str, Any]:
    text = builtin_knowledge_text()
    if not text:
        raise ValueError("Built-in Knowledge Base document is missing.")
    status = builtin_knowledge_status(projects_dir)
    data = load_knowledge_base(projects_dir)
    existing_builtin_id = status.get("document_id", "")
    if existing_builtin_id:
        data["documents"] = [
            doc for doc in data.get("documents", []) or []
            if str(doc.get("id") or "") != str(existing_builtin_id)
        ]
        data["chunks"] = [
            chunk for chunk in data.get("chunks", []) or []
            if str(chunk.get("document_id") or "") != str(existing_builtin_id)
        ]
        save_knowledge_base(projects_dir, data)
    return import_knowledge_document_with_metadata(
        projects_dir,
        BUILTIN_KB_FILENAME,
        text,
        source_type="builtin",
        protected=True,
    )


def _score_chunk(query_terms: List[str], chunk: Dict[str, Any]) -> float:
    text = f"{chunk.get('title', '')} {chunk.get('category', '')} {' '.join(chunk.get('tags', []) or [])} {chunk.get('text', '')}".lower()
    if not text:
        return 0.0
    score = 0.0
    for term in query_terms:
        if not term:
            continue
        hits = text.count(term)
        if hits:
            score += min(4.0, 1.0 + hits * 0.35)
        if term in (chunk.get("category") or "").lower():
            score += 2.0
        if term in [str(tag).lower() for tag in (chunk.get("tags") or [])]:
            score += 1.5
    return score


def search_knowledge_base(
    projects_dir: str,
    query: str,
    *,
    limit: int = 6,
    category: str = "",
    source: str = "",
) -> List[Dict[str, Any]]:
    terms = [term for term in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-']+", (query or "").lower()) if len(term) > 2]
    if not terms:
        return []
    data = load_knowledge_base(projects_dir)
    scored = []
    for chunk in data.get("chunks", []):
        if category and str(chunk.get("category") or "").lower() != category.strip().lower():
            continue
        if source and str(chunk.get("source") or "") != source:
            continue
        score = _score_chunk(terms, chunk)
        if score > 0:
            row = dict(chunk)
            row["score"] = round(score, 2)
            scored.append(row)
    scored.sort(key=lambda item: (item.get("score", 0), item.get("created_at", 0)), reverse=True)
    return scored[: max(1, limit)]


def list_knowledge_categories(projects_dir: str) -> List[str]:
    data = load_knowledge_base(projects_dir)
    categories = {
        str(chunk.get("category") or "reference")
        for chunk in data.get("chunks", []) or []
    }
    return sorted(categories)


def list_knowledge_sources(projects_dir: str) -> List[str]:
    data = load_knowledge_base(projects_dir)
    sources = {
        str(doc.get("filename") or "")
        for doc in data.get("documents", []) or []
        if str(doc.get("filename") or "").strip()
    }
    return sorted(sources)


def _extract_author_profile_from_text(text: str) -> Optional[Dict[str, str]]:
    clean = normalize_whitespace(text)
    match = re.search(
        r"Author biography:\s*(?P<name>[^.]+)\.\s*Major works:\s*(?P<works>[^.]+)\.\s*Useful for\s*(?P<traits>[^.]+)\.",
        clean,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    name = match.group("name").strip()
    traits = match.group("traits").strip()
    works = match.group("works").strip()
    if not name or not traits:
        return None
    return {
        "name": name,
        "works": works,
        "traits": traits,
        "query": f"{name} {traits} {works}",
    }


def list_author_style_profiles(projects_dir: str, *, limit: int = 250) -> List[Dict[str, str]]:
    """Return copyright-safe author craft profiles found in the Knowledge Base.

    These are style/craft lenses, not instructions to imitate an author's protected
    expression. The UI and prompt layer should present them as influence traits.
    """
    data = load_knowledge_base(projects_dir)
    profiles: Dict[str, Dict[str, str]] = {}
    for chunk in data.get("chunks", []) or []:
        profile = _extract_author_profile_from_text(str(chunk.get("text") or ""))
        if not profile:
            continue
        key = profile["name"].lower()
        profile["source"] = str(chunk.get("source") or "Knowledge Base")
        profiles[key] = profile
    return sorted(profiles.values(), key=lambda item: item["name"])[: max(1, limit)]


def suggest_author_style_lenses(
    projects_dir: str,
    project_text: str,
    *,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Suggest author/style lenses from the user's current project material."""
    clean = normalize_whitespace(project_text)
    terms = [
        term
        for term in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-']+", clean.lower())
        if len(term) > 3
    ]
    if not terms:
        return []
    stop_words = {
        "about", "after", "again", "against", "also", "because", "been", "before",
        "between", "chapter", "could", "every", "from", "have", "into", "more",
        "than", "that", "their", "them", "then", "there", "these", "they", "this",
        "through", "under", "were", "with", "would", "your",
    }
    query_terms = [term for term in terms if term not in stop_words]
    if not query_terms:
        return []
    query_counts: Dict[str, int] = {}
    for term in query_terms:
        query_counts[term] = query_counts.get(term, 0) + 1
    profiles = list_author_style_profiles(projects_dir, limit=500)
    suggestions: List[Dict[str, Any]] = []
    for profile in profiles:
        profile_text = " ".join(
            str(profile.get(field, ""))
            for field in ("name", "works", "traits", "query")
        ).lower()
        if not profile_text:
            continue
        profile_terms = {
            term
            for term in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-']+", profile_text)
            if len(term) > 3 and term not in stop_words
        }
        overlaps = sorted(
            (term for term in profile_terms if term in query_counts),
            key=lambda term: (query_counts.get(term, 0), len(term)),
            reverse=True,
        )
        search_query = " ".join([profile.get("query", ""), clean[:1800]])
        related = search_knowledge_base(projects_dir, search_query, limit=3)
        related_score = sum(float(item.get("score", 0) or 0) for item in related)
        score = (len(overlaps) * 4.0) + min(16.0, related_score * 0.4)
        trait_words = [
            word.strip(" ,")
            for word in re.split(r",| and ", str(profile.get("traits", "")))
            if word.strip()
        ]
        trait_hits = [trait for trait in trait_words if any(term in trait.lower() for term in overlaps[:12])]
        if not overlaps and score < 4.0:
            continue
        reason_bits = []
        if trait_hits:
            reason_bits.append("matches " + ", ".join(trait_hits[:3]))
        elif overlaps:
            reason_bits.append("shares signals: " + ", ".join(overlaps[:5]))
        if related:
            reason_bits.append("has supporting Knowledge Base references")
        suggestions.append(
            {
                "name": profile["name"],
                "works": profile.get("works", ""),
                "traits": profile.get("traits", ""),
                "score": round(score, 2),
                "confidence": min(0.95, round(0.45 + score / 60.0, 2)),
                "reason": "; ".join(reason_bits) or "general craft fit",
                "matched_terms": overlaps[:8],
            }
        )
    suggestions.sort(key=lambda item: (item.get("score", 0), item.get("confidence", 0)), reverse=True)
    return suggestions[: max(1, limit)]


def build_style_lens_context(
    projects_dir: str,
    author_names: List[str],
    *,
    project_goal: str = "",
    limit_per_author: int = 2,
) -> str:
    selected = [name.strip() for name in author_names if name and name.strip()]
    if not selected:
        return ""
    profiles_by_name = {
        profile["name"].lower(): profile
        for profile in list_author_style_profiles(projects_dir, limit=500)
    }
    blocks: List[str] = []
    for name in selected:
        profile = profiles_by_name.get(name.lower())
        if not profile:
            continue
        query = " ".join(part for part in [profile.get("query", ""), project_goal] if part)
        results = search_knowledge_base(projects_dir, query, limit=limit_per_author)
        reference_lines = []
        for item in results:
            reference_lines.append(
                f"- {item.get('category', 'reference')}: {(item.get('text') or '')[:420]}"
            )
        references = "\n".join(reference_lines) if reference_lines else "- No extra references found."
        blocks.append(
            f"STYLE LENS: {profile['name']}\n"
            f"Major works for context: {profile.get('works', '')}\n"
            f"Craft traits to adapt: {profile.get('traits', '')}\n"
            "Use these as abstract craft traits for original writing. Do not copy passages or directly impersonate a living/recent author.\n"
            f"Relevant Knowledge Base notes:\n{references}"
        )
    return "\n\n---\n\n".join(blocks)


def get_document_chunks(projects_dir: str, document_id: str, *, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    data = load_knowledge_base(projects_dir)
    chunks = [
        dict(chunk)
        for chunk in data.get("chunks", []) or []
        if str(chunk.get("document_id") or "") == str(document_id or "")
    ]
    chunks.sort(key=lambda item: item.get("title", ""))
    return chunks[:limit] if limit else chunks


def delete_knowledge_document(projects_dir: str, document_id: str, *, allow_protected: bool = False) -> bool:
    doc_id = str(document_id or "").strip()
    if not doc_id:
        return False
    data = load_knowledge_base(projects_dir)
    target = next(
        (doc for doc in data.get("documents", []) or [] if str(doc.get("id") or "") == doc_id),
        None,
    )
    if target and target.get("protected") and not allow_protected:
        return False
    documents = [doc for doc in data.get("documents", []) or [] if str(doc.get("id") or "") != doc_id]
    chunks = [chunk for chunk in data.get("chunks", []) or [] if str(chunk.get("document_id") or "") != doc_id]
    if len(documents) == len(data.get("documents", []) or []):
        return False
    data["documents"] = documents
    data["chunks"] = chunks
    save_knowledge_base(projects_dir, data)
    return True


def knowledge_stats(projects_dir: str) -> Dict[str, Any]:
    data = load_knowledge_base(projects_dir)
    chunks = data.get("chunks", []) or []
    documents = data.get("documents", []) or []
    categories: Dict[str, int] = {}
    tags: Dict[str, int] = {}
    for chunk in chunks:
        category = chunk.get("category") or "reference"
        categories[category] = categories.get(category, 0) + 1
        for tag in chunk.get("tags", []) or []:
            tags[tag] = tags.get(tag, 0) + 1
    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "categories": categories,
        "top_tags": sorted(tags.items(), key=lambda item: item[1], reverse=True)[:10],
    }


def build_knowledge_context(projects_dir: str, query: str, *, limit: int = 4) -> str:
    results = search_knowledge_base(projects_dir, query, limit=limit)
    if not results:
        return ""
    blocks = []
    for item in results:
        blocks.append(
            f"[{item.get('category', 'reference')}] {item.get('source', 'Knowledge Base')}\n"
            f"Tags: {', '.join(item.get('tags', []) or []) or 'none'}\n"
            f"{item.get('text', '')[:900]}"
        )
    return "\n\n---\n\n".join(blocks)
