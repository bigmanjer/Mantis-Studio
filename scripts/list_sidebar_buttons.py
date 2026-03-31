import json

from playwright.sync_api import sync_playwright


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1728, "height": 1117})
    page = ctx.new_page()
    page.goto("http://localhost:8510", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    labels = page.eval_on_selector_all(
        'section[data-testid="stSidebar"] button',
        "els => els.map(e => (e.innerText || '').trim()).filter(Boolean)",
    )
    print(json.dumps(labels, ensure_ascii=True))
    ctx.close()
    browser.close()
