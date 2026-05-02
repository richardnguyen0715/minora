"""Storage agent: persists pipeline results to markdown files and metadata DB."""

from datetime import datetime, timezone
from hashlib import sha256

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument
from app.domain.entities.pipeline import PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent
from app.infrastructure.knowledge.markdown_storage import MarkdownDocument, MarkdownStorage
from app.infrastructure.knowledge.repository import KnowledgeRepository


class StorageAgent(BaseAgent):
    """
    Persist all pipeline results to markdown + metadata DB.

    Updates the source node with extracted data, saves markdown file
    with full frontmatter and body, and creates all edges.
    """

    name = "storage"

    def __init__(self, session: AsyncSession, knowledge_root: str = "knowledge") -> None:
        self.session = session
        self.repository = KnowledgeRepository(session)
        self.storage = MarkdownStorage(knowledge_root)

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        if context.status == "failed":
            logger.warning("storage_skipped_failed_pipeline", extra={"source_id": context.source_id})
            return context

        document = self._build_source_document(context)
        file_path = self.storage.write_document(self._to_markdown(document))
        document.file_path = str(file_path)

        await self.repository.upsert_document(document)
        await self.repository.commit()

        context.status = "completed"
        logger.info("storage_complete", extra={"source_id": context.source_id, "file_path": str(file_path)})
        return context

    def _build_source_document(self, context: PipelineContext) -> KnowledgeDocument:
        now = datetime.now(timezone.utc)
        parse = context.parse_result
        extract = context.extract_result

        title = (parse.title if parse else None) or f"Source from {context.platform}"
        summary = extract.summary if extract else ""
        key_points = extract.key_points if extract else []
        concepts = extract.concepts if extract else []
        entities = extract.entities if extract else []
        topics = extract.topics if extract else []

        # Build enriched metadata (flat, per file-content.md)
        metadata = {
            "url": context.url,
            "platform": context.platform,
            "author": parse.author if parse else None,
            "language": parse.language if parse else "en",
            "source_type": "article",
            "ingested_by": context.user_id,
            "title_extracted": parse.title if parse else None,
            "summary": summary,
            "key_points": key_points,
            "entities": entities,
            "concept_candidates": concepts,
            "content_hash": sha256(context.url.encode()).hexdigest()[:16],
        }

        # Build markdown body
        content = self._build_body(title, summary, key_points, concepts, entities, context)
        tags = list(set(["imported"] + topics))

        # Collect edges from concepts and insights
        edges = []
        if context.concept_result:
            edges.extend(context.concept_result.edges)

        return KnowledgeDocument(
            id=context.source_id,
            type="source",
            title=title,
            content=content,
            slug=context.source_id,
            status="completed",
            confidence=1.0,
            tags=tags,
            metadata=metadata,
            edges=edges,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _build_body(title, summary, key_points, concepts, entities, context):
        lines = [f"# {title}", ""]

        if summary:
            lines.extend(["## Summary", summary, ""])

        if key_points:
            lines.append("## Key Points")
            for point in key_points:
                lines.append(f"- {point}")
            lines.append("")

        if concepts:
            lines.append("## Extracted Concepts")
            for concept in concepts:
                slug = concept.lower().replace(" ", "_")
                lines.append(f"- [[concept_{slug}]]")
            lines.append("")

        if entities:
            lines.append("## Entities")
            for entity in entities:
                lines.append(f"- {entity}")
            lines.append("")

        if context.insight_result and context.insight_result.insights:
            lines.append("## Insights")
            for insight in context.insight_result.insights:
                lines.append(f"- [{insight.impact.upper()}] {insight.text}")
            lines.append("")

        lines.extend(["## Source", f"URL: {context.url}", ""])
        return "\n".join(lines)

    @staticmethod
    def _to_markdown(document: KnowledgeDocument) -> MarkdownDocument:
        return MarkdownDocument(
            id=document.id, type=document.type, title=document.title,
            content=document.content, slug=document.slug, status=document.status,
            confidence=document.confidence, tags=document.tags,
            aliases=document.aliases, metadata=document.metadata,
            created_at=document.created_at, updated_at=document.updated_at,
            file_path=document.file_path,
        )
