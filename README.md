# Kevin Kiyose Pyo's portfolio

My personal site for DSC 106 [Lab 1](https://dsc106.com/labs/lab01/) and [Lab 2](https://dsc106.com/labs/lab02/). It's plain HTML with one shared stylesheet: no framework, build step, web fonts, or tracking scripts.

Live site: https://kevinkiyosepyo.github.io/portfolio/

## Pages

- `index.html` is the home page, with a short intro, my photo, and two selected projects.
- `projects/index.html` is a card grid with three real projects and nine placeholder cards.
- `contact/index.html` has a `mailto:` form with `method="POST"` and `enctype="text/plain"`.
- `resume/index.html` covers education, experience, projects, and skills, with `<time>` elements for every date.
- `style.css` holds the styles for every page.

Every page links to the other three with relative links, plus my GitHub profile in a new tab. GitHub Pages serves the site from the root of the `main` branch.

## Lab 2 changes

Each rule in `style.css` is labeled with the lab step it belongs to.

1. The `body` has `max-width: 100ch`, `margin-inline: auto`, and side padding.
2. The nav is a flex row of equal width links (`flex: 1`) with a gray bottom border. The `.current` link gets a thick border, and hovering shows `--color-accent` with a light `oklch(from ...)` tint. On phones the links wrap instead of overflowing.
3. Form controls use `font: inherit`. The form is a two column grid (`auto 1fr`) and each label uses `subgrid` to span both columns.
4. The projects page has 12 cards in a `repeat(auto-fill, minmax(15em, 1fr))` grid. Each card uses `subgrid` rows so headings, images, and text line up across a row. The `h1` is `400%`, and all headings get `line-height: 1.1` and `text-wrap: balance`.
5. The résumé is a timeline with accent dots on hover, date pills, and skills shown as chips in a grid. It's written with CSS nesting.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/. Opening `index.html` directly in a browser also works.

## Tests

The acceptance tests only need Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

The browser checks need Playwright and Google Chrome:

```sh
python3 tests/browser_check.py --url http://127.0.0.1:8000/
```

They load every page at four widths, check for horizontal overflow and broken images, click through the nav, and test the form's validation. Screenshots and the report go in `artifacts/`, which git ignores.

The contact form needs a mail app or browser mail handler. It doesn't send anything itself, and different mail apps show the subject and body differently. The tests intercept the submit instead of opening a mail app.

## Content and privacy

The résumé page is a shorter HTML version of my résumé, not the original file. It leaves out private contact details, my birth date, and ID details. The photo is cropped from my public [GitHub profile image](https://github.com/kevinkiyosepyo). Project descriptions come from my résumé and the linked repos.

## Submission

Submit the repository URL and an MP4 of one minute or less to Gradescope. The video has to show the résumé page, show the site resizing, and explain out loud the most interesting thing I learned in the lab.
