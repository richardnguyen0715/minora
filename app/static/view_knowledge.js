/** Knowledge list view */
var knState = { page:1, type:"", status:"", search:"", sort_by:"updated_at", sort_order:"desc" };
function knChangePage(p) { knState.page=p; renderKnowledge(); }

async function renderKnowledge() {
  var mc = document.getElementById("main-content");
  mc.innerHTML =
    '<div class="page-header"><div><h1 class="page-title">Knowledge Explorer</h1><p class="page-description">Browse, search and manage knowledge nodes</p></div>' +
      '<button class="btn btn-primary" onclick="openCreateNodeModal()">+ New Node</button></div>' +
    '<div class="toolbar">' +
      '<div class="search-box"><span class="search-icon">' + svgIcon("search", 16) + '</span><input id="kn-search" placeholder="Search nodes..." value="' + escapeHtml(knState.search) + '" onkeyup="knDebounceSearch(this.value)"></div>' +
      '<select id="kn-type" onchange="knState.type=this.value;knState.page=1;renderKnowledge()"><option value="">All Types</option><option value="source"' + (knState.type==="source"?" selected":"") + '>Source</option><option value="concept"' + (knState.type==="concept"?" selected":"") + '>Concept</option><option value="insight"' + (knState.type==="insight"?" selected":"") + '>Insight</option><option value="summary"' + (knState.type==="summary"?" selected":"") + '>Summary</option><option value="entity"' + (knState.type==="entity"?" selected":"") + '>Entity</option><option value="task"' + (knState.type==="task"?" selected":"") + '>Task</option></select>' +
      '<select id="kn-status" onchange="knState.status=this.value;knState.page=1;renderKnowledge()"><option value="">All Status</option><option value="draft"' + (knState.status==="draft"?" selected":"") + '>Draft</option><option value="imported"' + (knState.status==="imported"?" selected":"") + '>Imported</option><option value="processed"' + (knState.status==="processed"?" selected":"") + '>Processed</option><option value="archived"' + (knState.status==="archived"?" selected":"") + '>Archived</option></select>' +
    '</div><div id="kn-table-area"><div class="loading"><div class="spinner"></div></div></div>';
  try {
    var data = await API.listNodes({type:knState.type,status:knState.status,search:knState.search,sort_by:knState.sort_by,sort_order:knState.sort_order,page:knState.page,per_page:20});
    var area = document.getElementById("kn-table-area");
    if (!data.items.length) { area.innerHTML='<div class="empty-state"><div class="empty-icon">' + svgIcon("inbox", 48) + '</div><p>No nodes found</p></div>'; return; }
    var sortIcon = function(col) { return knState.sort_by===col ? (knState.sort_order==="asc"?" &uarr;":" &darr;") : ""; };
    var sortCls = function(col) { return knState.sort_by===col ? "sorted" : ""; };
    var html = '<div class="card" style="padding:0;overflow:hidden"><table class="data-table"><thead><tr>' +
      '<th class="' + sortCls("title") + '" onclick="knSort(\'title\')">Title' + sortIcon("title") + '</th>' +
      '<th>Type</th><th>Status</th><th>Tags</th>' +
      '<th class="' + sortCls("updated_at") + '" onclick="knSort(\'updated_at\')">Updated' + sortIcon("updated_at") + '</th>' +
      '<th>Actions</th></tr></thead><tbody>';
    for (var i = 0; i < data.items.length; i++) {
      var n = data.items[i];
      var tags = (n.tags||[]).slice(0,3).map(function(t){ return '<span class="tag tag-default">' + escapeHtml(t) + '</span>'; }).join("");
      html += '<tr>' +
        '<td class="clickable" onclick="navigateTo(\'detail\',{id:\'' + escapeHtml(n.id) + '\'})"><strong>' + escapeHtml(n.title) + '</strong><br><span style="font-size:11px;color:var(--text-muted)">' + escapeHtml(n.id) + '</span></td>' +
        '<td><span class="tag type-badge ' + typeTagClass(n.type) + '">' + escapeHtml(n.type) + '</span></td>' +
        '<td><span class="status-badge ' + statusClass(n.status) + '">' + escapeHtml(n.status) + '</span></td>' +
        '<td><div class="tag-list">' + (tags||'-') + '</div></td>' +
        '<td>' + formatDate(n.updated_at) + '</td>' +
        '<td><div class="actions-cell">' +
          '<button class="btn btn-sm btn-secondary" onclick="openEditNodeModal(\'' + escapeHtml(n.id) + '\')">Edit</button>' +
          '<button class="btn btn-sm btn-danger" onclick="confirmDeleteNode(\'' + escapeHtml(n.id) + '\')">Del</button>' +
        '</div></td></tr>';
    }
    html += "</tbody></table></div>";
    html += renderPagination(data.page, data.total_pages, "knChangePage");
    area.innerHTML = html;
  } catch(e) { document.getElementById("kn-table-area").innerHTML='<div class="empty-state"><p>Error: ' + escapeHtml(e.message) + '</p></div>'; }
}

var knSearchTimer = null;
function knDebounceSearch(val) { clearTimeout(knSearchTimer); knSearchTimer=setTimeout(function(){knState.search=val;knState.page=1;renderKnowledge();},400); }
function knSort(col) { if(knState.sort_by===col){knState.sort_order=knState.sort_order==="asc"?"desc":"asc";}else{knState.sort_by=col;knState.sort_order="asc";} knState.page=1; renderKnowledge(); }

