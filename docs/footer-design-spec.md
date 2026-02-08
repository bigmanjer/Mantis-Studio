# MANTIS Studio — Footer Design Spec

## Layout

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

## Section Order

| # | Section         | Content                                        |
|---|-----------------|------------------------------------------------|
| 1 | Brand/Copyright | App name, tagline (copyright moved to bottom)  |
| 2 | Navigation      | Dashboard, Projects, Outline, Export            |
| 3 | All Policies    | Terms of Service, Privacy Policy, All Policies  |
| 4 | Support         | Help, Report an Issue (GitHub), Contact (email) |

## Responsive Behavior

| Breakpoint  | Layout                              |
|-------------|-------------------------------------|
| > 768px     | 4-column grid (1.6fr 1fr 1fr 1fr)  |
| 481–768px   | 2-column grid                       |
| ≤ 480px     | Single-column stack, centered bottom|

## Accessibility

- `<footer>` element with `role="contentinfo"` and `aria-label="Site footer"`
- Each link section uses `<nav>` with a descriptive `aria-label`
- Section headings use `<h4>` for proper heading hierarchy
- All links support keyboard focus with visible `:focus-visible` outlines
- External links include `target="_blank"` with `rel="noopener noreferrer"`
- `mailto:` links used for contact (no placeholder emails)
- "Back to top" button has `aria-label="Back to top"`
- External links display a visible arrow indicator (↗)

## UX Enhancements

- **Back to top** pill in upper-right corner of the footer
- **Link hover underline** animation (transparent → accent border-bottom)
- **Section heading accent** color with bottom border separator
- **Subtle surface background** to visually separate footer from content
- **Bottom bar** separates copyright/version from main grid
- **GitHub link** in bottom bar for quick access
- **Icons** on Help (ℹ) and Contact (✉) links for visual scanning
- **External link indicator** (↗) on "Report an Issue"

## Link Mapping

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

## Styling

- Surface alt background for visual separation from page content
- Top border: 1px solid, uses `--mantis-divider` CSS variable
- Section headings: `Space Grotesk`, uppercase, accent-colored, with bottom border
- Links: inherit text color, green accent + underline on hover
- Focus rings: 2px solid accent color
- Max width: 960px, centered
- Bottom bar: separated by top border, flexbox with wrap
- "Back to top" pill: rounded, subtle border, accent on hover
- Consistent with existing Mantis theme tokens

## Pages Added

| Page  | Route          | Content Source       |
|-------|----------------|----------------------|
| Help  | `?page=help`   | `legal/help.md`      |
