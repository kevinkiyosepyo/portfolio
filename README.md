# Kevin Kiyose Pyo's portfolio

My personal site for DSC 106 [Lab 1](https://dsc106.com/labs/lab01/), [Lab 2](https://dsc106.com/labs/lab02/), and [Lab 3](https://dsc106.com/labs/lab03/). It's plain HTML, one stylesheet, and one script: no framework, build step, web fonts, or tracking.

Live site: https://kevinkiyosepyo.github.io/portfolio/

## Pages

- `index.html` is the home page, with a short intro, my photo, and two selected projects.
- `projects/index.html` is a card grid with three real projects and nine placeholder cards.
- `contact/index.html` has a `mailto:` form with `method="GET"`.
- `resume/index.html` covers education, experience, projects, and skills, with `<time>` elements for every date.
- `style.css` holds the styles for every page.
- `global.js` builds the nav, runs the theme menu, and handles the contact form.

Every page gets the same nav from `global.js`: the four pages plus my GitHub profile, which opens in a new tab. GitHub Pages serves the site from the root of the `main` branch.

## Lab 2 changes

Each rule in `style.css` is labeled with the lab step it belongs to.

1. The `body` has `max-width: 100ch`, `margin-inline: auto`, and side padding.
2. The nav is a flex row of equal width links (`flex: 1`) with a gray bottom border. The `.current` link gets a thick border, and hovering shows `--color-accent` with a light `oklch(from ...)` tint. On phones the links wrap instead of overflowing.
3. Form controls use `font: inherit`. The form is a two column grid (`auto 1fr`) and each label uses `subgrid` to span both columns.
4. The projects page has 12 cards in a `repeat(auto-fill, minmax(15em, 1fr))` grid. Each card uses `subgrid` rows so headings, images, and text line up across a row. The `h1` is `400%`, and all headings get `line-height: 1.1` and `text-wrap: balance`.
5. The résumé is a timeline with accent dots on hover, date pills, and skills shown as chips in a grid. It's written with CSS nesting.

## Lab 3 changes

Every page loads `global.js` with `type="module"`.

1. `global.js` logs `IT’S ALIVE!` and defines the `$$` helper.
2. Step 2 set the `current` class with `$$("nav a")`. Step 3 replaces that code, as the lab says to.
3. The pages no longer have a nav in their HTML. `global.js` builds it from a `pages` array and puts it in the page header. Each local link starts with `BASE_PATH`, which is `/` on a local server and `/portfolio/` on GitHub Pages. The current page's link gets the `current` class and `aria-current="page"`, and links to other sites get `target="_blank"`.
4. The root has `color-scheme: light dark`, and every color token uses `light-dark()` so the green palette has a dark version. The nav border is now `oklch(50% 10% 200 / 40%)`, and the hover tint mixes the accent with `canvas`. A Theme menu in the top right corner sets `color-scheme` on `<html>` to Automatic, Light, or Dark. The choice goes in `localStorage.colorScheme`, so it stays after a reload and on other pages.
5. (Optional step) The contact form uses `method="GET"` and no longer asks for the sender's email. On submit, `global.js` builds the `mailto:` URL with `encodeURIComponent`, so spaces arrive as `%20` instead of `+`.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/. Don't open the files directly: the nav picks its link paths from the hostname, so it only works on `localhost`, `127.0.0.1`, or GitHub Pages.

## Tests

The acceptance tests only need Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

The browser checks need Playwright and Google Chrome:

```sh
python3 tests/browser_check.py --url http://127.0.0.1:8000/
```

They load every page at four widths and check for horizontal overflow and broken images. Then they click through the nav and check which link is marked current, switch themes and reload to make sure the choice is saved, and load the site from the GitHub Pages URL to check the `/portfolio/` links. Screenshots and the report go in `artifacts/`, which git ignores.

The contact form needs a mail app or browser mail handler and doesn't send anything itself. The browser check points the form at a local URL so it can read the encoded query string instead of opening a mail app.

## Content and privacy

The résumé page is a shorter HTML version of my résumé, not the original file. It leaves out private contact details, my birth date, and ID details. The photo is cropped from my public [GitHub profile image](https://github.com/kevinkiyosepyo). Project descriptions come from my résumé and the linked repos.

## Submission

Submit the repository URL, the live site URL, and an MP4 of one minute or less to Gradescope. For Lab 3 the video has to show the site, switch between Automatic, Light, and Dark, reload to show the choice is saved, and point out the JavaScript changes. I also have to say out loud the most interesting thing I learned.
