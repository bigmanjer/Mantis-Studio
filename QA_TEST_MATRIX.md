# QA Test Matrix

## Phase 3.1 — Quarantine

| Page/Area | Action | Expected | Actual | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| App boots without error | `streamlit run Mantis_Studio.py --server.headless true --server.port 8501` | App starts and serves UI | App started; reachable at http://127.0.0.1:8501 | Pass | Headless Streamlit run.
| Dashboard renders | Click "Dashboard" nav item | Dashboard visible | Dashboard label clickable | Pass | Verified via Playwright click.
| Projects load/create | Click "Projects" nav item | Projects page visible | Projects label clickable | Pass | Verified via Playwright click.
| Outline page loads | Click "Outline" nav item | Outline visible | Outline label clickable | Pass | Verified via Playwright click.
| Chapters/Editor loads | Click "Editor" nav item | Editor visible | Editor label clickable | Pass | Label is "Editor" in nav.
| World Bible loads | Click "World Bible" nav item | World Bible visible | World Bible label clickable | Pass | Verified via Playwright click.
| Export page loads | Click "Export" nav item | Export visible | Export label clickable | Pass | Verified via Playwright click.
| AI Tools page loads | Click "AI Tools" nav item | AI Tools visible | AI Tools label clickable | Pass | Verified via Playwright click.
| Account/Auth access page loads | Navigate to `/Account_Settings` | Account page renders | Page loaded at `/Account_Settings` | Pass | Streamlit multipage route.
| Legal pages reachable via footer | Navigate to `/Legal_Center` | Legal page renders | Page loaded at `/Legal_Center` | Pass | Streamlit multipage route.
| Selftest (CLI) | `python scripts/smoke_test.py` | PASS | PASS | Pass | Selftest runs in CLI mode.
| Python compileall | `python -m compileall .` | No compile errors | No compile errors | Pass | Includes repo tree.

## Phase 3.2 — Delete verified-unused

| Page/Area | Action | Expected | Actual | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| App boots without error | `streamlit run Mantis_Studio.py --server.headless true --server.port 8501` | App starts and serves UI | App started; reachable at http://127.0.0.1:8501 | Pass | Headless Streamlit run. |
| Dashboard renders | Click "Dashboard" nav item | Dashboard visible | Dashboard label clickable | Pass | Verified via Playwright click. |
| Projects load/create | Click "Projects" nav item | Projects page visible | Projects label clickable | Pass | Verified via Playwright click. |
| Outline page loads | Click "Outline" nav item | Outline visible | Outline label clickable | Pass | Verified via Playwright click. |
| Chapters/Editor loads | Click "Editor" nav item | Editor visible | Editor label clickable | Pass | Label is "Editor" in nav. |
| World Bible loads | Click "World Bible" nav item | World Bible visible | World Bible label clickable | Pass | Verified via Playwright click. |
| Export page loads | Click "Export" nav item | Export visible | Export label clickable | Pass | Verified via Playwright click. |
| AI Tools page loads | Click "AI Tools" nav item | AI Tools visible | AI Tools label clickable | Pass | Verified via Playwright click. |
| Account/Auth access page loads | Navigate to `/Account_Settings` | Account page renders | Playwright browser crashed before loading URL | Fail (env) | Chromium SIGSEGV while launching second Playwright run. |
| Legal pages reachable via footer | Navigate to `/Legal_Center` | Legal page renders | Playwright browser crashed before loading URL | Fail (env) | Same Playwright crash as above. |
| Selftest (CLI) | `python scripts/smoke_test.py` | PASS | PASS | Pass | Selftest runs in CLI mode. |
| Python compileall | `python -m compileall .` | No compile errors | No compile errors | Pass | Includes repo tree. |

## Phase 3.3 — AI provider keys & export gating

| Page/Area | Action | Expected | Actual | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- |
| Guest: OpenAI session key | Paste OpenAI key in AI Settings → Use for this session → Generate outline | Outline generation runs | Not run (manual) | Pending | Requires valid OpenAI key. |
| Guest: Groq session key | Paste Groq key in AI Settings → Use for this session → Generate chapter | Chapter generation runs | Not run (manual) | Pending | Requires valid Groq key. |
| Guest: no key | Attempt generation without any key | Button disabled + “Add API key” message | Not run (manual) | Pending | Verify in Outline/Editor. |
| Guest: Export page | Navigate to Export page while signed out | Paywall card + Sign in button, no crash | Not run (manual) | Pending | Requires auth configured. |
| Logged-in: save OpenAI key | Save OpenAI key to account and rerun | Status shows “Using saved key” | Not run (manual) | Pending | Requires auth + key. |
| Logged-in: save Groq key | Save Groq key to account and rerun | Status shows “Using saved key” | Not run (manual) | Pending | Requires auth + key. |
| Clear session key | Clear session key then attempt generation | Generation disabled unless saved/default key | Not run (manual) | Pending | Validate fallback order. |
| Widget key stability | Use app normally | No StreamlitDuplicateElementKey | Not run (manual) | Pending | General smoke check. |
| App boots (Streamlit Cloud) | Deploy/run on Streamlit Cloud | No red error screens | Not run (manual) | Pending | Cloud environment verification. |
