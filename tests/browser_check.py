"""Browser acceptance checks; requires Playwright and installed Chrome."""
import argparse
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".svg": "image/svg+xml", ".jpg": "image/jpeg"}


def serve_from_repo(route):
    """Answer requests for the GitHub Pages URL with files from this checkout."""
    path = urlparse(route.request.url).path.removeprefix("/portfolio/")
    file = ROOT / path
    if file.is_dir():
        file = file / "index.html"
    if not file.is_file():
        return route.fulfill(status=404, body="not found")
    route.fulfill(body=file.read_bytes(), content_type=TYPES.get(file.suffix, "application/octet-stream"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8766/")
    parser.add_argument("--output", default=str(ROOT / "artifacts"))
    args = parser.parse_args()
    base = args.url.rstrip("/") + "/"
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    routes = ["", "projects/", "resume/", "contact/"]
    report = {"base_url": base, "viewports": [], "errors": [], "form_delivery": "not attempted; submission intercepted to avoid opening an external mail application"}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        page = context.new_page()
        page.on("pageerror", lambda error: report["errors"].append(str(error)))
        page.on("console", lambda message: report["errors"].append(message.text) if message.type == "error" else None)
        page.on("response", lambda response: report["errors"].append(f"HTTP {response.status}: {response.url}") if response.status >= 400 else None)
        for width in [320, 390, 768, 1280]:
            page.set_viewport_size({"width": width, "height": 900})
            for route in routes:
                response = page.goto(urljoin(base, route), wait_until="networkidle")
                assert response and response.ok, (route, response.status if response else None)
                assert page.locator("h1").count() == 1
                assert page.locator("nav a").count() == 5
                assert page.locator("nav a[aria-current='page']").count() == 1
                measurement = page.evaluate("""() => ({
                    viewport: innerWidth,
                    content: document.documentElement.scrollWidth,
                    brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src)
                })""")
                assert measurement["content"] <= width, (route, width, measurement)
                assert not measurement["brokenImages"], measurement
                report["viewports"].append({"route": route or "/", "width": width, "horizontal_overflow": False})
                if width in [390, 1280]:
                    page.screenshot(path=str(output / f"{route.strip('/') or 'home'}-{width}.png"), full_page=True)
        page.set_viewport_size({"width": 1280, "height": 900})
        for route in routes:
            page.goto(urljoin(base, route), wait_until="networkidle")
            links = page.locator("a[href]").evaluate_all("els => els.map(e => ({href:e.getAttribute('href'), absolute:e.href, inNav:!!e.closest('nav')}))")
            for link in links:
                href = link["href"]
                if href.startswith(("https:", "mailto:")):
                    continue
                # global.js builds nav links from BASE_PATH; hand-written links stay relative
                assert link["inNav"] or not href.startswith("/"), href
                local_url = urlparse(link["absolute"])
                result = context.request.get(link["absolute"].split("#")[0])
                assert result.ok, (route, href, result.status)
                if local_url.fragment:
                    checker = context.new_page()
                    checker.goto(link["absolute"], wait_until="domcontentloaded")
                    assert checker.locator(f'[id="{local_url.fragment}"]').count() == 1, link
                    checker.close()
        page.goto(base, wait_until="networkidle")
        nav = page.get_by_role("navigation")
        for label, expected in [("Projects", "projects/"), ("Résumé", "resume/"), ("Contact", "contact/"), ("Home", "")]:
            nav.get_by_role("link", name=label, exact=True).click()
            page.wait_for_url(urljoin(base, expected))
            assert nav.locator("a.current").inner_text() == label
        github = nav.get_by_role("link", name="GitHub", exact=False)
        assert github.get_attribute("target") == "_blank" and "noopener" in github.get_attribute("rel")
        page.goto(urljoin(base, "projects/index.html"), wait_until="networkidle")
        assert nav.locator("a.current").inner_text() == "Projects"
        report["navigation_clicks"] = "passed"

        # Step 5: the form builds a percent-encoded URL. Point it at a local URL
        # so the test can read the query string instead of opening a mail app.
        page.goto(urljoin(base, "contact/"), wait_until="networkidle")
        sent = []
        page.route("**/__mailto-check*", lambda route: (sent.append(route.request.url), route.fulfill(body="ok")))
        page.evaluate("document.querySelector('form').action = location.origin + '/__mailto-check'")
        page.get_by_role("button", name="Open email draft").click()
        page.wait_for_timeout(300)
        assert not sent, "Required fields should block an empty submit"
        page.get_by_label("Subject").fill("Portfolio test & symbols")
        page.get_by_label("Message", exact=True).fill("Hello Kevin,\nTesting a multi-line message.")
        page.get_by_role("button", name="Open email draft").click()
        page.wait_for_url("**/__mailto-check*")
        query = urlparse(sent[0]).query
        assert query == "subject=Portfolio%20test%20%26%20symbols&body=Hello%20Kevin%2C%0ATesting%20a%20multi-line%20message.", query
        report["form_validation_and_encoding"] = "passed"

        # Step 4: theme switcher follows the OS, then remembers a manual choice
        dark = browser.new_context(viewport={"width": 1280, "height": 900}, color_scheme="dark")
        tab = dark.new_page()
        tab.goto(base, wait_until="networkidle")
        background = "getComputedStyle(document.body).backgroundColor"
        assert tab.evaluate(background) == "rgb(21, 25, 23)"
        switcher = tab.locator(".color-scheme select")
        assert switcher.input_value() == "light dark"
        assert tab.locator(".color-scheme option").first.inner_text() == "Automatic (Dark)"
        box = tab.locator(".color-scheme").bounding_box()
        assert abs(box["y"] - 16) < 2 and abs(box["x"] + box["width"] - (1280 - 16)) < 2, box
        tab.screenshot(path=str(output / "home-dark-1280.png"), full_page=True)
        switcher.select_option("light")
        assert tab.evaluate(background) == "rgb(248, 247, 243)"
        assert tab.evaluate("localStorage.colorScheme") == "light"
        tab.reload(wait_until="networkidle")
        assert switcher.input_value() == "light" and tab.evaluate(background) == "rgb(248, 247, 243)"
        tab.goto(urljoin(base, "resume/"), wait_until="networkidle")
        assert switcher.input_value() == "light", "Choice should carry across pages"
        switcher.select_option("dark")
        tab.screenshot(path=str(output / "resume-dark-1280.png"), full_page=True)
        switcher.select_option("light dark")
        assert tab.evaluate(background) == "rgb(21, 25, 23)"
        dark.close()
        report["dark_mode_switch_and_persistence"] = "passed"

        # Step 3: on GitHub Pages the same nav must point inside /portfolio/
        pages_site = browser.new_context(viewport={"width": 1280, "height": 900})
        pages_site.route("https://kevinkiyosepyo.github.io/**", serve_from_repo)
        tab = pages_site.new_page()
        tab.goto("https://kevinkiyosepyo.github.io/portfolio/projects/", wait_until="networkidle")
        hrefs = tab.locator("nav a").evaluate_all("els => els.map(e => e.href)")
        assert hrefs[:4] == [f"https://kevinkiyosepyo.github.io/portfolio/{p}" for p in ["", "projects/", "resume/", "contact/"]], hrefs
        assert tab.locator("nav a.current").inner_text() == "Projects"
        tab.get_by_role("navigation").get_by_role("link", name="Résumé", exact=True).click()
        tab.wait_for_url("https://kevinkiyosepyo.github.io/portfolio/resume/")
        assert tab.locator("nav a.current").inner_text() == "Résumé"
        pages_site.close()
        report["github_pages_base_path"] = "passed"
        page.goto(base, wait_until="networkidle")
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.textContent") == "Skip to content"
        page.keyboard.press("Enter")
        assert page.evaluate("location.hash") == "#main"
        report["keyboard_skip_link"] = "passed"
        assert not report["errors"], report["errors"]
        context.close()
        browser.close()
    report["passed"] = True
    (output / "browser-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
