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
        --mantis-bg-primary: {palette.bg};
        --mantis-bg-secondary: {palette.bg_surface_raised};
        --mantis-surface: {palette.bg_surface};
        --mantis-surface-raised: {palette.bg_surface_raised};
        --mantis-surface-sunken: {palette.bg_surface_sunken};
        --mantis-surface-alt: {palette.bg_surface};
        --mantis-card-bg: {palette.bg_surface_raised};
        
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
        --mantis-danger: {palette.error};
        --mantis-info: {palette.info};
        --mantis-accent-teal: {palette.secondary};
        
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
        --mantis-top-offset: 0rem;
        
        /* === Dividers === */
        --mantis-divider: {"#143023" if theme == "Dark" else "#7a8e82"};
        --mantis-expander-border: {"#1f3b2d" if theme == "Dark" else "#708a7e"};
        
        /* === Background Effects === */
        --mantis-bg-glow: {"radial-gradient(circle at 20% 20%, rgba(34,197,94,0.18), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.18), transparent 40%)" if theme == "Dark" else "radial-gradient(circle at 20% 20%, rgba(34,197,94,0.08), transparent 45%), radial-gradient(circle at 80% 0%, rgba(74,222,128,0.06), transparent 40%)"};

        /* === Streamlit Core Theme Bridge === */
        --background-color: {palette.bg};
        --secondary-background-color: {palette.bg_surface};
        --text-color: {palette.text};
        
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

    /* === Dashboard Layout === */
    .mantis-dashboard-hero {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: {Spacing.LG};
        padding: {Spacing.LG};
        border-radius: {BorderRadius.XL};
        background: var(--mantis-surface);
        border: 1px solid var(--mantis-border-strong);
        box-shadow: var(--mantis-shadow-md);
        margin-bottom: {Spacing.LG};
    }}

    .mantis-dashboard-title {{
        font-size: {TYPOGRAPHY.display_md["size"]};
        font-weight: {TYPOGRAPHY.display_md["weight"]};
        letter-spacing: {TYPOGRAPHY.display_md["letter_spacing"]};
        margin: 6px 0 6px 0;
    }}

    .mantis-dashboard-sub {{
        color: var(--mantis-text-secondary);
        font-size: {TYPOGRAPHY.body_lg["size"]};
        line-height: {TYPOGRAPHY.body_lg["line_height"]};
        margin: 0;
    }}

    .mantis-kpi-strip {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: {Spacing.MD};
        margin-bottom: {Spacing.LG};
    }}

    .mantis-panel {{
        background: var(--mantis-surface);
        border: 1px solid var(--mantis-border);
        border-radius: {BorderRadius.LG};
        padding: {Spacing.MD};
        box-shadow: var(--mantis-shadow-sm);
    }}

    .mantis-panel + .mantis-panel {{
        margin-top: {Spacing.MD};
    }}

    .mantis-panel-title {{
        font-size: {TYPOGRAPHY.h4["size"]};
        font-weight: {TYPOGRAPHY.h4["weight"]};
        margin: 0 0 {Spacing.XS} 0;
    }}

    .mantis-action-tile {{
        display: flex;
        flex-direction: column;
        gap: {Spacing.SM};
        padding: {Spacing.MD};
        border-radius: {BorderRadius.LG};
        border: 1px solid var(--mantis-border);
        background: var(--mantis-surface-alt);
        height: 100%;
    }}

    .mantis-action-title {{
        font-weight: 700;
        font-size: {TYPOGRAPHY.h5["size"]};
    }}

    .mantis-action-desc {{
        color: var(--mantis-text-muted);
        font-size: {TYPOGRAPHY.body_sm["size"]};
        line-height: 1.5;
    }}

    .mantis-project-row {{
        display: grid;
        grid-template-columns: 2.4fr 1fr 1fr;
        gap: {Spacing.MD};
        align-items: center;
        padding: {Spacing.SM} 0;
        border-top: 1px solid var(--mantis-border-light);
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


def inject_enhanced_theme(theme: Literal["Dark", "Light"] = "Dark", page_key: str = "") -> None:
    """Inject enhanced theme with full design system"""
    del page_key  # Navigation should not force scroll position.
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

    final_theme_overrides = ""
    if theme == "Light":
        final_theme_overrides = """
        /* === Final Light-Mode Enforcement Layer === */
        .stButton > button,
        .stFormSubmitButton > button,
        .stLinkButton > a {
            background: #f4f8f5 !important;
            background-color: #f4f8f5 !important;
            background-image: none !important;
            border-color: #739787 !important;
            color: var(--mantis-text) !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }
        .stButton > button *,
        .stFormSubmitButton > button *,
        .stLinkButton > a * {
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
        }

        /* Force non-primary actions to stay readable in light mode */
        .stButton > button:not([kind="primary"]),
        .stFormSubmitButton > button:not([kind="primary"]),
        .stButton > button[data-testid="baseButton-secondary"],
        .stFormSubmitButton > button[data-testid="baseButton-secondary"] {
            background: #eef5f1 !important;
            background-color: #eef5f1 !important;
            border-color: #769583 !important;
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
        }

        .stButton > button:not([kind="primary"]):hover,
        .stFormSubmitButton > button:not([kind="primary"]):hover,
        .stButton > button[data-testid="baseButton-secondary"]:hover,
        .stFormSubmitButton > button[data-testid="baseButton-secondary"]:hover {
            background: #e7f0eb !important;
            background-color: #e7f0eb !important;
            border-color: #2f7f53 !important;
            color: #123a26 !important;
            -webkit-text-fill-color: #123a26 !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stLinkButton > a:hover {
            background: #eaf3ee !important;
            background-color: #eaf3ee !important;
            border-color: #2f7f53 !important;
            color: #163a28 !important;
        }

        .stButton > button[kind="primary"],
        .stFormSubmitButton > button[kind="primary"],
        .stButton > button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, #16944a, #127a3d) !important;
            border-color: #11743a !important;
            color: #ffffff !important;
        }

        .stButton > button[kind="primary"]:hover,
        .stFormSubmitButton > button[kind="primary"]:hover,
        .stButton > button[data-testid="baseButton-primary"]:hover {
            background: linear-gradient(135deg, #158842, #106d35) !important;
            border-color: #0f6733 !important;
            color: #ffffff !important;
        }

        .stButton > button[kind="primary"] *,
        .stFormSubmitButton > button[kind="primary"] *,
        .stButton > button[data-testid="baseButton-primary"] * {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] .stFormSubmitButton > button,
        section[data-testid="stSidebar"] .stLinkButton > a {
            background: #eef5f1 !important;
            background-color: #eef5f1 !important;
            border-color: #7f998c !important;
            color: #183a28 !important;
        }

        section[data-testid="stSidebar"] .stButton > button *,
        section[data-testid="stSidebar"] .stFormSubmitButton > button *,
        section[data-testid="stSidebar"] .stLinkButton > a * {
            color: #183a28 !important;
            -webkit-text-fill-color: #183a28 !important;
        }

        .stButton > button:disabled,
        .stFormSubmitButton > button:disabled,
        .stButton > button[disabled],
        .stFormSubmitButton > button[disabled],
        .stButton > button[aria-disabled="true"],
        .stFormSubmitButton > button[aria-disabled="true"],
        .stButton > button[kind="primary"]:disabled,
        .stFormSubmitButton > button[kind="primary"]:disabled,
        .stButton > button[kind="primary"][disabled],
        .stFormSubmitButton > button[kind="primary"][disabled],
        .stButton > button[kind="primary"][aria-disabled="true"],
        .stFormSubmitButton > button[kind="primary"][aria-disabled="true"],
        .stButton > button[kind="secondary"]:disabled,
        .stFormSubmitButton > button[kind="secondary"]:disabled,
        .stButton > button[kind="secondary"][disabled],
        .stFormSubmitButton > button[kind="secondary"][disabled],
        .stButton > button[kind="secondary"][aria-disabled="true"],
        .stFormSubmitButton > button[kind="secondary"][aria-disabled="true"] {
            background: #eef2ef !important;
            background-color: #eef2ef !important;
            background-image: none !important;
            border-color: #b7c4bb !important;
            color: #4f5f55 !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }

        .stButton > button[data-testid="baseButton-secondary"]:disabled,
        .stButton > button[data-testid="baseButton-secondary"][disabled],
        .stButton > button[data-testid="baseButton-primary"]:disabled,
        .stButton > button[data-testid="baseButton-primary"][disabled],
        .stFormSubmitButton > button[data-testid="baseButton-secondary"]:disabled,
        .stFormSubmitButton > button[data-testid="baseButton-secondary"][disabled],
        .stFormSubmitButton > button[data-testid="baseButton-primary"]:disabled,
        .stFormSubmitButton > button[data-testid="baseButton-primary"][disabled] {
            background: #eef2ef !important;
            background-color: #eef2ef !important;
            background-image: none !important;
            border-color: #b7c4bb !important;
            color: #4f5f55 !important;
            box-shadow: none !important;
            opacity: 1 !important;
        }

        .stButton > button:disabled *,
        .stFormSubmitButton > button:disabled *,
        .stButton > button[disabled] *,
        .stFormSubmitButton > button[disabled] *,
        .stButton > button[aria-disabled="true"] * {
            color: #4f5f55 !important;
            fill: #4f5f55 !important;
        }

        .stButton > button[data-testid="baseButton-primary"]:disabled *,
        .stButton > button[data-testid="baseButton-secondary"]:disabled *,
        .stFormSubmitButton > button[data-testid="baseButton-primary"]:disabled *,
        .stFormSubmitButton > button[data-testid="baseButton-secondary"]:disabled * {
            color: #4f5f55 !important;
            fill: #4f5f55 !important;
        }

        /* Force any Streamlit button variant to remain readable in light mode */
        button[data-testid^="baseButton"],
        button[data-testid^="stBaseButton"] {
            color: var(--mantis-text) !important;
            -webkit-text-fill-color: var(--mantis-text) !important;
        }

        button[data-testid^="baseButton"]:not([kind="primary"]),
        button[data-testid^="stBaseButton"]:not([kind="primary"]),
        button[data-testid="baseButton-secondary"],
        button[kind="secondary"] {
            background: #eef5f1 !important;
            background-color: #eef5f1 !important;
            background-image: none !important;
            border-color: #769583 !important;
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
            box-shadow: none !important;
        }

        button[data-testid^="baseButton"]:not([kind="primary"]):hover,
        button[data-testid^="stBaseButton"]:not([kind="primary"]):hover,
        button[data-testid="baseButton-secondary"]:hover,
        button[kind="secondary"]:hover {
            background: #e7f0eb !important;
            background-color: #e7f0eb !important;
            border-color: #2f7f53 !important;
            color: #123a26 !important;
            -webkit-text-fill-color: #123a26 !important;
        }

        button[data-testid^="baseButton"]:disabled,
        button[data-testid^="stBaseButton"]:disabled,
        button[data-testid^="baseButton"][disabled],
        button[data-testid^="stBaseButton"][disabled] {
            background: #eef2ef !important;
            border-color: #b7c4bb !important;
            color: #4f5f55 !important;
            -webkit-text-fill-color: #4f5f55 !important;
        }

        /* Sidebar hide/show controls and actions */
        section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
        section[data-testid="stSidebar"] .stFormSubmitButton > button[kind="secondary"],
        section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-secondary"] {
            background: #eaf2ee !important;
            border-color: #6f8d7d !important;
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
        }

        section[data-testid="stSidebar"] .stButton > button[kind="primary"],
        section[data-testid="stSidebar"] .stFormSubmitButton > button[kind="primary"],
        section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-primary"] {
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
        }

        /* Disabled checkbox labels must remain readable in light mode */
        div[data-testid="stCheckbox"] label {
            opacity: 1 !important;
            color: var(--mantis-text) !important;
        }
        div[data-testid="stCheckbox"] label p,
        div[data-testid="stCheckbox"] label span {
            color: var(--mantis-text) !important;
            -webkit-text-fill-color: var(--mantis-text) !important;
            opacity: 1 !important;
        }

        div[data-testid="stAlert"] {
            border: 1px solid var(--mantis-border) !important;
            color: var(--mantis-text) !important;
        }

        div[data-testid="stAlert"] p,
        div[data-testid="stAlert"] span,
        div[data-testid="stAlert"] li {
            color: var(--mantis-text) !important;
        }

        div[data-testid="stAlert"][kind="warning"] {
            background: #fef7dc !important;
            border-color: #e7cb6a !important;
        }

        div[data-testid="stAlert"][kind="warning"] p,
        div[data-testid="stAlert"][kind="warning"] span {
            color: #5e4a10 !important;
        }

        div[data-testid="stAlert"][kind="error"] {
            background: #fde8e8 !important;
            border-color: #e8aaaa !important;
        }

        div[data-testid="stAlert"][kind="error"] p,
        div[data-testid="stAlert"][kind="error"] span {
            color: #7d1d1d !important;
        }

        div[data-testid="stAlert"][kind="success"] {
            background: #e7f7ec !important;
            border-color: #96c8a6 !important;
        }

        div[data-testid="stAlert"][kind="success"] p,
        div[data-testid="stAlert"][kind="success"] span {
            color: #1f5f36 !important;
        }

        div[data-testid="stAlert"][kind="info"] {
            background: #e8f2fb !important;
            border-color: #a9c4df !important;
        }

        div[data-testid="stAlert"][kind="info"] p,
        div[data-testid="stAlert"][kind="info"] span {
            color: #1b4f76 !important;
        }

        section[data-testid="stSidebar"] .mantis-project-chip,
        section[data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: #f5f7f5 !important;
            border-color: #c8d4cc !important;
        }

        section[data-testid="stSidebar"] .mantis-project-chip__title {
            color: #183a28 !important;
        }

        section[data-testid="stSidebar"] .mantis-project-chip__meta {
            color: #496254 !important;
        }

        /* Radios/segments: keep labels visible in light mode */
        div[role="radiogroup"] > label {
            background: #eef5f1 !important;
            border: 1px solid #769583 !important;
            border-radius: 12px !important;
        }
        div[role="radiogroup"] > label p,
        div[role="radiogroup"] > label span,
        div[role="radiogroup"] > label div {
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
            opacity: 1 !important;
        }

        /* Expanders: prevent dark headers in light mode */
        details summary,
        .streamlit-expanderHeader {
            background: #eef5f1 !important;
            border: 1px solid #769583 !important;
            color: #173626 !important;
        }
        details summary *,
        .streamlit-expanderHeader * {
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
        }

        /* Sliders/toggles labels and values: improve contrast in settings */
        div[data-testid="stSlider"] label,
        div[data-testid="stSlider"] p,
        div[data-testid="stSlider"] span,
        div[data-testid="stSlider"] [data-testid="stMarkdownContainer"] * {
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
            opacity: 1 !important;
        }
        div[data-testid="stToggleSwitch"] label,
        div[data-testid="stToggleSwitch"] p,
        div[data-testid="stToggleSwitch"] span {
            color: #173626 !important;
            -webkit-text-fill-color: #173626 !important;
            opacity: 1 !important;
        }
        """
    
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

        body, html, [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
            background-color: var(--mantis-bg) !important;
            color: var(--mantis-text) !important;
        }}

        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
            background: var(--mantis-bg) !important;
        }}
        /* Remove Streamlit's default sidebar toggle chevrons (<< / >) */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [aria-label="Collapse sidebar"],
        [aria-label="Expand sidebar"],
        [title="Collapse sidebar"],
        [title="Expand sidebar"],
        button[kind="headerNoPadding"][aria-label*="sidebar"],
        button[kind="headerNoPadding"][title*="sidebar"] {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            visibility: hidden !important;
        }}

        section[data-testid="stMain"] div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: var(--mantis-surface) !important;
            border-color: var(--mantis-border) !important;
        }}

        [data-testid="stMain"] .block-container > div > div > div > div {{
            color: var(--mantis-text) !important;
        }}
        
        .block-container {{
            padding-top: 0.55rem;
            padding-bottom: 2.6rem;
            max-width: 1380px;
        }}

        div[data-testid="stMainBlockContainer"] {{
            padding-top: 0.45rem !important;
        }}

        section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {{
            padding-top: 0 !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }}

        section[data-testid="stSidebar"] .block-container {{
            padding-top: 0 !important;
            padding-left: 0.35rem !important;
            padding-right: 0.35rem !important;
            padding-bottom: 0.6rem !important;
        }}
        
        header[data-testid="stHeader"] {{
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
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

        .stTextArea textarea {{
            font-family: 'Crimson Pro', serif !important;
            font-size: 18px !important;
            line-height: 1.65 !important;
        }}

        /* === Light Mode Consistency === */
        [data-baseweb="popover"], [role="listbox"] {{
            background: var(--mantis-surface-raised) !important;
            color: var(--mantis-text) !important;
            border: 1px solid var(--mantis-border) !important;
        }}
        [role="option"] {{
            color: var(--mantis-text) !important;
        }}
        [role="option"][aria-selected="true"] {{
            background: var(--mantis-accent-soft) !important;
        }}
        .stMetric, .stAlert, .stDataFrame, .stExpander, .element-container div[data-testid="stVerticalBlockBorderWrapper"] {{
            color: var(--mantis-text) !important;
        }}
        /* Streamlit metric internals sometimes keep default colors in light mode */
        [data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{
            color: var(--mantis-text-secondary) !important;
        }}
        [data-testid="stMetricValue"], [data-testid="stMetricValue"] > div, [data-testid="stMetricValue"] p {{
            color: var(--mantis-text) !important;
        }}
        [data-testid="stMetricDelta"], [data-testid="stMetricDelta"] p {{
            color: var(--mantis-text-muted) !important;
        }}
        .stCodeBlock, pre, code {{
            background: var(--mantis-surface-sunken) !important;
            color: var(--mantis-text) !important;
            border-color: var(--mantis-border) !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stNumberInput input {{
            background: var(--mantis-input-bg) !important;
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
        {final_theme_overrides}
        
        </style>
        """,
    )


__all__ = [
    "inject_enhanced_theme",
    "generate_theme_css_variables",
    "generate_typography_css",
    "generate_component_css",
]


