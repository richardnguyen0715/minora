"""Insight agent: generates non-obvious insights from extracted content using LLM."""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument, KnowledgeEdge
from app.domain.entities.pipeline import InsightEntry, InsightResult, PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent
from app.infrastructure.knowledge.repository import KnowledgeRepository
from app.infrastructure.llm.provider import LLMProvider


class InsightAgent(BaseAgent):
    """
    LLM-powered insight generation.

    Generates high-value, non-obvious insights from extracted content.
    Creates insight nodes and edges linking to source.
    """

    name = "insight"

    def __init__(self, llm: LLMProvider, session: AsyncSession, max_insights: int = 5) -> None:
        self.llm = llm
        self.session = session
        self.repository = KnowledgeRepository(session)
        self.max_insights = max_insights

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        if not context.extract_result:
            raise ValueError("No extract result available for insight generation")

        summary = context.extract_result.summary
        key_points = context.extract_result.key_points
        prompt = self._build_prompt(summary, key_points)
        result = await self.llm.generate(prompt)

        raw_insights = result.get("insights", [])
        insights = []

        for index, raw in enumerate(raw_insights[: self.max_insights]):
            text = str(raw.get("text", raw) if isinstance(raw, dict) else raw).strip()
            impact = str(raw.get("impact", "medium") if isinstance(raw, dict) else "medium")
            if not text:
                continue

            insight_entry = InsightEntry(text=text, impact=impact)
            insights.append(insight_entry)

            insight_id = f"insight_{context.source_id}_{index:02d}"
            document = self._create_insight_document(insight_id, text, impact, context.source_id)
            await self.repository.upsert_document(document)

            edge = KnowledgeEdge(from_id=context.source_id, to_id=insight_id, type="generated_insight", weight=1.0)
            await self.repository.add_edge(edge)

        context.insight_result = InsightResult(insights=insights)
        logger.info("insight_generation_complete", extra={"source_id": context.source_id, "insights_count": len(insights)})
        return context

    def _build_prompt(self, summary: str, key_points: list[str]) -> str:
        points_text = "\n".join(f"- {p}" for p in key_points)
        return (
            "You are a strategic thinker. Given this summary and key points, generate insights.\n\n"
            f"Summary:\n{summary}\n\nKey Points:\n{points_text}\n\n"
            f"Generate up to {self.max_insights} insights focusing on non-obvious ideas and implications.\n\n"
            'Return JSON: {"insights": [{"text": "...", "impact": "high|medium|low"}]}\n'
            "Return ONLY the JSON object."
        )

    @staticmethod
    def _create_insight_document(insight_id: str, text: str, impact: str, source_id: str) -> KnowledgeDocument:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        content = f"# Insight\n\n{text}\n\n## Source\n- [[{source_id}]]\n\n## Impact\n{impact}\n"
        return KnowledgeDocument(
            id=insight_id, type="insight", title=text[:100], content=content,
            slug=insight_id, status="draft", confidence=0.7,
            metadata={"impact": impact, "source_id": source_id},
            created_at=now, updated_at=now,
        )
