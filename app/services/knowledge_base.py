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
from typing import Any, Dict, List, Tuple


KB_VERSION = 1
DEFAULT_KB_DIRNAME = ".knowledge_base"
DEFAULT_CHUNK_CHARS = 1100
MAX_IMPORT_CHARS = 500_000


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
            "created_at": created_at,
        }
    )
    data["documents"] = sorted(documents, key=lambda d: d.get("created_at", 0), reverse=True)
    data["chunks"] = existing_chunks + chunks
    save_knowledge_base(projects_dir, data)
    return {"document_id": doc_id, "chunks": len(chunks), "chars": len(clean), "category_counts": category_counts}


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


def search_knowledge_base(projects_dir: str, query: str, *, limit: int = 6) -> List[Dict[str, Any]]:
    terms = [term for term in re.findall(r"[a-zA-Z0-9][a-zA-Z0-9\-']+", (query or "").lower()) if len(term) > 2]
    if not terms:
        return []
    data = load_knowledge_base(projects_dir)
    scored = []
    for chunk in data.get("chunks", []):
        score = _score_chunk(terms, chunk)
        if score > 0:
            row = dict(chunk)
            row["score"] = round(score, 2)
            scored.append(row)
    scored.sort(key=lambda item: (item.get("score", 0), item.get("created_at", 0)), reverse=True)
    return scored[: max(1, limit)]


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
