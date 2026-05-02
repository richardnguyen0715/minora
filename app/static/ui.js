/**
 * UI utility functions: toast, modal, rendering helpers.
 */

/* ---- Toast notifications ---- */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => { toast.style.opacity = "0"; setTimeout(() => toast.remove(), 300); }, 3500);
}

/* ---- Modal ---- */
function openModal(title, bodyHtml, footerHtml = "") {
  const overlay = document.getElementById("modal-overlay");
  document.getElementById("modal-container").innerHTML = `
    <div class="modal-header"><span class="modal-title">${title}</span><button class="modal-close" onclick="closeModal()">&times;</button></div>
    <div class="modal-body">${bodyHtml}</div>
    ${footerHtml ? `<div class="modal-footer">${footerHtml}</div>` : ""}`;
  overlay.classList.add("active");
}
function closeModal() { document.getElementById("modal-overlay").classList.remove("active"); }
document.getElementById("modal-overlay").addEventListener("click", (e) => { if (e.target === e.currentTarget) closeModal(); });

/* ---- Helpers ---- */
function escapeHtml(text) {
  if (!text) return "";
  const div = document.createElement("div");
  div.textContent = String(text);
  return div.innerHTML;
}

function typeTagClass(type) {
  const map = { source: "tag-source", concept: "tag-concept", insight: "tag-insight", summary: "tag-summary", entity: "tag-entity", task: "tag-task" };
  return map[type] || "tag-default";
}

function statusClass(status) {
  const map = { draft: "status-draft", imported: "status-imported", processed: "status-processed", archived: "status-archived", new: "status-new" };
  return map[status] || "status-draft";
}

function formatDate(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleDateString("en-CA") + " " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function renderPagination(page, totalPages, onPageChange) {
  if (totalPages <= 1) return "";
  let html = '<div class="pagination">';
  html += `<button class="pagination-btn" ${page <= 1 ? "disabled" : ""} onclick="${onPageChange}(${page - 1})">&#8249;</button>`;
  const start = Math.max(1, page - 2), end = Math.min(totalPages, page + 2);
  if (start > 1) html += `<button class="pagination-btn" onclick="${onPageChange}(1)">1</button><span class="pagination-info">...</span>`;
  for (let i = start; i <= end; i++) {
    html += `<button class="pagination-btn ${i === page ? "active" : ""}" onclick="${onPageChange}(${i})">${i}</button>`;
  }
  if (end < totalPages) html += `<span class="pagination-info">...</span><button class="pagination-btn" onclick="${onPageChange}(${totalPages})">${totalPages}</button>`;
  html += `<button class="pagination-btn" ${page >= totalPages ? "disabled" : ""} onclick="${onPageChange}(${page + 1})">&#8250;</button>`;
  html += "</div>";
  return html;
}

function distBarColor(type) {
  const map = { source: "var(--accent-blue)", concept: "var(--accent-purple)", insight: "var(--accent-amber)", summary: "var(--accent-emerald)", entity: "var(--accent-cyan)", task: "var(--accent-rose)" };
  return map[type] || "var(--text-muted)";
}
