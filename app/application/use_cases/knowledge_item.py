"""Use cases for reading, updating, deleting, searching and visualizing knowledge items."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument
from app.infrastructure.database.models import NodeRecord
from app.infrastructure.knowledge.markdown_storage import MarkdownDocument, MarkdownStorage
from app.infrastructure.knowledge.repository import KnowledgeRepository


class KnowledgeItemUseCase:
    """Coordinates the 2-layer knowledge storage workflow."""

    def __init__(self, session: AsyncSession, knowledge_root: str = "knowledge") -> None:
        self.repository = KnowledgeRepository(session)
        self.storage = MarkdownStorage(knowledge_root)

    async def get(self, node_id: str) -> str:
        node = await self.repository.get_node(node_id)
        if node is None:
            return f"[ERROR] Knowledge item '{node_id}' not found"

        document = self._read_document(node)
        tags = await self.repository.get_tags_for_node(node_id)
        edges = await self.repository.get_edges_for_node(node_id)
        return self._format_detail_view(node, document, tags, edges)

    async def update(self, node_id: str, updates: dict[str, Any]) -> str:
        node = await self.repository.get_node(node_id)
        if node is None:
            return f"[ERROR] Knowledge item '{node_id}' not found"

        current = self._read_document(node)
        updated_document = self._apply_updates(current, updates)
        await self._persist_document(updated_document)
        return self._format_update_result(updated_document)

    async def delete(self, node_id: str) -> str:
        node = await self.repository.get_node(node_id)
        if node is None:
            return f"[ERROR] Knowledge item '{node_id}' not found"

        file_deleted = self.storage.delete_document(node.file_path)
        db_deleted = await self.repository.delete_node(node_id)
        await self.repository.commit()

        if db_deleted:
            return (
                f"[OK] Deleted knowledge item '{node_id}'\n"
                f"File deleted: {file_deleted}\n"
                f"Metadata removed: {db_deleted}"
            )

        return f"[ERROR] Failed to delete knowledge item '{node_id}'"

    async def find(self, query: str, limit: int = 10) -> str:
        nodes = await self.repository.search_nodes(query, limit=limit)
        if not nodes:
            return f"[WARN] No knowledge items found for '{query}'"

        lines = [f"[OK] Search results for '{query}' ({len(nodes)} items)"]
        for node in nodes:
            tags = await self.repository.get_tags_for_node(node.id)
            lines.append(
                f"- {node.id} | {node.type} | {node.title} | tags={', '.join(tags) if tags else '-'}"
            )
            lines.append(f"  file: {node.file_path}")
        return "\n".join(lines)

    async def visualize(self, node_id: str | None = None, limit: int = 10) -> str:
        if node_id:
            node = await self.repository.get_node(node_id)
            if node is None:
                return f"[ERROR] Knowledge item '{node_id}' not found"
            document = self._read_document(node)
            tags = await self.repository.get_tags_for_node(node_id)
            edges = await self.repository.get_edges_for_node(node_id)
            return self._format_detail_view(node, document, tags, edges)

        nodes = await self.repository.list_nodes(limit=limit)
        documents = [self._read_document(node) for node in nodes]
        return self._format_visualization(nodes, documents)

    async def replace(self, node_id: str, content: str) -> str:
        node = await self.repository.get_node(node_id)
        if node is None:
            return f"[ERROR] Knowledge item '{node_id}' not found"

        current = self._read_document(node)
        updated = replace(current, content=content)
        await self._persist_document(updated)
        return self._format_update_result(updated)

    def _read_document(self, node: NodeRecord) -> MarkdownDocument:
        loaded = self.storage.read_document(node.file_path)
        if loaded is not None:
            return loaded

        return MarkdownDocument(
            id=node.id,
            type=node.type,
            title=node.title,
            content=self._fallback_content(node),
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

    def _fallback_content(self, node: NodeRecord) -> str:
        metadata = json.dumps(node.metadata_json or {}, indent=2, ensure_ascii=False)
        return (
            f"# {node.title}\n\n"
            f"Metadata is stored in the database and rendered file:\n\n"
            f"```json\n{metadata}\n```\n"
        )

    def _apply_updates(self, document: MarkdownDocument, updates: dict[str, Any]) -> MarkdownDocument:
        raw_updates = dict(updates)
        raw_updates.pop("query", None)

        metadata = dict(document.metadata)
        for key in list(raw_updates.keys()):
            if key in {"title", "content", "status", "slug", "confidence", "tags", "aliases"}:
                continue
            metadata[key] = raw_updates.pop(key)

        tags = self._parse_list_value(raw_updates.pop("tags", document.tags))
        aliases = self._parse_list_value(raw_updates.pop("aliases", document.aliases))
        confidence = raw_updates.pop("confidence", document.confidence)
        if isinstance(confidence, str) and confidence:
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = document.confidence

        title = raw_updates.pop("title", document.title)
        content = raw_updates.pop("content", document.content)
        status = raw_updates.pop("status", document.status)
        slug = raw_updates.pop("slug", document.slug)

        return MarkdownDocument(
            id=document.id,
            type=document.type,
            title=title,
            content=content,
            slug=slug,
            status=status,
            confidence=confidence,
            tags=tags,
            aliases=aliases,
            metadata=metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            file_path=document.file_path,
        )

    async def _persist_document(self, document: MarkdownDocument) -> None:
        file_path = self.storage.write_document(document)
        document.file_path = str(file_path)
        knowledge_document = KnowledgeDocument(
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
        await self.repository.upsert_document(knowledge_document)
        await self.repository.commit()

    def _format_update_result(self, document: MarkdownDocument) -> str:
        return (
            f"[OK] Saved knowledge item '{document.id}'\n"
            f"Type: {document.type}\n"
            f"Title: {document.title}\n"
            f"File: {document.file_path}"
        )

    def _format_detail_view(
        self,
        node: NodeRecord,
        document: MarkdownDocument,
        tags: list[str],
        edges: list[Any],
    ) -> str:
        lines = [
            f"[OK] Knowledge item: {node.id}",
            f"Type: {node.type}",
            f"Title: {node.title}",
            f"Status: {node.status}",
            f"Slug: {node.slug}",
            f"File: {node.file_path}",
            f"Hash: {node.hash}",
            f"Tags: {', '.join(tags) if tags else '-'}",
            f"Aliases: {', '.join(document.aliases) if document.aliases else '-'}",
            "",
            "Metadata DB:",
            json.dumps(node.metadata_json or {}, indent=2, ensure_ascii=False),
            "",
            "Real-file content:",
            document.content.strip() or "(empty)",
        ]

        if edges:
            lines.extend(["", "Edges:"])
            for edge in edges:
                lines.append(f"- {edge.from_id} --{edge.type}/{edge.weight}--> {edge.to_id}")

        return "\n".join(lines)

    def _format_visualization(self, nodes: list[NodeRecord], documents: list[MarkdownDocument]) -> str:
        lines = [
            f"[OK] Knowledge database overview ({len(nodes)} items)",
            "",
            "Metadata DB:",
        ]

        for node in nodes:
            lines.extend(
                [
                    f"- {node.id} | {node.type} | {node.title}",
                    f"  status={node.status} confidence={node.confidence} file={node.file_path}",
                    f"  metadata={json.dumps(node.metadata_json or {}, ensure_ascii=False)}",
                ]
            )

        lines.extend(["", "Real files:"])
        for document in documents:
            preview = document.content.strip().splitlines()[:8]
            lines.append(f"- {document.id} -> {document.file_path}")
            lines.extend([f"  {line}" for line in preview])
            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    def _parse_list_value(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return [str(value).strip()]
