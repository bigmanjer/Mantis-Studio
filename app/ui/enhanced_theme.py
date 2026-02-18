"""
Enhanced Theme System for Mantis Studio

This module builds on the design system to provide advanced theming capabilities
including CSS variable generation, theme switching, and component styling.
"""

from __future__ import annotations
from typing import Dict, Literal
import streamlit as st

from app.ui.design_system import (
    get_palette,
    TYPOGRAPHY,
    Spacing,
    BorderRadius,
    Components,
    generate_spacing_css,
)


def generate_theme_css_variables(theme: Literal["Dark", "Light"] = "Dark") -> str:
    """Generate comprehensive CSS variables from design system"""
    palette = get_palette(theme)
    
    return f"""
    :root {{
        /* === Brand Colors === */
        --mantis-primary: {palette.primary};
        --mantis-primary-hover: {palette.primary_hover};
        --mantis-primary-light: {palette.primary_light};
        --mantis-primary-dark: {palette.primary_dark};
        
        /* === Secondary/Accent === */
        --mantis-secondary: {palette.secondary};
        --mantis-accent: {palette.accent};
        --mantis-accent-soft: {palette.accent_soft};
        --mantis-accent-glow: {palette.accent_glow};
        
        /* === Backgrounds === */
        --mantis-bg: {palette.bg};
        --mantis-surface: {palette.bg_surface};
        --mantis-surface-raised: {palette.bg_surface_raised};
        --mantis-surface-sunken: {palette.bg_surface_sunken};
        --mantis-surface-alt: {palette.bg_surface};
        
        /* === Text === */
        --mantis-text: {palette.text};
        --mantis-text-secondary: {palette.text_secondary};
        --mantis-text-muted: {palette.text_muted};
        --mantis-text-inverse: {palette.text_inverse};
        --mantis-muted: {palette.text_muted};
        
        /* === Borders === */
        --mantis-border: {palette.border};
        --mantis-border-light: {palette.border_light};
        --mantis-border-strong: {palette.border_strong};
        --mantis-card-border: {palette.border};
        
        /* === State Colors === */
        --mantis-success: {palette.success};
        --mantis-warning: {palette.warning};
        --mantis-error: {palette.error};
        --mantis-info: {palette.info};
        
        /* === Shadows === */
        --mantis-shadow-sm: {palette.shadow_sm};
        --mantis-shadow-md: {palette.shadow_md};
        --mantis-shadow-lg: {palette.shadow_lg};
        --mantis-shadow-xl: {palette.shadow_xl};
        --mantis-shadow-strong: {palette.shadow_lg};
        --mantis-shadow-button: {palette.shadow_md};
        
        /* === Button Colors === */
        --mantis-button-bg: {"linear-gradient(180deg, #0f1a15, #0b1411)" if theme == "Dark" else "linear-gradient(180deg, #fafbfa, #f0f5f2)"};
        --mantis-button-border: {"#163f2a" if theme == "Dark" else "#6a8a7b"};
        --mantis-button-hover-border: {palette.primary};
        --mantis-primary-bg: {"linear-gradient(135deg, #15803d, #22c55e)" if theme == "Dark" else "linear-gradient(135deg, #16a34a, #15803d)"};
        --mantis-primary-border: {palette.accent_glow};
        --mantis-primary-hover-border: {palette.primary_hover};
        
        /* === Input Colors === */
        --mantis-input-bg: {"#0b1216" if theme == "Dark" else "#fafbfa"};
        --mantis-input-border: {"#166534" if theme == "Dark" else "#6a8a7b"};
        
        /* === Sidebar === */
        --mantis-sidebar-bg: {"linear-gradient(180deg, #020617, #07150f)" if theme == "Dark" else "linear-gradient(180deg, #eef1ef, #e4e9e6)"};
        --mantis-sidebar-border: {"#123123" if theme == "Dark" else "#708378"};
        --mantis-sidebar-title: {"#7dd3a7" if theme == "Dark" else "#15803d"};
        --mantis-sidebar-brand-bg: {"linear-gradient(180deg, rgba(6,18,14,0.85), rgba(4,10,8,0.95))" if theme == "Dark" else "linear-gradient(180deg, rgba(250,251,250,0.95), rgba(243,247,245,0.95))"};
        --mantis-sidebar-brand-border: {palette.accent_soft};
        --mantis-sidebar-logo-bg: {palette.accent_soft};
        
        /* === Header === */
        --mantis-header-gradient: {"linear-gradient(135deg, #0b1216, #0f1a15)" if theme == "Dark" else "linear-gradient(135deg, #e2f3e8, #d0eddb)"};
        --mantis-header-logo-bg: {palette.accent_soft};
        --mantis-header-sub: {palette.text_secondary};
        
        /* === Dividers === */
        --mantis-divider: {"#143023" if theme == "Dark" else "#7a8e82"};
        --mantis-expander-border: {"#1f3b2d" if theme == "Dark" else "#708a7e"};
        
        /* === Background Effects === */
        --mantis-bg-glow: {"radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)" if theme == "Dark" else "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.08), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.06), transparent 40%)"};
        
        /* === Spacing === */
        --mantis-spacing-xs: {Spacing.XS};
        --mantis-spacing-sm: {Spacing.SM};
        --mantis-spacing-md: {Spacing.MD};
        --mantis-spacing-lg: {Spacing.LG};
        --mantis-spacing-xl: {Spacing.XL};
        --mantis-spacing-xxl: {Spacing.XXL};
        
        /* === Border Radius === */
        --mantis-radius-sm: {BorderRadius.SM};
        --mantis-radius-md: {BorderRadius.MD};
        --mantis-radius-lg: {BorderRadius.LG};
        --mantis-radius-xl: {BorderRadius.XL};
        --mantis-radius-full: {BorderRadius.FULL};
    }}
    """


