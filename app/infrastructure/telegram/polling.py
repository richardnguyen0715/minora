"""Long polling implementation for Telegram bot updates."""

import asyncio
from typing import Optional

from loguru import logger

from app.application.use_cases.handle_message import HandleMessageUseCase
from app.domain.entities.message import Message
from app.domain.enums.message_type import MessageType
from app.infrastructure.database import get_session_maker
from app.infrastructure.telegram.telegram_messenger import TelegramMessenger


class TelegramPoller:
    """
    Telegram long polling client.

    Continuously polls Telegram for new messages using getUpdates method.
    This is suitable for development and testing. For production with webhooks,
    see webhook.py instead.
    """

    def __init__(
        self,
        telegram_token: str,
        allowed_chat_id: Optional[str] = None,
    ):
        """
        Initialize the poller.

        Args:
            telegram_token (str): Telegram Bot API token.
            allowed_chat_id (str, optional): Only process messages from this chat.
        """
        self.telegram_token = telegram_token
        self.allowed_chat_id = allowed_chat_id
        self.messenger = TelegramMessenger(token=telegram_token)
        self.session_maker = get_session_maker()
        self.last_update_id = 0
        self.running = False

    def _normalize_message(self, telegram_update: dict) -> Optional[Message]:
        """
        Map Telegram update to domain Message entity.

        Args:
            telegram_update (dict): Telegram update object from getUpdates.

        Returns:
            Optional[Message]: Normalized message or None if invalid.
        """
        update_data = telegram_update.get("message")

        if not update_data:
            return None

        chat_data = update_data.get("chat")
        from_data = update_data.get("from")

        if not chat_data or not from_data:
            logger.warning("Missing chat or from data in message")
            return None

        chat_id = str(chat_data.get("id"))
        user_id = str(from_data.get("id"))

        # Determine message type
        text = update_data.get("text")
        if text:
            message_type = MessageType.TEXT
        elif update_data.get("photo") or update_data.get("document"):
            message_type = MessageType.MEDIA
            text = None
        else:
            message_type = MessageType.EMPTY
            text = None

        return Message(
            chat_id=chat_id,
            user_id=user_id,
            type=message_type,
            text=text,
        )

    async def _process_update(self, update: dict) -> None:
        """
        Process a single Telegram update.

        Args:
            update (dict): Telegram update object.
        """
        try:
            message = self._normalize_message(update)
            message_id = update.get("message", {}).get("message_id")

            if not message:
                return

            # Filter by chat_id if configured
            if self.allowed_chat_id and message.chat_id != self.allowed_chat_id:
                logger.debug(
                    "Message from unauthorized chat, ignoring",
                    extra={
                        "chat_id": message.chat_id,
                        "allowed": self.allowed_chat_id,
                    },
                )
                return

            logger.info(
                "Processing message via long polling",
                extra={
                    "update_id": update.get("update_id"),
                    "chat_id": message.chat_id,
                    "user_id": message.user_id,
                },
            )

            # Create database session for this update
            async with self.session_maker() as session:
                use_case = HandleMessageUseCase(
                    messenger=self.messenger,
                    session=session,
                )
                await use_case.execute(message, message_id=message_id)

        except Exception as e:
            logger.error(
                "Failed to process update",
                extra={
                    "error": str(e),
                    "update_id": update.get("update_id"),
                },
            )

    async def poll(self, timeout: int = 30, backoff_base: float = 2.0) -> None:
        """
        Start polling for updates.

        Uses exponential backoff on errors to avoid overwhelming the API.

        Args:
            timeout (int): Long polling timeout in seconds (30 is recommended).
            backoff_base (float): Exponential backoff multiplier on errors.
        """
        self.running = True
        consecutive_errors = 0
        max_backoff = 60

        logger.info(
            "Starting Telegram long polling",
            extra={
                "timeout": timeout,
                "allowed_chat_id": self.allowed_chat_id,
            },
        )

        try:
            while self.running:
                try:
                    # Get updates from Telegram
                    updates = await self.messenger.get_updates(
                        offset=self.last_update_id + 1,
                        timeout=timeout,
                    )

                    if not updates:
                        consecutive_errors = 0
                        await asyncio.sleep(0.1)
                        continue

                    logger.debug(
                        f"Received {len(updates)} updates",
                        extra={"count": len(updates)},
                    )

                    # Process each update
                    for update in updates:
                        await self._process_update(update)
                        self.last_update_id = update.get("update_id", self.last_update_id)

                    consecutive_errors = 0

                except Exception as e:
                    consecutive_errors += 1
                    backoff_time = min(
                        backoff_base ** consecutive_errors,
                        max_backoff,
                    )

                    logger.error(
                        f"Error in polling loop (attempt {consecutive_errors})",
                        extra={
                            "error": str(e),
                            "backoff_seconds": backoff_time,
                        },
                    )

                    await asyncio.sleep(backoff_time)

        except asyncio.CancelledError:
            logger.info("Polling cancelled")
        except Exception as e:
            logger.error(
                "Fatal error in polling loop",
                extra={"error": str(e)},
            )
        finally:
            self.running = False
            logger.info("Telegram polling stopped")

    def stop(self) -> None:
        """Stop the polling loop."""
        self.running = False
        logger.info("Stopping Telegram polling")
