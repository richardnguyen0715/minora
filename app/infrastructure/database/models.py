"""
Database models for metadata index and link storage following clean architecture principles.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.types import JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class LinkRecord(Base):
    """
    Domain model for stored links received from Telegram messages.

    Follows the design pattern from @docs/database-design.md:
    - Structured and normalized
    - Atomic with specific purpose
    - Includes metadata for traceability
    - AI-friendly schema

    Attributes:
        id (str): Unique identifier in format link_yyyymmdd_xxx
        url (str): The extracted URL
        title (str): Title/description of the link (optional, from message)
        chat_id (str): Telegram chat identifier
        user_id (str): Telegram user identifier
        source_type (str): Type of source (message_text, caption, etc.)
        message_id (int): Telegram message ID for reference
        status (str): Processing status (new, processed, archived)
        created_at (datetime): When the link was received
        processed_at (datetime): When the link was processed (optional)
    """

    __tablename__ = "links"

    id = Column(String(64), primary_key=True, default=lambda: f"link_{uuid4().hex[:12]}")
    url = Column(String(2048), nullable=False, unique=True, index=True)
    title = Column(Text, nullable=True)
    chat_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    source_type = Column(String(32), nullable=False, default="message_text")
    message_id = Column(Integer, nullable=True)
    status = Column(String(32), nullable=False, default="new")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("url", "chat_id", name="uq_link_per_chat"),
    )

    def to_dict(self) -> dict:
        """
        Convert record to dictionary for serialization.

        Returns:
            dict: Record attributes as dictionary.
        """
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "source_type": self.source_type,
            "message_id": self.message_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat()
            if self.processed_at
            else None,
        }


class NodeRecord(Base):
    """Graph/index node stored in the metadata DB."""

    __tablename__ = "nodes"

    id = Column(String(64), primary_key=True)
    type = Column(String(32), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="draft", index=True)
    confidence = Column(Float, nullable=True)
    file_path = Column(String(512), nullable=False, unique=True, index=True)
    hash = Column(String(64), nullable=False, index=True)
    metadata_json = Column("metadata", JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("type", "slug", name="uq_node_type_slug"),
    )


class EdgeRecord(Base):
    """Relationship edge between two knowledge nodes."""

    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    from_id = Column(String(64), nullable=False, index=True)
    to_id = Column(String(64), nullable=False, index=True)
    type = Column(String(64), nullable=False, index=True)
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        UniqueConstraint("from_id", "to_id", "type", name="uq_edge_triplet"),
    )


class TagRecord(Base):
    """Tag dictionary."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), nullable=False, unique=True, index=True)


class NodeTagRecord(Base):
    """Many-to-many mapping between nodes and tags."""

    __tablename__ = "node_tags"

    node_id = Column(String(64), primary_key=True)
    tag_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class EmbeddingRecord(Base):
    """Embedding chunks for AI retrieval."""

    __tablename__ = "embeddings"

    node_id = Column(String(64), primary_key=True)
    chunk_index = Column(Integer, primary_key=True)
    vector = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)


class SourceMetadataRecord(Base):
    """Source-specific metadata."""

    __tablename__ = "sources"

    node_id = Column(String(64), primary_key=True)
    url = Column(String(2048), nullable=False, index=True)
    platform = Column(String(64), nullable=True, index=True)
    author = Column(String(255), nullable=True)
    language = Column(String(32), nullable=True, index=True)


class ConceptMetadataRecord(Base):
    """Concept-specific metadata."""

    __tablename__ = "concepts"

    node_id = Column(String(64), primary_key=True)
    domain = Column(String(120), nullable=True, index=True)
    level = Column(String(64), nullable=True, index=True)


class InsightMetadataRecord(Base):
    """Insight-specific metadata."""

    __tablename__ = "insights"

    node_id = Column(String(64), primary_key=True)
    impact = Column(String(64), nullable=True, index=True)
