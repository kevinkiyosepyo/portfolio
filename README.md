# Kevin Kiyose Pyo's portfolio

My personal site for DSC 106 [Lab 1](https://dsc106.com/labs/lab01/), [Lab 2](https://dsc106.com/labs/lab02/), [Lab 3](https://dsc106.com/labs/lab03/), and [Lab 4](https://dsc106.com/labs/lab04/). It's plain HTML, one stylesheet, and JavaScript modules: no framework, build step, web fonts, or tracking.

Live site: https://kevinkiyosepyo.github.io/portfolio/

## Pages

- `index.html` is the home page, with a short intro, my photo, the first three projects from the shared data file, and live GitHub statistics.
- `projects/index.html` loads all 12 project cards from `lib/projects.json` and calculates the count in the heading.
- `contact/index.html` has a `mailto:` form with `method="GET"`.
- `resume/index.html` covers education, experience, projects, and skills, with `<time>` elements for every date.
- `style.css` holds the styles for every page.
- `global.js` builds the nav, runs the theme menu, handles the contact form, and exports shared data-loading and project-rendering functions.

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

## Lab 4 changes

- `lib/projects.json` contains 12 projects, each with a title, description, image path, and numeric year. Years span 2025 and 2026. Entries also retain project IDs and links. The local project graphic is a placeholder thumbnail, not a screenshot of each project.
- `fetchJSON(url)` checks the HTTP response, parses JSON, and reports failures. `fetchGitHubData(username)` reuses it for GitHub's public user endpoint.
- `renderProjects(projects, container, headingLevel)` clears the container, creates articles from one template, and supports different heading levels. It escapes text, limits URLs to HTTP(S), supplies a missing-image fallback, and handles an empty array.
- `projects/projects.js` renders the complete list using `h2` headings and sets `.projects-title` from the array length. The HTML contains no hardcoded project articles.
- `index.js` renders `projects.slice(0, 3)` using `h3` headings under Latest Projects. It independently fetches repositories, gists, followers, and following into a definition list in `#profile-stats`.
- Both pages show loading and error messages. Relative image paths resolve against the site root, so they work on the homepage, nested Projects page, and GitHub Pages.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Then open http://127.0.0.1:8000/. Use an HTTP server instead of opening the files directly: module imports and JSON fetching require HTTP(S).

## Tests

The acceptance tests only need Python's standard library:

```sh
python3 -m unittest discover -s tests -v
```

The browser checks need Playwright and Google Chrome:

```sh
python3 tests/browser_check.py --url http://127.0.0.1:8000/ --live-api
```

They load every page at four widths and check for horizontal overflow and broken images. Then they click through the nav and check which link is marked current, switch themes and reload to make sure the choice is saved, and load the site from the GitHub Pages URL to check the `/portfolio/` links. The Lab 4 checks also verify shared project data, dynamic counts, API statistics, repeated rendering, and failure states. Repeated checks use a fixed API response; `--live-api` checks the real endpoint once. Screenshots and the report go in `artifacts/`, which git ignores.

The contact form needs a mail app or browser mail handler and doesn't send anything itself. The browser check points the form at a local URL so it can read the encoded query string instead of opening a mail app.

## Content and privacy

The résumé page is a shorter HTML version of my résumé, not the original file. It leaves out private contact details, my birth date, and ID details. The photo is cropped from my public [GitHub profile image](https://github.com/kevinkiyosepyo). Project descriptions come from my résumé and the linked repos.

## Submission

Submit the repository URL, the live site URL, and a narrated MP4 of no more than one minute to Gradescope. For Lab 4, record the laptop screen, present the site, demonstrate the new JavaScript features, explain your actual most interesting learning, and answer one Think About It question. Written captions alone do not meet the spoken-explanation requirement.

A useful question to explain: why clear the container before rendering? Without clearing it, rendering again appends duplicate project cards. Replacing its content makes every render match the current data.

The lab also asks classmates to follow one another until each has at least three followers and three following. Those counts come from the real API, not hardcoded values.
