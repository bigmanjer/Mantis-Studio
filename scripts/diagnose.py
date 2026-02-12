#!/usr/bin/env python3
"""
Mantis Studio Diagnostic Tool

This script runs comprehensive diagnostics on your Mantis Studio installation
and helps identify common issues.

Usage:
    python scripts/diagnose.py
    python scripts/diagnose.py --verbose
    python scripts/diagnose.py --fix
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import pathlib
import platform
import sys
from typing import Any

# Add project root to path
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class DiagnosticResult:
    """Store diagnostic test results."""

    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.info = []

    def add_pass(self, test: str, message: str = ""):
        self.passed.append((test, message))

    def add_fail(self, test: str, message: str, fix: str = ""):
        self.failed.append((test, message, fix))

    def add_warning(self, test: str, message: str):
        self.warnings.append((test, message))

    def add_info(self, key: str, value: Any):
        self.info.append((key, value))

    def print_summary(self):
        """Print formatted diagnostic summary."""
        print("\n" + "=" * 70)
        print("🔍 MANTIS STUDIO DIAGNOSTIC REPORT")
        print("=" * 70)

        # System info
        if self.info:
            print("\n📊 SYSTEM INFORMATION")
            print("-" * 70)
            for key, value in self.info:
                print(f"  {key}: {value}")

        # Passed tests
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)} tests)")
            print("-" * 70)
            for test, message in self.passed:
                print(f"  ✓ {test}")
                if message:
                    print(f"    {message}")

        # Warnings
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)})")
            print("-" * 70)
            for test, message in self.warnings:
                print(f"  ! {test}")
                print(f"    {message}")

        # Failed tests
        if self.failed:
            print(f"\n❌ FAILED ({len(self.failed)} tests)")
            print("-" * 70)
            for test, message, fix in self.failed:
                print(f"  ✗ {test}")
                print(f"    Error: {message}")
                if fix:
                    print(f"    Fix: {fix}")

        # Summary
        print("\n" + "=" * 70)
        total = len(self.passed) + len(self.failed)
        if self.failed:
            print(f"RESULT: {len(self.failed)} issues found (out of {total} tests)")
            print("\nℹ️  See docs/guides/DEBUGGING_GUIDE.md for detailed help")
            return 1
        elif self.warnings:
            print(f"RESULT: All tests passed with {len(self.warnings)} warnings")
            print("\n✨ Your installation looks good!")
            return 0
        else:
            print("RESULT: All diagnostics passed!")
            print("\n✨ Your installation is healthy!")
            return 0


def check_python_version(results: DiagnosticResult) -> None:
    """Check if Python version is compatible."""
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    results.add_info("Python Version", version_str)
    results.add_info("Platform", platform.platform())

    if version.major < 3 or (version.major == 3 and version.minor < 10):
        results.add_fail(
            "Python Version",
            f"Python {version_str} is too old",
            "Install Python 3.10 or newer",
        )
    else:
        results.add_pass("Python Version", f"Python {version_str} is compatible")


def check_dependencies(results: DiagnosticResult) -> None:
    """Check if required dependencies are installed."""
    requirements_file = ROOT / "requirements.txt"
    if not requirements_file.exists():
        results.add_fail(
            "Requirements File",
            "requirements.txt not found",
            "Ensure you're running from project root",
        )
        return

    results.add_pass("Requirements File", "Found requirements.txt")

    # Read required packages
    required = []
    with open(requirements_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                # Extract package name (before >= or ==)
                pkg = line.split(">=")[0].split("==")[0].strip()
                required.append(pkg)

    # Check each package
    missing = []
    installed = []
    for pkg in required:
        # Handle package name differences (e.g., python-dotenv vs dotenv)
        import_name = pkg.replace("-", "_")
        try:
            importlib.import_module(import_name)
            installed.append(pkg)
        except ImportError:
            # Try alternate names
            try:
                if pkg == "python-dotenv":
                    importlib.import_module("dotenv")
                    installed.append(pkg)
                elif pkg == "Pillow":
                    importlib.import_module("PIL")
                    installed.append(pkg)
                else:
                    missing.append(pkg)
            except ImportError:
                missing.append(pkg)

    if missing:
        results.add_fail(
            "Dependencies",
            f"Missing packages: {', '.join(missing)}",
            "Run: pip install -r requirements.txt",
        )
    else:
        results.add_pass(
            "Dependencies", f"All {len(installed)} required packages installed"
        )


def check_critical_imports(results: DiagnosticResult) -> None:
    """Check if critical modules can be imported."""
    critical_modules = [
        "app.main",
        "app.state",
        "app.router",
        "app.services.projects",
        "app.services.storage",
        "app.utils.navigation",
    ]

    failed_imports = []
    for module in critical_modules:
        try:
            importlib.import_module(module)
        except Exception as e:
            failed_imports.append((module, str(e)))

    if failed_imports:
        for module, error in failed_imports:
            results.add_fail(
                f"Import {module}",
                error,
                "Check module for syntax errors",
            )
    else:
        results.add_pass(
            "Critical Imports", f"All {len(critical_modules)} modules import successfully"
        )


def check_file_structure(results: DiagnosticResult) -> None:
    """Check if essential files and directories exist."""
    required_paths = [
        ("app/main.py", "file"),
        ("app/state.py", "file"),
        ("app/services", "dir"),
        ("app/views", "dir"),
        ("scripts", "dir"),
        ("tests", "dir"),
        ("requirements.txt", "file"),
        ("VERSION.txt", "file"),
    ]

    missing = []
    for path_str, path_type in required_paths:
        path = ROOT / path_str
        if path_type == "file" and not path.is_file():
            missing.append(path_str)
        elif path_type == "dir" and not path.is_dir():
            missing.append(path_str)

    if missing:
        results.add_fail(
            "File Structure",
            f"Missing: {', '.join(missing)}",
            "Ensure you have a complete repository clone",
        )
    else:
        results.add_pass("File Structure", "All essential files present")


def check_version_file(results: DiagnosticResult) -> None:
    """Check VERSION.txt validity."""
    version_file = ROOT / "VERSION.txt"
    if not version_file.exists():
        results.add_fail(
            "VERSION.txt",
            "File not found",
            "Create VERSION.txt with format: MAJOR.MINOR (e.g., 88.7)",
        )
        return

    try:
        version = version_file.read_text().strip()
        results.add_info("App Version", version)

        # Validate format
        parts = version.split(".")
        if len(parts) != 2:
            results.add_warning(
                "VERSION.txt Format",
                f"Expected MAJOR.MINOR format, got: {version}",
            )
        else:
            major, minor = parts
            int(major)  # Validate numeric
            int(minor)
            results.add_pass("VERSION.txt", f"Valid version: {version}")
    except Exception as e:
        results.add_fail("VERSION.txt", f"Invalid format: {e}", "Use MAJOR.MINOR format")


def check_config_files(results: DiagnosticResult, verbose: bool = False) -> None:
    """Check for configuration files and their validity."""
    # Check for .env file (optional)
    env_file = ROOT / ".env"
    if env_file.exists():
        results.add_pass(".env file", "Found (optional configuration)")
        if verbose:
            # Count non-empty, non-comment lines
            with open(env_file) as f:
                lines = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.strip().startswith("#")
                ]
            results.add_info(".env entries", len(lines))
    else:
        results.add_info(".env file", "Not found (optional)")

    # Check projects directory
    try:
        from app.config.settings import AppConfig

        config = AppConfig()
        projects_dir = pathlib.Path(config.projects_dir)

        if projects_dir.exists():
            # Count projects
            project_files = list(projects_dir.glob("*.json"))
            results.add_pass(
                "Projects Directory", f"Found with {len(project_files)} projects"
            )
        else:
            results.add_warning(
                "Projects Directory",
                f"Not found at {projects_dir} (will be created on first use)",
            )
    except Exception as e:
        results.add_warning("Projects Directory", f"Could not check: {e}")


def check_test_infrastructure(results: DiagnosticResult) -> None:
    """Check if test infrastructure is working."""
    try:
        import pytest

        results.add_pass("pytest", "Installed")

        # Try to collect tests
        import subprocess

        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            # Count tests from output
            output = result.stdout
            if "test" in output.lower():
                results.add_pass("Test Collection", "Tests found and collectible")
        else:
            results.add_warning(
                "Test Collection", "pytest installed but test collection had issues"
            )

    except ImportError:
        results.add_warning(
            "pytest",
            "Not installed (required for running tests)",
        )
    except Exception as e:
        results.add_warning("Test Infrastructure", f"Check failed: {e}")


def run_diagnostics(verbose: bool = False) -> DiagnosticResult:
    """Run all diagnostic checks."""
    results = DiagnosticResult()

    print("Running diagnostics...")

    check_python_version(results)
    check_file_structure(results)
    check_version_file(results)
    check_dependencies(results)
    check_critical_imports(results)
    check_config_files(results, verbose)
    check_test_infrastructure(results)

    return results


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Mantis Studio diagnostic tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed output"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix common issues (future)"
    )

    args = parser.parse_args()

    if args.fix:
        print("⚠️  Auto-fix not yet implemented. Showing diagnostics only.")
        print()

    results = run_diagnostics(verbose=args.verbose)
    exit_code = results.print_summary()

    if exit_code != 0:
        print("\n💡 Quick fixes:")
        print("   • Missing dependencies: pip install -r requirements.txt")
        print("   • Import errors: python scripts/healthcheck.py")
        print("   • More help: docs/guides/DEBUGGING_GUIDE.md")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
