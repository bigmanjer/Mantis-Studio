#!/usr/bin/env python3
"""
Version Bumping Script for Mantis Studio

This script increments the version following the project's versioning rules:
- Increments minor version by 1 (e.g., 84.7 -> 84.8)
- When minor would reach 10, increment major and reset minor to 0 (84.9 -> 85.0)
- Versions can be MAJOR.MINOR or MAJOR.MINOR.PATCH; patch is ignored

Usage:
    python scripts/bump_version.py
"""

import sys
from pathlib import Path


def bump_version(current_version: str) -> str:
    """
    Bump version according to Mantis Studio rules.
    
    Args:
        current_version: Current version string (e.g., "84.7")
    
    Returns:
        New version string (e.g., "84.8")
    """
    try:
        parts = current_version.strip().split('.')
        if len(parts) not in (2, 3):
            raise ValueError(
                f"Invalid version format: {current_version} "
                "(expected MAJOR.MINOR or MAJOR.MINOR.PATCH)"
            )

        major = int(parts[0])
        minor = int(parts[1])
        if len(parts) == 3:
            _patch = int(parts[2])  # validate patch component if present

        # Increment minor by 1 (e.g., version x.y becomes x.(y+1)).
        minor += 1
        if minor >= 10:
            major += 1
            minor = 0

        return f"{major}.{minor}"
    
    except (ValueError, IndexError) as e:
        print(f"Error parsing version '{current_version}': {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point for version bumping."""
    # Find VERSION.txt relative to this script
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    version_file = repo_root / "VERSION.txt"
    
    if not version_file.exists():
        print(f"Error: VERSION.txt not found at {version_file}", file=sys.stderr)
        sys.exit(1)
    
    # Read current version
    try:
        current_version = version_file.read_text(encoding='utf-8').strip()
        print(f"Current version: {current_version}")
    except Exception as e:
        print(f"Error reading VERSION.txt: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Calculate new version
    new_version = bump_version(current_version)
    print(f"New version: {new_version}")
    
    # Write new version
    try:
        version_file.write_text(new_version + "\n", encoding='utf-8')
        print(f"✅ Version bumped: {current_version} → {new_version}")
    except Exception as e:
        print(f"Error writing VERSION.txt: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
