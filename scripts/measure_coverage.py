#!/usr/bin/env python3
"""Test coverage measurement and reporting script for Mantis Studio.

This script runs the test suite with coverage analysis and generates reports.

Usage:
    python scripts/measure_coverage.py          # Run tests and show coverage
    python scripts/measure_coverage.py --html   # Generate HTML report
    python scripts/measure_coverage.py --xml    # Generate XML report for CI
    python scripts/measure_coverage.py --all    # Generate all reports
"""
import argparse
import subprocess
import sys
from pathlib import Path


def run_coverage(html=False, xml=False, show_missing=True):
    """Run pytest with coverage analysis.
    
    Args:
        html: Generate HTML coverage report
        xml: Generate XML coverage report for CI
        show_missing: Show missing lines in terminal report
    """
    project_root = Path(__file__).resolve().parents[1]
    
    # Base pytest command with coverage
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--cov=app",
        "--cov-report=term",
    ]
    
    # Add missing lines to terminal report
    if show_missing:
        cmd[-1] = "--cov-report=term-missing"
    
    # Add HTML report
    if html:
        cmd.append("--cov-report=html")
        print("📊 Generating HTML coverage report...")
    
    # Add XML report for CI
    if xml:
        cmd.append("--cov-report=xml")
        print("📊 Generating XML coverage report...")
    
    # Run the tests with coverage
    print(f"🧪 Running tests with coverage analysis...")
    print(f"Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=project_root)
    
    # Print results
    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ Tests passed!")
    else:
        print("❌ Some tests failed!")
    
    # Show where reports were generated
    if html:
        html_report = project_root / "htmlcov" / "index.html"
        print(f"\n📄 HTML report generated: {html_report}")
        print(f"   Open in browser: file://{html_report}")
    
    if xml:
        xml_report = project_root / "coverage.xml"
        print(f"\n📄 XML report generated: {xml_report}")
    
    print("=" * 80)
    
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Measure test coverage for Mantis Studio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/measure_coverage.py              # Basic coverage report
  python scripts/measure_coverage.py --html       # Generate HTML report
  python scripts/measure_coverage.py --all        # Generate all reports
        """
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "--xml",
        action="store_true",
        help="Generate XML coverage report (for CI)"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate all coverage reports"
    )
    
    parser.add_argument(
        "--no-missing",
        action="store_true",
        help="Don't show missing lines in terminal report"
    )
    
    args = parser.parse_args()
    
    # If --all is specified, enable all reports
    if args.all:
        args.html = True
        args.xml = True
    
    # If no report type specified, default to terminal only
    if not args.html and not args.xml:
        print("📊 Running tests with terminal coverage report")
        print("   (use --html for HTML report, --all for all reports)\n")
    
    # Run coverage
    exit_code = run_coverage(
        html=args.html,
        xml=args.xml,
        show_missing=not args.no_missing
    )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
