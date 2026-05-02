# Multi-Agent Ingestion Pipeline & Real Command Implementation

Build a production-ready multi-agent ingestion pipeline that transforms `/import <url>` from a stub into a full pipeline: Fetch → Parse → Extract (LLM) → Concept → Insight → Storage → Report, with all other commands (`/find`, `/update`, `/delete`, etc.) operating on real data.

## User Review Required

> [!IMPORTANT]
> **Gemini API Key**: The plan assumes you will provide Gemini API key(s) via environment variable `GEMINI_API_KEYS` (comma-separated list for rotation). Please confirm.

> [!IMPORTANT]
> **Gemini Model**: The plan defaults to `gemini-2.0-flash` for cost-effective operation. Do you want a different model?

> [!WARNING]
> **Database Migration**: The existing `data/minora.db` will need new columns on the `nodes` table (e.g. `source_type`, `ingested_by`) and the `sources` table needs refactoring. The plan uses `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE` approach to migrate safely. Existing data will be preserved.

> [!CAUTION]
> **Breaking Change in Source Metadata**: The current `ImportSourceUseCase` creates minimal source documents. After refactoring, the frontmatter schema changes significantly (flat fields instead of nested `metadata`). Existing source files in `knowledge/sources/` may need to be re-imported.

## Open Questions

1. **Content fetching for Facebook/Twitter**: These platforms often block scrapers. Should we skip them initially and only support standard web articles?
2. **Embedding storage**: The docs mention embeddings but the current pipeline doesn't generate them. Should we defer embedding to a future phase?
3. **Redis queue**: The docs mention async queue processing. For now, should we run the pipeline inline (async but in-process) without Redis?

---

## Proposed Changes

### Phase 1: Configuration & LLM Infrastructure

Set up Gemini API integration with key rotation, YAML configs, and the LLM abstraction layer.

---

#### [NEW] [configs/agents.yaml](file:///Users/tgng_mac/Coding/minora/configs/agents.yaml)

Agent pipeline configuration:
```yaml
llm:
  provider: gemini
  model: gemini-2.0-flash
  max_retries: 3
  timeout_seconds: 60
  temperature: 0.3

agents:
  fetch:
    timeout_seconds: 30
    max_content_length: 100000
    user_agent: "Minora/1.0"
  parse:
    max_content_length: 50000
  extract:
    max_key_points: 10
    max_concepts: 15
    max_entities: 10
  concept:
    auto_create: true
    match_threshold: 0.8
  insight:
    max_insights: 5
  storage:
    knowledge_root: "knowledge"
  report:
    max_summary_length: 500

pipeline:
  parallel_extraction: true  # Run concept + insight in parallel
  dedup_by_url: true
  notify_on_complete: true
```

---

#### [MODIFY] [.env.example](file:///Users/tgng_mac/Coding/minora/.env.example)

Add Gemini API keys:
```diff
+# Gemini API keys (comma-separated for rotation/fallback)
+GEMINI_API_KEYS=key1,key2,key3
```

---

#### [MODIFY] [config.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/config.py)

Add `gemini_api_keys` field to Settings (list, parsed from comma-separated env var).

---

#### [NEW] [app/infrastructure/llm/__init__.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/llm/__init__.py)

Package init.

#### [NEW] [app/infrastructure/llm/provider.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/llm/provider.py)

Abstract `LLMProvider` interface:
```python
class LLMProvider(ABC):
    async def generate(self, prompt: str, response_format: str = "json") -> dict: ...
    async def generate_text(self, prompt: str) -> str: ...
```

#### [NEW] [app/infrastructure/llm/gemini_provider.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/llm/gemini_provider.py)

Gemini implementation with:
- Key rotation (round-robin through `GEMINI_API_KEYS`)
- Automatic fallback on `429`/`500` errors
- Retry with exponential backoff
- JSON response parsing with fallback to text extraction
- Structured logging for every API call

---

### Phase 2: Agent Framework

Build the base agent abstraction and all 7 pipeline agents.

---

#### [NEW] [app/application/interfaces/llm_provider.py](file:///Users/tgng_mac/Coding/minora/app/application/interfaces/llm_provider.py)

Abstract interface in the application layer (clean architecture boundary):
```python
class LLMProviderInterface(ABC):
    async def generate(self, prompt: str, response_format: str = "json") -> dict: ...
    async def generate_text(self, prompt: str) -> str: ...
```

#### [NEW] [app/domain/entities/pipeline.py](file:///Users/tgng_mac/Coding/minora/app/domain/entities/pipeline.py)

