# Changelog

All notable changes to Mantis Studio are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [91.6] - 2026-02-18

### Added
- ✨ **In-app "What's New" notification system**: Users now see a friendly notification banner when the app version updates
  - Shows key changes and improvements in each version
  - Includes direct link to full changelog
  - Dismissible with persistent memory of last seen version
  - Helps users understand what changed between updates
- 📊 Version tracking in user config to detect when app has been updated

### Changed
- 📝 Updated CHANGELOG.md to document all versions from 90.7 to 91.6
- 📖 Updated README.md to reflect current version (91.6) throughout documentation
- 🎯 Improved transparency about version changes and updates

### Fixed
- ❌ **Major UX Issue**: Users can now see what changed between versions
  - Previously, users reported "merged 4 times now with no changed from users point of view"
  - Version number was incrementing but changes were invisible to users
  - Now users get a clear notification when version changes
- 📚 Documentation version inconsistencies corrected

### Impact
This release directly addresses user feedback about version changes being invisible. Users will now be informed whenever the app updates, creating better awareness and transparency about ongoing improvements.

---

## [91.5] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [91.4] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [91.3] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [91.2] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [91.1] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [91.0] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [90.9] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

## [90.8] - 2026-02-18

### Changed
- Incremental improvements and bug fixes

---

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
