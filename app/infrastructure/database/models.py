"""
Database models for link storage following clean architecture principles.
"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
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
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
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
