"""Concept agent: maps extracted concepts to existing DB concepts or creates new ones."""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument, KnowledgeEdge
from app.domain.entities.pipeline import ConceptResult, PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent
from app.infrastructure.knowledge.repository import KnowledgeRepository


class ConceptAgent(BaseAgent):
    """
    Map extracted concept candidates to existing concepts or create new ones.

    For each concept candidate from the extract agent:
    1. Check if concept already exists in DB (by slug match)
    2. If exists: create edge (source -> concept)
    3. If not: create new concept node + edge

    No LLM involved - pure data logic.
    """

    name = "concept"

    def __init__(self, session: AsyncSession, auto_create: bool = True) -> None:
        """
        Initialize concept agent.

        Args:
            session (AsyncSession): Database session.
            auto_create (bool): Whether to auto-create new concept nodes.
        """
        self.session = session
        self.repository = KnowledgeRepository(session)
        self.auto_create = auto_create

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Map concepts and create edges.

        Args:
            context (PipelineContext): Pipeline context with extract_result.

        Returns:
            PipelineContext: Updated with concept_result.
        """
        if not context.extract_result:
            raise ValueError("No extract result available for concept mapping")

        candidates = context.extract_result.concepts
        created = []
        linked = []
        edges = []

        for concept_name in candidates:
            slug = self._normalize_slug(concept_name)
            concept_id = f"concept_{slug}"

            existing = await self.repository.get_node(concept_id)

            if existing:
                linked.append(concept_id)
                logger.debug(
                    "concept_linked_existing",
                    extra={
                        "concept_id": concept_id,
                        "source_id": context.source_id,
                    },
                )
            elif self.auto_create:
                document = self._create_concept_document(concept_id, concept_name, slug)
                await self.repository.upsert_document(document)
                created.append(concept_id)
                logger.info(
                    "concept_created",
                    extra={
                        "concept_id": concept_id,
                        "name": concept_name,
                    },
                )

            # Create edge: source -> concept
            edge = KnowledgeEdge(
                from_id=context.source_id,
                to_id=concept_id,
                type="references_concept",
                weight=1.0,
            )
            edges.append(edge)
            await self.repository.add_edge(edge)

        context.concept_result = ConceptResult(
            created=created,
            linked=linked,
            edges=edges,
        )

        logger.info(
            "concept_mapping_complete",
            extra={
                "source_id": context.source_id,
                "created_count": len(created),
                "linked_count": len(linked),
            },
        )

        return context

    @staticmethod
    def _normalize_slug(name: str) -> str:
        """
        Normalize concept name to a URL-safe slug.

        Args:
            name (str): Raw concept name.

        Returns:
            str: Normalized slug.
        """
        import re

        slug = name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "_", slug)
        slug = re.sub(r"_+", "_", slug).strip("_")
        return slug or "unknown"

    @staticmethod
    def _create_concept_document(
        concept_id: str, name: str, slug: str
    ) -> KnowledgeDocument:
        """
        Create a new concept knowledge document.

        Args:
            concept_id (str): Concept node ID.
            name (str): Human-readable concept name.
            slug (str): URL slug.

        Returns:
            KnowledgeDocument: New concept document.
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        content = (
            f"# {name}\n\n"
            f"## Definition\n"
            f"(Auto-generated concept - pending enrichment)\n\n"
            f"## Related\n"
            f"(Will be populated as more sources reference this concept)\n"
        )

        return KnowledgeDocument(
            id=concept_id,
            type="concept",
            title=name,
            content=content,
            slug=slug,
            status="draft",
            confidence=0.7,
            tags=[],
            metadata={"domain": "general"},
            created_at=now,
            updated_at=now,
        )
