"""Optional live browser check. Start the API before invoking this script."""

import argparse
import re
from pathlib import Path

from playwright.sync_api import sync_playwright, expect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:18642")
    parser.add_argument("--analyze", action="store_true")
    parser.add_argument("--shot-dir", type=Path)
    args = parser.parse_args()
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(args.url)
        expect(page.get_by_role("heading", name="Debug a failure.")).to_be_visible()
        expect(page.locator("#status")).to_contain_text("Base", ignore_case=True)
        page.select_option("#examples", "minute")
        expect(page.locator("#code")).to_have_value(
            re.compile("clock_parts")
        )
        if args.analyze:
            page.click("#analyze")
            expect(page.locator("#message")).to_contain_text("Analyzing locally")
            expect(page.locator("#result")).to_be_visible(timeout=165000)
            expect(page.locator("#fixed")).to_contain_text("clock_parts")
            expect(page.locator("#status")).to_contain_text("Base model active")
            print("Live model:", page.locator("#category").inner_text())
        for label, width, height in (("desktop", 1440, 960), ("mobile", 390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            expect(page.locator("#analyze")).to_be_enabled()
            if args.shot_dir:
                args.shot_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=args.shot_dir / f"{label}.png", full_page=True)
        assert not errors, errors
        browser.close()
    print("Desktop and mobile checks passed")


if __name__ == "__main__":
    main()
