console.log('IT’S ALIVE!');

function $$(selector, context = document) {
  return Array.from(context.querySelectorAll(selector));
}

// ---------- Step 3: build the nav from one list of pages ----------
let pages = [
  { url: '', title: 'Home' },
  { url: 'projects/', title: 'Projects' },
  { url: 'resume/', title: 'Résumé' },
  { url: 'contact/', title: 'Contact' },
  { url: 'https://github.com/kevinkiyosepyo', title: 'GitHub' },
];

// A local server serves the site at "/". GitHub Pages serves it under the repo name.
const BASE_PATH = (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
  ? '/'
  : '/portfolio/';

// "/projects/" and "/projects/index.html" are the same page.
const samePath = (a, b) => a.replace(/index\.html$/, '') === b.replace(/index\.html$/, '');

let nav = document.createElement('nav');
nav.setAttribute('aria-label', 'Main navigation');

for (let p of pages) {
  let url = !p.url.startsWith('http') ? BASE_PATH + p.url : p.url;

  let a = document.createElement('a');
  a.href = url;
  a.textContent = p.title;

  // Step 3.2: highlight the current page
  let isCurrent = a.host === location.host && samePath(a.pathname, location.pathname);
  a.classList.toggle('current', isCurrent);
  if (isCurrent) a.setAttribute('aria-current', 'page');

  // Step 3.2: external links open in a new tab
  if (a.host !== location.host) {
    a.target = '_blank';
    a.rel = 'noopener noreferrer';
    a.insertAdjacentHTML('beforeend',
      ' <span aria-hidden="true">↗</span><span class="visually-hidden"> (opens in a new tab)</span>');
  }

  nav.append(a);
}

// The nav goes in the page header so the skip link stays first in tab order.
const header = document.querySelector('.site-header');
if (header) header.append(nav);
else document.body.prepend(nav);

// ---------- Step 4: dark mode switcher ----------
const osScheme = matchMedia('(prefers-color-scheme: dark)').matches ? 'Dark' : 'Light';

(header ?? document.body).insertAdjacentHTML(
  'afterbegin',
  `
  <label class="color-scheme">
    Theme:
    <select>
      <option value="light dark">Automatic (${osScheme})</option>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  </label>`,
);

const select = document.querySelector('.color-scheme select');

function setColorScheme(colorScheme) {
  document.documentElement.style.setProperty('color-scheme', colorScheme);
  select.value = colorScheme;
}

// Step 4.5: reuse the saved choice on every page load
if ('colorScheme' in localStorage) {
  setColorScheme(localStorage.colorScheme);
}

select.addEventListener('input', function (event) {
  console.log('color scheme changed to', event.target.value);
  setColorScheme(event.target.value);
  localStorage.colorScheme = event.target.value;
});

// ---------- Step 5: contact form with properly encoded fields ----------
const form = document.querySelector('form');

form?.addEventListener('submit', function (event) {
  event.preventDefault();
  let data = new FormData(form);
  let params = [];

  for (let [name, value] of data) {
    params.push(name + '=' + encodeURIComponent(value));
  }

  let url = form.action + '?' + params.join('&');
  location.href = url;
});
