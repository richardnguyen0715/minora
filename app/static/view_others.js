/** Links view */
var lnState = { page:1, status:"", search:"", sort_by:"created_at", sort_order:"desc" };
function lnChangePage(p) { lnState.page=p; renderLinks(); }

async function renderLinks() {
  var mc = document.getElementById("main-content");
  mc.innerHTML =
    '<div class="page-header"><div><h1 class="page-title">Links Manager</h1><p class="page-description">Browse and manage saved links</p></div></div>' +
    '<div class="toolbar">' +
      '<div class="search-box"><span class="search-icon">' + svgIcon("search", 16) + '</span><input id="ln-search" placeholder="Search links..." value="' + escapeHtml(lnState.search) + '" onkeyup="lnDebounceSearch(this.value)"></div>' +
      '<select onchange="lnState.status=this.value;lnState.page=1;renderLinks()"><option value="">All Status</option><option value="new"' + (lnState.status==="new"?" selected":"") + '>New</option><option value="processed"' + (lnState.status==="processed"?" selected":"") + '>Processed</option><option value="archived"' + (lnState.status==="archived"?" selected":"") + '>Archived</option></select>' +
    '</div><div id="ln-table"><div class="loading"><div class="spinner"></div></div></div>';
  try {
    var data = await API.listLinks({status:lnState.status,search:lnState.search,sort_by:lnState.sort_by,sort_order:lnState.sort_order,page:lnState.page,per_page:20});
    var area = document.getElementById("ln-table");
    if(!data.items.length){ area.innerHTML='<div class="empty-state"><div class="empty-icon">' + svgIcon("inbox", 48) + '</div><p>No links found</p></div>'; return; }
    var html = '<div class="card" style="padding:0;overflow:hidden"><table class="data-table"><thead><tr><th>URL</th><th>Title</th><th>Status</th><th>Source</th><th>Created</th><th>Actions</th></tr></thead><tbody>';
    for(var i = 0; i < data.items.length; i++){
      var l = data.items[i];
      html += '<tr><td style="max-width:300px;overflow:hidden;text-overflow:ellipsis"><a href="' + escapeHtml(l.url) + '" target="_blank" style="color:var(--accent-blue);text-decoration:none">' + escapeHtml(l.url) + '</a></td>' +
        '<td>' + escapeHtml(l.title||"-") + '</td><td><span class="status-badge ' + statusClass(l.status) + '">' + escapeHtml(l.status) + '</span></td>' +
        '<td>' + escapeHtml(l.source_type||"-") + '</td><td>' + formatDate(l.created_at) + '</td>' +
        '<td><div class="actions-cell"><button class="btn btn-sm btn-secondary" onclick="openEditLinkModal(\'' + escapeHtml(l.id) + '\')">Edit</button><button class="btn btn-sm btn-danger" onclick="confirmDeleteLink(\'' + escapeHtml(l.id) + '\')">Del</button></div></td></tr>';
    }
    html += "</tbody></table></div>" + renderPagination(data.page,data.total_pages,"lnChangePage");
    area.innerHTML = html;
  } catch(e){ document.getElementById("ln-table").innerHTML='<div class="empty-state"><p>Error: ' + escapeHtml(e.message) + '</p></div>'; }
}
var lnSearchTimer=null;
function lnDebounceSearch(v){ clearTimeout(lnSearchTimer); lnSearchTimer=setTimeout(function(){lnState.search=v;lnState.page=1;renderLinks();},400); }

async function openEditLinkModal(linkId) {
  try {
    var l = await API.getLink(linkId);
    var body = '<div class="form-group"><label class="form-label">URL</label><input class="form-input" id="lf-url" value="' + escapeHtml(l.url) + '"></div>' +
      '<div class="form-group"><label class="form-label">Title</label><input class="form-input" id="lf-title" value="' + escapeHtml(l.title||"") + '"></div>' +
      '<div class="form-row"><div class="form-group"><label class="form-label">Status</label><select class="form-select" id="lf-status"><option value="new"' + (l.status==="new"?" selected":"") + '>New</option><option value="processed"' + (l.status==="processed"?" selected":"") + '>Processed</option><option value="archived"' + (l.status==="archived"?" selected":"") + '>Archived</option></select></div>' +
      '<div class="form-group"><label class="form-label">Source Type</label><input class="form-input" id="lf-srctype" value="' + escapeHtml(l.source_type||"") + '"></div></div>';
    openModal("Edit Link: " + l.id, body, '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitEditLink(\'' + escapeHtml(linkId) + '\')">Save</button>');
  } catch(e){ showToast(e.message,"error"); }
}
async function submitEditLink(linkId) {
  try {
    await API.updateLink(linkId, {url:document.getElementById("lf-url").value,title:document.getElementById("lf-title").value,status:document.getElementById("lf-status").value,source_type:document.getElementById("lf-srctype").value});
    closeModal(); showToast("Link updated","success"); renderLinks();
  } catch(e){ showToast(e.message,"error"); }
}
async function confirmDeleteLink(linkId) {
  openModal("Delete Link",'<p>Delete link <strong>' + escapeHtml(linkId) + '</strong>?</p>','<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-danger" onclick="doDeleteLink(\'' + escapeHtml(linkId) + '\')">Delete</button>');
}
async function doDeleteLink(linkId) { try{ await API.deleteLink(linkId); closeModal(); showToast("Link deleted","success"); renderLinks(); }catch(e){showToast(e.message,"error");} }

