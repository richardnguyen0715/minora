"""Knowledge domain entities for the 2-layer storage model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class KnowledgeEdge:
    """Graph edge between two knowledge nodes."""

    from_id: str
    to_id: str
    type: str = "references"
    weight: float = 1.0


@dataclass
class KnowledgeDocument:
    """
    Canonical knowledge document.

    This is the object that flows through the LLM -> markdown -> metadata pipeline.
    """

    id: str
    type: str
    title: str
    content: str
    slug: str | None = None
    status: str = "draft"
    confidence: float | None = None
    tags: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    edges: list[KnowledgeEdge] = field(default_factory=list)
    file_path: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_frontmatter(self) -> dict[str, Any]:
        """Serialize the document into markdown frontmatter."""
        frontmatter = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "slug": self.slug or self.id,
            "status": self.status,
            "tags": self.tags,
            "aliases": self.aliases,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

        if self.confidence is not None:
            frontmatter["confidence"] = self.confidence

        if self.file_path:
            frontmatter["file_path"] = self.file_path

        return frontmatter
