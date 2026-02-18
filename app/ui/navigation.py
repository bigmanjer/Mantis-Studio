"""Enhanced navigation components for Mantis Studio.

This module provides:
- Sidebar navigation with visual hierarchy
- Breadcrumb navigation
- Context-aware help and guidance
"""

from typing import List, Dict, Optional, Callable, Any
import streamlit as st


def render_nav_section(
    title: str,
    items: List[Dict[str, Any]],
    current_page: str,
) -> None:
    """Render a navigation section in the sidebar with grouped items.
    
    Args:
        title: Section title (e.g., "Core", "Tools", "Settings")
        items: List of navigation items, each with 'label', 'page', 'icon', optional 'badge'
        current_page: Currently active page key
    """
    html_items = []
    
    for item in items:
        label = item.get('label', '')
        page = item.get('page', '')
        icon = item.get('icon', '')
        badge = item.get('badge')
        disabled = item.get('disabled', False)
        
        is_active = page == current_page
        item_class = "mantis-nav-item"
        if is_active:
            item_class += " mantis-nav-item-active"
        if disabled:
            item_class += " mantis-nav-item-disabled"
        
        badge_html = f'<span class="mantis-nav-badge">{badge}</span>' if badge else ''
        
        html_items.append(f"""
        <div class="{item_class}" data-page="{page}">
            <div class="mantis-nav-icon">{icon}</div>
            <div class="mantis-nav-label">{label}</div>
            {badge_html}
        </div>
        """)
    
    html = f"""
    <div class="mantis-nav-section-container">
        <div class="mantis-nav-section-title">{title}</div>
        <div class="mantis-nav-section-items">
            {''.join(html_items)}
        </div>
    </div>
    <style>
    .mantis-nav-section-container {{
        margin-bottom: 1.5rem;
    }}
    .mantis-nav-section-title {{
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        margin-bottom: 0.75rem;
        padding: 0 0.5rem;
    }}
    .mantis-nav-section-items {{
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
    }}
    .mantis-nav-item {{
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.65rem 0.75rem;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.15s ease;
        background: transparent;
        border: 1px solid transparent;
        position: relative;
    }}
    .mantis-nav-item:hover:not(.mantis-nav-item-disabled) {{
        background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
        border-color: var(--mantis-accent-glow, rgba(34,197,94,0.25));
    }}
    .mantis-nav-item-active {{
        background: var(--mantis-accent-soft, rgba(34,197,94,0.12));
        border-color: var(--mantis-accent-glow, rgba(34,197,94,0.35));
    }}
    .mantis-nav-item-active::before {{
        content: '';
        position: absolute;
        left: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 60%;
        background: var(--mantis-accent, #22c55e);
        border-radius: 0 2px 2px 0;
    }}
    .mantis-nav-item-disabled {{
        opacity: 0.4;
        cursor: not-allowed;
    }}
    .mantis-nav-icon {{
        font-size: 18px;
        line-height: 1;
        flex-shrink: 0;
        width: 20px;
        text-align: center;
    }}
    .mantis-nav-label {{
        flex: 1;
        font-size: 14px;
        font-weight: 500;
        color: var(--mantis-text, #e2e8f0);
    }}
    .mantis-nav-badge {{
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 999px;
        background: var(--mantis-accent, #22c55e);
        color: #ffffff;
    }}
    </style>
    <script>
    // Add click handlers to navigation items
    document.querySelectorAll('.mantis-nav-item:not(.mantis-nav-item-disabled)').forEach(item => {{
        item.addEventListener('click', () => {{
            const page = item.getAttribute('data-page');
            if (page) {{
                // Use Streamlit's query params to trigger navigation
                window.parent.postMessage({{
                    type: 'streamlit:setQueryParams',
                    queryParams: {{ page: page }}
                }}, '*');
                // Also trigger a rerun by clicking a hidden button
                const navButton = window.parent.document.querySelector(`[data-testid="stButton"] button[id*="${{page}}"]`);
                if (navButton) navButton.click();
            }}
        }});
    }});
    </script>
    """
    st.html(html)


