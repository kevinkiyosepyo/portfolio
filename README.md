# Kevin Kiyose Pyo — Portfolio

A personal site for DSC 106 [Lab 1](https://dsc106.com/labs/lab01/) and [Lab 2](https://dsc106.com/labs/lab02/), built with semantic HTML and a shared CSS stylesheet. No framework, build step, external fonts, or tracking scripts.

- **Website:** https://kevinkiyosepyo.github.io/portfolio/
- **Repository:** https://github.com/kevinkiyosepyo/portfolio

## Pages

- `index.html`: personal introduction, local portrait with alt text, selected projects.
- `projects/index.html`: responsive card grid with Lightning Data Pipeline, Job Application Automation, RideWatch, and placeholder cards.
- `contact/index.html`: labeled native `mailto:` form with `method="POST"` and `enctype="text/plain"`.
- `resume/index.html`: education, experience, projects, and skills using sections, articles, lists, and machine-readable dates.
- `style.css`: shared system-UI body font, responsive layout, focus styles, and print rules.

Every page has relative navigation links to all four pages and a GitHub profile link that opens a new tab. The layout changes to one column on narrow screens. The repository-root `main` branch is the GitHub Pages source.

## Lab 2: Styling with CSS

[Lab 2](https://dsc106.com/labs/lab02/) changes, labeled by step in `style.css`:

1. **Width:** `body` has `max-width: 100ch`, `margin-inline: auto`, and side padding.
2. **Navigation:** Flexbox nav with equal-width (`flex: 1`) links, a cool-gray bottom border, a thick border on the `.current` page link, and an `--color-accent` hover with a tinted `oklch(from ...)` background. Links wrap on phones instead of overflowing.
3. **Contact form:** `font: inherit` on controls; the form is a two-column grid (`auto 1fr`) and each label uses `subgrid` to span both columns.
4. **Projects:** 12 cards (3 real projects, 9 placeholders) in a `repeat(auto-fill, minmax(15em, 1fr))` grid, with `subgrid` rows so headings, images, and text align. `h1` is `400%`; all headings get `line-height: 1.1` and `text-wrap: balance`.
5. **Résumé:** a timeline with accent dots on hover, date pills, accent list markers, and skills as a grid-based definition list with chips, written with CSS nesting.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000/. You can also open `index.html` directly in a browser.

## Check the lab requirements

The core acceptance tests use only Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

The optional browser checks need Python's Playwright package and Google Chrome:

```sh
python3 tests/browser_check.py --url http://127.0.0.1:8000/
```

They verify all four pages across desktop/mobile widths, navigation, loaded images, and native form validation. Screenshots and reports go in ignored `artifacts/`.

The mailto form depends on a configured email application or browser mail handler. It does not send email itself, and the way subject/body fields appear varies by client. Automated tests intercept submission rather than opening an external mail app or sending a message.

## Content and privacy

The résumé is a concise HTML adaptation of Kevin's current résumé, not a downloadable copy of the original document. Private contact details, birth date, and identity-document details are omitted. The portrait is cropped from the already-public [GitHub profile image](https://github.com/kevinkiyosepyo), with surrounding document material excluded. Project descriptions are grounded in the résumé and linked public repositories; interests come from Kevin's existing personal site.

## Submission

Submit this repository URL and an MP4 of **no more than one minute** to Gradescope. The video must show the customized résumé, demonstrate resizing, and verbally explain a personally meaningful takeaway from the lab. Review the site and explain it in your own words; a generated demo is a rehearsal aid, not evidence of your personal learning.
