# App Architecture

`app/main.py` is the canonical Streamlit runtime entry point.

## Current Structure

```text
app/
+-- main.py                 # Canonical app runtime
+-- router.py               # Page routing + render fallback
+-- session_init.py         # Session state bootstrap
+-- state.py                # Key helpers + compatibility state wrapper
+-- app_context.py          # Legacy compatibility module (still used by tests)
+-- ui_context.py           # Shared UI context helper class
+-- config/
¦   +-- settings.py         # App config + persistent config load/save
+-- services/
¦   +-- ai.py
¦   +-- export.py
¦   +-- projects.py
¦   +-- storage.py
¦   +-- world_bible.py
¦   +-- world_bible_db.py
¦   +-- world_bible_merge.py
+-- views/                  # Render wrappers used by router
+-- layout/                 # App shell elements (header/sidebar/footer)
+-- components/             # Reusable UI controls
+-- ui/                     # Theme/design-system and shared UI building blocks
+-- utils/
¦   +-- auth.py
¦   +-- branding_assets.py
¦   +-- helpers.py
¦   +-- keys.py
¦   +-- navigation.py       # Canonical navigation definitions
¦   +-- versioning.py
+-- models/
```

## Cleanup Notes

- `router.get_nav_config()` now delegates to `app.utils.navigation.get_nav_config()` to avoid duplicate nav mapping logic.
- Thin duplicate view wrappers that were not used by runtime routing were removed.
- Placeholder modules with no implementation were removed.
- Generated caches are intentionally excluded from source control.

## Runtime Entry Policy

- Preferred local run command: `streamlit run app/main.py`
- Deployment shim: `streamlit_app.py` (minimal compatibility launcher that calls `app.main._run_ui`)
