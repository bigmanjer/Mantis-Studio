#!/usr/bin/env python3
"""
Version Bumping Script for Mantis Studio

This script increments the version following the project's versioning rules:
- Increments patch version by 1 (e.g., 84.7.1 -> 84.7.2)
- Versions can be MAJOR.MINOR or MAJOR.MINOR.PATCH; patch defaults to 0

Usage:
    python scripts/bump_version.py
"""

import sys
from pathlib import Path


def bump_version(current_version: str) -> str:
    """
    Bump version according to Mantis Studio rules.
    
    Args:
        current_version: Current version string (e.g., "84.7.1")
    
    Returns:
        New version string (e.g., "84.7.2")
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
        patch = int(parts[2]) if len(parts) == 3 else 0

        # Increment patch by 1 (e.g., version x.y.1 becomes x.y.2)
        patch += 1

        return f"{major}.{minor}.{patch}"
    
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
