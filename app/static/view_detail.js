/** Node detail view */
async function renderDetail(nodeId) {
  const mc = document.getElementById("main-content");
  mc.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
  try {
    const n = await API.getNode(nodeId);
    const tags = (n.tags||[]).map(t=>`<span class="tag tag-default">${escapeHtml(t)}</span>`).join("");
    const aliases = (n.aliases||[]).map(a=>`<span class="tag tag-default">${escapeHtml(a)}</span>`).join("") || "-";
    let edgesHtml = "";
    if (n.edges && n.edges.length) {
      for (const e of n.edges) {
        edgesHtml += `<div class="edge-item"><span class="id-cell">${escapeHtml(e.from_id)}</span><span class="edge-arrow">→ <em>${escapeHtml(e.type)}</em> →</span><span class="id-cell">${escapeHtml(e.to_id)}</span><span style="margin-left:auto;color:var(--text-muted);font-size:11px">w=${e.weight}</span></div>`;
      }
    } else { edgesHtml = '<p style="color:var(--text-muted);font-size:13px">No edges</p>'; }
    let tmHtml = "";
    if (n.type_metadata && Object.keys(n.type_metadata).length) {
      for (const [k,v] of Object.entries(n.type_metadata)) {
        tmHtml += `<div class="detail-field"><div class="detail-field-label">${escapeHtml(k)}</div><div class="detail-field-value">${escapeHtml(v||"-")}</div></div>`;
      }
    }
    let metaHtml = "";
    if (n.metadata && Object.keys(n.metadata).length) {
      for (const [k,v] of Object.entries(n.metadata)) {
        metaHtml += `<div class="detail-field"><div class="detail-field-label">${escapeHtml(k)}</div><div class="detail-field-value">${escapeHtml(typeof v==="object"?JSON.stringify(v):v)}</div></div>`;
      }
    }
    mc.innerHTML = `
      <div class="detail-header"><div>
        <button class="btn btn-sm btn-secondary" onclick="window.history.back()" style="margin-bottom:12px">← Back</button>
        <h1 class="detail-title">${escapeHtml(n.title)}</h1>
        <div class="detail-meta"><span class="tag type-badge ${typeTagClass(n.type)}">${escapeHtml(n.type)}</span><span class="status-badge ${statusClass(n.status)}">${escapeHtml(n.status)}</span>${n.confidence!=null?`<span class="tag tag-default">confidence: ${n.confidence}</span>`:""}</div>
      </div><div><button class="btn btn-primary" onclick="openEditNodeModal('${escapeHtml(n.id)}')">Edit</button> <button class="btn btn-danger" onclick="confirmDeleteNode('${escapeHtml(n.id)}')">Delete</button></div></div>
      <div class="detail-grid"><div>
        <div class="card detail-section"><div class="detail-section-title">Content</div><div class="detail-content">${escapeHtml(n.content||"(empty)")}</div></div>
        <div class="card detail-section"><div class="detail-section-title">Edges</div>${edgesHtml}</div>
      </div><div>
        <div class="card detail-section"><div class="detail-section-title">Info</div>
          <div class="detail-field"><div class="detail-field-label">ID</div><div class="detail-field-value" style="font-family:monospace">${escapeHtml(n.id)}</div></div>
          <div class="detail-field"><div class="detail-field-label">Slug</div><div class="detail-field-value">${escapeHtml(n.slug||"-")}</div></div>
          <div class="detail-field"><div class="detail-field-label">File Path</div><div class="detail-field-value" style="font-size:12px">${escapeHtml(n.file_path)}</div></div>
          <div class="detail-field"><div class="detail-field-label">Hash</div><div class="detail-field-value" style="font-size:11px;font-family:monospace">${escapeHtml(n.hash||"-")}</div></div>
          <div class="detail-field"><div class="detail-field-label">Created</div><div class="detail-field-value">${formatDate(n.created_at)}</div></div>
          <div class="detail-field"><div class="detail-field-label">Updated</div><div class="detail-field-value">${formatDate(n.updated_at)}</div></div>
        </div>
        <div class="card detail-section"><div class="detail-section-title">Tags</div><div class="tag-list">${tags||'<span style="color:var(--text-muted)">-</span>'}</div></div>
        <div class="card detail-section"><div class="detail-section-title">Aliases</div><div class="tag-list">${aliases}</div></div>
        ${tmHtml?`<div class="card detail-section"><div class="detail-section-title">Type Metadata</div>${tmHtml}</div>`:""}
        ${metaHtml?`<div class="card detail-section"><div class="detail-section-title">Metadata</div>${metaHtml}</div>`:""}
      </div></div>`;
  } catch(e) { mc.innerHTML=`<div class="empty-state"><p>Error: ${escapeHtml(e.message)}</p></div>`; }
}
