"""Compatibility footer exports for legacy imports."""

from app.layout.layout import _build_footer_nav_links, render_footer


def build_footer_nav_links() -> str:
    return _build_footer_nav_links()


def render_footer_shared(
    version: str,
    support_url: str = "https://github.com/bigmanjer/mantis-testing/issues",
    contact_email: str = "support@mantis-studio.example",
) -> None:
    render_footer(version, support_url=support_url, contact_email=contact_email)


__all__ = ["build_footer_nav_links", "render_footer_shared"]
