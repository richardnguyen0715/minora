"""Use case for saving knowledge documents into the 2-layer storage model."""

from __future__ import annotations

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument
from app.infrastructure.knowledge.markdown_storage import MarkdownStorage
from app.infrastructure.knowledge.repository import KnowledgeRepository


class SaveKnowledgeItemUseCase:
    """Persist a knowledge document to markdown storage and metadata DB."""

    def __init__(self, session: AsyncSession, knowledge_root: str = "knowledge") -> None:
        self.repository = KnowledgeRepository(session)
        self.storage = MarkdownStorage(knowledge_root)

    async def execute(self, document: KnowledgeDocument) -> dict:
        """Write the markdown file first, then persist metadata in a single workflow."""
        logger.info(
            "knowledge_document_save_started",
            extra={"node_id": document.id, "type": document.type},
        )

        try:
            file_path = self.storage.write_document(
                document=self._to_markdown_document(document)
            )
            document.file_path = str(file_path)

            node = await self.repository.upsert_document(document)
            await self.repository.commit()

            logger.info(
                "knowledge_document_saved",
                extra={"node_id": document.id, "file_path": document.file_path},
            )
            return {
                "ok": True,
                "node": self._serialize_node(node),
                "file_path": document.file_path,
            }
        except Exception as exc:
            await self.repository.rollback()
            if document.file_path:
                self.storage.delete_document(document.file_path)
            logger.error(
                "knowledge_document_save_failed",
                extra={"node_id": document.id, "error": str(exc)},
            )
            raise

    async def delete(self, node_id: str) -> dict:
        """Delete a knowledge document from both layers."""
        node = await self.repository.get_node(node_id)
        if node is None:
            return {"ok": False, "reason": "not_found"}

        file_deleted = self.storage.delete_document(node.file_path)
        db_deleted = await self.repository.delete_node(node_id)
        await self.repository.commit()

        return {
            "ok": db_deleted,
            "file_deleted": file_deleted,
            "node_id": node_id,
        }

    async def replace(self, document: KnowledgeDocument) -> dict:
        """Replace an existing document atomically at the workflow level."""
        return await self.execute(document)

    def _to_markdown_document(self, document: KnowledgeDocument):
        from app.infrastructure.knowledge.markdown_storage import MarkdownDocument

        return MarkdownDocument(
            id=document.id,
            type=document.type,
            title=document.title,
            content=document.content,
            slug=document.slug,
            status=document.status,
            confidence=document.confidence,
            tags=document.tags,
            aliases=document.aliases,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            file_path=document.file_path,
        )

    def _serialize_node(self, node) -> dict:
        return {
            "id": node.id,
            "type": node.type,
            "title": node.title,
            "slug": node.slug,
            "status": node.status,
            "confidence": node.confidence,
            "file_path": node.file_path,
            "hash": node.hash,
            "metadata": node.metadata_json,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }
