"""
Mantis Studio Design System

This module provides a comprehensive, centralized design system for the entire application.
It defines:
- Color palettes (primary, secondary, surfaces, accents)
- Typography scales
- Spacing system (8px grid)
- Button styles
- Component patterns
- Layout constants

All UI components should reference this design system for consistency.
"""

from __future__ import annotations
from typing import Dict, Literal
from dataclasses import dataclass

# =============================================================================
# COLOR SYSTEM
# =============================================================================

@dataclass
class ColorPalette:
    """Comprehensive color palette for Mantis Studio"""
    # Brand colors
    primary: str
    primary_hover: str
    primary_light: str
    primary_dark: str
    
    # Secondary/Accent colors
    secondary: str
    accent: str
    accent_soft: str
    accent_glow: str
    
    # Backgrounds
    bg: str
    bg_surface: str
    bg_surface_raised: str
    bg_surface_sunken: str
    
    # Text colors
    text: str
    text_secondary: str
    text_muted: str
    text_inverse: str
    
    # Borders
    border: str
    border_light: str
    border_strong: str
    
    # State colors
    success: str
    warning: str
    error: str
    info: str
    
    # Shadows
    shadow_sm: str
    shadow_md: str
    shadow_lg: str
    shadow_xl: str


# Dark theme palette
DARK_PALETTE = ColorPalette(
    # Brand
    primary="#22c55e",
    primary_hover="#4ade80",
    primary_light="#86efac",
    primary_dark="#16a34a",
    
    # Secondary/Accent
    secondary="#38bdf8",
    accent="#22c55e",
    accent_soft="rgba(34,197,94,0.12)",
    accent_glow="rgba(34,197,94,0.35)",
    
    # Backgrounds
    bg="#020617",
    bg_surface="rgba(6,18,14,0.85)",
    bg_surface_raised="rgba(11,24,19,0.90)",
    bg_surface_sunken="rgba(3,10,8,0.95)",
    
    # Text
    text="#ecfdf5",
    text_secondary="#c7f2da",
    text_muted="#94a3b8",
    text_inverse="#0a0a0a",
    
    # Borders
    border="rgba(148,163,184,0.15)",
    border_light="rgba(148,163,184,0.08)",
    border_strong="rgba(34,197,94,0.25)",
    
    # States
    success="#22c55e",
    warning="#f59e0b",
    error="#ef4444",
    info="#38bdf8",
    
    # Shadows
    shadow_sm="0 2px 8px rgba(0,0,0,0.2)",
    shadow_md="0 8px 16px rgba(0,0,0,0.3)",
    shadow_lg="0 14px 32px rgba(0,0,0,0.4)",
    shadow_xl="0 20px 48px rgba(0,0,0,0.5)",
)

# Light theme palette
LIGHT_PALETTE = ColorPalette(
    # Brand
    primary="#16a34a",
    primary_hover="#15803d",
    primary_light="#4ade80",
    primary_dark="#14532d",
    
    # Secondary/Accent
    secondary="#0284c7",
    accent="#16a34a",
    accent_soft="rgba(22,163,74,0.12)",
    accent_glow="rgba(22,163,74,0.30)",
    
    # Backgrounds
    bg="#f4f6f5",
    bg_surface="rgba(250,251,250,0.95)",
    bg_surface_raised="#ffffff",
    bg_surface_sunken="rgba(240,243,241,0.95)",
    
    # Text
    text="#1a2e23",
    text_secondary="#276740",
    text_muted="#64748b",
    text_inverse="#ffffff",
    
    # Borders
    border="rgba(100,116,139,0.2)",
    border_light="rgba(100,116,139,0.1)",
    border_strong="rgba(22,163,74,0.35)",
    
    # States
    success="#15803d",
    warning="#b45309",
    error="#dc2626",
    info="#0284c7",
    
    # Shadows
    shadow_sm="0 1px 4px rgba(20,40,30,0.08)",
    shadow_md="0 4px 12px rgba(20,40,30,0.10)",
    shadow_lg="0 12px 24px rgba(20,40,30,0.12)",
    shadow_xl="0 20px 40px rgba(20,40,30,0.15)",
)


# =============================================================================
# TYPOGRAPHY SYSTEM
# =============================================================================

