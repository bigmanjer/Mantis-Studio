from __future__ import annotations

import json
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visual_regression"
OUT.mkdir(parents=True, exist_ok=True)


PAGES = [
    ("dashboard", "Dashboard"),
    ("projects", "Projects"),
    ("outline", "Outline"),
    ("chapters", "Chapters"),
    ("world_bible", "World Bible"),
    ("memory", "Memory"),
    ("insights", "Insights"),
    ("ai_settings", "AI Settings"),
]


def goto_top(page: Page) -> None:
    page.evaluate(
        """
        () => {
          const main = document.querySelector('section.main');
          if (main) { main.scrollTop = 0; }
          window.scrollTo(0, 0);
        }
        """
    )


def click_sidebar_button(page: Page, name: str) -> None:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    btn = sidebar.get_by_role("button", name=name).first
    if btn.count() == 0:
        raise RuntimeError(f"Sidebar button not found: {name}")
    if not btn.is_enabled():
        return
    btn.click(timeout=5000)
    page.wait_for_timeout(900)


def write_theme_config(theme_name: str) -> None:
    cfg_path = ROOT / "projects" / ".mantis_config.json"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    data["ui_theme"] = theme_name
    cfg_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def ensure_nav_section_open(page: Page, section_name: str) -> None:
    sidebar = page.locator('section[data-testid="stSidebar"]')
    section_btn = sidebar.get_by_role("button", name=section_name).first
    if section_btn.count() == 0:
        return
    try:
        section_btn.click(timeout=3000)
        page.wait_for_timeout(400)
    except Exception:
        pass


def goto_page(page: Page, label: str) -> None:
    if label == "AI Settings":
        try:
            click_sidebar_button(page, "Projects")
            page.wait_for_timeout(800)
            project_ai_btn = page.get_by_role("button", name="Go to AI Settings").first
            if project_ai_btn.count() > 0:
                project_ai_btn.click(timeout=4000)
                page.wait_for_timeout(1200)
                return
        except Exception:
            pass
        try:
            page.get_by_role("button", name="AI Settings").first.click(timeout=3000)
            page.wait_for_timeout(900)
            return
        except Exception as exc:
            raise RuntimeError(f"AI Settings navigation failed: {exc}") from exc

    click_sidebar_button(page, label)


def capture_suite(base_url: str) -> dict:
    results: dict = {"base_url": base_url, "themes": {}, "errors": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for theme in ["Dark", "Light"]:
            theme_key = theme.lower()
            results["themes"][theme_key] = {}
            write_theme_config(theme)
            context = browser.new_context(viewport={"width": 1728, "height": 1117})
            page = context.new_page()
            page.goto(base_url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2500)
            for slug, label in PAGES:
                try:
                    goto_page(page, label)
                    goto_top(page)
                    screenshot_path = OUT / f"{theme_key}_{slug}.png"
                    page.screenshot(path=str(screenshot_path), full_page=True)
                    results["themes"][theme_key][slug] = str(screenshot_path)
                except Exception as exc:  # noqa: BLE001
                    results["errors"].append(f"{theme}/{label}: {exc}")
            context.close()
        browser.close()
    return results


def main() -> int:
    started = time.time()
    summary = capture_suite("http://localhost:8510")
    summary["elapsed_seconds"] = round(time.time() - started, 2)
    output_json = OUT / "summary.json"
    output_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(output_json)
    if summary.get("errors"):
        print("Errors:")
        for err in summary["errors"]:
            print(f"- {err}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
