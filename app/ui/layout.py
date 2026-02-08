import datetime

import streamlit as st

_CURRENT_YEAR = datetime.datetime.now(datetime.timezone.utc).year


def _build_footer_nav_links() -> str:
    """Generate footer navigation ``<li>`` items from the centralized config.

    The links mirror the sidebar navigation defined in
    ``app/utils/navigation.py → NAV_ITEMS``.  To add or remove a nav entry
    edit **only** that list — the footer updates automatically.
    """
    from app.utils.navigation import get_nav_items

    lines = []
    for label, page_key, icon in get_nav_items():
        lines.append(
            f'<li><a href="?page={page_key}">'
            f'<span class="mantis-footer-icon">{icon}</span> {label}</a></li>'
        )
    return "\n                ".join(lines)


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    nav_links_html = _build_footer_nav_links()
    st.html(
        f"""
        <style>
        /* ── Footer container ── */
        .mantis-footer {{
            margin-top: 4rem;
            border-top: 1px solid var(--mantis-divider, #143023);
            background: var(--mantis-surface-alt, rgba(5,14,11,0.9));
            padding: 2.5rem 1.5rem 0;
        }}

        /* ── Back-to-top ── */
        .mantis-footer-top {{
            display: flex;
            justify-content: flex-end;
            max-width: 960px;
            margin: 0 auto 1.5rem;
        }}
        .mantis-footer-top a {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--mantis-muted, #9CA3AF);
            text-decoration: none;
            padding: 0.35rem 0.75rem;
            border-radius: 999px;
            border: 1px solid var(--mantis-divider, #143023);
            transition: color 0.15s, border-color 0.15s;
        }}
        .mantis-footer-top a:hover {{
            color: var(--mantis-accent, #22c55e);
            border-color: var(--mantis-accent, #22c55e);
        }}
        .mantis-footer-top a:focus-visible {{
            outline: 2px solid var(--mantis-accent, #22c55e);
            outline-offset: 2px;
            border-radius: 999px;
        }}

        /* ── Grid ── */
        .mantis-footer-grid {{
            display: grid;
            grid-template-columns: 1.6fr 1fr 1fr 1fr;
            gap: 2.5rem;
            max-width: 960px;
            margin: 0 auto;
        }}

        /* ── Section headings ── */
        .mantis-footer-section h4 {{
            font-family: 'Space Grotesk', sans-serif;
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--mantis-accent, #22c55e);
            margin: 0 0 0.85rem;
            padding-bottom: 0.45rem;
            border-bottom: 1px solid var(--mantis-divider, #143023);
        }}

        /* ── Lists ── */
        .mantis-footer-section ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .mantis-footer-section li {{
            margin-bottom: 0.45rem;
        }}

        /* ── Links ── */
        .mantis-footer-section a {{
            color: var(--mantis-text, #ecfdf5);
            text-decoration: none;
            font-size: 0.85rem;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.15rem 0;
            border-bottom: 1px solid transparent;
            transition: color 0.15s, border-color 0.15s;
        }}
        .mantis-footer-section a:hover {{
            color: var(--mantis-accent, #22c55e);
            border-bottom-color: var(--mantis-accent, #22c55e);
        }}
        .mantis-footer-section a:focus-visible {{
            outline: 2px solid var(--mantis-accent, #22c55e);
            outline-offset: 2px;
            border-radius: 2px;
        }}
        .mantis-footer-section a .mantis-footer-icon {{
            font-size: 0.9rem;
            line-height: 1;
            flex-shrink: 0;
        }}
        .mantis-footer-section a .mantis-footer-ext {{
            font-size: 0.7rem;
            opacity: 0.55;
        }}

        /* ── Brand ── */
        .mantis-footer-brand {{
            font-size: 0.85rem;
            color: var(--mantis-muted, #9CA3AF);
            line-height: 1.7;
        }}
        .mantis-footer-brand strong {{
            color: var(--mantis-text, #ecfdf5);
            font-family: 'Space Grotesk', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 0.03em;
        }}
        .mantis-footer-brand .mantis-footer-tagline {{
            display: block;
            margin-top: 0.15rem;
            font-size: 0.8rem;
            color: var(--mantis-muted, #9CA3AF);
        }}

        /* ── Bottom bar ── */
        .mantis-footer-bottom {{
            max-width: 960px;
            margin: 2rem auto 0;
            padding: 1rem 0;
            border-top: 1px solid var(--mantis-divider, #143023);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: var(--mantis-muted, #9CA3AF);
            flex-wrap: wrap;
            gap: 0.5rem;
        }}
        .mantis-footer-bottom a {{
            color: var(--mantis-muted, #9CA3AF);
            text-decoration: none;
            transition: color 0.15s;
        }}
        .mantis-footer-bottom a:hover {{
            color: var(--mantis-accent, #22c55e);
        }}
        .mantis-footer-bottom a:focus-visible {{
            outline: 2px solid var(--mantis-accent, #22c55e);
            outline-offset: 2px;
            border-radius: 2px;
        }}

        /* ── Responsive ── */
        @media (max-width: 768px) {{
            .mantis-footer {{ padding: 2rem 1rem 0; }}
            .mantis-footer-grid {{
                grid-template-columns: 1fr 1fr;
                gap: 1.75rem;
            }}
        }}
        @media (max-width: 480px) {{
            .mantis-footer-grid {{
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }}
            .mantis-footer-bottom {{
                flex-direction: column;
                text-align: center;
            }}
        }}
        </style>
        <footer class="mantis-footer" role="contentinfo" aria-label="Site footer">
          <div class="mantis-footer-top">
            <a href="#" onclick="window.scrollTo({{top:0,behavior:'smooth'}});return false;" aria-label="Back to top">&uarr; Back to top</a>
          </div>
          <div class="mantis-footer-grid">
            <div class="mantis-footer-section mantis-footer-brand">
              <strong>MANTIS Studio</strong>
              <span class="mantis-footer-tagline">Modular AI Narrative Text Intelligence System</span>
            </div>
            <nav class="mantis-footer-section" aria-label="Navigation">
              <h4>Navigation</h4>
              <ul>
                {nav_links_html}
              </ul>
            </nav>
            <nav class="mantis-footer-section" aria-label="All Policies">
              <h4>All Policies</h4>
              <ul>
                <li><a href="?page=terms">Terms of Service</a></li>
                <li><a href="?page=privacy">Privacy Policy</a></li>
                <li><a href="?page=legal">All Policies</a></li>
              </ul>
            </nav>
            <nav class="mantis-footer-section" aria-label="Support">
              <h4>Support</h4>
              <ul>
                <li><a href="?page=help"><span class="mantis-footer-icon">&#9432;</span> Help</a></li>
                <li><a href="{support_url}" target="_blank" rel="noopener noreferrer">Report an Issue <span class="mantis-footer-ext">&#8599;</span></a></li>
                <li><a href="mailto:{contact_email}"><span class="mantis-footer-icon">&#9993;</span> Contact</a></li>
              </ul>
            </nav>
          </div>
          <div class="mantis-footer-bottom">
            <span>&copy; {_CURRENT_YEAR} MANTIS Studio &middot; v{version}</span>
            <span>
              <a href="{support_url}" target="_blank" rel="noopener noreferrer" aria-label="MANTIS Studio on GitHub">GitHub</a>
            </span>
          </div>
        </footer>
        """,
    )
