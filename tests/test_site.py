"""Lab acceptance tests. Run: python3 -m unittest discover -s tests -v."""
from html.parser import HTMLParser
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

    def test_every_page_has_complete_relative_navigation(self):
        routes = ["index.html", "projects/index.html", "contact/index.html", "resume/index.html"]
        for route in routes:
            with self.subTest(route=route):
                path = ROOT / route
                doc = Document(path)
                self.assertTrue(doc.elements("nav"), f"Missing navigation on {route}")
                self.assertEqual(len(doc.elements("h1")), 1)
                self.assertTrue(doc.elements("title"))
                self.assertTrue(any(m.get("name") == "viewport" for m in doc.elements("meta")))
                links = doc.elements("a")
                for destination in routes:
                    self.assertTrue(any(
                        not a.get("href", "").startswith(("/", "http", "mailto:", "#"))
                        and (path.parent / a.get("href", "")).resolve() == ROOT / destination
                        for a in links
                    ), f"{route} does not link relatively to {destination}")
                self.assertTrue(any(a.get("aria-current") == "page" for a in links))
                github = [a for a in links if a.get("href") == "https://github.com/kevinkiyosepyo" and a.get("target") == "_blank"]
                self.assertTrue(github)
                self.assertIn("noopener", github[0].get("rel", ""))
                stylesheet = next(l for l in doc.elements("link") if l.get("rel") == "stylesheet")
                self.assertEqual((path.parent / stylesheet["href"]).resolve(), ROOT / "style.css")

    def test_contact_form_uses_required_mailto_contract(self):
        doc = Document(ROOT / "contact/index.html")
        self.assertEqual(doc.elements("form"), [{
            "action": "mailto:kevinkpyo@gmail.com", "method": "POST", "enctype": "text/plain"
        }])
        fields = {field.get("name"): field for field in doc.elements("input") + doc.elements("textarea")}
        self.assertEqual(set(fields), {"email", "subject", "body"})
        self.assertEqual(fields["email"]["type"], "email")
        self.assertEqual(len(doc.elements("label")), 3)
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
            "--color-border: oklch(80% 3% 200);", "nav a.current { border-bottom: 0.4em solid",
            "--color-accent:", "accent-color: var(--color-accent);",
            "nav a:hover { border-bottom: 0.4em solid var(--color-accent);",
            "oklch(from var(--color-accent) 95% 5% h)",
        )
        for route in ["index.html", "projects/index.html", "contact/index.html", "resume/index.html"]:
            doc = Document(ROOT / route)
            current = [a for a in doc.elements("a") if "current" in a.get("class", "").split()]
            self.assertEqual(len(current), 1, route)
            self.assertEqual(current[0].get("aria-current"), "page", route)

    def test_step3_contact_form_grid(self):
        self.assertCss(
            "font: inherit;", "form { display: grid; grid-template-columns: auto 1fr; gap: 1em; }",
            "grid-template-columns: subgrid;", "grid-column: 1 / -1;",
        )

    def test_step4_projects_grid(self):
        doc = Document(ROOT / "projects/index.html")
        self.assertIn({"class": "projects"}, doc.elements("div"))
        self.assertEqual(len(doc.elements("article")), 12)
        self.assertEqual(len(doc.elements("h2")), 12)
        images = doc.elements("img")
        self.assertEqual(len(images), 12)
        self.assertTrue(all("alt" in img for img in images))
        self.assertCss(
            "grid-template-columns: repeat(auto-fill, minmax(15em, 1fr));",
            "grid-template-rows: subgrid;", "grid-row: span 3;", "font-size: 400%;",
            "h1, h2, h3, h4, h5, h6 { line-height: 1.1; text-wrap: balance;",
        )

    def test_step5_resume_is_styled(self):
        self.assertCss(".resume-entry {", "&::before", ".skills {")


if __name__ == "__main__":
    unittest.main()
