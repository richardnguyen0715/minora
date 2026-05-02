/**
 * Minora Knowledge Base - Main application router.
 * Handles hash-based navigation and initializes the SPA.
 */

function navigateTo(view, params = {}) {
  let hash = `#${view}`;
  if (params.id) hash += `?id=${encodeURIComponent(params.id)}`;
  location.hash = hash;
}

function parseHash() {
  const raw = location.hash.slice(1) || "dashboard";
  const [view, queryStr] = raw.split("?");
  const params = {};
  if (queryStr) {
    for (const part of queryStr.split("&")) {
      const [key, val] = part.split("=");
      params[decodeURIComponent(key)] = decodeURIComponent(val || "");
    }
  }
  return { view, params };
}

function updateActiveNav(view) {
  document.querySelectorAll(".nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === view);
  });
}

async function route() {
  const { view, params } = parseHash();
  updateActiveNav(view);
  switch (view) {
    case "dashboard": await renderDashboard(); break;
    case "knowledge": await renderKnowledge(); break;
    case "detail": await renderDetail(params.id); break;
    case "links": await renderLinks(); break;
    case "edges": await renderEdges(); break;
    case "tags": await renderTags(); break;
    default: await renderDashboard(); break;
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("DOMContentLoaded", route);
