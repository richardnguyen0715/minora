/**
 * UI utility functions: toast, modal, rendering helpers, SVG icons.
 */

/* ---- SVG Icons (no emoji) ---- */
const SVG_ICONS = {
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
  knowledge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15 15 0 0 1 4 10 15 15 0 0 1-4 10 15 15 0 0 1-4-10 15 15 0 0 1 4-10z"/><path d="M2 12h20"/></svg>',
  link: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
  edge: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>',
  tag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
  inbox: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>',
  dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
};

function svgIcon(name, size) {
  const s = size || 20;
  const svg = SVG_ICONS[name] || '';
  return '<span style="display:inline-flex;width:' + s + 'px;height:' + s + 'px">' + svg + '</span>';
}

/* ---- Toast notifications ---- */
function showToast(message, type) {
  type = type || "info";
  var container = document.getElementById("toast-container");
  var toast = document.createElement("div");
  toast.className = "toast toast-" + type;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(function() { toast.style.opacity = "0"; setTimeout(function() { toast.remove(); }, 300); }, 3500);
}

/* ---- Modal ---- */
function openModal(title, bodyHtml, footerHtml) {
  footerHtml = footerHtml || "";
  var overlay = document.getElementById("modal-overlay");
  document.getElementById("modal-container").innerHTML =
    '<div class="modal-header"><span class="modal-title">' + title + '</span><button class="modal-close" onclick="closeModal()">&times;</button></div>' +
    '<div class="modal-body">' + bodyHtml + '</div>' +
    (footerHtml ? '<div class="modal-footer">' + footerHtml + '</div>' : '');
  overlay.classList.add("active");
}
function closeModal() { document.getElementById("modal-overlay").classList.remove("active"); }
document.getElementById("modal-overlay").addEventListener("click", function(e) { if (e.target === e.currentTarget) closeModal(); });

/* ---- Helpers ---- */
function escapeHtml(text) {
  if (!text) return "";
  var div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function typeTagClass(type) {
  var map = { source: "tag-source", concept: "tag-concept", insight: "tag-insight", summary: "tag-summary", entity: "tag-entity", task: "tag-task" };
  return map[type] || "tag-default";
}

function statusClass(status) {
  var map = { draft: "status-draft", imported: "status-imported", processed: "status-processed", completed: "status-completed", archived: "status-archived", new: "status-new" };
  return map[status] || "status-draft";
}

function formatDate(iso) {
  if (!iso) return "-";
  var d = new Date(iso);
  var now = new Date();
  var diffMs = now - d;
  var diffMin = Math.floor(diffMs / 60000);
  var diffHr = Math.floor(diffMs / 3600000);
  var diffDay = Math.floor(diffMs / 86400000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return diffMin + "m ago";
  if (diffHr < 24) return diffHr + "h ago";
  if (diffDay < 7) return diffDay + "d ago";
  return d.toLocaleDateString("en-CA") + " " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function renderPagination(page, totalPages, onPageChange) {
  if (totalPages <= 1) return "";
  var html = '<div class="pagination">';
  html += '<button class="pagination-btn" ' + (page <= 1 ? "disabled" : "") + ' onclick="' + onPageChange + '(' + (page - 1) + ')">&#8249;</button>';
  var start = Math.max(1, page - 2), end = Math.min(totalPages, page + 2);
  if (start > 1) html += '<button class="pagination-btn" onclick="' + onPageChange + '(1)">1</button><span class="pagination-info">...</span>';
  for (var i = start; i <= end; i++) {
    html += '<button class="pagination-btn ' + (i === page ? "active" : "") + '" onclick="' + onPageChange + '(' + i + ')">' + i + '</button>';
  }
  if (end < totalPages) html += '<span class="pagination-info">...</span><button class="pagination-btn" onclick="' + onPageChange + '(' + totalPages + ')">' + totalPages + '</button>';
  html += '<button class="pagination-btn" ' + (page >= totalPages ? "disabled" : "") + ' onclick="' + onPageChange + '(' + (page + 1) + ')">&#8250;</button>';
  html += "</div>";
  return html;
}

function distBarColor(type) {
  var map = { source: "var(--accent-blue)", concept: "var(--accent-purple)", insight: "var(--accent-amber)", summary: "var(--accent-emerald)", entity: "var(--accent-cyan)", task: "var(--accent-rose)" };
  return map[type] || "var(--text-muted)";
}

function renderMarkdown(text) {
  if (!text) return '<p style="color:var(--text-muted)">(empty)</p>';
  if (typeof marked !== "undefined" && marked.parse) {
    return marked.parse(text);
  }
  return '<pre style="white-space:pre-wrap">' + escapeHtml(text) + '</pre>';
}
