import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7.9.0/+esm';
import { fetchJSON, renderProjects } from '../global.js';

const projectsContainer = document.querySelector('.projects');
const projectsTitle = document.querySelector('.projects-title');
const searchInput = document.querySelector('.searchBar');
const svg = d3.select('#projects-pie-plot');
const legend = d3.select('.legend');

// Step 1.3: turns a slice's start and end angles into an SVG path. Inner radius 0 makes a pie.
const arcGenerator = d3.arc().innerRadius(0).outerRadius(50);
// Step 1.5: hands out one color per year. The domain is set once the data loads,
// so a year keeps the same color when a filter changes which slices are drawn.
const colors = d3.scaleOrdinal(d3.schemeTableau10);

let projects = [];
let query = '';         // Step 4.1: the search text
let selectedIndex = -1; // Step 5.2: -1 means no wedge is selected

// Step 4.4: all plotting lives in one function, so the chart can redraw for any list of projects.
function renderPieChart(projectsGiven) {
  // Step 3.1: count projects per year, oldest year first
  const rolledData = d3.rollups(projectsGiven, (v) => v.length, (d) => d.year);
  const data = rolledData
    .map(([year, count]) => ({ value: count, label: year }))
    .sort((a, b) => d3.ascending(a.label, b.label));

  // Step 1.4: d3.pie() works out each slice's angles. sort(null) keeps the years in order.
  const sliceGenerator = d3.pie().value((d) => d.value).sort(null);
  const arcData = sliceGenerator(data);
  const arcs = arcData.map((d) => arcGenerator(d));

  // Step 4.4: clear the previous slices and legend before drawing new ones
  svg.selectAll('path').remove();
  legend.selectAll('li').remove();

  arcs.forEach((arc, i) => {
    const { label, value } = data[i];
    svg
      .append('path')
      .attr('d', arc)
      .attr('fill', colors(label))
      .attr('data-year', label)
      .attr('tabindex', 0) // keyboard users can Tab to each wedge
      .attr('role', 'button')
      .attr('aria-label', `${label}: ${value} ${value === 1 ? 'project' : 'projects'}`)
      .attr('aria-pressed', false)
      .on('click', () => selectWedge(i, data))
      .on('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          selectWedge(i, data);
        }
      });
  });

  // Step 2.2: one legend item per slice. --color passes the slice color to the swatch.
  data.forEach(({ label, value }, idx) => {
    const item = legend
      .append('li')
      .attr('style', `--color:${colors(label)}`)
      .attr('class', 'legend-item')
      .on('click', () => selectWedge(idx, data));
    item.append('span').attr('class', 'swatch');
    item.append('span').text(label);
    item.append('em').text(`(${value})`);
  });
}

// Steps 5.2 and 5.3: select a wedge (or deselect it) and show only that year's projects
function selectWedge(i, data) {
  selectedIndex = selectedIndex === i ? -1 : i;

  svg
    .selectAll('path')
    .attr('class', (_, idx) => (idx === selectedIndex ? 'selected' : null))
    .attr('aria-pressed', (_, idx) => idx === selectedIndex);
  legend
    .selectAll('li')
    .attr('class', (_, idx) => (idx === selectedIndex ? 'legend-item selected' : 'legend-item'));

  if (selectedIndex === -1) {
    renderProjects(projects, projectsContainer, 'h2');
  } else {
    const selectedYear = data[selectedIndex].label;
    renderProjects(projects.filter((project) => project.year === selectedYear), projectsContainer, 'h2');
  }
}

// Steps 4.2 and 4.3: case-insensitive search across every field of a project
function searchProjects() {
  return projects.filter((project) => {
    const values = Object.values(project).join('\n').toLowerCase();
    return values.includes(query.trim().toLowerCase());
  });
}

try {
  const data = await fetchJSON('../lib/projects.json');
  if (!Array.isArray(data)) throw new TypeError('Project data must be an array.');
  projects = data;
  colors.domain(d3.sort(new Set(projects.map((project) => project.year))));
  renderProjects(projects, projectsContainer, 'h2');
  projectsTitle.textContent = `${projects.length} ${projects.length === 1 ? 'Project' : 'Projects'}`;
  renderPieChart(projects); // Step 4.4: draw the chart on page load
} catch {
  projectsTitle.textContent = 'Projects';
  projectsContainer.innerHTML = '<p class="data-message">Projects could not be loaded. Please try refreshing the page.</p>';
  searchInput.disabled = true;
} finally {
  projectsContainer.removeAttribute('aria-busy');
}

// Step 4.4: redraw the list and the chart as the search text changes
searchInput.addEventListener('input', (event) => {
  query = event.target.value;
  const filteredProjects = searchProjects();
  renderProjects(filteredProjects, projectsContainer, 'h2');
  renderPieChart(filteredProjects);
});
