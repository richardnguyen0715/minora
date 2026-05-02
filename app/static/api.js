/**
 * API client for the Minora Knowledge Base Web UI.
 * Provides methods to interact with all REST endpoints.
 */
const API = {
  async request(method, path, body = null) {
    const options = { method, headers: { "Content-Type": "application/json" } };
    if (body) options.body = JSON.stringify(body);
    const response = await fetch(`/api${path}`, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Request failed");
    }
    return response.json();
  },
  getStats() { return this.request("GET", "/stats"); },
  listNodes(params = {}) {
    const query_string = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== "")).toString();
    return this.request("GET", `/nodes?${query_string}`);
  },
  getNode(id) { return this.request("GET", `/nodes/${encodeURIComponent(id)}`); },
  createNode(data) { return this.request("POST", "/nodes", data); },
  updateNode(id, data) { return this.request("PUT", `/nodes/${encodeURIComponent(id)}`, data); },
  deleteNode(id) { return this.request("DELETE", `/nodes/${encodeURIComponent(id)}`); },
  replaceContent(id, content) { return this.request("PUT", `/nodes/${encodeURIComponent(id)}/content`, { content }); },
  listEdges(node_id = null) {
    const query_string = node_id ? `?node_id=${encodeURIComponent(node_id)}` : "";
    return this.request("GET", `/edges${query_string}`);
  },
  createEdge(data) { return this.request("POST", "/edges", data); },
  deleteEdge(id) { return this.request("DELETE", `/edges/${id}`); },
  listTags() { return this.request("GET", "/tags"); },
  listLinks(params = {}) {
    const query_string = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null && v !== "")).toString();
    return this.request("GET", `/links?${query_string}`);
  },
  getLink(id) { return this.request("GET", `/links/${encodeURIComponent(id)}`); },
  updateLink(id, data) { return this.request("PUT", `/links/${encodeURIComponent(id)}`, data); },
  deleteLink(id) { return this.request("DELETE", `/links/${encodeURIComponent(id)}`); },
};
