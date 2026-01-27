# QA Test Matrix

> **Note:** This matrix reflects a static click-path review (code-level) in this environment. Runtime verification still requires a live Streamlit session with valid API keys and Supabase credentials.

| Page | Control/Button label | Expected behavior | Actual behavior (static review) | Status (PASS/FAIL) | Fix commit reference / file + line |
| --- | --- | --- | --- | --- | --- |
| Dashboard/Home | Primary CTA (Start/Continue/Fix) | Opens recent project and routes to Projects/Outline/Chapters/World | Routes via `open_primary_cta()` → `open_recent_project()` with rerun | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | 📂 Resume project | Loads recent project and routes to Chapters | `open_recent_project("chapters")` triggers load + rerun | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | 🧭 New project | Routes to Projects | Sets `page = "projects"` + rerun | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Learn more | Opens Legal Center | Calls `open_legal_page()` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: ✍️ Editor | Routes to Chapters | Calls `open_recent_project("chapters")` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: 📝 Outline | Routes to Outline | Calls `open_recent_project("outline")` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: 🌍 World Bible | Routes to World Bible | Calls `open_recent_project("world")` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: 🧠 Memory | Routes to World Bible with Memory tab | Sets `world_focus_tab` + routes to `world` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: 📊 Insights | Routes to World Bible with Insights tab | Sets `world_focus_tab` + routes to `world` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Quick Action: ⬇️ Export | Routes to Export or Account gate | Uses `open_export()` with guest gating | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Project list “📂 {title}” | Loads project and routes to Chapters | Loads project then sets `page = "chapters"` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | Project list “Open” | Loads project and routes to Chapters | Loads project then sets `page = "chapters"` | PASS | Mantis_Studio.py (render_home) |
| Dashboard/Home | ⚙️ AI Settings | Routes to AI Tools | `open_ai_settings()` sets `page = "ai"` + rerun | PASS | Mantis_Studio.py (render_home) |
| Sidebar | Navigation radio | Updates page route | Sets `page` based on nav map, reruns | PASS | Mantis_Studio.py (sidebar nav) |
| Sidebar | 💾 Save | Saves active project | Calls `persist_project()` | PASS | Mantis_Studio.py (sidebar) |
| Sidebar | ✖ Close | Closes project and routes Home | Clears `project`, sets `page = "home"` + rerun | PASS | Mantis_Studio.py (sidebar) |
| Projects | Start guest sandbox | Creates guest project and routes to Outline | Creates project, sets `page = "outline"` | PASS | Mantis_Studio.py (render_projects) |
| Projects | Import & Analyze | Imports text, optionally AI outline, routes to Outline | Creates project + outline, routes to Outline | PASS | Mantis_Studio.py (render_projects) |
| Projects | Project tile “📂 {title}” | Loads project and routes to Chapters | Loads project + `page = "chapters"` | PASS | Mantis_Studio.py (render_projects) |
| Projects | Project tile “Open” | Loads project and routes to Chapters | Loads project + `page = "chapters"` | PASS | Mantis_Studio.py (render_projects) |
| Projects | ⬇️ Export | Routes to Export with selected project | Sets export path + `page = "export"` | PASS | Mantis_Studio.py (render_projects) |
| Projects | 🗑 (delete) | Opens delete confirmation | Sets delete state for confirm | PASS | Mantis_Studio.py (render_projects) |
| Projects | 🗑 Confirm delete | Deletes project + refreshes | Deletes file + refresh token | PASS | Mantis_Studio.py (render_projects) |
| Projects | Cancel (delete) | Closes delete confirmation | Clears delete state | PASS | Mantis_Studio.py (render_projects) |
| Projects | Close export | Closes export modal | Clears export path | PASS | Mantis_Studio.py (render_projects) |
| Outline | 💾 Save Project | Saves project metadata | Calls `persist_project()` | PASS | Mantis_Studio.py (render_outline) |
| Outline | 💾 Save Outline | Saves outline + entity scan | Saves and runs `extract_entities_ui()` | PASS | Mantis_Studio.py (render_outline) |
| Outline | ✨ Generate Structure | Generates outline via AI | Calls `StoryEngine.generate_outline()` | PASS | Mantis_Studio.py (render_outline) |
| Outline | 🔍 Scan entities | Scans entities from outline | Calls `extract_entities_ui()` | PASS | Mantis_Studio.py (render_outline) |
| Outline | Go to Projects (empty state) | Routes to Projects | Sets `page = "projects"` + rerun | PASS | Mantis_Studio.py (render_outline) |
| Outline | Start guest sandbox | Creates guest project + routes to Outline | Creates guest project + rerun | PASS | Mantis_Studio.py (render_outline) |
| Editor | ➕ Create Chapter 1 | Adds chapter and reruns | Adds chapter + `persist_project()` + rerun | PASS | Mantis_Studio.py (render_chapters) |
| Editor | 🧩 Go to Outline | Routes to Outline | Sets `page = "outline"` + rerun | PASS | Mantis_Studio.py (render_chapters) |
| Editor | Chapter list buttons | Select chapter | Updates `curr_chap_id` + rerun | PASS | Mantis_Studio.py (render_chapters) |
| Editor | ➕ New Chapter | Adds new chapter | Adds chapter + saves + rerun | PASS | Mantis_Studio.py (render_chapters) |
| Editor | 💾 Save Chapter | Saves chapter + entity scan | Updates chapter + scan + toast | PASS | Mantis_Studio.py (render_chapters) |
| Editor | 📝 Update Summary | Updates summary via AI | Calls AI summarizer; reruns on success | PASS | Mantis_Studio.py (render_chapters) |
| Editor | ✨ Improve / Rewrite / Auto-Write actions | Runs AI operations | Calls AI engines; updates pending text | PASS | Mantis_Studio.py (render_chapters) |
| Editor | Apply Changes | Applies improved text | Updates chapter and reruns | PASS | Mantis_Studio.py (render_chapters) |
| Editor | Regenerate | Regenerates AI improvement | Re-runs improvement, reruns | PASS | Mantis_Studio.py (render_chapters) |
| Editor | Discard | Clears improvement state | Clears pending state + rerun | PASS | Mantis_Studio.py (render_chapters) |
| World Bible | ➕ Add {Category} | Opens add form | Sets `add_open_{category}` | PASS | Mantis_Studio.py (render_world) |
| World Bible | ✅ Apply (suggestion) | Applies AI suggestion | Applies update + removes from queue | PASS | Mantis_Studio.py (render_world) |
| World Bible | 🗑 Ignore (suggestion) | Dismisses suggestion | Removes from queue | PASS | Mantis_Studio.py (render_world) |
| World Bible | 📖 Jump to Chapter | Routes to Editor | Sets `page = "chapters"` + `_force_nav` | PASS | Mantis_Studio.py (render_world) |
| World Bible | 🗑 Delete entity | Deletes entity | Removes entity or opens confirm | PASS | Mantis_Studio.py (render_world) |
| World Bible | 💾 Save Memory | Saves memory rules | Updates memory and saves | PASS | Mantis_Studio.py (render_world) |
| World Bible | 🔍 Run Coherence Check | Runs coherence check | Calls AI check and stores results | PASS | Mantis_Studio.py (render_world) |
| World Bible | Jump to Entity | Focuses entity | Sets `world_focus_entity` + search | PASS | Mantis_Studio.py (render_world) |
| Export | Go to Projects | Routes to Projects | Sets `page = "projects"` + rerun | PASS | Mantis_Studio.py (render_export) |
| Export | Start guest sandbox | Creates guest project + routes to Outline | Creates guest project + rerun | PASS | Mantis_Studio.py (render_export) |
| Export | Export (MD/PDF/DOCX/ZIP) | Generates downloadable export | Creates export in memory | PASS | Mantis_Studio.py (render_export) |
| Export | Close export | Clears export state | Clears `export_project_path` | PASS | Mantis_Studio.py (render_export) |
| AI Settings | Use for this session | Saves session key + clears input | Uses queued widget reset + rerun | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | Clear session key | Clears session key | Clears key + toast | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | Save to my account | Saves key to profile + clears input | Uses queued widget reset + rerun | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | ↻ Fetch OpenAI Models | Fetches models list | Calls `fetch_openai_models()` | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | 🔌 Test OpenAI Connection | Tests OpenAI | Calls `test_openai_connection()` | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | 🧪 Test All OpenAI Models | Tests each model | Calls `test_openai_model()` per model | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | ↻ Fetch Groq Models | Fetches models list | Calls `refresh_models()` | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | 🔌 Test Groq Connection | Tests Groq | Calls `test_groq_connection()` | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | 🧪 Test All Groq Models | Tests each model | Calls `test_groq_model()` per model | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | ↻ Refresh Groq/OpenAI Models | Refreshes model cache | Clears cache + refreshes | PASS | Mantis_Studio.py (render_ai_settings) |
| AI Settings | 💾 Save AI Settings | Saves app settings | Calls `save_app_settings()` with auth check | PASS | Mantis_Studio.py (render_ai_settings) |
| Account (in-shell) | Sign in / Create account | Routes to Account Settings page | Uses `request_account_access()` | PASS | Mantis_Studio.py (render_account) |
| Account (in-shell) | 👤 Profile & settings | Routes to Account Settings page | Calls `open_account_settings()` | PASS | Mantis_Studio.py (render_account) |
| Account Settings | Log in | Authenticates user | Calls `auth.auth_login()` + rerun | PASS | pages/Account Settings.py |
| Account Settings | Create account | Creates user | Calls `auth.auth_signup()` + rerun | PASS | pages/Account Settings.py |
| Account Settings | Send reset link | Requests password reset | Calls `auth.auth_request_password_reset()` | PASS | pages/Account Settings.py |
| Account Settings | Save profile | Updates profile | Calls `auth.update_profile()` | PASS | pages/Account Settings.py |
| Account Settings | Log out | Clears session | Calls `auth.logout_button()` | PASS | pages/Account Settings.py |
| Legal Center | ⬅ Back to Studio (top/footer) | Returns to Studio home | Sets `page = "home"` or `switch_page` | PASS | pages/Legal Center.py |
| Legal Center | Section nav | Scrolls to section | Uses navigation state in legal hub | PASS | pages/Legal Center.py |
| Footer | Terms / Privacy / Legal | Updates query params | Sets `st.query_params["page"]` and reruns | PASS | app/ui/layout.py |