def generate_typography_css() -> str:
    """Generate typography CSS from design system"""
    return f"""
    /* === Typography System === */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&family=Crimson+Pro:wght@400;600&display=swap');
    
    body, .stApp, .stMarkdown {{
        font-family: 'Inter', sans-serif;
        font-size: {TYPOGRAPHY.body["size"]};
        line-height: {TYPOGRAPHY.body["line_height"]};
        letter-spacing: {TYPOGRAPHY.body["letter_spacing"]};
    }}
    
    h1, .mantis-h1 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: {TYPOGRAPHY.h1["size"]};
        font-weight: {TYPOGRAPHY.h1["weight"]};
        line-height: {TYPOGRAPHY.h1["line_height"]};
        letter-spacing: {TYPOGRAPHY.h1["letter_spacing"]};
        color: var(--mantis-text);
        margin-bottom: {Spacing.MD};
    }}
    
    h2, .mantis-h2 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: {TYPOGRAPHY.h2["size"]};
        font-weight: {TYPOGRAPHY.h2["weight"]};
        line-height: {TYPOGRAPHY.h2["line_height"]};
        letter-spacing: {TYPOGRAPHY.h2["letter_spacing"]};
        color: var(--mantis-text);
        margin-bottom: {Spacing.SM};
    }}
    
    h3, .mantis-h3 {{
        font-family: 'Space Grotesk', sans-serif;
        font-size: {TYPOGRAPHY.h3["size"]};
        font-weight: {TYPOGRAPHY.h3["weight"]};
        line-height: {TYPOGRAPHY.h3["line_height"]};
        letter-spacing: {TYPOGRAPHY.h3["letter_spacing"]};
        color: var(--mantis-text);
        margin-bottom: {Spacing.SM};
    }}
    
    h4, .mantis-h4 {{
        font-size: {TYPOGRAPHY.h4["size"]};
        font-weight: {TYPOGRAPHY.h4["weight"]};
        line-height: {TYPOGRAPHY.h4["line_height"]};
        letter-spacing: {TYPOGRAPHY.h4["letter_spacing"]};
        color: var(--mantis-text);
    }}
    
    h5, .mantis-h5 {{
        font-size: {TYPOGRAPHY.h5["size"]};
        font-weight: {TYPOGRAPHY.h5["weight"]};
        line-height: {TYPOGRAPHY.h5["line_height"]};
        letter-spacing: {TYPOGRAPHY.h5["letter_spacing"]};
        color: var(--mantis-text);
    }}
    
    h6, .mantis-h6 {{
        font-size: {TYPOGRAPHY.h6["size"]};
        font-weight: {TYPOGRAPHY.h6["weight"]};
        line-height: {TYPOGRAPHY.h6["line_height"]};
        letter-spacing: {TYPOGRAPHY.h6["letter_spacing"]};
        color: var(--mantis-text);
    }}
    
    .mantis-body-lg {{
        font-size: {TYPOGRAPHY.body_lg["size"]};
        line-height: {TYPOGRAPHY.body_lg["line_height"]};
    }}
    
    .mantis-body-sm {{
        font-size: {TYPOGRAPHY.body_sm["size"]};
        line-height: {TYPOGRAPHY.body_sm["line_height"]};
    }}
    
    .mantis-caption {{
        font-size: {TYPOGRAPHY.caption["size"]};
        line-height: {TYPOGRAPHY.caption["line_height"]};
        color: var(--mantis-text-muted);
    }}
    
    .mantis-overline {{
        font-size: {TYPOGRAPHY.overline["size"]};
        font-weight: {TYPOGRAPHY.overline["weight"]};
        line-height: {TYPOGRAPHY.overline["line_height"]};
        letter-spacing: {TYPOGRAPHY.overline["letter_spacing"]};
        text-transform: uppercase;
        color: var(--mantis-text-muted);
    }}
    """