@dataclass
class TypographyScale:
    """Typography scale with consistent sizing and weights"""
    # Display
    display_xl: Dict[str, str]
    display_lg: Dict[str, str]
    display_md: Dict[str, str]
    
    # Headings
    h1: Dict[str, str]
    h2: Dict[str, str]
    h3: Dict[str, str]
    h4: Dict[str, str]
    h5: Dict[str, str]
    h6: Dict[str, str]
    
    # Body
    body_lg: Dict[str, str]
    body: Dict[str, str]
    body_sm: Dict[str, str]
    
    # Captions
    caption: Dict[str, str]
    caption_sm: Dict[str, str]
    
    # Overline/Label
    overline: Dict[str, str]


TYPOGRAPHY = TypographyScale(
    # Display (hero sections)
    display_xl={"size": "56px", "weight": "700", "line_height": "1.1", "letter_spacing": "-0.03em"},
    display_lg={"size": "48px", "weight": "700", "line_height": "1.15", "letter_spacing": "-0.03em"},
    display_md={"size": "40px", "weight": "700", "line_height": "1.2", "letter_spacing": "-0.02em"},
    
    # Headings
    h1={"size": "34px", "weight": "700", "line_height": "1.25", "letter_spacing": "-0.02em"},
    h2={"size": "28px", "weight": "600", "line_height": "1.3", "letter_spacing": "-0.015em"},
    h3={"size": "24px", "weight": "600", "line_height": "1.35", "letter_spacing": "-0.01em"},
    h4={"size": "20px", "weight": "600", "line_height": "1.4", "letter_spacing": "-0.01em"},
    h5={"size": "18px", "weight": "600", "line_height": "1.45", "letter_spacing": "0"},
    h6={"size": "16px", "weight": "600", "line_height": "1.5", "letter_spacing": "0"},
    
    # Body
    body_lg={"size": "17px", "weight": "400", "line_height": "1.65", "letter_spacing": "0"},
    body={"size": "15px", "weight": "400", "line_height": "1.6", "letter_spacing": "0"},
    body_sm={"size": "14px", "weight": "400", "line_height": "1.55", "letter_spacing": "0"},
    
    # Captions
    caption={"size": "13px", "weight": "400", "line_height": "1.5", "letter_spacing": "0"},
    caption_sm={"size": "12px", "weight": "400", "line_height": "1.4", "letter_spacing": "0"},
    
    # Overline/Label (uppercase labels)
    overline={"size": "11px", "weight": "600", "line_height": "1.3", "letter_spacing": "0.08em"},
)


# =============================================================================
# SPACING SYSTEM (8px grid)
# =============================================================================

class Spacing:
    """8px-based spacing system for consistent layouts"""
    # Base unit
    BASE = 8
    
    # Spacing scale (multiples of 8px)
    XS = "4px"    # 0.5x
    SM = "8px"    # 1x
    MD = "16px"   # 2x
    LG = "24px"   # 3x
    XL = "32px"   # 4x
    XXL = "40px"  # 5x
    XXXL = "48px" # 6x
    
    # Section spacing (larger gaps)
    SECTION_SM = "32px"
    SECTION_MD = "48px"
    SECTION_LG = "64px"
    SECTION_XL = "80px"
    
    # Component-specific spacing
    CARD_PADDING = "20px"
    BUTTON_PADDING = "12px 20px"
    INPUT_PADDING = "10px 14px"
    
    @staticmethod
    def scale(multiplier: float) -> str:
        """Generate spacing value based on multiplier of base unit"""
        return f"{int(Spacing.BASE * multiplier)}px"


# =============================================================================
# BORDER RADIUS SYSTEM
# =============================================================================

class BorderRadius:
    """Consistent border radius values"""
    NONE = "0"
    SM = "8px"
    MD = "12px"
    LG = "16px"
    XL = "20px"
    XXL = "24px"
    FULL = "9999px"
    
    # Component-specific
    BUTTON = "12px"
    CARD = "16px"
    INPUT = "10px"
    PILL = "9999px"


# =============================================================================
# BUTTON STYLES
# =============================================================================

