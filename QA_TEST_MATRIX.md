# QA Test Matrix

| Page | Button/Control | Expected | Actual (Before) | Fix Applied | Actual (After) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| Dashboard | Primary CTA (Start/Continue) | Opens the correct workspace page and loads the latest project when available. | Reported to route inconsistently when project missing. | Fixed account/legal routing + verified CTA navigation. | Primary CTA routed to the expected module in guest mode. | Click-tested in guest mode. |
| Dashboard | "➕ New project" | Routes to Projects screen. | Reported to route inconsistently. | Verified rerun + navigation on click. | Routes to Projects immediately. | Click-tested. |
| Dashboard | Quick action cards (Editor/Outline/World Bible/Memory/Insights/Export) | Each card routes to the intended module (with Memory/Insights tabs set). | Mixed reports of “no action.” | Confirmed navigation + tab focus logic; fixed account/legal routes. | All quick action cards route correctly, Memory/Insights land on World Bible. | Click-tested via Open/Export buttons. |
| Projects | "Open latest project" | Opens most recent project in Chapters editor. | Not available when no projects exist. | None. | Opens latest project and lands in Editor. | Click-tested after creating a guest sandbox. |
| Outline | Navigation radio (Outline) | Opens Outline module for active project. | No issue observed. | None. | Outline loads with active project content. |  |
| Chapters/Editor | "Resume project" (Dashboard) | Opens Chapter editor for active project. | Disabled when no recent project exists. | None. | Remains disabled until a project is available. | Verified disabled state is intentional. |
| World Bible | Tabs (Entities / Memory / Insights) | Each tab loads without errors and maintains state. | Memory/Insights were reachable but tab focus sometimes reset. | Ensured tab focus routing stays intact. | Tabs switch and retain focus. |  |
| Export | "Export" quick action | Opens Export screen with selected project path. | Export page sometimes opened without project path. | Confirmed export routing preserves project path when available. | Export view opens with project selection or prompts to select. |  |
| AI Tools | "⚙️ AI Settings" | Opens AI Tools screen. | No issue observed. | None. | AI Tools screen opens; Save/Refresh actions available. |  |
| Account access | "👤 Profile & settings" (header) | Opens Account Settings page (or prompts guest login). | Account access lived in sidebar; routing used missing page path. | Moved to header shortcut + fixed switch_page path. | Header button opens Account Settings; guest sees login screen. |  |
| Account page | Email sign-in form | Allows entering email and starting passwordless sign-in with cooldown. | No email sign-in path. | Added email sign-in flow with cooldown. | Email input renders; send button enabled only with configured provider. | Cooldown messaging shown after send. |
| Footer | Privacy button | Routes to privacy content. | Footer used HTML links that did not navigate. | Replaced with footer buttons + query param routing. | Privacy content loads via query param. | Click-tested. |
| Footer | Terms button | Routes to terms content. | Footer used HTML links that did not navigate. | Replaced with footer buttons + query param routing. | Terms content loads via query param. | Click-tested. |
| Footer | Legal hub button | Opens Legal Center page. | Linked to missing /pages/legal.py path. | Updated footer routing + redirect handling. | Legal Center opens at /Legal_Center. | Click-tested. |

## How to verify locally

- Run the app: `python -m streamlit run Mantis_Studio.py`
- From the dashboard, click each CTA (Start/Continue, New project, Editor/Outline/World Bible/Memory/Insights/Export).
- Open Projects, Outline, Chapters/Editor, World Bible tabs, Export, and AI Tools using the sidebar navigation.
- Click the header "👤 Profile & settings" button and confirm Account Settings loads without errors in guest mode.
- In Account Settings, use the Email sign-in form and verify the resend cooldown message appears.
- Scroll to the footer and confirm Privacy, Terms, and Legal buttons route correctly.
