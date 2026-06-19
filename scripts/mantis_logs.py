"""Log and previous-chat helpers for MANTIS launcher chat."""

from __future__ import annotations

import re
from pathlib import Path


def tail(path: Path, limit: int) -> list[str]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            return handle.readlines()[-limit:]
    except OSError:
        return []


def summarize_runtime_log(log_file: Path, mask, repo_root: Path | None = None) -> str:
    selected_log = _select_runtime_log(log_file, repo_root)
    if selected_log is None:
        return "I do not see a runtime log yet. The server may still be starting."

    lines = tail(selected_log, 25)
    if not lines:
        return f"The current runtime log exists, but it is empty right now: {selected_log}"

    issues = [
        line.strip()
        for line in lines
        if re.search(r"\b(error|exception|traceback|failed|warning)\b", line, re.I)
    ]
    if issues:
        preview = "\n".join(f"- {mask(line[:180])}" for line in issues[-5:])
        return f"I found these recent warning/error lines in {selected_log.name}:\n{preview}"

    preview = "\n".join(mask(line.rstrip()) for line in lines[-8:])
    return f"No obvious recent errors in {selected_log.name}. Latest log tail:\n{preview}"


def log_health(log_file: Path, repo_root: Path | None = None) -> str:
    selected_log = _select_runtime_log(log_file, repo_root)
    if selected_log is None:
        return "no log file yet"
    lines = tail(selected_log, 80)
    if not lines:
        return "log file exists but is empty"
    issue_count = sum(
        1
        for line in lines
        if re.search(r"\b(error|exception|traceback|failed)\b", line, re.I)
    )
    if issue_count:
        return f"{issue_count} recent issue-looking line(s); ask 'log' for details"
    return "no recent error-looking lines"


def _select_runtime_log(log_file: Path, repo_root: Path | None = None) -> Path | None:
    candidates = [log_file]
    folders = [log_file.parent]
    if repo_root is not None:
        folders.extend([repo_root / "logs" / "streamlit", repo_root / "logs"])
    for folder in folders:
        try:
            candidates.extend(path for path in folder.glob("streamlit*.log") if path.is_file())
        except OSError:
            continue
    unique = sorted(
        set(candidates),
        key=lambda path: path.stat().st_mtime if path.exists() else 0,
        reverse=True,
    )
    for path in unique:
        try:
            if path.exists() and path.stat().st_size > 0:
                return path
        except OSError:
            continue
    for path in unique:
        if path.exists():
            return path
    return None


def recent_chat_lines(repo_root: Path, current_chat_log: Path, limit: int = 500) -> list[str]:
    log_dirs = [
        current_chat_log.parent,
        repo_root / "logs" / "chat",
        repo_root / "logs",
    ]
    files: list[Path] = []
    for folder in log_dirs:
        try:
            files.extend(path for path in folder.glob("chat*.log") if path.is_file())
        except OSError:
            continue
    unique_files = sorted(set(files), key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    lines: list[str] = []
    for path in unique_files[:8]:
        lines.extend(tail(path, max(80, limit // 4)))
        if len(lines) >= limit:
            break
    return lines[-limit:]


def recent_research_topics(repo_root: Path, current_chat_log: Path, limit: int = 900) -> list[str]:
    topics: list[str] = []
    for line in recent_chat_lines(repo_root, current_chat_log, limit=limit):
        if " [user] " not in line:
            continue
        text = line.split(" [user] ", 1)[1].strip()
        lowered = text.lower()
        candidates: list[str] = []
        for pattern in (
            r"^/learn research\s+(.+)$",
            r"^/research\s+(.+)$",
        ):
            match = re.search(pattern, text, re.I)
            if match:
                candidates.append(match.group(1).strip())
        if "human history" in lowered:
            candidates.append("human history overview: ancient, medieval, early modern, modern, cultural, social, science, and technology history")
        if "fiction writing" in lowered or "writing craft" in lowered:
            candidates.append("core fiction writing craft: character, conflict, scene structure, pacing, dialogue, point of view, theme, revision, and prose style")
        if "todo list" in lowered:
            candidates.append("MANTIS roadmap and TODO list: learning jobs, research intake, simulator checks, logs, keys, and honest assistant behavior")
        if "better assistant" in lowered or "being assistant" in lowered:
            candidates.append("how to be a better conversational coding and writing assistant")

        for candidate in candidates:
            clean = clean_research_topic(candidate)
            if clean and clean.lower() not in [item.lower() for item in topics]:
                topics.insert(0, clean)
    return topics[:8]


def clean_research_topic(topic: str) -> str:
    clean = re.sub(r"\s+", " ", topic or "").strip(" .?!:")
    clean = re.sub(r"\b(i want you to|i want u to|i need you to|i need u to)\b", "", clean, flags=re.I).strip()
    clean = re.sub(r"\b(know|learn|research)\s+(all of|about)?\s*", "", clean, flags=re.I).strip()
    if not clean or clean.lower() in {"it", "all", "everything", "our todo list", "the todo list"}:
        return ""
    if re.search(r"\b(key|api|groq|tavily|save key|research key)\b", clean, re.I):
        return ""
    if len(clean) < 12:
        return ""
    return clean[:220]
