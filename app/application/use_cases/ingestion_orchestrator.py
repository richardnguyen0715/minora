"""Ingestion orchestrator: coordinates the multi-agent pipeline."""

import asyncio
from datetime import datetime, timezone
from hashlib import sha256

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.pipeline import PipelineContext
from app.domain.services.link_service import LinkService
from app.infrastructure.agents.concept_agent import ConceptAgent
from app.infrastructure.agents.extract_agent import ExtractAgent
from app.infrastructure.agents.fetch_agent import FetchAgent
from app.infrastructure.agents.insight_agent import InsightAgent
from app.infrastructure.agents.parse_agent import ParseAgent
from app.infrastructure.agents.report_agent import ReportAgent
from app.infrastructure.agents.storage_agent import StorageAgent
from app.infrastructure.config import settings
from app.infrastructure.knowledge.repository import KnowledgeRepository
from app.infrastructure.llm.gemini_provider import GeminiProvider
from app.infrastructure.llm.provider import LLMProvider


class IngestionOrchestrator:
    """
    Orchestrate the multi-agent ingestion pipeline.

    Flow: Fetch -> Parse -> Extract(LLM) -> [Concept + Insight](parallel) -> Storage -> Report
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = KnowledgeRepository(session)
        self._config = settings.get_agents_config()

    def _get_llm(self) -> LLMProvider:
        """Create LLM provider from configuration."""
        keys = settings.get_gemini_keys()
        if not keys:
            raise ValueError("No Gemini API keys configured. Set GEMINI_API_KEYS in .env")

        llm_config = self._config.get("llm", {})
        return GeminiProvider(
            api_keys=keys,
            model=llm_config.get("model", "gemini-2.0-flash"),
            max_retries=llm_config.get("max_retries", 3),
            timeout_seconds=llm_config.get("timeout_seconds", 60),
            temperature=llm_config.get("temperature", 0.3),
            max_output_tokens=llm_config.get("max_output_tokens", 4096),
            api_base_url=llm_config.get("api_base_url", ""),
        )

    def _generate_source_id(self, url: str, platform: str) -> str:
        """Generate unique source ID."""
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_hash = sha256(url.encode("utf-8")).hexdigest()[:8]
        return f"src_{date_str}_{platform}_{short_hash}"

    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL using YAML-configured platform map."""
        domain = LinkService.extract_domain(url).lower()
        platforms_config = self._config.get("platforms", {})
        for platform_name, keywords in platforms_config.items():
            for keyword in keywords:
                if keyword in domain:
                    return platform_name
        return "web"

    async def run(self, url: str, user_id: str, chat_id: str) -> str:
        """
        Execute the full ingestion pipeline.

        Args:
            url (str): URL to ingest.
            user_id (str): User who triggered the import.
            chat_id (str): Chat ID for notifications.

        Returns:
            str: Formatted report message for Telegram.
        """
        platform = self._detect_platform(url)
        source_id = self._generate_source_id(url, platform)

        logger.info("pipeline_started", extra={"source_id": source_id, "url": url, "user_id": user_id})

        # Check for duplicate
        existing = await self.repository.get_node_by_url(url)
        if existing:
            return f"[WARN] This source was already imported: {existing.id}"

        context = PipelineContext(
            url=url, user_id=user_id, chat_id=chat_id,
            source_id=source_id, platform=platform, status="pending",
        )

        agent_config = self._config.get("agents", {})
        pipeline_config = self._config.get("pipeline", {})

        try:
            # Step 1: Fetch
            fetch_cfg = agent_config.get("fetch", {})
            fetch_agent = FetchAgent(
                timeout_seconds=fetch_cfg.get("timeout_seconds", 30),
                max_content_length=fetch_cfg.get("max_content_length", 100000),
                user_agent=fetch_cfg.get("user_agent", "Minora/1.0"),
            )
            context = await fetch_agent.run(context)
            if context.status == "failed":
                return ReportAgent().format_report(context)

            # Step 2: Parse
            parse_cfg = agent_config.get("parse", {})
            parse_agent = ParseAgent(
                max_content_length=parse_cfg.get("max_content_length", 50000),
            )
            context = await parse_agent.run(context)
            if context.status == "failed":
                return ReportAgent().format_report(context)

            # Step 3: Extract (LLM)
            llm = self._get_llm()
            extract_cfg = agent_config.get("extract", {})
            llm_config = self._config.get("llm", {})
            extract_agent = ExtractAgent(
                llm=llm,
                max_key_points=extract_cfg.get("max_key_points", 10),
                max_concepts=extract_cfg.get("max_concepts", 15),
                max_entities=extract_cfg.get("max_entities", 10),
                max_prompt_content_length=llm_config.get("max_prompt_content_length", 30000),
            )
            context = await extract_agent.run(context)
            if context.status == "failed":
                return ReportAgent().format_report(context)

            # Step 4: Concept + Insight (parallel)
            concept_cfg = agent_config.get("concept", {})
            concept_agent = ConceptAgent(
                session=self.session,
                auto_create=concept_cfg.get("auto_create", True),
            )

            insight_cfg = agent_config.get("insight", {})
            insight_agent = InsightAgent(
                llm=llm, session=self.session,
                max_insights=insight_cfg.get("max_insights", 5),
            )

            if pipeline_config.get("parallel_extraction", True):
                concept_ctx, insight_ctx = await asyncio.gather(
                    concept_agent.run(PipelineContext(**vars(context))),
                    insight_agent.run(PipelineContext(**vars(context))),
                )
                # Merge results back
                context.concept_result = concept_ctx.concept_result
                context.insight_result = insight_ctx.insight_result
                if concept_ctx.status == "failed":
                    context.error = concept_ctx.error
                    context.error_stage = "concept"
                if insight_ctx.status == "failed":
                    context.error = insight_ctx.error
                    context.error_stage = "insight"
            else:
                context = await concept_agent.run(context)
                context = await insight_agent.run(context)

            # Step 5: Storage
            storage_cfg = agent_config.get("storage", {})
            storage_agent = StorageAgent(
                session=self.session,
                knowledge_root=storage_cfg.get("knowledge_root", "knowledge"),
            )
            context = await storage_agent.run(context)

            # Step 6: Report
            report_cfg = agent_config.get("report", {})
            report_agent = ReportAgent(
                max_summary_length=report_cfg.get("max_summary_length", 500),
            )
            report = report_agent.format_report(context)

            logger.info("pipeline_completed", extra={"source_id": source_id, "status": context.status})
            return report

        except Exception as exc:
            context.status = "failed"
            context.error = str(exc)
            logger.error("pipeline_fatal_error", extra={"source_id": source_id, "error": str(exc)})
            return f"[ERROR] Pipeline failed: {str(exc)}\nSource: {url}"
