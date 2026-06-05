#!/usr/bin/env python3
"""Full repository audit runner for MANTIS Studio.

This is the single entry point for a deep local check:

    python scripts/full_repo_audit.py

It is intentionally stdlib-first. If pytest is installed, it runs the full
test suite. If pytest is missing, the report records that clearly instead of
silently pretending the suite passed.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import py_compile
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "full_repo_audit"
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "artifacts",
    "venv",
    ".venv",
}
BINARY_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp", ".pdf", ".zip"}
TEXT_EXTS = {
    ".bat",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
ACTIVE_DOCS = {
    "README.md",
    "CONTRIBUTING.md",
    "docs/README.md",
    "docs/HANDBOOK.md",
    "tests/README.md",
    "legal/help.md",
    "app/README.md",
}
STALE_ACTIVE_DOC_PATTERNS = {
    "tests/test_all.py -v": "Use the full suite target: python -m pytest tests -q.",
    "pytest tests/test_all.py": "Use the full suite target: python -m pytest tests -q.",
    "artifacts/qa_report.md": "Use artifacts/full_repo_audit/full_repo_audit.md.",
    "AI Tools": "Current navigation label is AI Settings.",
    "README.md Section 9A": "Architecture notes now live in app/README.md and docs/README.md.",
    "Export` is a primary workflow item": "Export is handled from Projects; do not document a separate Export page.",
    "Visit the Export page": "Export is handled from Projects; do not document a separate Export page.",
    "Navigate to the **Export** page": "Export is handled from Projects; do not document a separate Export page.",
}


@dataclass
class Finding:
    severity: str
    file: str
    line: int | None
    title: str
    detail: str


@dataclass
class FileRecord:
    path: str
    category: str
    bytes: int
    lines: int | None
    sha256: str


@dataclass
class CommandRecord:
    name: str
    command: list[str]
    returncode: int | None
    stdout_tail: str = ""
    stderr_tail: str = ""
    skipped_reason: str = ""


@dataclass
class AuditReport:
    generated_at: str
    root: str
    files: list[FileRecord] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    commands: list[CommandRecord] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def iter_repo_files() -> Iterable[Path]:
    for path in sorted(ROOT.rglob("*")):
        if should_skip(path) or not path.is_file():
            continue
        yield path


def classify(path: Path) -> str:
    parts = set(path.relative_to(ROOT).parts)
    suffix = path.suffix.lower()
    if "tests" in parts:
        return "test"
    if "app" in parts and suffix == ".py":
        return "app-python"
    if "scripts" in parts and suffix == ".py":
        return "script-python"
    if "docs" in parts or "legal" in parts or suffix == ".md":
        return "documentation"
    if "assets" in parts:
        return "asset"
    if suffix == ".py":
        return "python"
    if suffix in {".toml", ".txt", ".bat"}:
        return "config"
    return "other"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path) -> str | None:
    if path.suffix.lower() in BINARY_EXTS:
        return None
    if path.suffix.lower() not in TEXT_EXTS:
        return None
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="cp1252")
        except UnicodeDecodeError:
            return None


def add_text_findings(report: AuditReport, path: Path, text: str) -> None:
    path_rel = rel(path)
    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped in {"<<<<<<< HEAD", "=======", ">>>>>>>"} or stripped.startswith(">>>>>>> "):
            report.findings.append(
                Finding("error", path_rel, idx, "Merge marker", "Unresolved merge marker found.")
            )
        if "\x00" in line:
            report.findings.append(
                Finding("error", path_rel, idx, "Null byte", "Text file contains a null byte.")
            )
        if line.rstrip() != line:
            report.findings.append(
                Finding("warning", path_rel, idx, "Trailing whitespace", "Line has trailing whitespace.")
            )

    if path.suffix.lower() == ".py":
        if "unsafe_allow_html" in text and path_rel.startswith("app/"):
            report.findings.append(
                Finding(
                    "error",
                    path_rel,
                    None,
                    "Unsafe Streamlit HTML path",
                    "App Python module still references unsafe_allow_html.",
                )
            )
        unstable_key_lines = []
        if path_rel.startswith("app/"):
            unstable_key_lines = [
                idx
                for idx, source_line in enumerate(text.splitlines(), start=1)
                if "key=" in source_line and "uuid.uuid4().hex" in source_line
            ]
        for line_no in unstable_key_lines:
            report.findings.append(
                Finding(
                    "warning",
                    path_rel,
                    line_no,
                    "Possible unstable widget key",
                    "Widget key appears to include uuid.uuid4().hex; keys should be stable across reruns.",
                )
            )
        if "except Exception" in text:
            report.findings.append(
                Finding(
                    "info",
                    path_rel,
                    None,
                    "Broad exception handling",
                    "Broad exception handlers exist; verify they log enough context and do not hide defects.",
                )
            )


def add_python_findings(report: AuditReport, path: Path, text: str) -> None:
    path_rel = rel(path)
    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        report.findings.append(
            Finding("error", path_rel, exc.lineno, "Syntax error", exc.msg)
        )

    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        report.findings.append(
            Finding("error", path_rel, None, "Compile error", exc.msg)
        )


def add_documentation_policy_findings(report: AuditReport) -> None:
    """Check active docs for stale references and consolidation drift."""
    records = {item.path: item for item in report.files}
    readme = records.get("README.md")
    if readme and readme.lines and readme.lines > 150:
        report.findings.append(
            Finding(
                "warning",
                "README.md",
                None,
                "Root README too large",
                "Root README should stay concise; move operational detail to docs/HANDBOOK.md.",
            )
        )

    for doc_path in sorted(ACTIVE_DOCS):
        path = ROOT / doc_path
        if not path.exists():
            report.findings.append(
                Finding("warning", doc_path, None, "Missing active doc", "Expected active documentation file is missing.")
            )
            continue
        text = read_text(path) or ""
        for pattern, guidance in STALE_ACTIVE_DOC_PATTERNS.items():
            if pattern in text:
                report.findings.append(
                    Finding("warning", doc_path, None, "Stale documentation reference", guidance)
                )

    handbook = read_text(ROOT / "docs" / "HANDBOOK.md") or ""
    changelog = read_text(ROOT / "docs" / "CHANGELOG.md") or ""
    if "scripts/full_repo_audit.py" not in handbook:
        report.findings.append(
            Finding(
                "warning",
                "docs/HANDBOOK.md",
                None,
                "Missing audit gate",
                "Handbook should document scripts/full_repo_audit.py as the primary quality gate.",
            )
        )
    if "Documentation consolidation" not in changelog and "documentation consolidation" not in changelog.lower():
        report.findings.append(
            Finding(
                "warning",
                "docs/CHANGELOG.md",
                None,
                "Missing docs change entry",
                "Changelog should mention documentation consolidation when docs are reorganized.",
            )
        )


def inventory(report: AuditReport) -> None:
    for path in iter_repo_files():
        text = read_text(path)
        lines = None if text is None else len(text.splitlines())
        report.files.append(
            FileRecord(
                path=rel(path),
                category=classify(path),
                bytes=path.stat().st_size,
                lines=lines,
                sha256=sha256(path),
            )
        )
        if text is not None:
            add_text_findings(report, path, text)
            if path.suffix.lower() == ".py":
                add_python_findings(report, path, text)
    add_documentation_policy_findings(report)


def tail(value: str, limit: int = 4000) -> str:
    value = value or ""
    return value[-limit:]


def run_command(name: str, command: list[str], timeout: int = 180) -> CommandRecord:
    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandRecord(
            name=name,
            command=command,
            returncode=completed.returncode,
            stdout_tail=tail(completed.stdout),
            stderr_tail=tail(completed.stderr),
        )
    except FileNotFoundError as exc:
        return CommandRecord(
            name=name,
            command=command,
            returncode=None,
            skipped_reason=f"Executable not found: {exc}",
        )
    except subprocess.TimeoutExpired as exc:
        return CommandRecord(
            name=name,
            command=command,
            returncode=None,
            stdout_tail=tail(exc.stdout or ""),
            stderr_tail=tail(exc.stderr or ""),
            skipped_reason=f"Timed out after {timeout}s",
        )


def run_execution_checks(report: AuditReport, *, skip_tests: bool) -> None:
    report.commands.append(
        run_command("selftest", [sys.executable, "-m", "app.main", "--selftest"], timeout=120)
    )
    report.commands.append(
        run_command("healthcheck", [sys.executable, "scripts/healthcheck.py"], timeout=120)
    )
    if skip_tests:
        report.commands.append(
            CommandRecord(
                name="pytest",
                command=[sys.executable, "-m", "pytest", "tests", "-q"],
                returncode=None,
                skipped_reason="Skipped by --skip-tests",
            )
        )
    else:
        report.commands.append(
            run_command("pytest", [sys.executable, "-m", "pytest", "tests", "-q"], timeout=300)
        )


def summarize(report: AuditReport) -> None:
    report.summary = {
        "files": len(report.files),
        "python_files": sum(1 for item in report.files if item.path.endswith(".py")),
        "test_files": sum(1 for item in report.files if item.category == "test"),
        "documentation_files": sum(1 for item in report.files if item.category == "documentation"),
        "asset_files": sum(1 for item in report.files if item.category == "asset"),
        "errors": sum(1 for f in report.findings if f.severity == "error"),
        "warnings": sum(1 for f in report.findings if f.severity == "warning"),
        "info": sum(1 for f in report.findings if f.severity == "info"),
        "command_failures": sum(1 for c in report.commands if c.returncode not in (0, None)),
        "command_skips": sum(1 for c in report.commands if c.returncode is None),
    }


def write_json(report: AuditReport) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "full_repo_audit.json"
    path.write_text(json.dumps(asdict(report), indent=2), encoding="utf-8")
    return path


def write_markdown(report: AuditReport) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "full_repo_audit.md"
    lines: list[str] = [
        "# Full Repository Audit",
        "",
        f"- Generated: {report.generated_at}",
        f"- Root: `{report.root}`",
        "",
        "## Summary",
    ]
    for key, value in report.summary.items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Command Results"])
    for command in report.commands:
        if command.returncode == 0:
            status = "PASS"
        elif command.returncode is None:
            status = "SKIP"
        else:
            status = "FAIL"
        lines.append(f"- {command.name}: {status} (`{' '.join(command.command)}`)")
        if command.skipped_reason:
            lines.append(f"  - Reason: {command.skipped_reason}")

    lines.extend(["", "## Findings"])
    if report.findings:
        for finding in report.findings:
            location = finding.file
            if finding.line:
                location = f"{location}:{finding.line}"
            lines.append(f"- [{finding.severity.upper()}] `{location}` - {finding.title}: {finding.detail}")
    else:
        lines.append("- No static findings.")

    lines.extend(["", "## File Inventory"])
    for item in report.files:
        line_text = "binary" if item.lines is None else str(item.lines)
        lines.append(
            f"- `{item.path}` ({item.category}, {item.bytes} bytes, {line_text} lines, sha256 `{item.sha256[:12]}...`)"
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a full MANTIS Studio repository audit.")
    parser.add_argument("--skip-tests", action="store_true", help="Do not execute pytest.")
    parser.add_argument("--json-only", action="store_true", help="Only write JSON output.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    started = time.time()
    report = AuditReport(
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        root=str(ROOT),
    )
    inventory(report)
    run_execution_checks(report, skip_tests=args.skip_tests)
    summarize(report)
    json_path = write_json(report)
    md_path = None if args.json_only else write_markdown(report)

    elapsed = round(time.time() - started, 2)
    print(f"Full repo audit complete in {elapsed}s")
    print(f"JSON: {json_path}")
    if md_path:
        print(f"Markdown: {md_path}")

    failed_commands = [c for c in report.commands if c.returncode not in (0, None)]
    hard_errors = [f for f in report.findings if f.severity == "error"]
    return 1 if failed_commands or hard_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