Pipeline data transfer objects:
```python
@dataclass
class FetchResult:
    html: str
    status_code: int
    content_type: str

@dataclass
class ParseResult:
    title: str
    content: str
    author: str | None
    published_at: str | None
    language: str

@dataclass
class ExtractResult:
    summary: str
    key_points: list[str]
    concepts: list[str]
    entities: list[str]
    topics: list[str]

@dataclass
class ConceptResult:
    created: list[str]
    linked: list[str]
    edges: list[KnowledgeEdge]

@dataclass
class InsightResult:
    insights: list[dict]  # {text, impact}

@dataclass
class PipelineContext:
    url: str
    user_id: str
    chat_id: str
    source_id: str
    status: str  # pending → parsed → extracted → completed → failed
    fetch_result: FetchResult | None = None
    parse_result: ParseResult | None = None
    extract_result: ExtractResult | None = None
    concept_result: ConceptResult | None = None
    insight_result: InsightResult | None = None
    error: str | None = None
```

---

#### [NEW] [app/infrastructure/agents/__init__.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/__init__.py)

Package init.

#### [NEW] [app/infrastructure/agents/base_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/base_agent.py)

Base agent with logging, error handling, retry:
```python
class BaseAgent(ABC):
    name: str
    async def run(self, context: PipelineContext) -> PipelineContext: ...
    async def _execute(self, context: PipelineContext) -> PipelineContext: ...
```

#### [NEW] [app/infrastructure/agents/fetch_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/fetch_agent.py)

HTTP fetch using `httpx` (already a dependency). No LLM. Returns raw HTML.

#### [NEW] [app/infrastructure/agents/parse_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/parse_agent.py)

Extract main content from HTML. Uses a lightweight approach:
- Strip `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>` tags
- Extract `<article>` or `<main>` content preferentially
- Extract `<title>`, `<meta>` author/description
- Convert to clean text
- No external dependency (use built-in `html.parser` or add `beautifulsoup4`)

> [!NOTE]
> Will add `beautifulsoup4` as dependency for robust HTML parsing.

#### [NEW] [app/infrastructure/agents/extract_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/extract_agent.py)

LLM-powered extraction. Sends parsed content to Gemini with structured JSON prompt. Extracts: summary, key_points, concepts, entities, topics.

#### [NEW] [app/infrastructure/agents/concept_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/concept_agent.py)

Maps extracted concepts to existing DB concepts or creates new ones. Creates edges between source → concept.

#### [NEW] [app/infrastructure/agents/insight_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/insight_agent.py)

LLM-powered insight generation. Creates insight nodes with edges to source.

#### [NEW] [app/infrastructure/agents/storage_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/storage_agent.py)

Saves all results to markdown files + metadata DB:
- Updates source node with full extracted data
- Creates concept nodes/files
- Creates insight nodes/files
- Creates all edges

#### [NEW] [app/infrastructure/agents/report_agent.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/agents/report_agent.py)

Formats pipeline results into a Telegram-friendly report message.

---

### Phase 3: Ingestion Orchestrator

The central brain that runs the pipeline.

---

#### [NEW] [app/application/use_cases/ingestion_orchestrator.py](file:///Users/tgng_mac/Coding/minora/app/application/use_cases/ingestion_orchestrator.py)

```python
class IngestionOrchestrator:
    """Orchestrate the multi-agent ingestion pipeline."""

    async def run(self, url: str, user_id: str, chat_id: str) -> str:
        """
        Full pipeline:
        1. Create source (status=pending)
        2. Fetch content
        3. Parse content (status=parsed)
        4. Extract with LLM (status=extracted)
        5. Concept mapping + Insight generation (parallel)
        6. Storage (status=completed)
        7. Report generation
        """
```

Key features:
- Each step updates `PipelineContext.status`
- On failure at any step: status=failed, error logged, partial results saved
- Concept + Insight agents run in parallel via `asyncio.gather`
- Returns formatted report string

---

### Phase 4: Database & Schema Refactor