def help_tooltip(
    text: str,
    title: Optional[str] = None,
) -> None:
    """Display a help tooltip that provides contextual guidance.
    
    Args:
        text: Help text content
        title: Optional title for the help section
    """
    title_html = f'<div class="mantis-help-title">{title}</div>' if title else ''
    
    html = f"""
    <div class="mantis-help-tooltip">
        <div class="mantis-help-icon">💡</div>
        <div class="mantis-help-content">
            {title_html}
            <div class="mantis-help-text">{text}</div>
        </div>
    </div>
    <style>
    .mantis-help-tooltip {{
        display: flex;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        background: rgba(56, 189, 248, 0.08);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 10px;
        margin: 1rem 0;
    }}
    .mantis-help-icon {{
        font-size: 20px;
        line-height: 1;
        flex-shrink: 0;
    }}
    .mantis-help-content {{
        flex: 1;
    }}
    .mantis-help-title {{
        font-weight: 600;
        font-size: 13px;
        color: var(--mantis-text, #e2e8f0);
        margin-bottom: 0.25rem;
    }}
    .mantis-help-text {{
        font-size: 13px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        line-height: 1.5;
    }}
    </style>
    """
    st.html(html)


def quick_action_card(
    title: str,
    description: str,
    icon: str,
    action_label: str,
    on_click: Optional[Callable] = None,
    disabled: bool = False,
    key: Optional[str] = None,
) -> None:
    """Display a quick action card for common workflows.
    
    Args:
        title: Card title
        description: Brief description of the action
        icon: Emoji/icon to display
        action_label: Button label
        on_click: Optional callback function
        disabled: Whether the action is disabled
        key: Unique key for the button
    """
    # Generate a unique key if not provided
    if key is None:
        key = f"quick_action_{title.lower().replace(' ', '_')}"
    
    html = f"""
    <div class="mantis-quick-action-card">
        <div class="mantis-quick-action-icon">{icon}</div>
        <div class="mantis-quick-action-content">
            <div class="mantis-quick-action-title">{title}</div>
            <div class="mantis-quick-action-desc">{description}</div>
        </div>
    </div>
    <style>
    .mantis-quick-action-card {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.25rem;
        background: var(--mantis-surface, rgba(6,18,14,0.85));
        border: 1px solid var(--mantis-card-border, rgba(148, 163, 184, 0.15));
        border-radius: 14px;
        transition: all 0.2s ease;
        margin-bottom: 0.75rem;
    }}
    .mantis-quick-action-card:hover {{
        border-color: var(--mantis-accent-glow, rgba(34,197,94,0.35));
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    .mantis-quick-action-icon {{
        font-size: 28px;
        line-height: 1;
        flex-shrink: 0;
    }}
    .mantis-quick-action-content {{
        flex: 1;
    }}
    .mantis-quick-action-title {{
        font-weight: 600;
        font-size: 15px;
        color: var(--mantis-text, #e2e8f0);
        margin-bottom: 0.25rem;
    }}
    .mantis-quick-action-desc {{
        font-size: 13px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        line-height: 1.4;
    }}
    </style>
    """
    st.html(html)
    
    # Render button below the card
    if st.button(action_label, key=key, disabled=disabled, use_container_width=True, type="primary"):
        if on_click:
            on_click()


def empty_state(
    title: str,
    description: str,
    icon: str = "📭",
    action_label: Optional[str] = None,
    on_action: Optional[Callable] = None,
    key: Optional[str] = None,
) -> None:
    """Display an empty state when no content is available.
    
    Args:
        title: Empty state title
        description: Explanation or call to action
        icon: Emoji/icon to display
        action_label: Optional primary action button label
        on_action: Optional callback for the action button
        key: Unique key for the button
    """
    action_html = ""
    if action_label and on_action:
        if key is None:
            key = f"empty_state_action_{title.lower().replace(' ', '_')}"
    
    html = f"""
    <div class="mantis-empty-state">
        <div class="mantis-empty-icon">{icon}</div>
        <div class="mantis-empty-title">{title}</div>
        <div class="mantis-empty-desc">{description}</div>
    </div>
    <style>
    .mantis-empty-state {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 2rem;
        margin: 2rem 0;
    }}
    .mantis-empty-icon {{
        font-size: 48px;
        margin-bottom: 1rem;
        opacity: 0.7;
    }}
    .mantis-empty-title {{
        font-size: 20px;
        font-weight: 700;
        color: var(--mantis-text, #e2e8f0);
        margin-bottom: 0.5rem;
    }}
    .mantis-empty-desc {{
        font-size: 14px;
        color: var(--mantis-muted, rgba(226, 232, 240, 0.7));
        line-height: 1.6;
        max-width: 400px;
        margin-bottom: 1.5rem;
    }}
    </style>
    """
    st.html(html)
    
    if action_label and on_action:
        if st.button(action_label, key=key, type="primary"):
            on_action()
