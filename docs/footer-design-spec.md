# MANTIS Studio — Footer Design Spec

## Layout

The footer uses a four-column grid layout with clear section hierarchy:

```
┌──────────────────────────────────────────────────────────────────┐
│  MANTIS Studio          Navigation      Legal Center   Support  │
│  Modular narrative      Dashboard       Terms of       Help     │
│  workspace              Projects        Service        Report   │
│  © 2024 · v{version}    Outline         Privacy        an Issue │
│                         Export          Policy         Contact  │
│                                        All Policies            │
└──────────────────────────────────────────────────────────────────┘
```

## Section Order

| # | Section         | Content                                        |
|---|-----------------|------------------------------------------------|
| 1 | Brand/Copyright | App name, tagline, copyright, version          |
| 2 | Navigation      | Dashboard, Projects, Outline, Export            |
| 3 | Legal Center    | Terms of Service, Privacy Policy, All Policies  |
| 4 | Support         | Help, Report an Issue (GitHub), Contact (email) |

## Responsive Behavior

| Breakpoint  | Layout                              |
|-------------|-------------------------------------|
| > 640px     | 4-column grid (1.5fr 1fr 1fr 1fr)  |
| 401–640px   | 2-column grid                       |
| ≤ 400px     | Single-column stack                 |

## Accessibility

- `<footer>` element with `role="contentinfo"` and `aria-label="Site footer"`
- Each link section uses `<nav>` with a descriptive `aria-label`
- Section headings use `<h4>` for proper heading hierarchy
- All links support keyboard focus with visible `:focus-visible` outlines
- External links include `target="_blank"` with `rel="noopener noreferrer"`
- `mailto:` links used for contact (no placeholder emails)

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

## Styling

- Top border: 1px solid, uses `--mantis-divider` CSS variable
- Section headings: uppercase, 0.75rem, letter-spaced
- Links: inherit text color, green accent on hover
- Focus rings: 2px solid accent color
- Max width: 960px, centered
- Consistent with existing Mantis theme tokens

## Pages Added

| Page  | Route          | Content Source       |
|-------|----------------|----------------------|
| Help  | `?page=help`   | `legal/help.md`      |
