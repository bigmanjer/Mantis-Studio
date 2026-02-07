import streamlit as st


def render_footer(
    version: str,
    support_url: str = "https://github.com/bigmanjer/Mantis-Studio/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    st.markdown(
        f"""
        <style>
        .mantis-footer {{
            margin-top: 3rem;
            border-top: 1px solid var(--mantis-divider, #143023);
            padding: 2rem 1rem 1.5rem;
        }}
        .mantis-footer-grid {{
            display: grid;
            grid-template-columns: 1.5fr 1fr 1fr 1fr;
            gap: 2rem;
            max-width: 960px;
            margin: 0 auto;
        }}
        .mantis-footer-section h4 {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--mantis-muted, #9CA3AF);
            margin: 0 0 0.75rem;
        }}
        .mantis-footer-section ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .mantis-footer-section li {{
            margin-bottom: 0.4rem;
        }}
        .mantis-footer-section a {{
            color: var(--mantis-text, #ecfdf5);
            text-decoration: none;
            font-size: 0.85rem;
            transition: color 0.15s;
        }}
        .mantis-footer-section a:hover {{
            color: var(--mantis-accent, #22c55e);
        }}
        .mantis-footer-section a:focus-visible {{
            outline: 2px solid var(--mantis-accent, #22c55e);
            outline-offset: 2px;
            border-radius: 2px;
        }}
        .mantis-footer-brand {{
            font-size: 0.85rem;
            color: var(--mantis-muted, #9CA3AF);
            line-height: 1.6;
        }}
        .mantis-footer-brand strong {{
            color: var(--mantis-text, #ecfdf5);
            font-size: 0.95rem;
        }}
        @media (max-width: 640px) {{
            .mantis-footer-grid {{
                grid-template-columns: 1fr 1fr;
                gap: 1.5rem;
            }}
        }}
        @media (max-width: 400px) {{
            .mantis-footer-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        <footer class="mantis-footer" role="contentinfo" aria-label="Site footer">
          <div class="mantis-footer-grid">
            <div class="mantis-footer-section mantis-footer-brand">
              <strong>MANTIS Studio</strong><br>
              Modular narrative workspace<br>
              <small>&copy; 2024 MANTIS Studio &middot; v{version}</small>
            </div>
            <nav class="mantis-footer-section" aria-label="Navigation">
              <h4>Navigation</h4>
              <ul>
                <li><a href="?page=home">Dashboard</a></li>
                <li><a href="?page=projects">Projects</a></li>
                <li><a href="?page=outline">Outline</a></li>
                <li><a href="?page=export">Export</a></li>
              </ul>
            </nav>
            <nav class="mantis-footer-section" aria-label="Legal Center">
              <h4>Legal Center</h4>
              <ul>
                <li><a href="?page=terms">Terms of Service</a></li>
                <li><a href="?page=privacy">Privacy Policy</a></li>
                <li><a href="?page=legal">All Policies</a></li>
              </ul>
            </nav>
            <nav class="mantis-footer-section" aria-label="Support">
              <h4>Support</h4>
              <ul>
                <li><a href="?page=help">Help</a></li>
                <li><a href="{support_url}" target="_blank" rel="noopener noreferrer">Report an Issue</a></li>
                <li><a href="mailto:{contact_email}">Contact</a></li>
              </ul>
            </nav>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )
