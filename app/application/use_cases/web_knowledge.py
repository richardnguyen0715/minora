"""Use cases for the Web UI knowledge management interface.

Provides structured JSON-friendly responses for all CRUD operations
on the 2-layer knowledge store (metadata DB + markdown files).
"""

from __future__ import annotations

from dataclasses import replace as dataclass_replace
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument, KnowledgeEdge
from app.infrastructure.database.models import (
    ConceptMetadataRecord,
    EdgeRecord,
    InsightMetadataRecord,
    LinkRecord,
    NodeRecord,
    NodeTagRecord,
    SourceMetadataRecord,
    TagRecord,
)
from app.infrastructure.knowledge.markdown_storage import (
    MarkdownDocument,
    MarkdownStorage,
)
from app.infrastructure.knowledge.repository import KnowledgeRepository


class WebKnowledgeUseCase:
    """Coordinates 2-layer knowledge operations with structured dict responses."""

    def __init__(
        self, session: AsyncSession, knowledge_root: str = "knowledge"
    ) -> None:
        """
        Initialize use case with database session and storage root.

        Args:
            session (AsyncSession): Async database session.
            knowledge_root (str): Root directory for markdown storage.
        """
        self.session = session
        self.repository = KnowledgeRepository(session)
        self.storage = MarkdownStorage(knowledge_root)

    # ------------------------------------------------------------------ #
    #  Statistics                                                         #
    # ------------------------------------------------------------------ #

    async def get_stats(self) -> dict[str, Any]:
        """
        Aggregate dashboard statistics across all tables.

        Returns:
            dict: Counts per entity type, tag distribution, and recent items.
        """
        node_count = await self._scalar(select(func.count()).select_from(NodeRecord))
        edge_count = await self._scalar(select(func.count()).select_from(EdgeRecord))
        tag_count = await self._scalar(select(func.count()).select_from(TagRecord))
        link_count = await self._scalar(select(func.count()).select_from(LinkRecord))

        type_distribution = await self._type_distribution()
        status_distribution = await self._status_distribution()
        recent_nodes = await self._recent_nodes(limit=5)

        return {
            "node_count": node_count,
            "edge_count": edge_count,
            "tag_count": tag_count,
            "link_count": link_count,
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "recent_nodes": recent_nodes,
        }

    # ------------------------------------------------------------------ #
    #  Nodes                                                              #
    # ------------------------------------------------------------------ #

    async def list_nodes(
        self,
        node_type: str | None = None,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """
        List nodes with filtering, search, sorting, and pagination.

        Args:
            node_type (str | None): Filter by node type.
            status (str | None): Filter by status.
            search (str | None): Full-text search query.
            sort_by (str): Column to sort by.
            sort_order (str): 'asc' or 'desc'.
            page (int): Page number (1-indexed).
            per_page (int): Items per page.

        Returns:
            dict: Paginated list of node summaries.
        """
        if search:
            nodes = await self.repository.search_nodes(search, limit=per_page * page)
            if node_type:
                nodes = [n for n in nodes if n.type == node_type]
            if status:
                nodes = [n for n in nodes if n.status == status]
            total = len(nodes)
            offset = (page - 1) * per_page
            nodes = nodes[offset : offset + per_page]
        else:
            statement = select(NodeRecord)
            if node_type:
                statement = statement.where(NodeRecord.type == node_type)
            if status:
                statement = statement.where(NodeRecord.status == status)

            sort_column = self._resolve_sort_column(sort_by)
            if sort_order == "asc":
                statement = statement.order_by(sort_column.asc())
            else:
                statement = statement.order_by(sort_column.desc())

            count_stmt = select(func.count()).select_from(statement.subquery())
            total = await self._scalar(count_stmt)

            statement = statement.offset((page - 1) * per_page).limit(per_page)
            result = await self.session.execute(statement)
            nodes = list(result.scalars().all())

        items = []
        for node in nodes:
            tags = await self.repository.get_tags_for_node(node.id)
            items.append(self._node_to_summary(node, tags))

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    async def get_node(self, node_id: str) -> dict[str, Any] | None:
        """
        Get full node detail including tags, edges, type-specific metadata, and markdown content.

        Args:
            node_id (str): Node identifier.

        Returns:
            dict | None: Full node data or None if not found.
        """
        node = await self.repository.get_node(node_id)
        if node is None:
            return None

        tags = await self.repository.get_tags_for_node(node_id)
        edges = await self.repository.get_edges_for_node(node_id)
        type_metadata = await self._get_type_metadata(node_id, node.type)
        document = self._read_document(node)

        return {
            "id": node.id,
            "type": node.type,
            "title": node.title,
            "slug": node.slug,
            "status": node.status,
            "confidence": node.confidence,
            "file_path": node.file_path,
            "hash": node.hash,
            "metadata": dict(node.metadata_json or {}),
            "tags": tags,
            "edges": [
                {
                    "from_id": edge.from_id,
                    "to_id": edge.to_id,
                    "type": edge.type,
                    "weight": edge.weight,
                }
                for edge in edges
            ],
            "type_metadata": type_metadata,
            "content": document.content if document else "",
            "aliases": document.aliases if document else [],
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }

    async def create_node(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new knowledge node (both DB and markdown file).

        Args:
            payload (dict): Node data including id, type, title, content, tags, etc.

        Returns:
            dict: Created node summary.
        """
        now = datetime.now(timezone.utc)
        document = MarkdownDocument(
            id=payload["id"],
            type=payload["type"],
            title=payload["title"],
            content=payload.get("content", ""),
            slug=payload.get("slug"),
            status=payload.get("status", "draft"),
            confidence=self._parse_float(payload.get("confidence")),
            tags=self._ensure_list(payload.get("tags", [])),
            aliases=self._ensure_list(payload.get("aliases", [])),
            metadata=payload.get("metadata", {}),
            created_at=now,
            updated_at=now,
        )

        file_path = self.storage.write_document(document)
        document.file_path = str(file_path)

        knowledge_doc = self._to_knowledge_document(document)
        await self.repository.upsert_document(knowledge_doc)
        await self.repository.commit()

        logger.info(
            "web_node_created",
            extra={"node_id": document.id, "type": document.type},
        )
        return {"id": document.id, "file_path": str(file_path)}

    async def update_node(
        self, node_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Update an existing node's fields.

        Args:
            node_id (str): Node to update.
            updates (dict): Fields to update.

        Returns:
            dict | None: Updated node summary or None if not found.
        """
        node = await self.repository.get_node(node_id)
        if node is None:
            return None

        current = self._read_document(node)
        updated = self._apply_updates(current, updates)
        file_path = self.storage.write_document(updated)
        updated.file_path = str(file_path)

        knowledge_doc = self._to_knowledge_document(updated)
        await self.repository.upsert_document(knowledge_doc)
        await self.repository.commit()

        logger.info("web_node_updated", extra={"node_id": node_id})
        return await self.get_node(node_id)

    async def delete_node(self, node_id: str) -> bool:
        """
        Delete a node from both DB and filesystem.

        Args:
            node_id (str): Node to delete.

        Returns:
            bool: True if deleted, False if not found.
        """
        node = await self.repository.get_node(node_id)
        if node is None:
            return False

        self.storage.delete_document(node.file_path)
        await self.repository.delete_node(node_id)
        await self.repository.commit()

        logger.info("web_node_deleted", extra={"node_id": node_id})
        return True

    async def replace_content(
        self, node_id: str, content: str
    ) -> dict[str, Any] | None:
        """
        Replace only the markdown content of a node.

        Args:
            node_id (str): Node to update.
            content (str): New markdown content.

        Returns:
            dict | None: Updated node or None if not found.
        """
        return await self.update_node(node_id, {"content": content})

    # ------------------------------------------------------------------ #
    #  Edges                                                              #
    # ------------------------------------------------------------------ #

    async def list_edges(
        self, node_id: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List edges, optionally filtered by a node.

        Args:
            node_id (str | None): Filter edges involving this node.

        Returns:
            list[dict]: Edge records.
        """
        if node_id:
            edges = await self.repository.get_edges_for_node(node_id)
            return [
                {
                    "from_id": edge.from_id,
                    "to_id": edge.to_id,
                    "type": edge.type,
                    "weight": edge.weight,
                }
                for edge in edges
            ]

        result = await self.session.execute(
            select(EdgeRecord).order_by(EdgeRecord.created_at.desc())
        )
        records = result.scalars().all()
        return [
            {
                "id": record.id,
                "from_id": record.from_id,
                "to_id": record.to_id,
                "type": record.type,
                "weight": record.weight,
                "created_at": record.created_at.isoformat()
                if record.created_at
                else None,
            }
            for record in records
        ]

    async def create_edge(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Create a new relationship edge.

        Args:
            payload (dict): Edge data with from_id, to_id, type, weight.

        Returns:
            dict: Created edge data.
        """
        edge = KnowledgeEdge(
            from_id=payload["from_id"],
            to_id=payload["to_id"],
            type=payload.get("type", "references"),
            weight=float(payload.get("weight", 1.0)),
        )
        record = await self.repository.add_edge(edge)
        await self.repository.commit()

        logger.info(
            "web_edge_created",
            extra={"from_id": edge.from_id, "to_id": edge.to_id},
        )
        return {
            "id": record.id,
            "from_id": record.from_id,
            "to_id": record.to_id,
            "type": record.type,
            "weight": record.weight,
        }

    async def delete_edge(self, edge_id: int) -> bool:
        """
        Delete an edge by ID.

        Args:
            edge_id (int): Edge to delete.

        Returns:
            bool: True if deleted.
        """
        result = await self.session.execute(
            select(EdgeRecord).where(EdgeRecord.id == edge_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return False

        await self.session.delete(record)
        await self.session.commit()
        return True

    # ------------------------------------------------------------------ #
    #  Tags                                                               #
    # ------------------------------------------------------------------ #

    async def list_tags(self) -> list[dict[str, Any]]:
        """
        List all tags with usage counts.

        Returns:
            list[dict]: Tags with name and count.
        """
        statement = (
            select(TagRecord.id, TagRecord.name, func.count(NodeTagRecord.node_id).label("count"))
            .outerjoin(NodeTagRecord, TagRecord.id == NodeTagRecord.tag_id)
            .group_by(TagRecord.id, TagRecord.name)
            .order_by(func.count(NodeTagRecord.node_id).desc())
        )
        result = await self.session.execute(statement)
        return [
            {"id": row.id, "name": row.name, "count": row.count}
            for row in result.all()
        ]

    # ------------------------------------------------------------------ #
    #  Links                                                              #
    # ------------------------------------------------------------------ #

    async def list_links(
        self,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        """
        List links with filtering, search, sorting, and pagination.

        Args:
            status (str | None): Filter by status.
            search (str | None): Search URL or title.
            sort_by (str): Column to sort by.
            sort_order (str): 'asc' or 'desc'.
            page (int): Page number.
            per_page (int): Items per page.

        Returns:
            dict: Paginated link list.
        """
        statement = select(LinkRecord)

        if status:
            statement = statement.where(LinkRecord.status == status)
        if search:
            pattern = f"%{search.lower()}%"
            statement = statement.where(
                func.lower(LinkRecord.url).like(pattern)
                | func.lower(LinkRecord.title).like(pattern)
            )

        sort_col = getattr(LinkRecord, sort_by, LinkRecord.created_at)
        if sort_order == "asc":
            statement = statement.order_by(sort_col.asc())
        else:
            statement = statement.order_by(sort_col.desc())

        count_stmt = select(func.count()).select_from(statement.subquery())
        total = await self._scalar(count_stmt)

        statement = statement.offset((page - 1) * per_page).limit(per_page)
        result = await self.session.execute(statement)
        links = result.scalars().all()

        return {
            "items": [link.to_dict() for link in links],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }

    async def get_link(self, link_id: str) -> dict[str, Any] | None:
        """
        Get a single link by ID.

        Args:
            link_id (str): Link identifier.

        Returns:
            dict | None: Link data or None.
        """
        result = await self.session.execute(
            select(LinkRecord).where(LinkRecord.id == link_id)
        )
        link = result.scalar_one_or_none()
        return link.to_dict() if link else None

    async def update_link(
        self, link_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Update a link's fields.

        Args:
            link_id (str): Link to update.
            updates (dict): Fields to update.

        Returns:
            dict | None: Updated link or None if not found.
        """
        result = await self.session.execute(
            select(LinkRecord).where(LinkRecord.id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            return None

        allowed_fields = {"url", "title", "status", "source_type"}
        for field, value in updates.items():
            if field in allowed_fields:
                setattr(link, field, value)

        await self.session.commit()
        return link.to_dict()

    async def delete_link(self, link_id: str) -> bool:
        """
        Delete a link by ID.

        Args:
            link_id (str): Link to delete.

        Returns:
            bool: True if deleted.
        """
        result = await self.session.execute(
            select(LinkRecord).where(LinkRecord.id == link_id)
        )
        link = result.scalar_one_or_none()
        if link is None:
            return False

        await self.session.delete(link)
        await self.session.commit()
        return True

    # ------------------------------------------------------------------ #
    #  Private helpers                                                    #
    # ------------------------------------------------------------------ #

    async def _scalar(self, statement) -> int:
        """Execute a scalar query and return integer result."""
        result = await self.session.execute(statement)
        return result.scalar() or 0

    async def _type_distribution(self) -> dict[str, int]:
        """Count nodes grouped by type."""
        result = await self.session.execute(
            select(NodeRecord.type, func.count())
            .group_by(NodeRecord.type)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _status_distribution(self) -> dict[str, int]:
        """Count nodes grouped by status."""
        result = await self.session.execute(
            select(NodeRecord.status, func.count())
            .group_by(NodeRecord.status)
        )
        return {row[0]: row[1] for row in result.all()}

    async def _recent_nodes(self, limit: int = 5) -> list[dict[str, Any]]:
        """Get most recently updated nodes."""
        result = await self.session.execute(
            select(NodeRecord)
            .order_by(NodeRecord.updated_at.desc())
            .limit(limit)
        )
        nodes = result.scalars().all()
        items = []
        for node in nodes:
            tags = await self.repository.get_tags_for_node(node.id)
            items.append(self._node_to_summary(node, tags))
        return items

    async def _get_type_metadata(
        self, node_id: str, node_type: str
    ) -> dict[str, Any]:
        """Fetch type-specific metadata for a node."""
        if node_type == "source":
            record = await self.session.get(SourceMetadataRecord, node_id)
            if record:
                return {
                    "url": record.url,
                    "platform": record.platform,
                    "author": record.author,
                    "language": record.language,
                }
        elif node_type == "concept":
            record = await self.session.get(ConceptMetadataRecord, node_id)
            if record:
                return {"domain": record.domain, "level": record.level}
        elif node_type == "insight":
            record = await self.session.get(InsightMetadataRecord, node_id)
            if record:
                return {"impact": record.impact}
        return {}

    def _node_to_summary(
        self, node: NodeRecord, tags: list[str]
    ) -> dict[str, Any]:
        """Convert a NodeRecord to a summary dict."""
        return {
            "id": node.id,
            "type": node.type,
            "title": node.title,
            "slug": node.slug,
            "status": node.status,
            "confidence": node.confidence,
            "file_path": node.file_path,
            "tags": tags,
            "created_at": node.created_at.isoformat() if node.created_at else None,
            "updated_at": node.updated_at.isoformat() if node.updated_at else None,
        }

    def _read_document(self, node: NodeRecord) -> MarkdownDocument:
        """Read the markdown file for a node, falling back to a stub."""
        loaded = self.storage.read_document(node.file_path)
        if loaded is not None:
            return loaded

        return MarkdownDocument(
            id=node.id,
            type=node.type,
            title=node.title,
            content=f"# {node.title}\n\n(No markdown file found)",
            slug=node.slug,
            status=node.status,
            confidence=node.confidence,
            tags=[],
            aliases=[],
            metadata=dict(node.metadata_json or {}),
            file_path=node.file_path,
            created_at=node.created_at,
            updated_at=node.updated_at,
        )

    def _apply_updates(
        self, document: MarkdownDocument, updates: dict[str, Any]
    ) -> MarkdownDocument:
        """Apply a dict of updates to a MarkdownDocument."""
        metadata = dict(document.metadata)
        direct_fields = {
            "title", "content", "status", "slug", "confidence", "tags", "aliases",
        }

        for key, value in updates.items():
            if key not in direct_fields:
                metadata[key] = value

        confidence = updates.get("confidence", document.confidence)
        if isinstance(confidence, str) and confidence:
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = document.confidence

        return MarkdownDocument(
            id=document.id,
            type=document.type,
            title=updates.get("title", document.title),
            content=updates.get("content", document.content),
            slug=updates.get("slug", document.slug),
            status=updates.get("status", document.status),
            confidence=confidence,
            tags=self._ensure_list(updates.get("tags", document.tags)),
            aliases=self._ensure_list(updates.get("aliases", document.aliases)),
            metadata=metadata,
            created_at=document.created_at,
            updated_at=datetime.now(timezone.utc),
            file_path=document.file_path,
        )

    def _to_knowledge_document(
        self, document: MarkdownDocument
    ) -> KnowledgeDocument:
        """Convert MarkdownDocument to KnowledgeDocument for repository."""
        return KnowledgeDocument(
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
            file_path=document.file_path,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _resolve_sort_column(self, sort_by: str):
        """Map sort field name to SQLAlchemy column."""
        column_map = {
            "title": NodeRecord.title,
            "type": NodeRecord.type,
            "status": NodeRecord.status,
            "created_at": NodeRecord.created_at,
            "updated_at": NodeRecord.updated_at,
            "confidence": NodeRecord.confidence,
        }
        return column_map.get(sort_by, NodeRecord.updated_at)

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        """Normalize a value to a list of strings."""
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value).strip()]

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        """Safely parse a value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
