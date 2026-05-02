# Multi-Agent Ingestion Pipeline - Task Tracker

## Phase 1: Configuration & LLM Infrastructure
- [ ] Create `configs/agents.yaml`
- [ ] Update `.env.example` with Gemini keys
- [ ] Update `app/infrastructure/config.py` with Gemini settings
- [ ] Create `app/infrastructure/llm/__init__.py`
- [ ] Create `app/infrastructure/llm/provider.py`
- [ ] Create `app/infrastructure/llm/gemini_provider.py`
- [ ] Add dependencies to `pyproject.toml`

## Phase 2: Agent Framework
- [ ] Create `app/application/interfaces/llm_provider.py`
- [ ] Create `app/domain/entities/pipeline.py`
- [ ] Create `app/infrastructure/agents/__init__.py`
- [ ] Create `app/infrastructure/agents/base_agent.py`
- [ ] Create `app/infrastructure/agents/fetch_agent.py`
- [ ] Create `app/infrastructure/agents/parse_agent.py`
- [ ] Create `app/infrastructure/agents/extract_agent.py`
- [ ] Create `app/infrastructure/agents/concept_agent.py`
- [ ] Create `app/infrastructure/agents/insight_agent.py`
- [ ] Create `app/infrastructure/agents/storage_agent.py`
- [ ] Create `app/infrastructure/agents/report_agent.py`

## Phase 3: Ingestion Orchestrator
- [ ] Create `app/application/use_cases/ingestion_orchestrator.py`

## Phase 4: Database & Schema Refactor
- [ ] Update `app/infrastructure/database/models.py`
- [ ] Update `app/infrastructure/database/__init__.py`
- [ ] Update `app/infrastructure/knowledge/repository.py`

## Phase 5: Refactor Import Command & Wire Pipeline
- [ ] Create `app/domain/entities/command_context.py`
- [ ] Update `app/domain/entities/command.py`
- [ ] Update `app/application/services/command_dispatcher.py`
- [ ] Update `app/application/use_cases/handle_command.py`
- [ ] Refactor `app/application/use_cases/import_source.py`
- [ ] Update `app/infrastructure/commands/handlers/config.py`
- [ ] Update `app/infrastructure/commands/setup.py`

## Phase 6: Real Command Implementations
- [ ] Update `app/infrastructure/commands/handlers/data.py`

## Phase 7: Source Markdown Refactor
- [ ] Update `app/infrastructure/knowledge/markdown_storage.py`

## Testing & Verification
- [ ] Create `tests/unit/test_gemini_provider.py`
- [ ] Create `tests/unit/test_agents.py`
- [ ] Create `tests/unit/test_ingestion_orchestrator.py`
- [ ] Run all tests and fix issues
