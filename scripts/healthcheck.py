#!/usr/bin/env python3
"""Minimal healthcheck: compile Python files and import key modules."""
from __future__ import annotations

import importlib
import importlib.util
import pathlib
import py_compile
import sys
from types import ModuleType
from typing import Optional


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}
sys.path.insert(0, str(ROOT))


def _should_skip(path: pathlib.Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def compile_sources() -> int:
    failures = 0
    for path in ROOT.rglob("*.py"):
        if _should_skip(path):
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            failures += 1
            print(f"[compile] {path}: {exc.msg}")
    return failures


def _import_page_module(label: str, path: pathlib.Path) -> Optional[ModuleType]:
    if not path.exists():
        raise FileNotFoundError(f"Page not found: {path}")
    spec = importlib.util.spec_from_file_location(label, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def import_modules() -> int:
    failures = 0
    modules = [
        "app.main",
        "app.utils.navigation",
        "app.layout.layout",
    ]
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - healthcheck should capture all failures
            failures += 1
            print(f"[import] {module}: {exc}")
    return failures


def main() -> int:
    failures = compile_sources() + import_modules()
    if failures:
        print(f"Healthcheck failed with {failures} issue(s).")
        return 1
    print("Healthcheck passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
