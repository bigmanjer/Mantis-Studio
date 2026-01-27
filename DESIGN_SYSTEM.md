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