class ButtonStyles:
    """Standardized button style configurations"""
    
    @staticmethod
    def primary() -> Dict[str, str]:
        return {
            "background": "var(--mantis-primary-bg)",
            "color": "#ffffff",
            "border": "1px solid var(--mantis-primary-border)",
            "border_radius": BorderRadius.BUTTON,
            "padding": "10px 20px",
            "font_weight": "600",
            "font_size": "14px",
            "hover_border": "var(--mantis-primary-hover-border)",
            "box_shadow": "var(--mantis-shadow-button)",
        }
    
    @staticmethod
    def secondary() -> Dict[str, str]:
        return {
            "background": "var(--mantis-button-bg)",
            "color": "var(--mantis-text)",
            "border": "1px solid var(--mantis-button-border)",
            "border_radius": BorderRadius.BUTTON,
            "padding": "10px 20px",
            "font_weight": "600",
            "font_size": "14px",
            "hover_border": "var(--mantis-button-hover-border)",
            "box_shadow": "none",
        }
    
    @staticmethod
    def destructive() -> Dict[str, str]:
        return {
            "background": "linear-gradient(135deg, #dc2626, #991b1b)",
            "color": "#ffffff",
            "border": "1px solid rgba(220,38,38,0.5)",
            "border_radius": BorderRadius.BUTTON,
            "padding": "10px 20px",
            "font_weight": "600",
            "font_size": "14px",
            "hover_border": "#ef4444",
            "box_shadow": "0 4px 12px rgba(220,38,38,0.25)",
        }
    
    @staticmethod
    def ghost() -> Dict[str, str]:
        return {
            "background": "transparent",
            "color": "var(--mantis-text)",
            "border": "1px solid transparent",
            "border_radius": BorderRadius.BUTTON,
            "padding": "10px 20px",
            "font_weight": "600",
            "font_size": "14px",
            "hover_border": "var(--mantis-border)",
            "box_shadow": "none",
        }


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================

class Layout:
    """Layout constants and breakpoints"""
    # Container widths
    CONTAINER_SM = "640px"
    CONTAINER_MD = "768px"
    CONTAINER_LG = "1024px"
    CONTAINER_XL = "1280px"
    CONTAINER_2XL = "1380px"
    
    # Sidebar
    SIDEBAR_WIDTH = "280px"
    
    # Header heights
    HEADER_HEIGHT = "64px"
    HEADER_HEIGHT_COMPACT = "48px"
    
    # Content area
    CONTENT_MAX_WIDTH = "1380px"
    CONTENT_PADDING = Spacing.LG


# =============================================================================
# COMPONENT PATTERNS
# =============================================================================

class Components:
    """Reusable component style patterns"""
    
    @staticmethod
    def card_elevated() -> Dict[str, str]:
        return {
            "background": "var(--mantis-surface)",
            "border": "1px solid var(--mantis-border)",
            "border_radius": BorderRadius.CARD,
            "padding": Spacing.CARD_PADDING,
            "box_shadow": "var(--mantis-shadow-md)",
        }
    
    @staticmethod
    def card_flat() -> Dict[str, str]:
        return {
            "background": "var(--mantis-surface-alt)",
            "border": "1px solid var(--mantis-border-light)",
            "border_radius": BorderRadius.CARD,
            "padding": Spacing.CARD_PADDING,
            "box_shadow": "none",
        }
    
    @staticmethod
    def pill() -> Dict[str, str]:
        return {
            "display": "inline-flex",
            "align_items": "center",
            "gap": "6px",
            "padding": "6px 12px",
            "border_radius": BorderRadius.PILL,
            "border": "1px solid var(--mantis-accent-glow)",
            "background": "var(--mantis-accent-soft)",
            "font_size": TYPOGRAPHY.caption_sm["size"],
            "font_weight": "500",
            "color": "var(--mantis-text)",
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_palette(theme: Literal["Dark", "Light"] = "Dark") -> ColorPalette:
    """Get color palette for specified theme"""
    return DARK_PALETTE if theme == "Dark" else LIGHT_PALETTE


def get_css_variable(name: str) -> str:
    """Generate CSS variable reference"""
    return f"var(--mantis-{name})"


def generate_spacing_css() -> str:
    """Generate CSS for spacing utilities"""
    css_lines = []
    for i in range(0, 13):  # 0 to 96px (12 * 8)
        value = Spacing.scale(i)
        css_lines.append(f".mt-{i} {{ margin-top: {value}; }}")
        css_lines.append(f".mb-{i} {{ margin-bottom: {value}; }}")
        css_lines.append(f".ml-{i} {{ margin-left: {value}; }}")
        css_lines.append(f".mr-{i} {{ margin-right: {value}; }}")
        css_lines.append(f".pt-{i} {{ padding-top: {value}; }}")
        css_lines.append(f".pb-{i} {{ padding-bottom: {value}; }}")
        css_lines.append(f".pl-{i} {{ padding-left: {value}; }}")
        css_lines.append(f".pr-{i} {{ padding-right: {value}; }}")
    return "\n".join(css_lines)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ColorPalette",
    "DARK_PALETTE",
    "LIGHT_PALETTE",
    "TypographyScale",
    "TYPOGRAPHY",
    "Spacing",
    "BorderRadius",
    "ButtonStyles",
    "Layout",
    "Components",
    "get_palette",
    "get_css_variable",
    "generate_spacing_css",
]
