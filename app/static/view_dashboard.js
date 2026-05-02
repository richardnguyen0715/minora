/** Dashboard view renderer */
async function renderDashboard() {
  var mc = document.getElementById("main-content");
  mc.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    var stats = await API.getStats();
    var nc = stats.node_count||0, ec = stats.edge_count||0, tc = stats.tag_count||0, lc = stats.link_count||0;
    document.getElementById("nav-node-count").textContent = nc;
    document.getElementById("nav-edge-count").textContent = ec;
    document.getElementById("nav-tag-count").textContent = tc;
    document.getElementById("nav-link-count").textContent = lc;
    var td = stats.type_distribution||{}, sd = stats.status_distribution||{}, rn = stats.recent_nodes||[];
    var maxType = Math.max(1, ...Object.values(td));
    var distHtml = "";
    for (var t in td) {
      if (!td.hasOwnProperty(t)) continue;
      var c = td[t];
      distHtml += '<div class="dist-bar-container"><div class="dist-bar-label"><span>' + escapeHtml(t) + '</span><span>' + c + '</span></div><div class="dist-bar-track"><div class="dist-bar-fill" style="width:' + (c/maxType*100).toFixed(0) + '%;background:' + distBarColor(t) + '"></div></div></div>';
    }
    var statusHtml = "";
    for (var s in sd) {
      if (!sd.hasOwnProperty(s)) continue;
      statusHtml += '<span class="status-badge ' + statusClass(s) + '" style="margin-right:8px">' + escapeHtml(s) + ': ' + sd[s] + '</span>';
    }
    var recentHtml = "";
    if (rn.length) {
      recentHtml = '<table class="data-table"><thead><tr><th>ID</th><th>Type</th><th>Title</th><th>Updated</th></tr></thead><tbody>';
      for (var i = 0; i < rn.length; i++) {
        var n = rn[i];
        recentHtml += '<tr class="clickable" onclick="navigateTo(\'detail\',{id:\'' + escapeHtml(n.id) + '\'})"><td class="id-cell">' + escapeHtml(n.id) + '</td><td><span class="tag type-badge ' + typeTagClass(n.type) + '">' + escapeHtml(n.type) + '</span></td><td>' + escapeHtml(n.title) + '</td><td>' + formatDate(n.updated_at) + '</td></tr>';
      }
      recentHtml += "</tbody></table>";
    } else { recentHtml = '<div class="empty-state"><p>No knowledge items yet</p></div>'; }
    mc.innerHTML =
      '<div class="page-header"><div><h1 class="page-title">Dashboard</h1><p class="page-description">Overview of your knowledge base</p></div></div>' +
      '<div class="stats-grid">' +
        '<div class="stat-card"><div class="stat-icon purple">' + svgIcon("knowledge", 22) + '</div><div><div class="stat-value">' + nc + '</div><div class="stat-label">Knowledge Nodes</div></div></div>' +
        '<div class="stat-card"><div class="stat-icon blue">' + svgIcon("link", 22) + '</div><div><div class="stat-value">' + lc + '</div><div class="stat-label">Saved Links</div></div></div>' +
        '<div class="stat-card"><div class="stat-icon emerald">' + svgIcon("edge", 22) + '</div><div><div class="stat-value">' + ec + '</div><div class="stat-label">Edges</div></div></div>' +
        '<div class="stat-card"><div class="stat-icon amber">' + svgIcon("tag", 22) + '</div><div><div class="stat-value">' + tc + '</div><div class="stat-label">Tags</div></div></div>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">' +
        '<div class="card"><div class="card-header"><span class="card-title">Type Distribution</span></div>' + (distHtml || '<p style="color:var(--text-muted)">No data</p>') + '</div>' +
        '<div class="card"><div class="card-header"><span class="card-title">Status Overview</span></div><div style="padding:8px 0">' + (statusHtml || '<p style="color:var(--text-muted)">No data</p>') + '</div></div>' +
      '</div>' +
      '<div class="card" style="margin-top:24px"><div class="card-header"><span class="card-title">Recent Items</span></div>' + recentHtml + '</div>';
  } catch(e) { mc.innerHTML = '<div class="empty-state"><p>Error loading dashboard: ' + escapeHtml(e.message) + '</p></div>'; }
}
