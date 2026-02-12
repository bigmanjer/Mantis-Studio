# MANTIS Studio — UX Audit

## Summary
This audit reviews the current in-app flow and lists prioritized UX improvements with severity, impact, effort, and file locations.

## UX comparison
| Area | Current behavior | Expected experience | Severity | Impact | Effort | File / Location |
| --- | --- | --- | --- | --- | --- | --- |
| Legal access | All Policies displays all policy documents in expandable sections. | Consistent layout with all policies visible and navigable. | Medium | Trust + compliance | Low | `app/main.py` → `render_legal_redirect` |
| Footer navigation | Footer links navigate to Terms, Privacy, and All Policies pages. | All footer links navigate to valid, content-rich destinations. | Medium | Trust + usability | Low | `app/ui/layout.py` → `render_footer` |
| Dashboard onboarding | Dashboard shows project overview with first-time welcome. | Clear getting-started instructions and quick tips for navigation. | Medium | Clarity | Low | `app/main.py` → `render_home` |

## Prioritized roadmap

1. **All Policies polish** (Medium)
   - Display all policy documents in an organized layout.
   - Files: `app/main.py` → `render_legal_redirect`, `app/ui/layout.py`.

2. **Dashboard onboarding improvements** (Medium)
   - Better first-time user experience with clear next steps.
   - Files: `app/main.py` → `render_home`.

3. **Footer link consistency** (Medium)
   - Ensure all footer links lead to real, content-rich pages.
   - Files: `app/ui/layout.py` → `render_footer`.
