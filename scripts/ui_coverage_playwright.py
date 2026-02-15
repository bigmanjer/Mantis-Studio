"""Playwright UI coverage test for the Mantis Studio Streamlit app.

Install:
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
    pip install -r requirements.txt
    pip install playwright requests
    playwright install

Run:
    python scripts/ui_coverage_playwright.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, TypeAlias

import requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
APP_URL = "http://localhost:8501"
PROJECTS_LABEL = "Projects"
NAV_LABELS = [
    "Dashboard",
    PROJECTS_LABEL,
    "Write",
    "Editor",
    "World Bible",
    "Export",
    "AI Settings",
]
SAMPLE_TEXT = "Automated UI coverage input."
DEFAULT_TIMEOUT_MS = 5000
REQUEST_TIMEOUT_SECONDS = 2
Scope: TypeAlias = Page | Locator


@dataclass
class UIAction:
    """Represents a single UI action and its result."""

    label: str
    status: str
    details: str = ""


def _record(actions: list[UIAction], label: str, status: str, details: str = "") -> None:
    actions.append(UIAction(label=label, status=status, details=details))
    detail_suffix = f" ({details})" if details else ""
    print(f"[UI] {label}: {status}{detail_suffix}")


def _start_streamlit() -> subprocess.Popen:
    """Launch the Streamlit app in a subprocess."""
    env = os.environ.copy()
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/main.py",
        "--server.headless",
        "true",
        "--server.port",
        "8501",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false",
    ]
    return subprocess.Popen(
        cmd,
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )


def _wait_for_server(timeout_seconds: int = 60) -> None:
    """Wait for the Streamlit server to respond."""
    for _ in range(timeout_seconds):
        try:
            health_response = requests.get(
                f"{APP_URL}/_stcore/health", timeout=REQUEST_TIMEOUT_SECONDS
            )
            if health_response.ok:
                return
        except requests.RequestException:
            pass
        try:
            # Fallback to root endpoint if the health check is unavailable.
            root_response = requests.get(APP_URL, timeout=REQUEST_TIMEOUT_SECONDS)
            if root_response.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError("Streamlit server did not start within the expected timeout.")


def _click_with_side_effects(
    page: Page, locator: Locator, actions: list[UIAction], label: str
) -> None:
    """Click a locator and handle optional popups/downloads."""
    if locator.count() == 0:
        _record(actions, label, "failed", "not found")
        return
    element = locator.first
    try:
        if not element.is_visible():
            _record(actions, label, "skipped", "not visible")
            return
        if not element.is_enabled():
            _record(actions, label, "skipped", "disabled")
            return
    except PlaywrightError as exc:
        _record(actions, label, "failed", f"state error: {exc}")
        return

    try:
        with page.expect_popup(timeout=1000) as popup_info:
            element.click(timeout=DEFAULT_TIMEOUT_MS)
        popup = popup_info.value
        _record(actions, label, "clicked", "popup opened")
        popup.close()
        page.wait_for_timeout(500)
        return
    except PlaywrightTimeoutError:
        pass

    try:
        with page.expect_download(timeout=1000) as download_info:
            element.click(timeout=DEFAULT_TIMEOUT_MS)
        download = download_info.value
        download_path = Path(tempfile.gettempdir()) / download.suggested_filename
        download.save_as(str(download_path))
        _record(actions, label, "clicked", f"downloaded {download_path.name}")
        page.wait_for_timeout(500)
        return
    except PlaywrightTimeoutError:
        pass

    try:
        element.click(timeout=DEFAULT_TIMEOUT_MS)
        _record(actions, label, "clicked")
        page.wait_for_timeout(500)
    except PlaywrightError as exc:
        _record(actions, label, "failed", str(exc))


def _fill_textboxes(scope: Scope, actions: list[UIAction]) -> None:
    """Fill any visible text inputs with sample data."""
    textboxes = scope.get_by_role("textbox")
    for idx in range(textboxes.count()):
        box = textboxes.nth(idx)
        try:
            if not box.is_visible() or not box.is_editable():
                continue
            label = box.get_attribute("aria-label") or "textbox"
            current = box.input_value()
            new_value = f"{SAMPLE_TEXT} #{idx + 1}"
            if current != new_value:
                box.fill(new_value)
                _record(actions, f"Textbox: {label}", "filled")
            else:
                _record(actions, f"Textbox: {label}", "skipped", "already set")
        except PlaywrightError as exc:
            _record(actions, "Textbox", "failed", str(exc))


def _fill_number_inputs(scope: Scope, actions: list[UIAction]) -> None:
    """Adjust number inputs so they register a change."""
    spinbuttons = scope.get_by_role("spinbutton")
    for idx in range(spinbuttons.count()):
        spin = spinbuttons.nth(idx)
        try:
            if not spin.is_visible() or not spin.is_editable():
                continue
            label = spin.get_attribute("aria-label") or "number input"
            spin.fill(str(3 + idx))
            _record(actions, f"Number input: {label}", "set")
        except PlaywrightError as exc:
            _record(actions, "Number input", "failed", str(exc))


def _toggle_checkboxes(scope: Scope, page: Page, actions: list[UIAction]) -> None:
    """Toggle each checkbox once."""
    checkboxes = scope.get_by_role("checkbox")
    for idx in range(checkboxes.count()):
        checkbox = checkboxes.nth(idx)
        try:
            if not checkbox.is_visible() or not checkbox.is_enabled():
                continue
            label = checkbox.get_attribute("aria-label") or f"checkbox {idx + 1}"
            checkbox.click()
            _record(actions, f"Checkbox: {label}", "toggled")
            page.wait_for_timeout(200)
        except PlaywrightError as exc:
            _record(actions, "Checkbox", "failed", str(exc))


def _select_comboboxes(scope: Scope, page: Page, actions: list[UIAction]) -> None:
    """Open comboboxes and select the first available option."""
    comboboxes = scope.locator("[role='combobox']")
    for idx in range(comboboxes.count()):
        combo = comboboxes.nth(idx)
        try:
            if not combo.is_visible() or not combo.is_enabled():
                continue
            label = combo.get_attribute("aria-label") or f"combobox {idx + 1}"
            combo.click()
            options = page.locator("[role='listbox'] [role='option']")
            if options.count() == 0:
                _record(actions, f"Combobox: {label}", "skipped", "no options")
                continue
            options.first.click()
            _record(actions, f"Combobox: {label}", "selected")
        except PlaywrightError as exc:
            _record(actions, "Combobox", "failed", str(exc))


def _click_radios(scope: Scope, page: Page, actions: list[UIAction]) -> None:
    """Click each radio button."""
    radios = scope.locator("[role='radio']")
    for idx in range(radios.count()):
        radio = radios.nth(idx)
        try:
            if not radio.is_visible() or not radio.is_enabled():
                continue
            label = radio.get_attribute("aria-label") or f"radio {idx + 1}"
            radio.click()
            _record(actions, f"Radio: {label}", "selected")
            page.wait_for_timeout(200)
        except PlaywrightError as exc:
            _record(actions, "Radio", "failed", str(exc))


def _click_tabs(scope: Scope, page: Page, actions: list[UIAction]) -> None:
    """Click each tab in tab sets to reveal content."""
    tabs = scope.get_by_role("tab")
    for idx in range(tabs.count()):
        tab = tabs.nth(idx)
        try:
            if not tab.is_visible() or not tab.is_enabled():
                continue
            label = tab.inner_text() or f"tab {idx + 1}"
            tab.click()
            _record(actions, f"Tab: {label}", "clicked")
            page.wait_for_timeout(300)
        except PlaywrightError as exc:
            _record(actions, "Tab", "failed", str(exc))


def _upload_file_if_present(scope: Scope, actions: list[UIAction]) -> None:
    """Upload a sample file when a file input is present."""
    file_inputs = scope.locator("input[type='file']")
    if file_inputs.count() == 0:
        return
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as tmp:
            tmp.write("Sample draft for automated UI coverage.\n")
        for idx in range(file_inputs.count()):
            file_input = file_inputs.nth(idx)
            try:
                if not file_input.is_visible() or not file_input.is_enabled():
                    continue
                file_input.set_input_files(tmp_path)
                _record(actions, "File upload", "uploaded", os.path.basename(tmp_path))
            except PlaywrightError as exc:
                _record(actions, "File upload", "failed", str(exc))
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)


def _should_skip_label(label: str, skip_set_lower: Iterable[str]) -> bool:
    """Return True when a label matches a lowercase skip token."""
    return label.lower() in skip_set_lower


def _collect_nav_skip_labels(page: Page) -> list[str]:
    """Collect nav button labels (including emojis) for skip filtering."""
    labels = list(NAV_LABELS)
    for nav in NAV_LABELS:
        locator = page.get_by_role("button", name=re.compile(nav, re.IGNORECASE))
        if locator.count():
            text = locator.first.inner_text().strip()
            if text and text not in labels:
                labels.append(text)
    return labels


def _click_visible_buttons(
    scope: Scope, page: Page, actions: list[UIAction], skip_labels: Iterable[str]
) -> None:
    """Click every visible button except those in the skip list."""
    skip_set_lower = {label.lower() for label in skip_labels}
    button_texts = scope.locator("button").all_inner_texts()
    link_buttons = scope.locator("a[role='button']").all_inner_texts()
    ordered_labels: list[str] = []
    seen_labels = set()
    for text in button_texts + link_buttons:
        label = text.strip()
        if not label or label in seen_labels:
            continue
        seen_labels.add(label)
        ordered_labels.append(label)
    for label in ordered_labels:
        if _should_skip_label(label, skip_set_lower):
            continue
        locator = scope.locator("button", has_text=label)
        if locator.count() == 0:
            locator = scope.locator("a[role='button']", has_text=label)
        _click_with_side_effects(page, locator, actions, f"Button: {label}")


def _exercise_controls(
    scope: Scope, page: Page, actions: list[UIAction], skip_labels: Iterable[str]
) -> None:
    """Exercise inputs, tabs, and buttons within a page scope."""
    _fill_textboxes(scope, actions)
    _fill_number_inputs(scope, actions)
    _toggle_checkboxes(scope, page, actions)
    _select_comboboxes(scope, page, actions)
    _click_radios(scope, page, actions)
    _click_tabs(scope, page, actions)
    _upload_file_if_present(scope, actions)
    _click_visible_buttons(scope, page, actions, skip_labels=skip_labels)
    # Run a second pass to catch buttons revealed by expanders or reruns.
    _click_visible_buttons(scope, page, actions, skip_labels=skip_labels)


def _click_nav(page: Page, actions: list[UIAction], label: str) -> None:
    """Navigate using sidebar buttons."""
    locator = page.get_by_role("button", name=re.compile(label, re.IGNORECASE))
    _click_with_side_effects(page, locator, actions, f"Nav: {label}")
    page.wait_for_timeout(800)


def _ensure_project_created(page: Page, actions: list[UIAction]) -> None:
    """Create a project if the create form is present."""
    if page.get_by_role("button", name=re.compile("Create Project", re.IGNORECASE)).count() == 0:
        return
    _fill_textboxes(page, actions)
    create_button = page.get_by_role("button", name=re.compile("Create Project", re.IGNORECASE))
    _click_with_side_effects(page, create_button, actions, "Create Project")
    page.wait_for_timeout(1200)


def _run_ui_coverage() -> list[UIAction]:
    """Run the UI coverage flow across all navigation sections."""
    actions: list[UIAction] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT_MS)

        sidebar = page.locator("section[data-testid='stSidebar']")
        main_area = page.locator("section[data-testid='stMain']")
        if sidebar.count() == 0:
            sidebar = page
        if main_area.count() == 0:
            main_area = page
        nav_skip_labels = _collect_nav_skip_labels(page)

        for nav in NAV_LABELS:
            _click_nav(page, actions, nav)
            _exercise_controls(sidebar, page, actions, skip_labels=nav_skip_labels)
            if nav == PROJECTS_LABEL:
                _ensure_project_created(page, actions)
            _exercise_controls(main_area, page, actions, skip_labels=[])

        browser.close()
    return actions


def main() -> int:
    """Entry point for the UI coverage script."""
    streamlit_process = _start_streamlit()
    try:
        _wait_for_server()
        actions = _run_ui_coverage()
    finally:
        streamlit_process.terminate()
        try:
            streamlit_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            streamlit_process.kill()

    status_counts = {}
    for action in actions:
        status_counts[action.status] = status_counts.get(action.status, 0) + 1
    success_statuses = {"clicked", "filled", "set", "toggled", "selected", "uploaded"}
    summary = {
        "total_actions": len(actions),
        "successful": sum(
            1 for action in actions if action.status in success_statuses
        ),
        "failed": status_counts.get("failed", 0),
        "skipped": status_counts.get("skipped", 0),
        "status_counts": status_counts,
    }
    print("[UI] Summary:", json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
