"""Browser acceptance checks; requires Playwright and installed Chrome."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
TYPES = {".html": "text/html", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml", ".jpg": "image/jpeg"}
API_URL = "https://api.github.com/users/kevinkiyosepyo"
API_PATTERN = "https://api.github.com/users/**"
PROFILE = {"login": "kevinkiyosepyo", "public_repos": 37, "public_gists": 0, "followers": 14, "following": 9}


def mock_profile(context):
    """Keep repeated layout/regression tests independent of API quotas and changes."""
    def respond(route):
        assert route.request.url == API_URL, route.request.url
        route.fulfill(json=PROFILE)
    context.route(API_PATTERN, respond)


def assert_project_cards(page, projects, heading, base):
    cards = page.locator(".projects > article")
    expect(cards).to_have_count(len(projects))
    for index, project in enumerate(projects):
        card = cards.nth(index)
        expect(card.locator(heading)).to_have_text(project["title"])
        expect(card).to_contain_text(project["description"])
        image = card.locator("img")
        expect(image).to_have_count(1)
        assert image.get_attribute("alt") is not None
        assert image.evaluate("image => image.src") == urljoin(base, project["image"])
    if not projects:
        expect(page.locator(".projects")).to_contain_text(re.compile(r"no projects", re.I))


def assert_profile(page, profile=PROFILE):
    stats = page.locator("#profile-stats")
    expect(stats.locator("dl")).to_have_count(1)
    expect(stats.locator("dt")).to_have_count(4)
    expect(stats.locator("dd")).to_have_text([
        str(profile[key]) for key in ["public_repos", "public_gists", "followers", "following"]
    ])
    labels = stats.locator("dt").all_text_contents()
    for label, pattern in zip(labels, [r"public repo", r"public gist", r"followers", r"following"]):
        assert re.search(pattern, label, re.I), labels


def assert_friendly_error(locator):
    expect(locator).to_contain_text(re.compile(r"could not|couldn.t|unable|unavailable|failed|try again|error", re.I))
    assert not re.search(r"TypeError|SyntaxError|undefined|\bat \w+ \(", locator.inner_text())


def check_dynamic_data(browser, base, projects, report):
    """Prove both pages respond to changed JSON without changing their HTML."""
    context = browser.new_context()
    mock_profile(context)
    changed = [dict(project, title=f"Updated project {i + 1}") for i, project in enumerate(projects[:2])]
    context.route("**/lib/projects.json", lambda route: route.fulfill(json=changed))
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(urljoin(base, "projects/"), wait_until="networkidle")
    assert_project_cards(page, changed, "h2", base)
    expect(page.locator(".projects-title")).to_contain_text(re.compile(r"\b2\b"))
    page.goto(base, wait_until="networkidle")
    assert_project_cards(page, changed, "h3", base)
    assert_profile(page)

    # Exercise the reusable public function: changing the heading and rendering
    # a second time must replace the previous result, including an empty result.
    result = page.evaluate("""async ({moduleUrl, projects}) => {
        const {renderProjects} = await import(moduleUrl);
        const container = document.createElement('div');
        document.querySelector('main').append(container);
        renderProjects(projects, container, 'h4');
        renderProjects(projects, container, 'h4');
        const repeated = {articles: container.querySelectorAll('article').length,
            headings: [...container.querySelectorAll('h4')].map(h => h.textContent)};
        renderProjects(projects.slice(0, 1), container);
        const defaultHeading = container.querySelector('h2')?.textContent;
        const remaining = container.querySelectorAll('article').length;
        renderProjects([], container);
        const empty = {articles: container.querySelectorAll('article').length, text: container.textContent};
        container.remove();
        return {repeated, defaultHeading, remaining, empty};
    }""", {"moduleUrl": urljoin(base, "global.js"), "projects": changed})
    assert result["repeated"] == {"articles": 2, "headings": [project["title"] for project in changed]}, result
    assert result["remaining"] == 1 and result["defaultHeading"] == changed[0]["title"], result
    assert result["empty"]["articles"] == 0 and re.search(r"no projects", result["empty"]["text"], re.I), result

    context.unroute("**/lib/projects.json")
    context.route("**/lib/projects.json", lambda route: route.fulfill(json=[]))
    page.goto(urljoin(base, "projects/"), wait_until="networkidle")
    assert_project_cards(page, [], "h2", base)
    expect(page.locator(".projects-title")).to_contain_text(re.compile(r"\b0\b"))
    page.goto(base, wait_until="networkidle")
    assert_project_cards(page, [], "h3", base)
    assert_profile(page)
    assert not errors, errors
    context.close()
    report["dynamic_data_count_headings_and_empty_states"] = "passed"
    report["reusable_renderer_replaces_previous_content"] = "passed"


def check_failures(browser, base, projects, report):
    cases = [
        ("projects_http_failure", "projects/", "projects", 404, "missing"),
        ("projects_invalid_json", "projects/", "projects", 200, "{not valid json"),
        ("home_project_failure_preserves_profile", "", "projects", 503, "unavailable"),
        ("home_api_failure_preserves_projects", "", "profile", 403, '{"message":"rate limit"}'),
        ("home_api_invalid_json_preserves_projects", "", "profile", 200, "{not valid json"),
    ]
    report["failure_resilience"] = []
    for name, route, failed_service, status, body in cases:
        context = browser.new_context()
        mock_profile(context)
        pattern = "**/lib/projects.json" if failed_service == "projects" else API_PATTERN
        context.route(pattern, lambda request: request.fulfill(
            status=status, content_type="application/json", body=body))
        page = context.new_page()
        errors, logs = [], []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: logs.append(message.text) if message.type == "error" else None)
        page.goto(urljoin(base, route), wait_until="networkidle")
        if failed_service == "projects":
            expect(page.locator(".projects > article")).to_have_count(0)
            assert_friendly_error(page.locator(".projects"))
            if not route:
                assert_profile(page)
        else:
            assert_friendly_error(page.locator("#profile-stats"))
            assert_project_cards(page, projects[:3], "h3", base)
        assert page.get_by_role("navigation").is_visible()
        page.locator(".color-scheme select").select_option("dark")
        assert page.evaluate("localStorage.colorScheme") == "dark"
        assert not errors, (name, errors)
        assert logs, f"{name} should log the failed fetch or parse for diagnosis"
        report["failure_resilience"].append(name)
        context.close()


def check_live_api(browser, base, report):
    """Optional single real API request, separate from deterministic regressions."""
    context = browser.new_context()
    page = context.new_page()
    with page.expect_response(API_URL, timeout=30000) as response_info:
        page.goto(base, wait_until="networkidle")
    response = response_info.value
    assert response.ok, f"Live GitHub API returned HTTP {response.status}"
    profile = response.json()
    assert profile["login"].lower() == "kevinkiyosepyo", profile["login"]
    assert_profile(page, profile)
    report["live_github_api"] = {"status": response.status, "login": profile["login"],
        "displayed_stats": {key: profile[key] for key in ["public_repos", "public_gists", "followers", "following"]}}
    context.close()


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
    parser.add_argument("--live-api", action="store_true", help="Also verify one real GitHub API response")
    args = parser.parse_args()
    base = args.url.rstrip("/") + "/"
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    routes = ["", "projects/", "resume/", "contact/"]
    projects = json.loads((ROOT / "lib/projects.json").read_text())
    report = {"base_url": base, "viewports": [], "errors": [], "form_delivery": "not attempted; submission intercepted to avoid opening an external mail application"}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 900}, reduced_motion="reduce")
        mock_profile(context)
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
                if route == "projects/":
                    assert_project_cards(page, projects, "h2", base)
                    expect(page.locator(".projects-title")).to_contain_text(re.compile(rf"\b{len(projects)}\b"))
                elif route == "":
                    expect(page.get_by_role("heading", name=re.compile("Latest Projects"), level=2)).to_have_count(1)
                    assert_project_cards(page, projects[:3], "h3", base)
                    assert_profile(page)
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
                    checker.goto(link["absolute"], wait_until="networkidle")
                    expect(checker.locator(f'[id="{local_url.fragment}"]')).to_have_count(1)
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
        mock_profile(dark)
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
        mock_profile(pages_site)
        pages_site.route("https://kevinkiyosepyo.github.io/**", serve_from_repo)
        tab = pages_site.new_page()
        tab.goto("https://kevinkiyosepyo.github.io/portfolio/projects/", wait_until="networkidle")
        hrefs = tab.locator("nav a").evaluate_all("els => els.map(e => e.href)")
        assert hrefs[:4] == [f"https://kevinkiyosepyo.github.io/portfolio/{p}" for p in ["", "projects/", "resume/", "contact/"]], hrefs
        assert tab.locator("nav a.current").inner_text() == "Projects"
        assert_project_cards(tab, projects, "h2", "https://kevinkiyosepyo.github.io/portfolio/")
        assert tab.locator(".projects img").evaluate_all("images => images.every(image => image.complete && image.naturalWidth > 0)")
        tab.get_by_role("navigation").get_by_role("link", name="Résumé", exact=True).click()
        tab.wait_for_url("https://kevinkiyosepyo.github.io/portfolio/resume/")
        assert tab.locator("nav a.current").inner_text() == "Résumé"
        tab.get_by_role("navigation").get_by_role("link", name="Home", exact=True).click()
        tab.wait_for_url("https://kevinkiyosepyo.github.io/portfolio/")
        assert_project_cards(tab, projects[:3], "h3", "https://kevinkiyosepyo.github.io/portfolio/")
        assert_profile(tab)
        pages_site.close()
        report["github_pages_base_path"] = "passed"
        page.goto(base, wait_until="networkidle")
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.textContent") == "Skip to content"
        page.keyboard.press("Enter")
        assert page.evaluate("location.hash") == "#main"
        report["keyboard_skip_link"] = "passed"
        assert not report["errors"], report["errors"]
        check_dynamic_data(browser, base, projects, report)
        check_failures(browser, base, projects, report)
        if args.live_api:
            check_live_api(browser, base, report)
        context.close()
        browser.close()
    report["passed"] = True
    (output / "browser-report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
