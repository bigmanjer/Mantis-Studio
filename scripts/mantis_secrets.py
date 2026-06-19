"""Secret/key storage helpers for MANTIS launcher tools."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


@dataclass
class KeySource:
    label: str
    key: str


def load_app_config(repo_root: Path) -> dict[str, object]:
    config_path = Path(
        os.getenv("MANTIS_CONFIG_PATH")
        or repo_root / "projects" / ".mantis_config.json"
    )
    try:
        with config_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def load_streamlit_secrets(repo_root: Path) -> dict[str, object]:
    if tomllib is None:
        return load_streamlit_secrets_lenient(repo_root)
    secrets_path = repo_root / ".streamlit" / "secrets.toml"
    try:
        with secrets_path.open("rb") as handle:
            data = tomllib.load(handle)
        return data if isinstance(data, dict) else {}
    except (OSError, tomllib.TOMLDecodeError):
        return load_streamlit_secrets_lenient(repo_root)


def load_streamlit_secrets_lenient(repo_root: Path) -> dict[str, object]:
    secrets_path = repo_root / ".streamlit" / "secrets.toml"
    try:
        text = secrets_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}

    data: dict[str, object] = {}
    current_section = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        section_match = re.fullmatch(r"\[([A-Za-z0-9_.-]+)\]", line)
        if section_match:
            current_section = section_match.group(1)
            data.setdefault(current_section, {})
            continue
        match = re.match(r"([A-Za-z0-9_.-]+)\s*=\s*(['\"])(.*)\2\s*(?:#.*)?$", line)
        if not match:
            continue
        key, _quote, value = match.groups()
        cleaned = value.encode("utf-8", errors="replace").decode("unicode_escape", errors="replace")
        if current_section and isinstance(data.get(current_section), dict):
            data[current_section][key] = cleaned  # type: ignore[index]
        else:
            data[key] = cleaned
    return data


def nested_secret(data: dict[str, object], section: str, key: str) -> object:
    value = data.get(section)
    if isinstance(value, dict):
        return value.get(key)
    return None


def research_api_key(repo_root: Path) -> str:
    secrets = load_streamlit_secrets(repo_root)
    candidates = [
        os.getenv("MANTIS_RESEARCH_API_KEY"),
        os.getenv("TAVILY_API_KEY"),
        secrets.get("MANTIS_RESEARCH_API_KEY"),
        secrets.get("TAVILY_API_KEY"),
        secrets.get("tavily_api_key"),
        nested_secret(secrets, "research", "api_key"),
        nested_secret(secrets, "tavily", "api_key"),
    ]
    for key in candidates:
        clean = clean_research_key(key)
        if clean:
            return clean
    return ""


def valid_groq_key(value: object) -> str:
    clean = extract_groq_key(value)
    if re.fullmatch(r"gsk_[A-Za-z0-9_-]{20,}", clean):
        return clean
    return ""


def extract_groq_key(value: object) -> str:
    clean = str(value or "").strip()
    match = re.search(r"gsk_[A-Za-z0-9_-]{20,}", clean)
    if match:
        return match.group(0)
    return ""


def clean_api_key(value: object) -> str:
    clean = str(value or "").strip().strip("'\"")
    match = re.search(
        r"(gsk_[A-Za-z0-9_-]{20,}|tvly-[A-Za-z0-9_-]{20,}|[A-Za-z0-9][A-Za-z0-9_.-]{15,})",
        clean,
    )
    if not match:
        return ""
    candidate = match.group(1)
    if any(ord(ch) < 32 or ord(ch) == 127 or ch.isspace() for ch in candidate):
        return ""
    return candidate


def clean_research_key(value: object) -> str:
    clean = str(value or "").strip().strip("'\"")
    match = re.search(r"tvly-[A-Za-z0-9_-]{20,}", clean)
    if not match:
        return ""
    return match.group(0)


def save_named_secret(repo_root: Path, names: list[str], preferred_name: str, value: str) -> tuple[bool, str]:
    secrets_path = repo_root / ".streamlit" / "secrets.toml"
    secrets_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        existing = secrets_path.read_text(encoding="utf-8") if secrets_path.exists() else ""
        existing = repair_toml_control_chars(existing)
        replacement = f'{preferred_name} = "{toml_escape(value)}"'
        updated = existing
        for name in names:
            if re.search(rf"(?m)^{re.escape(name)}\s*=", updated):
                updated = re.sub(
                    rf'(?m)^{re.escape(name)}\s*=.*$',
                    lambda _match: replacement,
                    updated,
                )
                break
        else:
            spacer = "" if not updated or updated.endswith("\n") else "\n"
            updated = f"{updated}{spacer}{replacement}\n"
        secrets_path.write_text(updated, encoding="utf-8")
    except OSError as exc:
        return False, str(exc)
    return True, ""


def toml_escape(value: str) -> str:
    return json.dumps(value)[1:-1]


def repair_toml_control_chars(text: str) -> str:
    def repair(match: re.Match[str]) -> str:
        key, quote, value = match.groups()
        if quote == '"':
            return f'{key}"{toml_escape(value)}"'
        safe = value.replace("\\", "\\\\").replace("'", "\\'")
        return f"{key}'{safe}'"

    return re.sub(r"(?m)^([A-Za-z0-9_.-]+\s*=\s*)(['\"])(.*)\2\s*$", repair, text)
