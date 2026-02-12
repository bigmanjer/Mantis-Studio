# MANTIS Design System

## Color Palette
- **Primary (Mantis Green):** `#22c55e`
- **Primary Dark:** `#16a34a`
- **Secondary Accent (Blue/Teal):** `#38bdf8`
- **Background:** `#050b0f`
- **Surface:** `#0b141a`
- **Surface Alt:** `#0f1c24`
- **Border:** `rgba(148, 163, 184, 0.15)`
- **Text:** `#e2e8f0`
- **Muted Text:** `rgba(226, 232, 240, 0.7)`

## Typography
- **H1:** 30–34px, 700 weight
- **H2:** 20–24px, 600 weight
- **Body:** 14–16px, 400–500 weight

## Components
- **Cards:** soft shadow, rounded 16–18px, dark surface.
- **CTA Tiles:** compact cards used for quick actions.
- **Pills:** rounded badges for status/role.

## Buttons
- **Primary:** green gradient / solid, `type="primary"` in Streamlit
- **Secondary:** neutral outline, `type="secondary"`
- **Destructive:** red emphasis (use `st.button` + error toast)

## Layout Rules
- 8px spacing grid
- Use 2–3 column layouts for dashboards
- Use 3-column layout for Editor (list / editor / tools)

## CSS Injection
Centralized in `app/ui/theme.py` using `inject_theme()`.

---

## Information Architecture + Navigation

### Primary Navigation (Sidebar)
- **Dashboard** → `page="home"`
- **Projects** → `page="projects"`
- **Write (Outline)** → `page="outline"`
- **Editor** → `page="chapters"`
- **World Bible** → `page="world"`
- **Export** → `page="export"`
- **AI Settings** → `page="ai"`

### Secondary Navigation (Header)
- **App title + logo** (left)
- **Current project selector** (center)
  - Loads selected project and routes to `chapters`.
- **Quick actions** (contextual per page)

### Footer Navigation
- **Terms** → `page="terms"` (renders `legal/terms.md`)
- **Privacy** → `page="privacy"` (renders `legal/privacy.md`)
- **Legal** → `page="legal"` (All Policies)
- **Support** → external link to GitHub Issues
- **Contact** → mailto link
- **Version** → displays current app version

### Page Rendering Map
- `home` → Dashboard / Home
- `projects` → Projects
- `outline` → Outline (Write)
- `chapters` → Editor (Write)
- `world` → World Bible
- `export` → Export
- `ai` → AI Settings
- `legal` → All Policies
- `terms` → Terms of Service
- `privacy` → Privacy Policy
- `copyright` → Copyright Notice
- `cookie` → Cookie Policy

### Header Actions by Page
- **Dashboard:** Resume project, New project
- **Projects:** Create project, Import
- **Outline:** Save outline, Generate outline, Scan entities
- **Editor:** Save chapter, Update summary
- **World Bible:** Add entity, Run coherence check
- **Export:** Export current project
- **AI Settings:** Save settings, Refresh models

---

## Footer Design Spec

### Footer Layout

The footer uses a four-column grid layout with clear section hierarchy,
a "Back to top" pill, and a separated bottom bar for copyright and social links:

```
┌──────────────────────────────────────────────────────────────────┐
│                                            ↑ Back to top        │
│                                                                  │
│  MANTIS Studio          Navigation      All Policies   Support  │
│  Modular narrative      Dashboard       Terms of       ℹ Help   │
│  workspace              Projects        Service        Report   │
│                         Outline         Privacy         an Issue│
│                         Export          Policy          ✉ Contact│
│                                        All Policies             │
│                                                                  │
│─────────────────────────────────────────────────────────────────│
│  © 2025 MANTIS Studio · v{version}                     GitHub   │
└──────────────────────────────────────────────────────────────────┘
```

### Footer Section Order

| # | Section         | Content                                        |
|---|-----------------|------------------------------------------------|
| 1 | Brand/Copyright | App name, tagline (copyright moved to bottom)  |
| 2 | Navigation      | Dashboard, Projects, Outline, Export            |
| 3 | All Policies    | Terms of Service, Privacy Policy, All Policies  |
| 4 | Support         | Help, Report an Issue (GitHub), Contact (email) |

### Responsive Behavior

