# Minora Knowledge Base Web UI - Walkthrough

## Summary

Built a full-featured Web UI for visualizing and interacting with the Minora 2-layer knowledge store (SQLite metadata DB + markdown files). The UI runs as a standalone FastAPI server on port `8080`.

## How to Run

```bash
conda run -n minora python -m app.web_main
# Open http://localhost:8080
```

## Screenshots

### Dashboard
![Dashboard with stats, type distribution, and recent items](/Users/tgng_mac/.gemini/antigravity/brain/1c8736e7-cd7a-43b3-9f67-9861a674b7f5/dashboard.png)

### Knowledge Explorer
![Knowledge table with search, filter, sort, and CRUD actions](/Users/tgng_mac/.gemini/antigravity/brain/1c8736e7-cd7a-43b3-9f67-9861a674b7f5/knowledge.png)

### Node Detail
![Full node detail with content, edges, metadata, tags](/Users/tgng_mac/.gemini/antigravity/brain/1c8736e7-cd7a-43b3-9f67-9861a674b7f5/detail.png)

## Files Created

### Backend (4 files)
| File | Purpose |
|------|---------|
| [web_config.yaml](file:///Users/tgng_mac/Coding/minora/configs/web_config.yaml) | Server config (host, port, pagination) |
| [web_knowledge.py](file:///Users/tgng_mac/Coding/minora/app/application/use_cases/web_knowledge.py) | Use case layer with structured JSON responses for CRUD on nodes, edges, tags, links |
| [web_ui.py](file:///Users/tgng_mac/Coding/minora/app/interface/api/web_ui.py) | FastAPI REST API routes with Pydantic validation |
| [web_main.py](file:///Users/tgng_mac/Coding/minora/app/web_main.py) | Standalone entry point (no Telegram dependency) |

### Frontend (8 files in `app/static/`)
| File | Purpose |
|------|---------|
| [index.html](file:///Users/tgng_mac/Coding/minora/app/static/index.html) | SPA shell with sidebar navigation |
| [style.css](file:///Users/tgng_mac/Coding/minora/app/static/style.css) | Dark-mode design system with glassmorphism |
| [api.js](file:///Users/tgng_mac/Coding/minora/app/static/api.js) | REST API client |
| [ui.js](file:///Users/tgng_mac/Coding/minora/app/static/ui.js) | Toast, modal, rendering helpers |
| [view_dashboard.js](file:///Users/tgng_mac/Coding/minora/app/static/view_dashboard.js) | Dashboard with stats cards and charts |
| [view_knowledge.js](file:///Users/tgng_mac/Coding/minora/app/static/view_knowledge.js) | Knowledge table + Create/Edit/Delete modals |
| [view_detail.js](file:///Users/tgng_mac/Coding/minora/app/static/view_detail.js) | Node detail page |
| [view_others.js](file:///Users/tgng_mac/Coding/minora/app/static/view_others.js) | Links, Edges, Tags views with CRUD |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/nodes` | List nodes (filter, search, sort, paginate) |
| GET | `/api/nodes/{id}` | Node detail with content, edges, tags |
| POST | `/api/nodes` | Create node |
| PUT | `/api/nodes/{id}` | Update node |
| DELETE | `/api/nodes/{id}` | Delete node + markdown file |
| PUT | `/api/nodes/{id}/content` | Replace markdown content |
| GET/POST/DELETE | `/api/edges` | Edge CRUD |
| GET | `/api/tags` | List tags with counts |
| GET/PUT/DELETE | `/api/links` | Link CRUD |

## Architecture

Follows the existing clean architecture pattern:

- **Interface** → `web_ui.py` (REST routes)
- **Application** → `web_knowledge.py` (use cases)
- **Infrastructure** → Existing `KnowledgeRepository` + `MarkdownStorage`
- **Domain** → Existing `KnowledgeDocument` + `KnowledgeEdge`

## Verification

- ✅ API returns correct data (`/api/stats` returns 5 nodes, 1 tag)
- ✅ Dashboard renders with stats, distribution bars, recent items
- ✅ Knowledge Explorer shows all nodes with search/filter/sort
- ✅ Node Detail displays content, edges, tags, metadata
- ✅ Edit/Create/Delete modals functional
- ✅ Links, Edges, Tags views render correctly
