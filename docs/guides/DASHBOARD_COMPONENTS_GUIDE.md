# Dashboard Components Quick Reference

## Usage Guide for `app/ui/dashboard_components.py`

### Import

```python
from app.ui.dashboard_components import (
    render_hero_header,
    render_metrics_row,
    render_workspace_hub_section,
    render_feature_group,
    render_dashboard_section_header,
    add_vertical_space,
    add_divider_with_spacing,
    spacing,
)
```

---

## Components

### 1. Hero Header

Creates a prominent top section with large title and action buttons.

```python
render_hero_header(
    status_label="🟢 Operational",
    status_caption="💾 Auto-saving",
    primary_action=lambda: print("New Project"),
    secondary_action=lambda: print("Open Workspace"),
    tertiary_action=lambda: print("Run Analysis"),
)
```

**Features:**
- Large 44px MANTIS title
- Full subtitle
- Status indicators
- 3 action buttons (primary + 2 secondary)

---

### 2. Metrics Row

Displays metric cards in a horizontal row with hover effects.

```python
metrics = [
    ("Total Projects", "42"),
    ("Active Workspace", "My Story"),
    ("AI Operations Today", "5"),
    ("System Mode", "Cloud"),
]
render_metrics_row(metrics)
```

**Features:**
- Responsive grid layout
- Centered alignment
- Hover effects (lift + glow)
- Consistent card styling

---

### 3. Section Header

Renders a section title with optional description.

```python
render_dashboard_section_header(
    "Workspace Hub",
    "Open recent projects or create a new workspace."
)
```

**Features:**
- 24px heading
- Optional muted description
- Consistent spacing (24px above, 16px below)

---

### 4. Workspace Hub Section

Creates a card section within the workspace hub.

```python
def my_content():
    st.markdown("**Recent Projects**")
    st.caption("Last modified: 2024-02-18")

render_workspace_hub_section(
    "Recent Projects",
    my_content
)
```

**Features:**
- Bordered container
- Section title
- Custom content via callback

---

### 5. Feature Group

Renders a collapsible feature group with action buttons.

```python
features = [
    ("Feature Name", "Description text", lambda: action_function()),
    ("Another Feature", "More description", lambda: other_action()),
]

render_feature_group(
    "🧠 Intelligence",
    features,
    expanded=True,
    key_prefix="dashboard"
)
```

**Features:**
- Collapsible expander
- 3:1 layout (info:button)
- Auto-generated safe keys
- Loading spinners
- Spacing between items

---

## Utilities

### Spacing Function

```python
# Generate spacing based on 8px system
spacing(1)  # "8px"
spacing(2)  # "16px"
spacing(3)  # "24px"
```

### Add Vertical Space

```python
# Add vertical spacing
add_vertical_space(2)  # 16px gap
add_vertical_space(3)  # 24px gap
```

### Add Divider with Spacing

```python
# Add divider with spacing above and below
add_divider_with_spacing(top=3, bottom=3)  # 24px top, 24px bottom
```

---

## Design System

### Spacing Scale (8px base)
- **1 unit** = 8px (tight spacing, within components)
- **2 units** = 16px (default spacing, between elements)
- **3 units** = 24px (section spacing, major divisions)
- **4 units** = 32px (large gaps, rarely used)

### Typography Scale
- **H1** (Hero): 44px, weight 700
- **H2** (Sections): 24px, weight 600
- **H3** (Cards): 20px, weight 600
- **Body**: 15px
- **Caption**: 13-14px, muted color

### CSS Variables Used
```css
var(--mantis-text)          /* Primary text */
var(--mantis-muted)         /* Secondary/caption text */
var(--mantis-surface-alt)   /* Card backgrounds */
var(--mantis-card-border)   /* Card borders */
var(--mantis-accent-glow)   /* Hover glow effects */
```

These automatically adapt to light/dark themes.

---

## Examples

### Complete Dashboard Section

```python
# Hero
render_hero_header(
    status_label="🟢 Operational",
    primary_action=create_project,
    secondary_action=open_workspace,
    tertiary_action=run_analysis,
)

add_divider_with_spacing(top=3, bottom=3)

# Metrics
render_dashboard_section_header("Metrics Overview")
render_metrics_row([
    ("Projects", "10"),
    ("Chapters", "45"),
    ("Words", "123,456"),
])

add_divider_with_spacing(top=3, bottom=3)

# Features
render_dashboard_section_header(
    "Tools",
    "Quick access to key features"
)

features = [
    ("Editor", "Write and edit", open_editor),
    ("Analysis", "Run analysis", run_analysis),
]

render_feature_group(
    "✍ Writing",
    features,
    expanded=True,
    key_prefix="tools"
)
```

---

## Best Practices

### DO ✅
- Use the spacing utilities for consistency
- Pass callbacks to action parameters
- Use descriptive key_prefixes
- Keep feature descriptions concise
- Use emojis sparingly and meaningfully

### DON'T ❌
- Hardcode pixel values (use `spacing()`)
- Skip the key_prefix (causes conflicts)
- Make feature descriptions too long
- Nest these components deeply
- Override CSS variables inline

---

## Troubleshooting

### Issue: Button keys conflict
**Solution:** Ensure unique `key_prefix` for each `render_feature_group()` call.

### Issue: Spacing looks wrong
**Solution:** Use `add_vertical_space()` and `spacing()` utilities instead of hardcoded values.

### Issue: Theme colors wrong
**Solution:** Verify you're using CSS variables (e.g., `var(--mantis-text)`) not hardcoded colors.

### Issue: Callbacks not working
**Solution:** Pass lambda functions or function references, not function calls:
```python
# ✅ Correct
primary_action=lambda: my_function()
primary_action=my_function

# ❌ Wrong
primary_action=my_function()  # Calls immediately!
```

---

## Migration from Old Code

### Before (Old Style)
```python
render_card("Command Center", _hero_section)
st.divider()
render_section_header("Metrics Overview")
metric_cols = st.columns(4)
with metric_cols[0]:
    render_metric("Projects", "10")
```

### After (New Style)
```python
render_hero_header(
    primary_action=action_fn,
    secondary_action=action_fn2,
)
add_divider_with_spacing(top=3, bottom=3)
render_dashboard_section_header("Metrics Overview")
render_metrics_row([("Projects", "10")])
```

---

## Performance Notes

- Components use minimal inline styles
- CSS is injected once per render cycle
- Callbacks prevent unnecessary reruns
- Key generation is deterministic

---

## Accessibility

All components follow accessibility best practices:
- ✅ Keyboard navigation supported
- ✅ Focus indicators visible
- ✅ Proper heading hierarchy
- ✅ Color contrast meets WCAG standards
- ✅ Screen reader friendly

---

## Future Enhancements

Planned improvements:
- [ ] Animated transitions
- [ ] Customizable metric card icons
- [ ] Drag-and-drop support
- [ ] More spacing presets
- [ ] Additional card variants
