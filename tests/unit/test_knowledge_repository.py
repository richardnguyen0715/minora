"""Tests for the metadata/index repository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.knowledge import KnowledgeDocument, KnowledgeEdge
from app.infrastructure.database.models import (
    Base,
    ConceptMetadataRecord,
    EdgeRecord,
    NodeRecord,
    NodeTagRecord,
    TagRecord,
)
from app.infrastructure.knowledge.repository import KnowledgeRepository


@pytest.mark.asyncio
async def test_knowledge_repository_upsert_document():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_factory() as session:
        repository = KnowledgeRepository(session)
        document = KnowledgeDocument(
            id="concept_llm",
            type="concept",
            title="LLM",
            content="# LLM\nLarge language model.",
            slug="concept-llm",
            status="processed",
            confidence=0.92,
            tags=["ai", "llm"],
            aliases=["large-language-model"],
            metadata={"domain": "ai", "level": "intermediate"},
            edges=[KnowledgeEdge(from_id="concept_llm", to_id="concept_rag", type="related_to")],
        )

        node = await repository.upsert_document(document)
        await repository.commit()

        assert node.id == "concept_llm"
        assert node.file_path.endswith("concept-llm.md")

        node_result = await session.get(NodeRecord, "concept_llm")
        assert node_result is not None
        assert node_result.type == "concept"
        assert node_result.metadata_json["domain"] == "ai"

        tag_result = await session.execute(TagRecord.__table__.select())
        assert len(tag_result.fetchall()) == 2

        node_tag_result = await session.execute(NodeTagRecord.__table__.select())
        assert len(node_tag_result.fetchall()) == 2

        edge_result = await session.execute(EdgeRecord.__table__.select())
        edges = edge_result.fetchall()
        assert len(edges) == 1
        assert edges[0].type == "related_to"

        concept_result = await session.get(ConceptMetadataRecord, "concept_llm")
        assert concept_result is not None
        assert concept_result.domain == "ai"

    await engine.dispose()
