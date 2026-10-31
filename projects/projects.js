import * as d3 from 'https://cdn.jsdelivr.net/npm/d3@7.9.0/+esm';
import { fetchJSON, renderProjects } from '../global.js';

const projectsContainer = document.querySelector('.projects');
const projectsTitle = document.querySelector('.projects-title');
const searchInput = document.querySelector('.searchBar');
const filterStatus = document.querySelector('.filter-status');
const svg = d3.select('#projects-pie-plot');
const legend = d3.select('.legend');

// Step 1.3: turns a slice's start and end angles into an SVG path. Inner radius 0 makes a pie.
const arcGenerator = d3.arc().innerRadius(0).outerRadius(50);
// Step 1.5: hands out one color per year. The domain is set once the data loads,
// so a year keeps the same color when a filter changes which slices are drawn.
const colors = d3.scaleOrdinal(d3.schemeTableau10);

let projects = [];
let query = '';         // Step 4.1: the search text
// Step 5.2: the selected wedge, saved as its year. null means nothing is selected.
// Step 5.4 fix: a year means the same thing after the search redraws the pie. An index does not.
let selectedYear = null;

// Step 4.4: all plotting lives in one function, so the chart can redraw for any list of projects.
function renderPieChart(projectsGiven) {
  // Step 3.1: count projects per year, oldest year first
  const rolledData = d3.rollups(projectsGiven, (v) => v.length, (d) => d.year);
  const data = rolledData.map(([year, count]) => ({ value: count, label: year }));
  // keep the selected year in the legend even if the search leaves it 0 projects, so it can be cleared
  if (selectedYear !== null && !data.some((d) => d.label === selectedYear)) {
    data.push({ value: 0, label: selectedYear });
  }
  data.sort((a, b) => d3.ascending(a.label, b.label));

  // Step 1.4: d3.pie() works out each slice's angles. sort(null) keeps the years in order.
  const sliceGenerator = d3.pie().value((d) => d.value).sort(null);
  const arcData = sliceGenerator(data);
  const arcs = arcData.map((d) => arcGenerator(d));

  // Step 4.4: clear the previous slices and legend before drawing new ones
  svg.selectAll('path').remove();
  legend.selectAll('li').remove();

  arcs.forEach((arc, i) => {
    const { label, value } = data[i];
    if (value === 0) return; // a year with no matches has no wedge to draw
    const isSelected = label === selectedYear;
    svg
      .append('path')
      .attr('d', arc)
      .attr('fill', colors(label))
      .attr('class', isSelected ? 'selected' : null)
      .attr('data-year', label)
      .attr('tabindex', 0) // keyboard users can Tab to each wedge
      .attr('role', 'button')
      .attr('aria-label', `${label}: ${value} ${value === 1 ? 'project' : 'projects'}`)
      .attr('aria-pressed', isSelected)
      .on('click', () => toggleYear(label))
      .on('keydown', (event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          toggleYear(label);
        }
      });
  });

  // Step 2.2: one legend item per slice. --color passes the slice color to the swatch.
  data.forEach(({ label, value }) => {
    const item = legend
      .append('li')
      .attr('style', `--color:${colors(label)}`)
      .attr('class', label === selectedYear ? 'legend-item selected' : 'legend-item')
      .on('click', () => toggleYear(label));
    item.append('span').attr('class', 'swatch');
    item.append('span').text(label);
    item.append('em').text(`(${value})`);
  });
}

// Step 5.2: clicking a wedge selects its year. Clicking it again clears the selection.
function toggleYear(year) {
  const wedgeHadFocus = document.activeElement?.matches?.('#projects-pie-plot path');
  selectedYear = selectedYear === year ? null : year;
  updatePage();
  // the wedges were redrawn, so hand keyboard focus back to the same year's wedge
  if (wedgeHadFocus) svg.select(`path[data-year="${year}"]`).node()?.focus();
}

// Steps 4.2 and 4.3: case-insensitive search across every field of a project
function searchProjects() {
  return projects.filter((project) => {
    const values = Object.values(project).join('\n').toLowerCase();
    return values.includes(query.trim().toLowerCase());
  });
}

// Step 5.4 fix: the search box and the pie both call this, so both filters always apply.
// It starts from the full list every time: search first, then the selected year.
function updatePage() {
  const searchedProjects = searchProjects();
  const visibleProjects = selectedYear === null
    ? searchedProjects
    : searchedProjects.filter((project) => project.year === selectedYear);

  renderProjects(visibleProjects, projectsContainer, 'h2');
  // the pie counts the searched projects, so every matching year stays clickable
  renderPieChart(searchedProjects);

  if (!projects.length) {
    filterStatus.textContent = '';
    return;
  }
  if (!visibleProjects.length) {
    projectsContainer.innerHTML = '<p class="data-message">No projects match. Try another search or clear the year.</p>';
  }
  const filters = [
    selectedYear !== null && `from ${selectedYear}`,
    query.trim() && `matching “${query.trim()}”`,
  ].filter(Boolean);
  filterStatus.textContent = filters.length
    ? `Showing ${visibleProjects.length} of ${projects.length} projects ${filters.join(' ')}.`
    : `Showing all ${projects.length} projects. Select a slice to filter by year.`;
}

try {
  const data = await fetchJSON('../lib/projects.json');
  if (!Array.isArray(data)) throw new TypeError('Project data must be an array.');
  projects = data;
  colors.domain(d3.sort(new Set(projects.map((project) => project.year))));
  projectsTitle.textContent = `${projects.length} ${projects.length === 1 ? 'Project' : 'Projects'}`;
  updatePage(); // Step 4.4: draw the list and the chart on page load
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
  updatePage();
});
