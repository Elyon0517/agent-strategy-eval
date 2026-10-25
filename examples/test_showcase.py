"""Browser acceptance test. Run: uv run --with playwright python examples/test_showcase.py"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / "examples/showcase.py")], cwd=root, check=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1100})
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((root / "docs/showcase/index.html").as_uri())
        expect(page.get_by_role("heading", name="Which context survives?")).to_be_visible()
        expect(page.locator("tbody tr:visible")).to_have_count(15)
        page.get_by_label("Fixture", exact=True).select_option("profile")
        expect(page.locator("tbody tr:visible")).to_have_count(5)
        personalized = page.locator("tbody tr:visible").filter(has_text="personalized-memory")
        personalized.get_by_text("Inspect context").click()
        expect(personalized.locator("pre")).to_contain_text("Answer in Spanish")
        expect(personalized).to_contain_text("PASS")
        data = json.loads((root / "docs/showcase/report.json").read_text())
        assert len(data["measurements"]) == 15
        assert data["strategies"]["no-memory"]["fixture_pass_rate"] == 0
        assert data["strategies"]["personalized-memory"]["fixture_pass_rate"] == 1
        page.get_by_label("Fixture", exact=True).select_option("all")
        screenshots = root / "docs/screenshots"
        screenshots.mkdir(exist_ok=True)
        page.screenshot(path=str(screenshots / "strategy-scorecard.png"), full_page=True)
        page.set_viewport_size({"width": 390, "height": 844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        assert errors == []
        browser.close()
    print("Browser acceptance passed: strategy-scorecard")


if __name__ == "__main__":
    main()