/** Edges view */
async function renderEdges() {
  var mc = document.getElementById("main-content");
  mc.innerHTML = '<div class="page-header"><div><h1 class="page-title">Edges</h1><p class="page-description">Relationship graph between knowledge nodes</p></div>' +
    '<button class="btn btn-primary" onclick="openCreateEdgeModal()">+ New Edge</button></div><div id="ed-table"><div class="loading"><div class="spinner"></div></div></div>';
  try {
    var edges = await API.listEdges();
    var area = document.getElementById("ed-table");
    if(!edges.length){ area.innerHTML='<div class="empty-state"><div class="empty-icon">' + svgIcon("edge", 48) + '</div><p>No edges yet</p></div>'; return; }
    var html='<div class="card" style="padding:0;overflow:hidden"><table class="data-table"><thead><tr><th>From</th><th></th><th>To</th><th>Type</th><th>Weight</th><th>Actions</th></tr></thead><tbody>';
    for(var i = 0; i < edges.length; i++){
      var e = edges[i];
      html += '<tr><td class="id-cell clickable" onclick="navigateTo(\'detail\',{id:\'' + escapeHtml(e.from_id) + '\'})">' + escapeHtml(e.from_id) + '</td><td class="edge-arrow">&rarr;</td><td class="id-cell clickable" onclick="navigateTo(\'detail\',{id:\'' + escapeHtml(e.to_id) + '\'})">' + escapeHtml(e.to_id) + '</td>' +
        '<td><span class="tag tag-default">' + escapeHtml(e.type) + '</span></td><td>' + e.weight + '</td>' +
        '<td><button class="btn btn-sm btn-danger" onclick="confirmDeleteEdge(' + e.id + ')">Del</button></td></tr>';
    }
    html += "</tbody></table></div>";
    area.innerHTML = html;
  } catch(e){ document.getElementById("ed-table").innerHTML='<div class="empty-state"><p>Error: ' + escapeHtml(e.message) + '</p></div>'; }
}

function openCreateEdgeModal() {
  var body = '<div class="form-group"><label class="form-label">From Node ID</label><input class="form-input" id="edf-from" placeholder="src_20260501_001"></div>' +
    '<div class="form-group"><label class="form-label">To Node ID</label><input class="form-input" id="edf-to"></div>' +
    '<div class="form-row"><div class="form-group"><label class="form-label">Type</label><select class="form-select" id="edf-type"><option value="references">references</option><option value="related_concept">related_concept</option><option value="derived_from">derived_from</option></select></div>' +
    '<div class="form-group"><label class="form-label">Weight</label><input class="form-input" id="edf-weight" type="number" value="1.0" min="0" step="0.1"></div></div>';
  openModal("Create Edge", body, '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitCreateEdge()">Create</button>');
}
async function submitCreateEdge() {
  try {
    var d = {from_id:document.getElementById("edf-from").value.trim(),to_id:document.getElementById("edf-to").value.trim(),type:document.getElementById("edf-type").value,weight:parseFloat(document.getElementById("edf-weight").value)||1.0};
    if(!d.from_id||!d.to_id){showToast("Both node IDs required","error");return;}
    await API.createEdge(d); closeModal(); showToast("Edge created","success"); renderEdges();
  } catch(e){showToast(e.message,"error");}
}
async function confirmDeleteEdge(edgeId) {
  openModal("Delete Edge",'<p>Delete edge #' + edgeId + '?</p>','<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-danger" onclick="doDeleteEdge(' + edgeId + ')">Delete</button>');
}
async function doDeleteEdge(edgeId) { try{ await API.deleteEdge(edgeId); closeModal(); showToast("Edge deleted","success"); renderEdges(); }catch(e){showToast(e.message,"error");} }

/** Tags view */
async function renderTags() {
  var mc = document.getElementById("main-content");
  mc.innerHTML = '<div class="page-header"><div><h1 class="page-title">Tags</h1><p class="page-description">All tags and their usage counts</p></div></div><div id="tg-area"><div class="loading"><div class="spinner"></div></div></div>';
  try {
    var tags = await API.listTags();
    var area = document.getElementById("tg-area");
    if(!tags.length){ area.innerHTML='<div class="empty-state"><div class="empty-icon">' + svgIcon("tag", 48) + '</div><p>No tags yet</p></div>'; return; }
    var html = '<div class="card" style="padding:0;overflow:hidden"><table class="data-table"><thead><tr><th>Tag</th><th>Usage Count</th></tr></thead><tbody>';
    for(var i = 0; i < tags.length; i++) html += '<tr><td><span class="tag tag-default">' + escapeHtml(tags[i].name) + '</span></td><td>' + tags[i].count + '</td></tr>';
    html += "</tbody></table></div>";
    area.innerHTML = html;
  } catch(e){ document.getElementById("tg-area").innerHTML='<div class="empty-state"><p>Error: ' + escapeHtml(e.message) + '</p></div>'; }
}