def generate_component_css() -> str:
    """Generate component CSS using design system"""
    card_elevated = Components.card_elevated()
    card_flat = Components.card_flat()
    pill = Components.pill()
    
    return f"""
    /* === Card Components === */
    .mantis-card {{
        background: {card_elevated["background"]};
        border: {card_elevated["border"]};
        border-radius: {card_elevated["border_radius"]};
        padding: {card_elevated["padding"]};
        box-shadow: {card_elevated["box_shadow"]};
        margin-bottom: {Spacing.MD};
    }}
    
    .mantis-card-flat {{
        background: {card_flat["background"]};
        border: {card_flat["border"]};
        border-radius: {card_flat["border_radius"]};
        padding: {card_flat["padding"]};
        box-shadow: {card_flat["box_shadow"]};
    }}
    
    .mantis-card-soft {{
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-border-light);
        border-radius: {BorderRadius.LG};
        padding: {Spacing.MD};
    }}
    
    /* === Pill Component === */
    .mantis-pill {{
        display: {pill["display"]};
        align-items: {pill["align_items"]};
        gap: {pill["gap"]};
        padding: {pill["padding"]};
        border-radius: {pill["border_radius"]};
        border: {pill["border"]};
        background: {pill["background"]};
        font-size: {pill["font_size"]};
        font-weight: {pill["font_weight"]};
        color: {pill["color"]};
    }}
    
    /* === Navigation Section Headers === */
    .mantis-nav-section {{
        margin-top: {Spacing.MD};
        margin-bottom: {Spacing.SM};
        font-weight: 600;
        font-size: {TYPOGRAPHY.overline["size"]};
        color: var(--mantis-muted);
        text-transform: uppercase;
        letter-spacing: {TYPOGRAPHY.overline["letter_spacing"]};
    }}
    
    /* === Header Bar === */
    .mantis-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: {Spacing.MD};
        padding: {Spacing.MD} {Spacing.LG};
        border-radius: {BorderRadius.XL};
        background: var(--mantis-header-gradient);
        border: 1px solid var(--mantis-border-strong);
        box-shadow: var(--mantis-shadow-strong);
        margin-bottom: {Spacing.LG};
    }}
    
    /* === Page Header === */
    .mantis-page-header {{
        margin-bottom: {Spacing.SECTION_MD};
    }}
    
    .mantis-page-title {{
        font-size: {TYPOGRAPHY.display_md["size"]};
        font-weight: {TYPOGRAPHY.display_md["weight"]};
        line-height: {TYPOGRAPHY.display_md["line_height"]};
        letter-spacing: {TYPOGRAPHY.display_md["letter_spacing"]};
        color: var(--mantis-text);
        margin-bottom: {Spacing.XS};
    }}
    
    .mantis-page-subtitle {{
        font-size: {TYPOGRAPHY.body_lg["size"]};
        color: var(--mantis-text-secondary);
        line-height: {TYPOGRAPHY.body_lg["line_height"]};
    }}
    
    /* === Section Headers === */
    .mantis-section-header {{
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        gap: {Spacing.MD};
        margin-bottom: {Spacing.MD};
    }}
    
    .mantis-section-title {{
        font-size: {TYPOGRAPHY.h3["size"]};
        font-weight: {TYPOGRAPHY.h3["weight"]};
        color: var(--mantis-text);
        margin: 0;
    }}
    
    .mantis-section-caption {{
        font-size: {TYPOGRAPHY.caption["size"]};
        color: var(--mantis-text-muted);
        margin-top: {Spacing.XS};
    }}
    
    /* === Muted Text Utility === */
    .mantis-muted {{
        color: var(--mantis-text-muted);
    }}
    
    /* === Divider === */
    .mantis-divider {{
        height: 1px;
        background: var(--mantis-divider);
        margin: {Spacing.LG} 0;
        border: none;
    }}
    
    /* === Avatar === */
    .mantis-avatar {{
        width: 36px;
        height: 36px;
        border-radius: {BorderRadius.MD};
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: var(--mantis-accent-soft);
        border: 1px solid var(--mantis-accent-glow);
        font-weight: 700;
    }}
    
    /* === Quick Grid Layout === */
    .mantis-quick-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: {Spacing.MD};
        margin-bottom: {Spacing.LG};
    }}
    
    /* === Stat Tile === */
    .mantis-stat-tile {{
        display: flex;
        flex-direction: column;
        gap: {Spacing.SM};
        padding: {Spacing.MD};
        border-radius: {BorderRadius.LG};
        background: var(--mantis-surface-alt);
        border: 1px solid var(--mantis-border);
    }}
    
    .mantis-stat-label {{
        font-size: {TYPOGRAPHY.overline["size"]};
        text-transform: uppercase;
        letter-spacing: {TYPOGRAPHY.overline["letter_spacing"]};
        color: var(--mantis-text-muted);
        font-weight: 600;
    }}
    
    .mantis-stat-value {{
        font-size: {TYPOGRAPHY.h2["size"]};
        font-weight: 700;
        color: var(--mantis-text);
    }}
    
    /* === CTA Tile === */
    .mantis-cta-tile {{
        background: var(--mantis-surface);
        border: 1px solid var(--mantis-border);
        border-radius: {BorderRadius.LG};
        padding: {Spacing.LG};
        cursor: pointer;
        transition: all 0.2s cubic-bezier(0.22, 1, 0.36, 1);
    }}
    
    .mantis-cta-tile:hover {{
        transform: translateY(-2px);
        border-color: var(--mantis-accent);
        box-shadow: var(--mantis-shadow-lg), 0 0 20px var(--mantis-accent-glow);
    }}
    
    .mantis-cta-icon {{
        font-size: 32px;
        margin-bottom: {Spacing.SM};
    }}
    
    .mantis-cta-title {{
        font-size: {TYPOGRAPHY.h4["size"]};
        font-weight: 600;
        color: var(--mantis-text);
        margin-bottom: {Spacing.XS};
    }}
    
    .mantis-cta-body {{
        font-size: {TYPOGRAPHY.body_sm["size"]};
        color: var(--mantis-text-muted);
        line-height: 1.5;
    }}
    """


