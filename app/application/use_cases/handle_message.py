from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.messenger import Messenger
from app.application.use_cases.save_link import SaveLinkUseCase
from app.application.use_cases.handle_command import HandleCommandUseCase
from app.domain.entities.message import Message
from app.domain.services.command_parser import CommandParser
from app.domain.services.link_service import LinkService
from app.domain.services.message_service import MessageService
from app.infrastructure.commands.registry import get_command_registry


class HandleMessageUseCase:
    """
    Use case for handling incoming messages.

    Orchestrates the workflow:
    1. Check if message is a command
    2. If command: execute HandleCommandUseCase
    3. If not command: extract and save links
    4. Generate appropriate reply
    5. Send response
    """

    def __init__(
        self, messenger: Messenger, session: Optional[AsyncSession] = None
    ) -> None:
        """
        Initialize the use case with a messenger implementation.

        Args:
            messenger (Messenger): The messenger interface implementation.
            session (Optional[AsyncSession]): Database session for link operations.
        """
        self.messenger = messenger
        self.session = session
        self.save_link_use_case = SaveLinkUseCase(session) if session else None
        self.command_use_case = HandleCommandUseCase(messenger)

    async def execute(
        self, message: Message, message_id: Optional[int] = None
    ) -> None:
        """
        Execute the message handling workflow.

        Args:
            message (Message): The normalized message to handle.
            message_id (Optional[int]): Telegram message ID for reference.
        """
        logger.info(
            "Processing message",
            extra={
                "chat_id": message.chat_id,
                "user_id": message.user_id,
                "type": message.type.value,
            },
        )

        # Check if message is a command (starts with /)
        if message.text and CommandParser.is_command(message.text):
            logger.info(
                "Command detected in message",
                extra={"text": message.text},
            )

            # Execute command use case
            await self.command_use_case.execute(
                chat_id=message.chat_id,
                text=message.text,
                user_id=message.user_id,
            )

            logger.info(
                "Message processed successfully (command)",
                extra={"chat_id": message.chat_id},
            )
            return

        # Not a command - handle as regular message
        # Generate default reply
        reply = MessageService.generate_reply(message)
        responses_to_send = [reply]

        # Check for links and save them
        if message.text and LinkService.has_links(message.text):
            logger.debug(
                "Links detected in message",
                extra={"chat_id": message.chat_id},
            )

            if self.save_link_use_case:
                try:
                    result = await self.save_link_use_case.execute(
                        chat_id=message.chat_id,
                        user_id=message.user_id,
                        text=message.text,
                        message_id=message_id or 0,
                    )

                    # Add link-specific responses
                    if result["responses"]:
                        responses_to_send = result["responses"]

                    logger.info(
                        "Links processed and saved",
                        extra={
                            "chat_id": message.chat_id,
                            "count": result["links_found"],
                        },
                    )

                except Exception as e:
                    logger.error(
                        "Failed to process links",
                        extra={
                            "chat_id": message.chat_id,
                            "error": str(e),
                        },
                    )

        # Send all responses
        logger.info(
            "Preparing to send responses",
            extra={
                "chat_id": message.chat_id,
                "response_count": len(responses_to_send),
                "responses": responses_to_send,
            },
        )

        for i, response in enumerate(responses_to_send):
            logger.info(
                f"Sending response {i+1}/{len(responses_to_send)}",
                extra={"chat_id": message.chat_id, "response": response},
            )

            try:
                await self.messenger.send(message.chat_id, response)
                logger.info(
                    "Response sent successfully",
                    extra={"chat_id": message.chat_id},
                )
            except Exception as e:
                logger.error(
                    "Failed to send response",
                    extra={"chat_id": message.chat_id, "error": str(e)},
                )

        logger.info(
            "Message processed successfully",
            extra={"chat_id": message.chat_id},
        )
