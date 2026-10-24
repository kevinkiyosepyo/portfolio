import { fetchJSON, renderProjects, fetchGitHubData } from './global.js';

async function loadLatestProjects() {
  const container = document.querySelector('.projects');
  if (!container) return;
  try {
    const projects = await fetchJSON('./lib/projects.json');
    if (!Array.isArray(projects)) throw new TypeError('Project data must be an array.');
    renderProjects(projects.slice(0, 3), container, 'h3');
  } catch {
    container.innerHTML = '<p class="data-message">Projects could not be loaded. Please try refreshing the page.</p>';
  } finally {
    container.removeAttribute('aria-busy');
  }
}

async function loadGitHubStats() {
  const profileStats = document.querySelector('#profile-stats');
  if (!profileStats) return;
  try {
    const githubData = await fetchGitHubData('kevinkiyosepyo');
    const fields = ['public_repos', 'public_gists', 'followers', 'following'];
    if (!fields.every((key) => Number.isInteger(githubData?.[key]) && githubData[key] >= 0)) {
      throw new TypeError('GitHub returned incomplete profile statistics.');
    }
    profileStats.innerHTML = `
      <dl>
        <dt>Public repos</dt><dd>${githubData.public_repos}</dd>
        <dt>Public gists</dt><dd>${githubData.public_gists}</dd>
        <dt>Followers</dt><dd>${githubData.followers}</dd>
        <dt>Following</dt><dd>${githubData.following}</dd>
      </dl>
    `;
  } catch {
    profileStats.innerHTML = '<p class="data-message">GitHub stats are unavailable right now. Please try again later or <a href="https://github.com/kevinkiyosepyo">visit my GitHub profile</a>.</p>';
  } finally {
    profileStats.removeAttribute('aria-busy');
  }
}

// Independent requests: a GitHub outage should not stop the project cards loading.
await Promise.all([loadLatestProjects(), loadGitHubStats()]);
