"""
Use case for saving links from messages.
"""
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.services.link_service import LinkService
from app.infrastructure.database.repository import LinkRepository


class SaveLinkUseCase:
    """
    Use case for extracting and saving links from messages.

    Orchestrates the workflow:
    1. Extract links from message text
    2. Generate response for user
    3. Save links to database
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize use case with database session.

        Args:
            session (AsyncSession): Async database session.
        """
        self.repository = LinkRepository(session)
        self.session = session

    async def execute(
        self,
        chat_id: str,
        user_id: str,
        text: str,
        message_id: int,
    ) -> dict:
        """
        Extract links from message and save to database.

        Args:
            chat_id (str): Telegram chat ID.
            user_id (str): Telegram user ID.
            text (str): Message text.
            message_id (int): Telegram message ID.

        Returns:
            dict: Result with links found and responses to send.
        """
        logger.info(
            "Extracting links from message",
            extra={
                "chat_id": chat_id,
                "user_id": user_id,
                "message_id": message_id,
            },
        )

        # Extract links from text
        links = LinkService.extract_links(text)

        result = {
            "links_found": len(links),
            "links": [],
            "responses": [],
        }

        if not links:
            logger.debug(
                "No links found in message",
                extra={"chat_id": chat_id},
            )
            return result

        # Save each link and generate response
        for url in links:
            try:
                # Check if link already exists
                existing = await self.repository.get_link_by_url(url, chat_id)

                if existing:
                    logger.info(
                        "Link already exists",
                        extra={
                            "url": url,
                            "chat_id": chat_id,
                            "link_id": existing.id,
                        },
                    )
                    response = f"You already sent this link: {url}"
                else:
                    # Save new link
                    link_record = await self.repository.save_link(
                        url=url,
                        chat_id=chat_id,
                        user_id=user_id,
                        source_type="message_text",
                        message_id=message_id,
                    )

                    response = LinkService.generate_link_response(url)

                    result["links"].append({
                        "id": link_record.id,
                        "url": url,
                        "status": link_record.status,
                    })

                result["responses"].append(response)

            except Exception as e:
                logger.error(
                    "Failed to save link",
                    extra={
                        "url": url,
                        "chat_id": chat_id,
                        "error": str(e),
                    },
                )
                result["responses"].append(f"Error saving link: {url}")

        # Commit all changes
        try:
            await self.repository.commit()
            logger.info(
                "Links saved successfully",
                extra={
                    "chat_id": chat_id,
                    "count": len(result["links"]),
                },
            )
        except Exception as e:
            logger.error(
                "Failed to commit link saves",
                extra={
                    "chat_id": chat_id,
                    "error": str(e),
                },
            )
            await self.repository.rollback()
            raise

        return result
