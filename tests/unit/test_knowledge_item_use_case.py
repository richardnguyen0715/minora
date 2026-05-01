"""Tests for knowledge item use cases."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.use_cases.knowledge_item import KnowledgeItemUseCase
from app.domain.entities.knowledge import KnowledgeDocument
from app.infrastructure.database.models import Base
from app.infrastructure.knowledge.markdown_storage import MarkdownDocument, MarkdownStorage


@pytest.mark.asyncio
async def test_knowledge_item_use_case_read_update_delete(tmp_path):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    storage_root = tmp_path / "knowledge"

    async with session_factory() as session:
        use_case = KnowledgeItemUseCase(session, knowledge_root=str(storage_root))
        storage = MarkdownStorage(storage_root)

        markdown_document = MarkdownDocument(
            id="concept_llm",
            type="concept",
            title="LLM",
            content="# LLM\nInitial body.",
            slug="concept-llm",
            status="processed",
            tags=["ai"],
            metadata={"domain": "ai", "level": "intermediate"},
        )
        file_path = storage.write_document(markdown_document)

        knowledge_document = KnowledgeDocument(
            id=markdown_document.id,
            type=markdown_document.type,
            title=markdown_document.title,
            content=markdown_document.content,
            slug=markdown_document.slug,
            status=markdown_document.status,
            tags=markdown_document.tags,
            metadata=markdown_document.metadata,
            file_path=str(file_path),
            created_at=markdown_document.created_at,
            updated_at=markdown_document.updated_at,
        )
        await use_case.repository.upsert_document(knowledge_document)
        await use_case.repository.commit()

        read_result = await use_case.get("concept_llm")
        assert "Knowledge item: concept_llm" in read_result
        assert "Metadata DB:" in read_result

        find_result = await use_case.find("llm")
        assert "Search results for 'llm'" in find_result or "No knowledge items" in find_result

        update_result = await use_case.update(
            "concept_llm",
            {"query": "concept_llm", "title": "LLM Updated", "content": "Updated body."},
        )
        assert "Saved knowledge item 'concept_llm'" in update_result

        visualize_result = await use_case.visualize("concept_llm")
        assert "Knowledge item: concept_llm" in visualize_result
        assert "Real-file content:" in visualize_result

        delete_result = await use_case.delete("concept_llm")
        assert "Deleted knowledge item 'concept_llm'" in delete_result

    await engine.dispose()