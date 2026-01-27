# Tree Refactor Plan (Deferred)

## Goal
Organize the repo into clear folders without breaking routing, imports, or JSON data formats.

## Proposed Plan
1. **Inventory entry points**
   - Confirm `Mantis_Studio.py` is the primary Streamlit entry.
   - Confirm secondary multipage files in `pages/` are referenced via `st.switch_page`.
2. **Stabilize imports**
   - Move any non-core scripts into `scripts/` (if not already).
   - Keep `app/` for UI + utility modules and `mantis/` for runtime services.
3. **Assets + Legal**
   - Keep `assets/` and `legal/` at repo root since they are referenced by absolute paths.
4. **Data separation**
   - Ensure `projects/` and runtime data directories are excluded or documented for local use only.

## Why deferred
- Refactoring paths risks breaking Streamlit `st.switch_page()` routes and asset lookups.
- Requires a full interactive pass to validate multipage routing and asset loading.

## Next Steps
- Perform refactor only after a full UI run with screenshots on each page.
- Add a migration checklist for any path changes.