| Breakpoint  | Layout                              |
|-------------|-------------------------------------|
| > 768px     | 4-column grid (1.6fr 1fr 1fr 1fr)  |
| 481–768px   | 2-column grid                       |
| ≤ 480px     | Single-column stack, centered bottom|

### Footer Accessibility

- `<footer>` element with `role="contentinfo"` and `aria-label="Site footer"`
- Each link section uses `<nav>` with a descriptive `aria-label`
- Section headings use `<h4>` for proper heading hierarchy
- All links support keyboard focus with visible `:focus-visible` outlines
- External links include `target="_blank"` with `rel="noopener noreferrer"`
- `mailto:` links used for contact (no placeholder emails)
- "Back to top" button has `aria-label="Back to top"`
- External links display a visible arrow indicator (↗)

### Footer UX Enhancements

- **Back to top** pill in upper-right corner of the footer
- **Link hover underline** animation (transparent → accent border-bottom)
- **Section heading accent** color with bottom border separator
- **Subtle surface background** to visually separate footer from content
- **Bottom bar** separates copyright/version from main grid
- **GitHub link** in bottom bar for quick access
- **Icons** on Help (ℹ) and Contact (✉) links for visual scanning
- **External link indicator** (↗) on "Report an Issue"

### Footer Link Mapping

| Label            | Destination                                          | Type      |
|------------------|------------------------------------------------------|-----------|
| Dashboard        | `?page=home`                                         | Internal  |
| Projects         | `?page=projects`                                     | Internal  |
| Outline          | `?page=outline`                                      | Internal  |
| Export           | `?page=export`                                       | Internal  |
| Terms of Service | `?page=terms`                                        | Internal  |
| Privacy Policy   | `?page=privacy`                                      | Internal  |
| All Policies     | `?page=legal`                                        | Internal  |
| Help             | `?page=help`                                         | Internal  |
| Report an Issue  | https://github.com/bigmanjer/Mantis-Studio/issues    | External  |
| Contact          | mailto:support@mantis-studio.example                 | Email     |
| GitHub           | https://github.com/bigmanjer/Mantis-Studio/issues    | External  |

### Footer Styling

- Surface alt background for visual separation from page content
- Top border: 1px solid, uses `--mantis-divider` CSS variable
- Section headings: `Space Grotesk`, uppercase, accent-colored, with bottom border
- Links: inherit text color, green accent + underline on hover
- Focus rings: 2px solid accent color
- Max width: 960px, centered
- Bottom bar: separated by top border, flexbox with wrap
- "Back to top" pill: rounded, subtle border, accent on hover
- Consistent with existing Mantis theme tokens

### Footer Pages Added

| Page  | Route          | Content Source       |
|-------|----------------|----------------------|
| Help  | `?page=help`   | `legal/help.md`      |

---

## UX Audit

### Summary
This audit reviews the current in-app flow and lists prioritized UX improvements with severity, impact, effort, and file locations.

### UX Comparison
| Area | Current behavior | Expected experience | Severity | Impact | Effort | File / Location |
| --- | --- | --- | --- | --- | --- | --- |
| Legal access | All Policies displays all policy documents in expandable sections. | Consistent layout with all policies visible and navigable. | Medium | Trust + compliance | Low | `app/main.py` → `render_legal_redirect` |
| Footer navigation | Footer links navigate to Terms, Privacy, and All Policies pages. | All footer links navigate to valid, content-rich destinations. | Medium | Trust + usability | Low | `app/ui/layout.py` → `render_footer` |
| Dashboard onboarding | Dashboard shows project overview with first-time welcome. | Clear getting-started instructions and quick tips for navigation. | Medium | Clarity | Low | `app/main.py` → `render_home` |

### Prioritized Roadmap

1. **All Policies polish** (Medium)
   - Display all policy documents in an organized layout.
   - Files: `app/main.py` → `render_legal_redirect`, `app/ui/layout.py`.

2. **Dashboard onboarding improvements** (Medium)
   - Better first-time user experience with clear next steps.
   - Files: `app/main.py` → `render_home`.

3. **Footer link consistency** (Medium)
   - Ensure all footer links lead to real, content-rich pages.
   - Files: `app/ui/layout.py` → `render_footer`.
