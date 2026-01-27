# MANTIS Studio — UX Comparison & Audit (User POV)

## Summary
This audit compares the current in-app flow to what users typically expect in a guest-first SaaS writing studio. It also lists prioritized fixes, severity, impact, effort, and exact file/function locations.

## User POV comparison list
| Area | Current behavior | Expected experience | Severity | Impact | Effort | File / Location |
| --- | --- | --- | --- | --- | --- | --- |
| Guest landing | Guest banner appears, but CTAs are inconsistent and sometimes say “Enable cloud save.” | Clear “Create account” + “Sign in” calls-to-action on the dashboard landing. | Medium | Conversion + clarity | Low | `Mantis_Studio.py` → `render_guest_banner`, sidebar guest card |
| Account access | Account page is functional but visually utilitarian; debug info unavailable. | Polished account access screen with clear benefits + guest safe path + debug mode for ops. | Medium | Trust + clarity | Medium | `pages/account.py`, `app/utils/auth.py` |
| Auth troubleshooting | No built-in visibility into `st.user` fields for debugging provider issues. | Toggleable debug panel showing `st.user` keys and selected `user_id`. | High | Login reliability | Low | `pages/account.py`, `Mantis_Studio.py`, `app/utils/auth.py` |
| Legal access | Legal is available but needs consistent “SaaS policy hub” layout with last-updated dates. | A fully designed legal hub with table of contents and support contact. | Medium | Trust + compliance | Low | `pages/legal.py` |
| User ID resolution | Session could fail when `email` is missing from provider payload. | Never block; resolve ID via email → preferred_username/upn → name → sub. | High | Access + data storage | Medium | `app/utils/auth.py`, `Mantis_Studio.py` |
| Auth configuration guidance | No centralized runbook; Cloud secrets setup is not documented end-to-end. | A clear setup/runbook with redirect URLs and common failure modes. | High | Ops + onboarding | Low | `docs/streamlit-auth-runbook.md`, README |

## Prioritized roadmap
1. **Fix auth user ID fallback chain** (High)
   - Update fallback logic and remove hard-fail paths.
   - Files: `app/utils/auth.py`, `Mantis_Studio.py`.

2. **Add DEBUG_AUTH mode** (High)
   - Expose `st.user` keys + chosen user_id on Account page.
   - Files: `pages/account.py`, `Mantis_Studio.py`.

3. **Guest-first onboarding refresh** (Medium)
   - Standardize CTAs and reduce friction for sign-in vs create account.
   - Files: `Mantis_Studio.py`, `app/utils/auth.py`.

4. **Account Access page polish** (Medium)
   - Provide stronger framing + trust messaging + clear provider buttons.
   - Files: `pages/account.py`, `app/utils/auth.py`.

5. **Legal hub polish + no-auth access** (Medium)
   - Keep Legal always accessible and consistent with theme.
   - Files: `pages/legal.py`, `app/ui/layout.py`.

6. **Secrets runbook + Cloud setup** (High)
   - Document Cloud secrets and failure modes.
   - Files: `docs/streamlit-auth-runbook.md`, `README.md`.
