# Changelog

All notable changes to Mantis Studio are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [90.7] - 2026-02-18

### Changed
- Refreshed documentation links and guidance so all referenced files and commands match the current repository layout.
- Updated contributor and testing docs to use direct `pip`/`pytest` workflows (no Makefile assumptions).

### Fixed
- Corrected stale internal links in docs.
- Corrected changelog historical notes that referenced removed files.

---

## [89.2] - 2026-02-12

### Added
- Production-grade repository structure.
- Modern Python packaging and test configuration via `pyproject.toml`.
- Consolidated documentation under `docs/`.

### Changed
- Simplified dependency management to a single `requirements.txt`.
- Improved project organization and documentation.

### Fixed
- Removed duplicate dependency files from legacy structure.

---

## [89.1] - 2026-02-11

### Changed
- Foundation release in the 89.x stabilization cycle.

---

## Version History Reference

- **90.x** - Documentation and maintenance improvements.
- **89.x** - Production infrastructure improvements.
- **88.x** - Debugging and troubleshooting framework.
- **87.x** - User experience enhancements.
- See [`../VERSION.txt`](../VERSION.txt) for the current version.
