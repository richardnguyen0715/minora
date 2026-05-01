"""Markdown file storage for the real-file knowledge layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
import re

import yaml


@dataclass
class MarkdownDocument:
    """Canonical markdown document with frontmatter and body."""

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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    file_path: str | None = None

    def to_frontmatter(self) -> dict[str, Any]:
        """Serialize document metadata to frontmatter."""
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


class MarkdownStorage:
    """Persist and load markdown documents from a deterministic folder layout."""

    def __init__(self, root_dir: str | Path = "knowledge") -> None:
        self.root_dir = Path(root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or "item"

    @staticmethod
    def _compute_hash(document: MarkdownDocument) -> str:
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

    def build_path(self, document: MarkdownDocument) -> Path:
        """Build the on-disk path for a document based on its type."""
        slug = self._slugify(document.slug or document.title or document.id)
        created_at = document.created_at

        if document.type == "source":
            return self.root_dir / "sources" / created_at.strftime("%Y") / created_at.strftime("%m") / f"{slug}.md"
        if document.type == "concept":
            domain = self._slugify(str(document.metadata.get("domain", "general")))
            return self.root_dir / "concepts" / domain / f"{slug}.md"
        if document.type == "insight":
            return self.root_dir / "insights" / created_at.strftime("%Y") / created_at.strftime("%m") / f"{slug}.md"
        if document.type == "summary":
            return self.root_dir / "summaries" / f"{slug}.md"
        if document.type == "entity":
            category = self._slugify(str(document.metadata.get("category", "general")))
            return self.root_dir / "entities" / category / f"{slug}.md"
        if document.type == "task":
            return self.root_dir / "tasks" / f"{slug}.md"

        return self.root_dir / document.type / f"{slug}.md"

    def write_document(self, document: MarkdownDocument) -> Path:
        """Create or replace a markdown document on disk."""
        target_path = Path(document.file_path) if document.file_path else self.build_path(document)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        document.file_path = str(target_path)
        document.updated_at = datetime.now(timezone.utc)
        document_hash = self._compute_hash(document)

        frontmatter = document.to_frontmatter()
        frontmatter["hash"] = document_hash

        content = ["---", yaml.safe_dump(frontmatter, sort_keys=False).strip(), "---", "", document.content.strip(), ""]
        target_path.write_text("\n".join(content), encoding="utf-8")
        return target_path

    def replace_document(self, document: MarkdownDocument) -> Path:
        """Alias for write_document to make intent explicit."""
        return self.write_document(document)

    def read_document(self, file_path: str | Path) -> MarkdownDocument | None:
        """Load a document from disk."""
        path = Path(file_path)
        if not path.exists():
            return None

        raw = path.read_text(encoding="utf-8")
        frontmatter, content = self._split_frontmatter(raw)
        if frontmatter is None:
            return None

        data = yaml.safe_load(frontmatter) or {}
        return MarkdownDocument(
            id=str(data.get("id", path.stem)),
            type=str(data.get("type", path.parent.name)),
            title=str(data.get("title", path.stem)),
            content=content.strip(),
            slug=data.get("slug"),
            status=str(data.get("status", "draft")),
            confidence=data.get("confidence"),
            tags=list(data.get("tags", []) or []),
            aliases=list(data.get("aliases", []) or []),
            metadata=dict(data.get("metadata", {}) or {}),
            file_path=str(path),
            created_at=self._parse_datetime(data.get("created_at")),
            updated_at=self._parse_datetime(data.get("updated_at")),
        )

    def delete_document(self, file_path: str | Path) -> bool:
        """Delete a markdown document if it exists."""
        path = Path(file_path)
        if not path.exists():
            return False
        path.unlink()
        return True

    def move_document(self, source_path: str | Path, target_path: str | Path) -> Path:
        """Move a markdown document to a new location."""
        source = Path(source_path)
        target = Path(target_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        source.replace(target)
        return target

    @staticmethod
    def _split_frontmatter(raw: str) -> tuple[str | None, str]:
        if not raw.startswith("---\n"):
            return None, raw

        parts = raw.split("\n---\n", 1)
        if len(parts) != 2:
            return None, raw

        frontmatter = parts[0].removeprefix("---\n")
        content = parts[1]
        return frontmatter, content

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(str(value))
