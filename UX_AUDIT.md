# UX Audit (User POV)

## Summary
The current app offers strong features but uses multiple navigation patterns and dense layouts that feel like a tool rather than a modern SaaS workspace. This audit identifies friction points, severity, and recommendations.

## Findings

### 1) Navigation duplication (High)
**Issue:** Sidebar radio nav, page-header profile button, and scattered “Go to” CTAs create multiple navigation systems that compete for user attention.
**Impact:** Users are unsure which navigation is canonical; account access appears in multiple places.
**Recommendation:** Consolidate into a single sidebar nav for primary routes, move account into a header menu, and keep legal only in footer.

### 2) Dashboard density + repeated content (High)
**Issue:** The dashboard mixes hero sections, pills, and cards that repeat the same information.
**Impact:** Visual noise and unclear hierarchy.
**Recommendation:** Emphasize one primary “Resume” area, 4–6 quick actions, and a clean recent projects list.

### 3) AI Settings UX inconsistency (High)
**Issue:** Provider configuration is split between tabs and multiple action rows; primary actions are not clearly grouped.
**Impact:** Users may miss save/refresh actions or model tests.
**Recommendation:** Use provider cards with clear “key → model → test” flow and a single action strip.

### 4) Account access is visually disconnected (Medium)
**Issue:** Account page looks different from main app and lacks a consistent header.
**Impact:** Feels like a different product, harder to return to the studio.
**Recommendation:** Apply the same design system and add a persistent “Back to Studio” CTA.

### 5) World Bible / Editor tool sprawl (Medium)
**Issue:** Many controls are stacked without clear grouping, which increases scanning time.
**Impact:** Users get lost in tools and may skip relevant actions.
**Recommendation:** Use a three-column editor layout (list/editor/tools) and tabbed World Bible sections.

### 6) Export and Legal discoverability (Low)
**Issue:** Export is visible in multiple places but legal is only in a subpage.
**Recommendation:** Keep export in sidebar nav and legal in footer to reduce clutter.

## Next Steps
- Implement unified sidebar navigation.
- Apply design system tokens and reusable cards.
- Rebuild pages with consistent header + content hierarchy.
