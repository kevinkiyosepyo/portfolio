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

// ---------- Lab 4: shared data loading and project templates ----------
export async function fetchJSON(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch ${url}: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching or parsing JSON data:', error);
    // Let each page display a useful error instead of treating a failed request as no data.
    throw error;
  }
}

export async function fetchGitHubData(username) {
  return fetchJSON(`https://api.github.com/users/${encodeURIComponent(username)}`);
}

// Project paths are relative to the site root, even when rendered on a nested page.
const siteRoot = new URL('./', import.meta.url);
const placeholderImage = new URL('images/project-placeholder.svg', siteRoot).href;

function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  })[character]);
}

function projectURL(value, fallback) {
  try {
    const url = new URL(value, siteRoot);
    return ['http:', 'https:'].includes(url.protocol) ? url.href : fallback;
  } catch {
    return fallback;
  }
}

export function renderProjects(projects, containerElement, headingLevel = 'h2') {
  if (!(containerElement instanceof Element)) {
    throw new TypeError('renderProjects needs a valid container element.');
  }
  if (!Array.isArray(projects)) {
    throw new TypeError('Project data must be an array.');
  }
  const heading = /^h[1-6]$/.test(headingLevel) ? headingLevel : 'h2';
  containerElement.innerHTML = '';

  if (projects.length === 0) {
    containerElement.innerHTML = '<p class="data-message">No projects to display yet.</p>';
    return;
  }

  for (const project of projects) {
    const article = document.createElement('article');
    if (project.id) article.id = project.id;
    const title = escapeHTML(project.title || 'Untitled project');
    const image = projectURL(project.image || placeholderImage, placeholderImage);
    const url = project.url ? projectURL(project.url, '') : '';
    const year = /^\d{4}$/.test(String(project.year)) ? String(project.year) : '';

    article.innerHTML = `
      <${heading}>${title}</${heading}>
      <img src="${escapeHTML(image)}" alt="${escapeHTML(project.imageAlt || project.title || 'Project image')}" width="640" height="360">
      <div class="project-details">
        <p class="project-year">${year ? `<time datetime="${year}">${year}</time>` : 'Year not specified'}${project.status ? ` · ${escapeHTML(project.status)}` : ''}</p>
        <p>${escapeHTML(project.description || 'A description will be added soon.')}</p>
        ${url ? `<p><a href="${escapeHTML(url)}">View project <span aria-hidden="true">↗</span></a></p>` : ''}
      </div>
    `;
    article.querySelector('img').addEventListener('error', (event) => {
      event.currentTarget.src = placeholderImage;
      event.currentTarget.alt = `Image unavailable for ${project.title || 'this project'}`;
    }, { once: true });
    containerElement.appendChild(article);
  }
}
