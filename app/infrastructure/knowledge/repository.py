"""Repository for the metadata/index layer of the knowledge store."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable

from loguru import logger
from sqlalchemy import cast, delete, func, or_, select, Text as SAText
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument, KnowledgeEdge
from app.infrastructure.knowledge.markdown_storage import MarkdownStorage
from app.infrastructure.database.models import (
    ConceptMetadataRecord,
    EdgeRecord,
    EmbeddingRecord,
    InsightMetadataRecord,
    NodeRecord,
    NodeTagRecord,
    SourceMetadataRecord,
    TagRecord,
)


class KnowledgeRepository:
    """Async repository for metadata DB operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_document(self, document: KnowledgeDocument) -> NodeRecord:
        """Insert or update a metadata node."""
        node = await self.get_node(document.id)
        node_payload = self._build_node_payload(document)

        if node is None:
            node = NodeRecord(**node_payload)
            self.session.add(node)
        else:
            for key, value in node_payload.items():
                setattr(node, key, value)

        await self.session.flush()
        await self._sync_type_specific_metadata(document)
        await self._sync_tags(document.id, document.tags)
        await self._sync_edges(document.id, document.edges)
        logger.info(
            "knowledge_node_upserted",
            extra={"node_id": document.id, "type": document.type},
        )
        return node

    async def get_node(self, node_id: str) -> NodeRecord | None:
        """Get a node by ID."""
        result = await self.session.execute(select(NodeRecord).where(NodeRecord.id == node_id))
        return result.scalar_one_or_none()

    async def get_node_by_file_path(self, file_path: str) -> NodeRecord | None:
        """Get a node by markdown file path."""
        result = await self.session.execute(
            select(NodeRecord).where(NodeRecord.file_path == file_path)
        )
        return result.scalar_one_or_none()

    async def list_nodes(self, node_type: str | None = None, limit: int | None = None) -> list[NodeRecord]:
        """List nodes, optionally filtered by type."""
        statement = select(NodeRecord).order_by(NodeRecord.updated_at.desc())
        if node_type:
            statement = statement.where(NodeRecord.type == node_type)
        if limit is not None:
            statement = statement.limit(limit)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def search_nodes(self, query: str, limit: int = 10) -> list[NodeRecord]:
        """Search nodes by title, type, slug, tags, and metadata."""
        pattern = f"%{query.lower()}%"

        tagged_node_ids = (
            select(NodeTagRecord.node_id)
            .join(TagRecord, TagRecord.id == NodeTagRecord.tag_id)
            .where(func.lower(TagRecord.name).like(pattern))
        )

        statement = (
            select(NodeRecord)
            .where(
                or_(
                    func.lower(NodeRecord.title).like(pattern),
                    func.lower(NodeRecord.slug).like(pattern),
                    func.lower(NodeRecord.type).like(pattern),
                    func.lower(NodeRecord.file_path).like(pattern),
                    func.lower(cast(NodeRecord.metadata_json, SAText)).like(pattern),
                    NodeRecord.id.in_(tagged_node_ids),
                )
            )
            .order_by(NodeRecord.updated_at.desc())
            .limit(limit)
        )

        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_tags_for_node(self, node_id: str) -> list[str]:
        """Return tag names attached to a node."""
        result = await self.session.execute(
            select(TagRecord.name)
            .join(NodeTagRecord, TagRecord.id == NodeTagRecord.tag_id)
            .where(NodeTagRecord.node_id == node_id)
            .order_by(TagRecord.name.asc())
        )
        return list(result.scalars().all())

    async def get_edges_for_node(self, node_id: str) -> list[KnowledgeEdge]:
        """Return all incoming and outgoing edges for a node."""
        result = await self.session.execute(
            select(EdgeRecord)
            .where(or_(EdgeRecord.from_id == node_id, EdgeRecord.to_id == node_id))
            .order_by(EdgeRecord.created_at.desc())
        )
        return [
            KnowledgeEdge(
                from_id=edge.from_id,
                to_id=edge.to_id,
                type=edge.type,
                weight=edge.weight,
            )
            for edge in result.scalars().all()
        ]

    async def delete_node(self, node_id: str) -> bool:
        """Delete a node and associated metadata."""
        node = await self.get_node(node_id)
        if node is None:
            return False

        await self.session.execute(delete(NodeTagRecord).where(NodeTagRecord.node_id == node_id))
        await self.session.execute(delete(EdgeRecord).where(EdgeRecord.from_id == node_id))
        await self.session.execute(delete(EdgeRecord).where(EdgeRecord.to_id == node_id))
        await self.session.execute(delete(EmbeddingRecord).where(EmbeddingRecord.node_id == node_id))
        await self.session.execute(delete(SourceMetadataRecord).where(SourceMetadataRecord.node_id == node_id))
        await self.session.execute(delete(ConceptMetadataRecord).where(ConceptMetadataRecord.node_id == node_id))
        await self.session.execute(delete(InsightMetadataRecord).where(InsightMetadataRecord.node_id == node_id))
        await self.session.delete(node)
        await self.session.flush()
        return True

    async def add_edge(self, edge: KnowledgeEdge) -> EdgeRecord:
        """Add or update a relationship edge."""
        result = await self.session.execute(
            select(EdgeRecord).where(
                (EdgeRecord.from_id == edge.from_id)
                & (EdgeRecord.to_id == edge.to_id)
                & (EdgeRecord.type == edge.type)
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            record = EdgeRecord(
                from_id=edge.from_id,
                to_id=edge.to_id,
                type=edge.type,
                weight=edge.weight,
                created_at=datetime.now(timezone.utc),
            )
            self.session.add(record)
        else:
            record.weight = edge.weight

        await self.session.flush()
        return record

    async def save_embedding(self, node_id: str, chunk_index: int, vector: bytes) -> EmbeddingRecord:
        """Store an embedding chunk."""
        result = await self.session.execute(
            select(EmbeddingRecord).where(
                (EmbeddingRecord.node_id == node_id)
                & (EmbeddingRecord.chunk_index == chunk_index)
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            record = EmbeddingRecord(
                node_id=node_id,
                chunk_index=chunk_index,
                vector=vector,
            )
            self.session.add(record)
        else:
            record.vector = vector

        await self.session.flush()
        return record

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    def _build_node_payload(self, document: KnowledgeDocument) -> dict[str, Any]:
        file_path = document.file_path or str(MarkdownStorage().build_path(document))
        return {
            "id": document.id,
            "type": document.type,
            "title": document.title,
            "slug": document.slug or document.id,
            "status": document.status,
            "confidence": document.confidence,
            "file_path": file_path,
            "hash": self._build_hash(document),
            "metadata_json": document.metadata,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
        }

    def _build_hash(self, document: KnowledgeDocument) -> str:
        from hashlib import sha256
        import yaml

        payload = "\n".join(
            [
                document.id,
                document.type,
                document.title,
                document.slug or "",
                document.status,
                str(document.confidence or ""),
                yaml.safe_dump(document.metadata, sort_keys=True),
                yaml.safe_dump(document.tags, sort_keys=True),
                yaml.safe_dump(document.aliases, sort_keys=True),
                document.content,
            ]
        )
        return sha256(payload.encode("utf-8")).hexdigest()

    async def _sync_tags(self, node_id: str, tags: Iterable[str]) -> None:
        await self.session.execute(delete(NodeTagRecord).where(NodeTagRecord.node_id == node_id))
        for tag_name in tags:
            tag = await self._get_or_create_tag(tag_name)
            self.session.add(NodeTagRecord(node_id=node_id, tag_id=tag.id))
        await self.session.flush()

    async def _get_or_create_tag(self, tag_name: str) -> TagRecord:
        result = await self.session.execute(select(TagRecord).where(TagRecord.name == tag_name))
        tag = result.scalar_one_or_none()
        if tag is None:
            tag = TagRecord(name=tag_name)
            self.session.add(tag)
            await self.session.flush()
        return tag

    async def _sync_edges(self, node_id: str, edges: Iterable[KnowledgeEdge]) -> None:
        await self.session.execute(delete(EdgeRecord).where(EdgeRecord.from_id == node_id))
        for edge in edges:
            await self.add_edge(edge)

    async def _sync_type_specific_metadata(self, document: KnowledgeDocument) -> None:
        if document.type == "source":
            await self._upsert_source_metadata(document)
        elif document.type == "concept":
            await self._upsert_concept_metadata(document)
        elif document.type == "insight":
            await self._upsert_insight_metadata(document)

    async def _upsert_source_metadata(self, document: KnowledgeDocument) -> None:
        if not document.metadata:
            await self.session.execute(delete(SourceMetadataRecord).where(SourceMetadataRecord.node_id == document.id))
            return
        record = await self.session.get(SourceMetadataRecord, document.id)
        payload = {
            "node_id": document.id,
            "url": str(document.metadata.get("url", "")),
            "platform": document.metadata.get("platform"),
            "author": document.metadata.get("author"),
            "language": document.metadata.get("language"),
        }
        if record is None:
            self.session.add(SourceMetadataRecord(**payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)

    async def _upsert_concept_metadata(self, document: KnowledgeDocument) -> None:
        if not document.metadata:
            await self.session.execute(delete(ConceptMetadataRecord).where(ConceptMetadataRecord.node_id == document.id))
            return
        record = await self.session.get(ConceptMetadataRecord, document.id)
        payload = {
            "node_id": document.id,
            "domain": document.metadata.get("domain"),
            "level": document.metadata.get("level"),
        }
        if record is None:
            self.session.add(ConceptMetadataRecord(**payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)

    async def _upsert_insight_metadata(self, document: KnowledgeDocument) -> None:
        if not document.metadata:
            await self.session.execute(delete(InsightMetadataRecord).where(InsightMetadataRecord.node_id == document.id))
            return
        record = await self.session.get(InsightMetadataRecord, document.id)
        payload = {
            "node_id": document.id,
            "impact": document.metadata.get("impact"),
        }
        if record is None:
            self.session.add(InsightMetadataRecord(**payload))
        else:
            for key, value in payload.items():
                setattr(record, key, value)