Align the metadata DB and markdown schema with [file-content.md](file:///Users/tgng_mac/Coding/minora/docs/file-content.md).

---

#### [MODIFY] [models.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/database/models.py)

Update `SourceMetadataRecord` to add new fields per file-content.md:
```diff
 class SourceMetadataRecord(Base):
     __tablename__ = "sources"
     node_id = Column(String(64), primary_key=True)
     url = Column(String(2048), nullable=False, index=True)
     platform = Column(String(64), nullable=True, index=True)
     author = Column(String(255), nullable=True)
     language = Column(String(32), nullable=True, index=True)
+    source_type = Column(String(32), nullable=True)  # article | video | tweet
+    ingested_by = Column(String(64), nullable=True)
+    title_extracted = Column(Text, nullable=True)
+    summary = Column(Text, nullable=True)
+    content_hash = Column(String(64), nullable=True, index=True)
```

#### [MODIFY] [__init__.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/database/__init__.py)

Add a `migrate_db()` function that safely adds new columns using `ALTER TABLE` if they don't exist.

#### [MODIFY] [repository.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/knowledge/repository.py)

Update `_upsert_source_metadata` to handle new fields from the pipeline context.

---

### Phase 5: Refactor Import Command & Wire Pipeline

Replace the stub `/import` handler with the real pipeline.

---

#### [MODIFY] [import_source.py](file:///Users/tgng_mac/Coding/minora/app/application/use_cases/import_source.py)

Refactor to use `IngestionOrchestrator`:
- Still handles URL validation and duplicate detection
- Delegates heavy work to orchestrator
- Returns pipeline report for Telegram response

#### [MODIFY] [config.py (handlers)](file:///Users/tgng_mac/Coding/minora/app/infrastructure/commands/handlers/config.py)

Update `handle_import` to:
1. Send immediate "Processing..." message
2. Run orchestrator asynchronously via `asyncio.create_task`
3. Send full report when done

For this, `handle_import` needs access to the `messenger` and `chat_id`. We'll modify the command handler signature to pass a `CommandContext` object.

> [!IMPORTANT]
> **Handler Signature Change**: Current handlers have signature `(args, user_id) -> str`. To support async notifications (Phase 2 response), we need to either:
> - **Option A**: Add optional `context` param with `messenger` and `chat_id` (backward compatible)
> - **Option B**: Use `asyncio.create_task` inside handler and return immediate response
>
> **Recommendation**: Option B — return immediate "Processing..." response, run pipeline in background task, and have the orchestrator send the report directly via messenger. This requires the handler to receive `messenger` and `chat_id`.

I'll extend the `Command` entity to support a `context_handler` that receives the full context alongside the basic handler.

#### [MODIFY] [command.py](file:///Users/tgng_mac/Coding/minora/app/domain/entities/command.py)

Add optional `requires_context: bool = False` field to Command. When True, the dispatcher passes extended context.

#### [MODIFY] [command_dispatcher.py](file:///Users/tgng_mac/Coding/minora/app/application/services/command_dispatcher.py)

When `command.requires_context`, pass `CommandContext(args, user_id, chat_id, messenger)` to handler.

#### [NEW] [app/domain/entities/command_context.py](file:///Users/tgng_mac/Coding/minora/app/domain/entities/command_context.py)

```python
@dataclass
class CommandContext:
    args: dict
    user_id: str
    chat_id: str
    messenger: Any  # Messenger interface
```

#### [MODIFY] [handle_command.py](file:///Users/tgng_mac/Coding/minora/app/application/use_cases/handle_command.py)

Pass `chat_id` and `messenger` to dispatcher for context-aware commands.

---

### Phase 6: Real Command Implementations

Make `/find`, `/list`, `/read`, `/update`, `/delete`, `/visualize` work with real data.

---

#### [MODIFY] [data.py (handlers)](file:///Users/tgng_mac/Coding/minora/app/infrastructure/commands/handlers/data.py)

These handlers already delegate to `KnowledgeItemUseCase` which already works with real data. The main changes needed:
- `handle_find`: Already working. Add full-text search across `summary` field in sources.
- `handle_list`: Already working. Add filter by type and status.
- `handle_update`: Already working. Ensure it can update status and pipeline fields.
- `handle_delete`: Already working. Ensure cleanup of related concepts/insights.

The `KnowledgeItemUseCase` and `KnowledgeRepository` are already functional. Minimal changes needed here.

---

### Phase 7: Source Markdown Refactor

Update markdown body template to match file-content.md spec.

---

#### [MODIFY] [markdown_storage.py](file:///Users/tgng_mac/Coding/minora/app/infrastructure/knowledge/markdown_storage.py)

Update `MarkdownDocument.to_frontmatter()` for source type: use flat fields instead of nested `metadata` dict. Add:
```yaml
url: ...
platform: ...
author: ...
language: ...
source_type: article
ingested_by: user_123
status: pending  # → parsed → extracted → completed
title_extracted: ...
summary: ...
key_points: []
entities: []
concept_candidates: []
related_concepts: []
related_sources: []
content_hash: ...
```

Update body template for sources:
```markdown
# {{title_extracted or title}}

## Summary
{{summary}}

## Key Points
{{key_points as bullets}}

## Extracted Concepts
{{concepts as wikilinks}}

## Entities
{{entities as wikilinks}}

## Insights
{{insights}}

## Raw Content
{{truncated raw content}}
```

---

### Dependency Addition

#### [MODIFY] [pyproject.toml](file:///Users/tgng_mac/Coding/minora/pyproject.toml)

```diff
+    "beautifulsoup4 (>=4.13.0,<5.0.0)",
+    "google-genai (>=1.0.0,<2.0.0)",
```

---

## Verification Plan

### Automated Tests

#### New test files:
- `tests/unit/test_gemini_provider.py` — Mock API calls, test key rotation, retry, JSON parsing
- `tests/unit/test_agents.py` — Test each agent in isolation with mock LLM
- `tests/unit/test_ingestion_orchestrator.py` — Test full pipeline with mocked agents
- `tests/unit/test_pipeline_entities.py` — Test data transfer objects

#### Run existing tests:
```bash
conda activate minora && cd /Users/tgng_mac/Coding/minora && python -m pytest tests/ -v
```

### Manual Verification
1. Start the bot: `python -m app.main`
2. Send `/import https://en.wikipedia.org/wiki/Large_language_model` in Telegram
3. Verify:
   - Immediate "Processing..." response
   - Full report after pipeline completes
   - Source markdown file created in `knowledge/sources/`
   - Concept files created in `knowledge/concepts/`
   - Insight file created in `knowledge/insights/`
   - All nodes/edges/tags in `data/minora.db`
4. Test `/find llm` → returns matching items
5. Test `/read <source_id>` → shows full detail
6. Test `/visualize` → shows DB overview

---

## Summary of Files Changed

| Action | File | Phase |
|--------|------|-------|
| NEW | `configs/agents.yaml` | 1 |
| MODIFY | `.env.example` | 1 |
| MODIFY | `app/infrastructure/config.py` | 1 |
| NEW | `app/infrastructure/llm/__init__.py` | 1 |
| NEW | `app/infrastructure/llm/provider.py` | 1 |
| NEW | `app/infrastructure/llm/gemini_provider.py` | 1 |
| NEW | `app/application/interfaces/llm_provider.py` | 2 |
| NEW | `app/domain/entities/pipeline.py` | 2 |
| NEW | `app/infrastructure/agents/__init__.py` | 2 |
| NEW | `app/infrastructure/agents/base_agent.py` | 2 |
| NEW | `app/infrastructure/agents/fetch_agent.py` | 2 |
| NEW | `app/infrastructure/agents/parse_agent.py` | 2 |
| NEW | `app/infrastructure/agents/extract_agent.py` | 2 |
| NEW | `app/infrastructure/agents/concept_agent.py` | 2 |
| NEW | `app/infrastructure/agents/insight_agent.py` | 2 |
| NEW | `app/infrastructure/agents/storage_agent.py` | 2 |
| NEW | `app/infrastructure/agents/report_agent.py` | 2 |
| NEW | `app/application/use_cases/ingestion_orchestrator.py` | 3 |
| MODIFY | `app/infrastructure/database/models.py` | 4 |
| MODIFY | `app/infrastructure/database/__init__.py` | 4 |
| MODIFY | `app/infrastructure/knowledge/repository.py` | 4 |
| MODIFY | `app/application/use_cases/import_source.py` | 5 |
| MODIFY | `app/infrastructure/commands/handlers/config.py` | 5 |
| NEW | `app/domain/entities/command_context.py` | 5 |
| MODIFY | `app/domain/entities/command.py` | 5 |
| MODIFY | `app/application/services/command_dispatcher.py` | 5 |
| MODIFY | `app/application/use_cases/handle_command.py` | 5 |
| MODIFY | `app/infrastructure/commands/handlers/data.py` | 6 |
| MODIFY | `app/infrastructure/knowledge/markdown_storage.py` | 7 |
| MODIFY | `pyproject.toml` | - |
| NEW | `tests/unit/test_gemini_provider.py` | - |
| NEW | `tests/unit/test_agents.py` | - |
| NEW | `tests/unit/test_ingestion_orchestrator.py` | - |
