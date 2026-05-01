"""
Repository pattern implementation for link data access.
"""
from datetime import datetime
from typing import Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import LinkRecord


class LinkRepository:
    """
    Data access layer for link records.

    Implements repository pattern to abstract database operations.
    Supports async/await for scalability.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize repository with database session.

        Args:
            session (AsyncSession): Async database session.
        """
        self.session = session

    async def save_link(
        self,
        url: str,
        chat_id: str,
        user_id: str,
        title: Optional[str] = None,
        source_type: str = "message_text",
        message_id: Optional[int] = None,
    ) -> LinkRecord:
        """
        Save a new link to the database.

        Args:
            url (str): The URL to save.
            chat_id (str): Telegram chat ID.
            user_id (str): Telegram user ID.
            title (Optional[str]): Optional title/description.
            source_type (str): Type of source.
            message_id (Optional[int]): Telegram message ID.

        Returns:
            LinkRecord: The created link record.

        Raises:
            Exception: If save operation fails.
        """
        try:
            link = LinkRecord(
                url=url,
                chat_id=chat_id,
                user_id=user_id,
                title=title,
                source_type=source_type,
                message_id=message_id,
                status="new",
            )
            self.session.add(link)
            await self.session.flush()

            logger.info(
                "Link saved to database",
                extra={
                    "link_id": link.id,
                    "url": url,
                    "chat_id": chat_id,
                },
            )
            return link

        except Exception as e:
            logger.error(
                "Failed to save link",
                extra={
                    "url": url,
                    "chat_id": chat_id,
                    "error": str(e),
                },
            )
            raise

    async def get_link_by_url(self, url: str, chat_id: str) -> Optional[LinkRecord]:
        """
        Retrieve a link by URL and chat ID.

        Args:
            url (str): The URL to search for.
            chat_id (str): The chat ID.

        Returns:
            Optional[LinkRecord]: The link record or None if not found.
        """
        result = await self.session.execute(
            select(LinkRecord).where(
                (LinkRecord.url == url) & (LinkRecord.chat_id == chat_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_links_by_chat(self, chat_id: str) -> list[LinkRecord]:
        """
        Retrieve all links for a specific chat.

        Args:
            chat_id (str): The chat ID.

        Returns:
            list[LinkRecord]: List of link records for the chat.
        """
        result = await self.session.execute(
            select(LinkRecord)
            .where(LinkRecord.chat_id == chat_id)
            .order_by(LinkRecord.created_at.desc())
        )
        return result.scalars().all()

    async def mark_processed(self, link_id: str) -> LinkRecord:
        """
        Mark a link as processed.

        Args:
            link_id (str): The link ID to mark as processed.

        Returns:
            LinkRecord: The updated link record.
        """
        result = await self.session.execute(
            select(LinkRecord).where(LinkRecord.id == link_id)
        )
        link = result.scalar_one_or_none()

        if link:
            link.status = "processed"
            link.processed_at = datetime.utcnow()
            await self.session.flush()

            logger.debug(
                "Link marked as processed",
                extra={"link_id": link_id},
            )

        return link

    async def commit(self) -> None:
        """Commit current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback current transaction."""
        await self.session.rollback()
