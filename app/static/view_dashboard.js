/** Dashboard view renderer */
async function renderDashboard() {
  const mc = document.getElementById("main-content");
  mc.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const stats = await API.getStats();
    const nc = stats.node_count||0, ec = stats.edge_count||0, tc = stats.tag_count||0, lc = stats.link_count||0;
    document.getElementById("nav-node-count").textContent = nc;
    document.getElementById("nav-edge-count").textContent = ec;
    document.getElementById("nav-tag-count").textContent = tc;
    document.getElementById("nav-link-count").textContent = lc;
    const td = stats.type_distribution||{}, sd = stats.status_distribution||{}, rn = stats.recent_nodes||[];
    const maxType = Math.max(1, ...Object.values(td));
    let distHtml = "";
    for (const [t,c] of Object.entries(td)) {
      distHtml += `<div class="dist-bar-container"><div class="dist-bar-label"><span>${escapeHtml(t)}</span><span>${c}</span></div><div class="dist-bar-track"><div class="dist-bar-fill" style="width:${(c/maxType*100).toFixed(0)}%;background:${distBarColor(t)}"></div></div></div>`;
    }
    let statusHtml = "";
    for (const [s,c] of Object.entries(sd)) {
      statusHtml += `<span class="status-badge ${statusClass(s)}" style="margin-right:8px">${escapeHtml(s)}: ${c}</span>`;
    }
    let recentHtml = "";
    if (rn.length) {
      recentHtml = '<table class="data-table"><thead><tr><th>ID</th><th>Type</th><th>Title</th><th>Updated</th></tr></thead><tbody>';
      for (const n of rn) {
        recentHtml += `<tr class="clickable" onclick="navigateTo('detail',{id:'${escapeHtml(n.id)}'})"><td class="id-cell">${escapeHtml(n.id)}</td><td><span class="tag type-badge ${typeTagClass(n.type)}">${escapeHtml(n.type)}</span></td><td>${escapeHtml(n.title)}</td><td>${formatDate(n.updated_at)}</td></tr>`;
      }
      recentHtml += "</tbody></table>";
    } else { recentHtml = '<div class="empty-state"><p>No knowledge items yet</p></div>'; }
    mc.innerHTML = `
      <div class="page-header"><div><h1 class="page-title">Dashboard</h1><p class="page-description">Overview of your knowledge base</p></div></div>
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-icon purple">🧠</div><div><div class="stat-value">${nc}</div><div class="stat-label">Knowledge Nodes</div></div></div>
        <div class="stat-card"><div class="stat-icon blue">🔗</div><div><div class="stat-value">${lc}</div><div class="stat-label">Saved Links</div></div></div>
        <div class="stat-card"><div class="stat-icon emerald">🔀</div><div><div class="stat-value">${ec}</div><div class="stat-label">Edges</div></div></div>
        <div class="stat-card"><div class="stat-icon amber">🏷️</div><div><div class="stat-value">${tc}</div><div class="stat-label">Tags</div></div></div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
        <div class="card"><div class="card-header"><span class="card-title">Type Distribution</span></div>${distHtml||'<p style="color:var(--text-muted)">No data</p>'}</div>
        <div class="card"><div class="card-header"><span class="card-title">Status Overview</span></div><div style="padding:8px 0">${statusHtml||'<p style="color:var(--text-muted)">No data</p>'}</div></div>
      </div>
      <div class="card" style="margin-top:24px"><div class="card-header"><span class="card-title">Recent Items</span></div>${recentHtml}</div>`;
  } catch(e) { mc.innerHTML = `<div class="empty-state"><p>Error loading dashboard: ${escapeHtml(e.message)}</p></div>`; }
}
