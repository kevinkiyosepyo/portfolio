import { fetchJSON, renderProjects } from '../global.js';

const projectsContainer = document.querySelector('.projects');
const projectsTitle = document.querySelector('.projects-title');

try {
  const projects = await fetchJSON('../lib/projects.json');
  renderProjects(projects, projectsContainer, 'h2');
  projectsTitle.textContent = `${projects.length} ${projects.length === 1 ? 'Project' : 'Projects'}`;
} catch {
  projectsTitle.textContent = 'Projects';
  projectsContainer.innerHTML = '<p class="data-message">Projects could not be loaded. Please try refreshing the page.</p>';
} finally {
  projectsContainer.removeAttribute('aria-busy');
}
