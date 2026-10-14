"""Headless software UI test for the local app, separate from personal browser state.

Start the server, then:
uv run --with playwright python tests/browser_smoke.py
"""

import json
import os
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def main():
    previews = Path(".intentbench/previews")
    previews.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1080})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(
            os.environ.get("INTENTBENCH_TEST_URL", "http://127.0.0.1:8765"),
            wait_until="networkidle",
        )
        page.wait_for_selector("#scenario-rows tr")
        assert page.locator("#scenario-rows tr").count() == 90
        page.screenshot(path=str(previews / "workbench.png"), full_page=True)
        page.select_option("#suite", "smoke")
        expect(page.locator("#scenario-rows tr")).to_have_count(9)
        page.select_option("#agent", "gullible")
        page.click("#run")
        page.wait_for_selector("#results:not(.hide)")
        assert page.locator("#episode-rows tr").count() == 9
        assert "100.0%" in page.locator("#metrics").inner_text()
        page.locator("#episode-rows tr").filter(has_text="email.injection.attack").click()
        assert page.locator("#evidence .violation").count() > 0
        page.screenshot(path=str(previews / "trace.png"), full_page=True)
        page.locator("[data-view=history]").click()
        page.wait_for_selector("#history-rows tr")
        page.locator("[data-view=author]").click()
        assert page.locator("#author-view").is_visible()
        page.locator("[data-view=benchmarks]").click()
        expect(page.locator("#benchmark-catalog tr")).to_have_count(6)
        assert page.locator("#native-config").is_visible()
        if os.environ.get("INTENTBENCH_TEST_NATIVE_FIXTURE"):
            # Server must run with PYTHONPATH=tests to load this trusted offline fixture.
            page.locator("#native-config").fill(
                json.dumps(
                    {
                        "benchmark": "stwebagentbench",
                        "task_ids": ["0"],
                        "environment_factory": "test_benchmarks:create_native_fixture",
                        "agent": {
                            "kind": "python",
                            "factory": "test_benchmarks:agent",
                            "options": {"actions": ["click('1')", "click('2')"], "fixture": True},
                        },
                    }
                )
            )
            page.locator("#native-run").click()
            expect(page.locator("#native-result")).to_contain_text('"reward": 0.375', timeout=15000)
            expect(page.locator("#native-history [data-native-run]").first).to_be_visible()
        page.screenshot(path=str(previews / "benchmarks.png"), full_page=True)
        page.locator("[data-view=workbench]").click()
        page.select_option("#suite", "research-factors")
        expect(page.locator("#scenario-rows tr")).to_have_count(108)
        page.set_viewport_size({"width": 390, "height": 844})
        page.locator("[data-view=benchmarks]").click()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.locator("[data-view=workbench]").click()
        page.screenshot(path=str(previews / "mobile.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert not errors, errors
        browser.close()
    print(f"Browser run, trace, history, and narrow-screen checks passed. Previews: {previews}")


if __name__ == "__main__":
    main()
