"""Optional browser QA: pip install playwright; playwright install chromium."""

from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1365, "height": 1000})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((ROOT / "examples/demo-report/report.html").as_uri())
        assert page.locator(".finding:visible").count() == 7
        page.locator("#severity").select_option("high")
        assert page.locator(".finding:visible").count() == 1
        page.locator("#severity").select_option("all")
        page.locator("#region").select_option("ap-southeast-1")
        assert page.locator(".finding:visible").count() == 1
        page.locator("#region").select_option("all")
        page.locator("#search").fill("this-resource-does-not-exist")
        assert page.locator("#empty").is_visible()
        page.locator("#search").fill("")
        assert page.locator(".finding:visible").count() == 7
        output = ROOT / "reports" / "screenshots"
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / "desktop.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
        page.locator("summary").first.click()
        assert page.locator("details").first.get_attribute("open") is not None
        page.screenshot(path=str(output / "mobile.png"), full_page=True)
        assert not errors, errors
        browser.close()
    print("Browser report checks passed.")


if __name__ == "__main__":
    main()
