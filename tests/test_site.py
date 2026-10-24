"""Lab acceptance tests. Run: python3 -m unittest discover -s tests -v."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.tags = []
        self.text = path.read_text() if path.exists() else ""
        self.feed(self.text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def elements(self, tag):
        return [attrs for name, attrs in self.tags if name == tag]


class LabAcceptanceTests(unittest.TestCase):
    def test_homepage_introduces_kevin_with_accessible_local_photo(self):
        doc = Document(ROOT / "index.html")
        self.assertIn("Kevin Kiyose Pyo: Personal site and portfolio", doc.text)
        self.assertIn("<h1>Kevin Kiyose Pyo</h1>", doc.text)
        self.assertIn("UC San Diego", doc.text)
        self.assertTrue(doc.elements("p"))
        self.assertTrue(doc.elements("img"), "The homepage needs a local photo")
        image = doc.elements("img")[0]
        self.assertTrue(image.get("alt"))
        self.assertTrue(image["src"].startswith("images/"))
        self.assertTrue((ROOT / image["src"]).is_file())
        self.assertIn({"charset": "utf-8"}, doc.elements("meta"))
        self.assertTrue(any(m.get("name") == "viewport" for m in doc.elements("meta")))
        self.assertTrue(any(l.get("href") == "style.css" for l in doc.elements("link")))
        self.assertTrue((ROOT / "style.css").is_file())

    def test_every_page_loads_global_js_instead_of_a_hardcoded_nav(self):
        routes = ["index.html", "projects/index.html", "contact/index.html", "resume/index.html"]
        for route in routes:
            with self.subTest(route=route):
                path = ROOT / route
                doc = Document(path)
                self.assertFalse(doc.elements("nav"), f"{route} still has a hand-written nav")
                self.assertIn({"class": "site-header"}, doc.elements("header"))
                self.assertEqual(len(doc.elements("h1")), 1)
                self.assertTrue(doc.elements("title"))
                self.assertTrue(any(m.get("name") == "viewport" for m in doc.elements("meta")))
                scripts = [s for s in doc.elements("script") if s.get("type") == "module"]
                script_paths = {(path.parent / script["src"]).resolve() for script in scripts}
                expected_scripts = {ROOT / "global.js"}
                if route == "index.html":
                    expected_scripts.add(ROOT / "index.js")
                elif route == "projects/index.html":
                    expected_scripts.add(ROOT / "projects/projects.js")
                self.assertEqual(script_paths, expected_scripts, route)
                self.assertEqual(len(scripts), len(expected_scripts), "Do not load a module twice")
                self.assertTrue(all(script.is_file() for script in script_paths))
                stylesheet = next(l for l in doc.elements("link") if l.get("rel") == "stylesheet")
                self.assertEqual((path.parent / stylesheet["href"]).resolve(), ROOT / "style.css")

    def test_contact_form_uses_get_mailto_contract(self):
        doc = Document(ROOT / "contact/index.html")
        self.assertEqual(doc.elements("form"), [{"action": "mailto:kevinkpyo@gmail.com", "method": "GET"}])
        fields = {field.get("name"): field for field in doc.elements("input") + doc.elements("textarea")}
        self.assertEqual(set(fields), {"subject", "body"})
        self.assertEqual(len(doc.elements("label")), 2)
        self.assertTrue(doc.elements("button"))
        self.assertFalse(doc.elements("table"))

    def test_resume_uses_semantic_sections_and_actual_experience(self):
        doc = Document(ROOT / "resume/index.html")
        for tag in ["section", "article", "h2", "h3", "p", "ul", "li", "a", "time"]:
            self.assertTrue(doc.elements(tag), f"Missing résumé element: {tag}")
        for fact in ["Qualcomm Institute", "Halıcıoğlu Data Science Institute", "Adobe", "Handshake", "May 2028", "Data Science"]:
            self.assertIn(fact, doc.text)
        self.assertTrue(all(t.get("datetime") for t in doc.elements("time")))
        self.assertIn({"datetime": "2028-05"}, doc.elements("time"))
        self.assertTrue(all(s.get("aria-labelledby") for s in doc.elements("section")))


class Lab2StylingTests(unittest.TestCase):
    """Checks the CSS and markup each Lab 2 step asks for."""

    css = re.sub(r"\s+", " ", (ROOT / "style.css").read_text())

    def assertCss(self, *snippets):
        for snippet in snippets:
            self.assertIn(snippet, self.css)

    def test_step1_body_width(self):
        self.assertCss("max-width: 100ch;", "margin-inline: auto;", "padding-inline:")

    def test_step2_navigation(self):
        self.assertCss(
            "nav ul, nav li { display: contents; }", "nav { display: flex;",
            "flex: 1;", "text-decoration: none;", "color: inherit;", "text-align: center;",
            "padding: 0.5em;", "border-bottom: 1px solid var(--color-border);",
            "nav a.current { border-bottom: 0.4em solid",
            "--color-accent:", "accent-color: var(--color-accent);",
            "nav a:hover { border-bottom: 0.4em solid var(--color-accent);",
            "background-color: var(--color-accent-soft);",
        )

    def test_step3_contact_form_grid(self):
        self.assertCss(
            "font: inherit;", "form { display: grid; grid-template-columns: auto 1fr; gap: 1em; }",
            "grid-template-columns: subgrid;", "grid-column: 1 / -1;",
        )

    def test_step4_projects_grid(self):
        doc = Document(ROOT / "projects/index.html")
        self.assertTrue(any("projects" in element.get("class", "").split() for element in doc.elements("div")))
        self.assertFalse(doc.elements("article"), "Lab 4 loads the project cards from JSON")
        self.assertRegex(
            self.css,
            r"grid-template-columns: repeat\(auto-fill, minmax\((?:15em|min\(15em, 100%\)), 1fr\)\);",
        )
        self.assertCss(
            "grid-template-rows: subgrid;", "grid-row: span 3;", "font-size: 400%;",
            "h1, h2, h3, h4, h5, h6 { line-height: 1.1; text-wrap: balance;",
        )

    def test_step5_resume_is_styled(self):
        self.assertCss(".resume-entry {", "&::before", ".skills {")


class Lab3JavaScriptTests(unittest.TestCase):
    """Checks the code each Lab 3 step asks for. tests/browser_check.py runs it."""

    js = re.sub(r"\s+", " ", (ROOT / "global.js").read_text())
    css = Lab2StylingTests.css

    def assertJs(self, *snippets):
        for snippet in snippets:
            self.assertIn(snippet, self.js)

    def test_step1_global_js(self):
        self.assertJs("console.log('IT’S ALIVE!');", "function $$(selector, context = document)")

    def test_step3_nav_built_from_pages(self):
        self.assertJs(
            "let pages = [", "{ url: '', title: 'Home' }", "{ url: 'projects/', title: 'Projects' }",
            "location.hostname === 'localhost'", "'/portfolio/'", "document.createElement('nav')",
            "for (let p of pages)", "!p.url.startsWith('http') ? BASE_PATH + p.url : p.url",
            "document.createElement('a')", "a.classList.toggle('current'",
            "a.host === location.host", "a.target = '_blank';",
        )

    def test_step4_dark_mode(self):
        self.assertIn("color-scheme: light dark;", self.css)
        self.assertIn("--color-border: oklch(50% 10% 200 / 40%);", self.css)
        self.assertIn("color-mix(in oklch, var(--color-accent), canvas 85%)", self.css)
        self.assertIn(".color-scheme { position: absolute; top: 1rem; right: 1rem; font-size: 80%; }", self.css)
        self.assertJs(
            '<label class="color-scheme">', '<option value="light dark">', '<option value="light">',
            '<option value="dark">', "matchMedia('(prefers-color-scheme: dark)')",
            "select.addEventListener('input'", "document.documentElement.style.setProperty('color-scheme'",
            "'colorScheme' in localStorage", "localStorage.colorScheme = event.target.value",
            "select.value = colorScheme",
        )

    def test_step5_contact_form(self):
        self.assertJs(
            "form?.addEventListener('submit'", "event.preventDefault()", "new FormData(form)",
            "for (let [name, value] of data)", "encodeURIComponent(value)", "location.href = url",
        )


class Lab4DataTests(unittest.TestCase):
    """Validate the persistent data contract; browser_check.py tests its behavior."""

    def test_project_data_has_at_least_twelve_complete_records_and_multiple_years(self):
        projects = json.loads((ROOT / "lib/projects.json").read_text())
        self.assertIsInstance(projects, list)
        self.assertGreaterEqual(len(projects), 12)
        for index, project in enumerate(projects):
            with self.subTest(project=index):
                for key in ["title", "image", "description"]:
                    self.assertIsInstance(project.get(key), str, key)
                    self.assertTrue(project[key].strip(), key)
                self.assertRegex(str(project.get("year", "")), r"^\d{4}$")
                image = project["image"]
                if not image.startswith(("https://", "http://")):
                    self.assertTrue((ROOT / image).is_file(), image)
        self.assertGreater(len({str(project["year"]) for project in projects}), 1)
        self.assertEqual(len({project["title"] for project in projects}), len(projects))

    def test_page_placeholders_support_dynamic_content(self):
        projects = Document(ROOT / "projects/index.html")
        self.assertTrue(any("projects-title" in h.get("class", "").split() for h in projects.elements("h1")))
        home = Document(ROOT / "index.html")
        self.assertIn("Latest Projects", home.text)
        self.assertTrue(any("projects" in element.get("class", "").split() for element in home.elements("div")))
        self.assertTrue(any(attrs.get("id") == "profile-stats" for _, attrs in home.tags))


if __name__ == "__main__":
    unittest.main()
