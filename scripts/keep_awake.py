"""Open the deployed Streamlit app in a headless browser so it never goes to sleep.

Streamlit Community Cloud puts an app to sleep after a period without visitors.
A plain HTTP request does not count as a visit, so this script loads the page in
Chromium like a real visitor. If the app is already asleep it clicks the
"Yes, get this app back up!" button and waits until the site has loaded again.

Usage:  python scripts/keep_awake.py https://your-app.streamlit.app
Exit code 0 = the app is up, 1 = it could not be confirmed.
"""
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

WAKE_TEXT = "get this app back up"
READY_TEXT = "Choose your"  # heading near the end of the welcome page
URL = sys.argv[1] if len(sys.argv) > 1 else ""


def app_ready(page):
    """True when the Overview page (inside Streamlit Cloud's iframe or directly) is rendered."""
    for frame in page.frames:
        try:
            if frame.get_by_text(READY_TEXT, exact=False).count() > 0:
                return True
        except Exception:
            pass
    return False


def main():
    if not URL.startswith("http"):
        print("Give the app URL, e.g. python scripts/keep_awake.py https://stores-sales-eda.streamlit.app")
        return 1
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        for attempt in range(1, 4):
            print(f"Attempt {attempt}: opening {URL}")
            try:
                page.goto(URL, wait_until="domcontentloaded", timeout=90_000)
            except PlaywrightTimeout:
                print("  page did not respond in 90 s")
                continue
            deadline = time.time() + 240
            woke = False
            while time.time() < deadline:
                if app_ready(page):
                    print("  app is up" + (" (woken from sleep)" if woke else ""))
                    browser.close()
                    return 0
                button = page.get_by_role("button", name=WAKE_TEXT, exact=False)
                if button.count() > 0 and not woke:
                    print("  app was asleep: clicking the wake-up button")
                    button.first.click()
                    woke = True
                page.wait_for_timeout(5_000)
            print("  app did not finish loading in 4 minutes")
        page.screenshot(path="keep_awake_failure.png", full_page=True)
        browser.close()
    return 1


if __name__ == "__main__":
    sys.exit(main())
