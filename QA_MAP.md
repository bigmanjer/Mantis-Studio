# QA Map — Page + Navigation Inventory

This document inventories the Streamlit UI surface for MANTIS Studio, including page render functions, navigation actions, and session_state usage.

## Page Render Functions

### Mantis_Studio.py (single-app shell)
- `render_home()` — Dashboard/Home
- `render_projects()` — Projects hub
- `render_outline()` — Outline page
- `render_chapters()` — Chapters/Editor
- `render_world()` — World Bible + Memory + Insights
- `render_export()` — Export page
- `render_ai_settings()` — AI Tools / AI Settings
- `render_account()` — Account Access (guest-only in-shell)
- `render_legal_redirect()` — Legal redirect panel
- Query-param pages: `render_privacy()`, `render_terms()`, `render_copyright()`

### pages/Account Settings.py (Streamlit multipage)
- `_render_login_ui()` — Login / Signup / Password reset
- `_render_settings_ui()` — Profile update + account tools

### pages/Legal Center.py (Streamlit multipage)
- Legal Hub UI composed from `SECTIONS` and markdown content

## Navigation Actions (Expected Destinations)

> **Legend:** “Destination” is the page or action expected after clicking.

### Global / Sidebar
- Sidebar radio (Navigation) → updates `st.session_state.page` to the mapped destination (Dashboard/Projects/Outline/Editor/World/Memory/Insights/Export/Legal/Account).
- Sidebar “Save” → save active project.
- Sidebar “Close” → returns to Dashboard (`page = "home"`).

### Dashboard/Home
- Primary CTA (“Start your story” / “Continue Chapter …” / “Fix story issues”) → Opens recent project and routes to Projects/Outline/Chapters/World.
- “Resume project” → Loads latest project and routes to Chapters.
- “New project” → Routes to Projects.
- “Editor / Outline / World Bible / Memory / Insights” action cards → Routes to `chapters`, `outline`, or `world` (with tab focus for Memory/Insights).
- “Export” action card → Routes to Export (guest users get Account Access gate).
- “Open” buttons in project list → Loads project and routes to Chapters.
- “AI Settings” utility CTA → Routes to AI Tools.

### Projects
- “Start guest sandbox” → Creates guest project and routes to Outline.
- “Import & Analyze” → Creates project from text and routes to Outline.
- “Open” / project tile buttons → Loads project and routes to Chapters.
- “Export” → Routes to Export with selected project.
- “Delete” / confirm delete → Removes project and refreshes list.

### Outline
- “Save Project” → Saves project metadata.
- “Save Outline” → Saves outline + scans entities.
- “Generate Structure” → Creates outline via AI.
- “Scan entities” → Extracts entities from outline.
- “Go to Projects” (empty state) → Routes to Projects.
- “Start guest sandbox” (guest CTA) → Routes to Outline after creating guest project.

### Chapters/Editor
- Header “New Chapter” → Adds chapter and remains in Editor.
- Header “Go to outline” → Routes to Outline.
- Chapter list buttons → Selects chapter.
- “Save Chapter” → Saves chapter + entity scan.
- “Update Summary” → Updates chapter summary.
- “Auto-Write / Improve / Rewrite” actions → AI actions, stays on Editor.
- “Apply Changes / Discard / Regenerate” → Applies improvements and reruns.

### World Bible
- “Add {Category}” → Opens add form.
- “Apply / Ignore” AI review queue items → Applies update or dismisses suggestion.
- “Jump to Chapter” → Routes to Editor (with chapter focus).
- “Delete” / Confirm delete → Removes entity.
- “Save Memory” → Saves memory rules.
- “Run Coherence Check” → Runs consistency checks.
- “Jump to Entity” → Focuses entity and routes to World.

### Export
- “Export” (markdown/PDF/DOCX/ZIP) → Generates download.
- “Close export” → Clears export panel.
- “Go to Projects” → Routes to Projects.
- “Start guest sandbox” → Creates guest project and routes to Outline.

### AI Tools / AI Settings
- “Use for this session” → Saves session key + clears input.
- “Clear session key” → Removes session key.
- “Save to my account” → Saves key to user profile.
- “Fetch models / Test connection / Test all models” → Fetches / validates models.
- “Save AI Settings” → Saves configuration.
- “Refresh models” → Refreshes model list.

### Account Access (Mantis_Studio)
- “Profile & settings” → Routes to Account Settings (multipage).
- “Sign in / Create account” → Routes to Account Settings (multipage).
- “Open Account Access” (auth UI) → Routes to Account Settings.

### Legal
- “Open Legal Hub” → Routes to Legal Center (multipage).
- Footer “Terms / Privacy / Legal” → Updates query params to render legal content.

## Session State Inventory (Key Usage)

### Core initialized keys (Mantis_Studio.py)
- `user_id`, `projects_dir`, `project`, `page`, `auto_save`, `ghost_text`, `pending_improvement_text`, `pending_improvement_meta`
- `chapter_text_prev`, `chapter_drafts`, `editor_improve__copy_buffer`, `first_run`, `is_premium`
- `guest_mode`, `pending_action`, `guest_project`, `guest_session_id`
- `openai_base_url`, `openai_key_input`, `openai_model`, `openai_model_list`, `openai_model_tests`
- `groq_base_url`, `groq_key_input`, `groq_model`, `groq_model_list`, `groq_model_tests`
- `ai_provider`, `ai_session_keys`, `ai_saved_keys_cache`, `ai_saved_keys_user_id`
- `ui_theme`, `daily_word_goal`, `weekly_sessions_goal`, `focus_minutes`
- `activity_log`, `projects_refresh_token`, `delete_project_path`, `delete_project_title`
- `delete_entity_id`, `delete_entity_name`, `export_project_path`
- `world_search`, `world_search_pending`, `world_focus_entity`, `world_focus_tab`, `world_tabs`, `world_bible_review`
- `last_entity_scan`, `locked_chapters`, `canon_health_log`
- `_chapter_sync_id`, `_chapter_sync_text`, `_outline_sync`, `out_txt_project_id`, `curr_chap_id`
- `_force_nav`
- Debug keys: `debug`, `last_action`, `last_action_ts`, `last_exception`
- Pending widget updates: `_pending_widget_updates`

### Dynamic/patterned keys
- `ed_{chapter_id}` — editor text areas per chapter
- `n_{chapter_id}` — chapter navigation buttons
- `apply_suggestion_{idx}`, `ignore_suggestion_{idx}` — World Bible AI review actions
- `coh_apply_{idx}`, `coh_ignore_{idx}` — Coherence fix actions
- `jump_{entity_id}`, `del_{entity_id}` — entity nav/actions
- `open_{project_path}`, `export_{project_path}`, `del_{project_path}` — project list actions
- `apply_suggestion_{idx}` — apply suggestion actions
- `world_filter_*` — World Bible filters
- `editor_improve__*` — editor improvement actions per chapter

