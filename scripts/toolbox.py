#!/usr/bin/env python3
"""Unified maintenance toolbox for MANTIS Studio.

Single entrypoint for:
- version bump
- healthcheck (compile + imports)
- smoke run
- test run
- visual regression run
- comprehensive QA report
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import pathlib
import py_compile
import subprocess
import sys
import time
from typing import Iterable


ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", "archive"}


def _run(cmd: list[str], *, check: bool = False, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(ROOT),
        check=check,
        capture_output=capture,
        text=True,
    )


def bump_version(current_version: str) -> str:
    parts = current_version.strip().split(".")
    if len(parts) != 2:
        raise SystemExit(f"Invalid version format: {current_version} (expected MAJOR.MINOR)")
    major = int(parts[0])
    minor = int(parts[1]) + 1
    if minor >= 10:
        major += 1
        minor = 0
    return f"{major}.{minor}"


def cmd_bump(_args: argparse.Namespace) -> int:
    version_file = ROOT / "VERSION.txt"
    if not version_file.exists():
        print(f"VERSION.txt not found: {version_file}")
        return 1
    current = version_file.read_text(encoding="utf-8").strip()
    new_version = bump_version(current)
    version_file.write_text(new_version + "\n", encoding="utf-8")
    print(f"Version bumped: {current} -> {new_version}")
    return 0


def _should_skip(path: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def _compile_sources() -> tuple[int, list[str]]:
    failures: list[str] = []
    for path in ROOT.rglob("*.py"):
        if _should_skip(path):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"{path}: {exc.msg}")
    return len(failures), failures


def _import_modules(modules: Iterable[str]) -> tuple[int, list[str]]:
    failures: list[str] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{module}: {exc}")
    return len(failures), failures


def cmd_health(_args: argparse.Namespace) -> int:
    compile_count, compile_failures = _compile_sources()
    import_count, import_failures = _import_modules(
        ["app.main", "app.utils.navigation", "app.layout.layout", "app.ui.enhanced_theme"]
    )
    total = compile_count + import_count
    if total:
        print("Healthcheck failed:")
        for item in compile_failures + import_failures:
            print(f"- {item}")
        return 1
    print("Healthcheck passed.")
    return 0


def cmd_smoke(_args: argparse.Namespace) -> int:
    ok = True
    try:
        navigation = importlib.import_module("app.utils.navigation")
        labels, page_map = navigation.get_nav_config(True)
        assert "Dashboard" in labels and page_map.get("Dashboard") == "home"
    except Exception as exc:  # noqa: BLE001
        print(f"[SMOKE] Navigation import failed: {exc}")
        ok = False

    try:
        ui = importlib.import_module("app.components.ui")
        required = ("card", "section_header", "primary_button", "stat_tile", "action_card")
        missing = [name for name in required if not hasattr(ui, name)]
        if missing:
            raise RuntimeError(f"Missing UI helpers: {', '.join(missing)}")
    except Exception as exc:  # noqa: BLE001
        print(f"[SMOKE] UI import failed: {exc}")
        ok = False

    selftest = _run([sys.executable, "-m", "app.main", "--selftest"], check=False, capture=True)
    if selftest.stdout.strip():
        print(selftest.stdout.strip())
    if selftest.returncode != 0:
        if selftest.stderr.strip():
            print(selftest.stderr.strip())
        ok = False

    print("[SMOKE] PASS" if ok else "[SMOKE] FAIL")
    return 0 if ok else 1


def cmd_test(args: argparse.Namespace) -> int:
    target = args.target or "tests/test_all.py"
    result = _run([sys.executable, "-m", "pytest", target, "-q"], check=False, capture=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def cmd_visual(args: argparse.Namespace) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # noqa: BLE001
        print(f"Playwright not available: {exc}")
        return 1

    base_url = args.base_url
    out_dir = ROOT / "artifacts" / "visual_regression"
    out_dir.mkdir(parents=True, exist_ok=True)
    pages = [
        ("dashboard", "Dashboard"),
        ("projects", "Projects"),
        ("outline", "Outline"),
        ("chapters", "Chapters"),
        ("world_bible", "World Bible"),
        ("memory", "Memory"),
        ("insights", "Insights"),
    ]

    def _write_theme(theme_name: str) -> None:
        cfg_path = ROOT / "projects" / ".mantis_config.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg = {}
        if cfg_path.exists():
            try:
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception:
                cfg = {}
        cfg["ui_theme"] = theme_name
        cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

    summary: dict = {"base_url": base_url, "themes": {}, "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for theme in ("Dark", "Light"):
            key = theme.lower()
            summary["themes"][key] = {}
            _write_theme(theme)
            context = browser.new_context(viewport={"width": 1728, "height": 1117})
            page = context.new_page()
            try:
                page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2200)
                for slug, label in pages:
                    try:
                        btn = page.locator('section[data-testid="stSidebar"]').get_by_role("button", name=label).first
                        if btn.count() > 0 and btn.is_enabled():
                            btn.click(timeout=5000)
                            page.wait_for_timeout(800)
                        page.evaluate("window.scrollTo(0,0)")
                        out = out_dir / f"{key}_{slug}.png"
                        page.screenshot(path=str(out), full_page=True)
                        summary["themes"][key][slug] = str(out)
                    except Exception as exc:  # noqa: BLE001
                        summary["errors"].append(f"{theme}/{label}: {exc}")
            except Exception as exc:  # noqa: BLE001
                summary["errors"].append(f"{theme} boot: {exc}")
            context.close()
        browser.close()

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary_path)
    if summary.get("errors"):
        print("Visual errors:")
        for err in summary["errors"]:
            print(f"- {err}")
        return 1
    return 0


def cmd_qa(args: argparse.Namespace) -> int:
    started = time.time()
    report_dir = ROOT / "artifacts"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "qa_report.md"

    results: list[tuple[str, int, str]] = []

    h = cmd_health(args)
    results.append(("health", h, "Compile + import validation"))

    s = cmd_smoke(args)
    results.append(("smoke", s, "Selftest + critical import checks"))

    t_args = argparse.Namespace(target="tests/test_all.py")
    t = cmd_test(t_args)
    results.append(("tests", t, "Canonical unified pytest suite"))

    v_status = 0
    if args.with_visual:
        v = cmd_visual(args)
        v_status = v
        results.append(("visual", v, "Dark/light browser regression"))

    elapsed = round(time.time() - started, 2)
    lines = [
        "# MANTIS QA Report",
        "",
        f"- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Duration: {elapsed}s",
        "",
        "## Results",
    ]
    for name, code, desc in results:
        status = "PASS" if code == 0 else "FAIL"
        lines.append(f"- **{name}**: {status} ({desc})")

    if args.with_visual:
        summary_json = ROOT / "artifacts" / "visual_regression" / "summary.json"
        if summary_json.exists():
            try:
                data = json.loads(summary_json.read_text(encoding="utf-8"))
                errors = data.get("errors", [])
                lines.append("")
                lines.append("## Visual Regression")
                lines.append(f"- Errors: {len(errors)}")
                if errors:
                    for err in errors[:10]:
                        lines.append(f"- {err}")
            except Exception as exc:  # noqa: BLE001
                lines.append("")
                lines.append(f"- Visual summary parse error: {exc}")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"QA report: {report_path}")

    failures = [code for _, code, _ in results if code != 0]
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MANTIS unified toolbox")
    sub = parser.add_subparsers(dest="command", required=True)

    p_bump = sub.add_parser("bump", help="Bump VERSION.txt")
    p_bump.set_defaults(func=cmd_bump)

    p_health = sub.add_parser("health", help="Compile + import healthcheck")
    p_health.set_defaults(func=cmd_health)

    p_smoke = sub.add_parser("smoke", help="Smoke test run")
    p_smoke.set_defaults(func=cmd_smoke)

    p_test = sub.add_parser("test", help="Run pytest (default: tests/test_all.py)")
    p_test.add_argument("--target", default="tests/test_all.py")
    p_test.set_defaults(func=cmd_test)

    p_visual = sub.add_parser("visual", help="Run visual regression script")
    p_visual.add_argument("--base-url", default="http://localhost:8501")
    p_visual.set_defaults(func=cmd_visual)

    p_qa = sub.add_parser("qa", help="Run comprehensive QA")
    p_qa.add_argument("--with-visual", action="store_true")
    p_qa.set_defaults(func=cmd_qa)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