function openCreateNodeModal() {
  var body =
    '<div class="form-row"><div class="form-group"><label class="form-label">ID</label><input class="form-input" id="cf-id" placeholder="src_20260501_001"></div>' +
    '<div class="form-group"><label class="form-label">Type</label><select class="form-select" id="cf-type"><option value="source">Source</option><option value="concept">Concept</option><option value="insight">Insight</option><option value="summary">Summary</option><option value="entity">Entity</option><option value="task">Task</option></select></div></div>' +
    '<div class="form-group"><label class="form-label">Title</label><input class="form-input" id="cf-title"></div>' +
    '<div class="form-row"><div class="form-group"><label class="form-label">Status</label><select class="form-select" id="cf-status"><option value="draft">Draft</option><option value="imported">Imported</option><option value="processed">Processed</option></select></div>' +
    '<div class="form-group"><label class="form-label">Confidence</label><input class="form-input" id="cf-conf" type="number" min="0" max="1" step="0.1" placeholder="0.0-1.0"></div></div>' +
    '<div class="form-group"><label class="form-label">Tags (comma-separated)</label><input class="form-input" id="cf-tags"></div>' +
    '<div class="form-group"><label class="form-label">Content</label><textarea class="form-textarea" id="cf-content" rows="5"></textarea></div>';
  var footer = '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitCreateNode()">Create</button>';
  openModal("Create Knowledge Node", body, footer);
}

async function submitCreateNode() {
  try {
    var data = { id:document.getElementById("cf-id").value.trim(), type:document.getElementById("cf-type").value, title:document.getElementById("cf-title").value.trim(),
      status:document.getElementById("cf-status").value, content:document.getElementById("cf-content").value,
      tags:document.getElementById("cf-tags").value.split(",").map(function(s){return s.trim();}).filter(Boolean) };
    var conf = document.getElementById("cf-conf").value;
    if(conf) data.confidence = parseFloat(conf);
    if(!data.id||!data.title){ showToast("ID and Title are required","error"); return; }
    await API.createNode(data);
    closeModal(); showToast("Node created","success"); renderKnowledge();
  } catch(e) { showToast(e.message,"error"); }
}

async function openEditNodeModal(nodeId) {
  try {
    var n = await API.getNode(nodeId);
    var body =
      '<div class="form-group"><label class="form-label">Title</label><input class="form-input" id="ef-title" value="' + escapeHtml(n.title) + '"></div>' +
      '<div class="form-row"><div class="form-group"><label class="form-label">Status</label><select class="form-select" id="ef-status"><option value="draft"' + (n.status==="draft"?" selected":"") + '>Draft</option><option value="imported"' + (n.status==="imported"?" selected":"") + '>Imported</option><option value="processed"' + (n.status==="processed"?" selected":"") + '>Processed</option><option value="archived"' + (n.status==="archived"?" selected":"") + '>Archived</option></select></div>' +
      '<div class="form-group"><label class="form-label">Confidence</label><input class="form-input" id="ef-conf" type="number" min="0" max="1" step="0.1" value="' + (n.confidence!=null?n.confidence:"") + '"></div></div>' +
      '<div class="form-group"><label class="form-label">Slug</label><input class="form-input" id="ef-slug" value="' + escapeHtml(n.slug||"") + '"></div>' +
      '<div class="form-group"><label class="form-label">Tags</label><input class="form-input" id="ef-tags" value="' + escapeHtml((n.tags||[]).join(", ")) + '"></div>' +
      '<div class="form-group"><label class="form-label">Aliases</label><input class="form-input" id="ef-aliases" value="' + escapeHtml((n.aliases||[]).join(", ")) + '"></div>' +
      '<div class="form-group"><label class="form-label">Content</label><textarea class="form-textarea" id="ef-content" rows="8">' + escapeHtml(n.content) + '</textarea></div>';
    var footer = '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="submitEditNode(\'' + escapeHtml(nodeId) + '\')">Save</button>';
    openModal("Edit: " + n.id, body, footer);
  } catch(e) { showToast(e.message,"error"); }
}

async function submitEditNode(nodeId) {
  try {
    var data = { title:document.getElementById("ef-title").value.trim(), status:document.getElementById("ef-status").value,
      slug:document.getElementById("ef-slug").value.trim()||null,
      tags:document.getElementById("ef-tags").value.split(",").map(function(s){return s.trim();}).filter(Boolean),
      aliases:document.getElementById("ef-aliases").value.split(",").map(function(s){return s.trim();}).filter(Boolean),
      content:document.getElementById("ef-content").value };
    var conf = document.getElementById("ef-conf").value;
    if(conf!=="") data.confidence = parseFloat(conf);
    await API.updateNode(nodeId, data);
    closeModal(); showToast("Node updated","success");
    if(location.hash.startsWith("#detail")) renderDetail(nodeId); else renderKnowledge();
  } catch(e) { showToast(e.message,"error"); }
}

async function confirmDeleteNode(nodeId) {
  openModal("Confirm Delete", '<p>Are you sure you want to delete <strong>' + escapeHtml(nodeId) + '</strong>?<br>This will remove both the database record and the markdown file.</p>',
    '<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-danger" onclick="doDeleteNode(\'' + escapeHtml(nodeId) + '\')">Delete</button>');
}
async function doDeleteNode(nodeId) {
  try { await API.deleteNode(nodeId); closeModal(); showToast("Node deleted","success"); renderKnowledge(); } catch(e){ showToast(e.message,"error"); }
}