def inject_enhanced_theme(theme: Literal["Dark", "Light"] = "Dark") -> None:
    """Inject enhanced theme with full design system"""
    theme_vars = generate_theme_css_variables(theme)
    typography = generate_typography_css()
    components = generate_component_css()
    spacing = generate_spacing_css()
    
    # Load button CSS from assets
    from pathlib import Path
    styles_path = Path(__file__).resolve().parents[2] / "assets" / "styles.css"
    button_css = ""
    try:
        button_css = styles_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        pass
    
    st.html(
        f"""
        <style>
        {theme_vars}
        {typography}
        {components}
        {spacing}
        
        /* === Global Styles === */
        .stApp {{
            background-color: var(--mantis-bg);
            background-image: var(--mantis-bg-glow);
            color: var(--mantis-text);
            font-family: 'Inter', sans-serif;
        }}
        
        .block-container {{
            padding-top: 2.6rem;
            padding-bottom: 2.6rem;
            max-width: 1380px;
        }}
        
        header[data-testid="stHeader"] {{
            height: 2.6rem;
        }}
        
        /* === Streamlit Component Overrides === */
        .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown li, .stMarkdown div,
        .stTextInput label, .stSelectbox label, .stCheckbox label, .stRadio label,
        .stNumberInput label, .stTextArea label {{
            color: var(--mantis-text) !important;
        }}
        
        .stTextInput input,
        .stNumberInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stMultiSelect div[data-baseweb="select"] > div {{
            background-color: var(--mantis-input-bg) !important;
            color: var(--mantis-text) !important;
            border: 1px solid var(--mantis-input-border) !important;
            border-radius: var(--mantis-radius-md) !important;
        }}
        
        div[data-baseweb="select"] input {{
            color: var(--mantis-text) !important;
        }}
        
        /* === Sidebar Styling === */
        section[data-testid="stSidebar"] {{
            background: var(--mantis-sidebar-bg);
            border-right: 1px solid var(--mantis-sidebar-border);
        }}
        
        section[data-testid="stSidebar"] h3 {{
            color: var(--mantis-sidebar-title);
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-size: 12px;
        }}
        
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {{
            color: var(--mantis-text);
        }}
        
        /* === Sidebar Brand === */
        .mantis-sidebar-brand {{
            display: flex;
            gap: 12px;
            align-items: center;
            padding: 14px 12px;
            margin: 4px 8px 10px 8px;
            border-radius: {BorderRadius.LG};
            background: var(--mantis-sidebar-brand-bg);
            border: 1px solid var(--mantis-sidebar-brand-border);
        }}
        
        /* === Dividers === */
        .stDivider {{
            border-color: var(--mantis-divider) !important;
        }}
        
        /* === Expanders === */
        .streamlit-expanderHeader {{
            border-radius: {BorderRadius.MD} !important;
            border-color: var(--mantis-expander-border) !important;
            background: var(--mantis-surface-sunken) !important;
        }}
        
        /* === Button System from assets/styles.css === */
        {button_css}
        
        /* === Scroll behavior === */
        </style>
        <script>
            // Scroll to top on page navigation
            var mainSection = window.parent.document.querySelector('section.main');
            if (mainSection) mainSection.scrollTo(0, 0);
        </script>
        """,
    )


__all__ = [
    "inject_enhanced_theme",
    "generate_theme_css_variables",
    "generate_typography_css",
    "generate_component_css",
]
