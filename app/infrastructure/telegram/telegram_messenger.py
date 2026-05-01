import httpx
from loguru import logger

from app.application.interfaces.messenger import Messenger

# Telegram API base URL
TELEGRAM_API_BASE_URL = "https://api.telegram.org"


class TelegramMessenger(Messenger):
    """
    Messenger implementation for Telegram Bot API.

    Sends messages to Telegram chats using the official Telegram Bot API.
    """

    def __init__(self, token: str) -> None:
        """
        Initialize the Telegram messenger.

        Args:
            token (str): Telegram Bot API token.
        """
        self.token = token
        self.base_url = f"{TELEGRAM_API_BASE_URL}/bot{token}"

    async def send(self, chat_id: str, text: str) -> None:
        """
        Send a message to a Telegram chat.

        Args:
            chat_id (str): The Telegram chat ID.
            text (str): The message text to send.

        Raises:
            httpx.RequestError: If the HTTP request fails.
            ValueError: If the Telegram API returns an error.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)

                if response.status_code != 200:
                    logger.error(
                        "Telegram API error",
                        extra={
                            "chat_id": chat_id,
                            "status_code": response.status_code,
                            "response": response.text,
                        },
                    )
                    response.raise_for_status()

                logger.debug(
                    "Message sent to Telegram",
                    extra={"chat_id": chat_id},
                )

        except httpx.RequestError as e:
            logger.error(
                "Failed to send message to Telegram",
                extra={
                    "chat_id": chat_id,
                    "error": str(e),
                },
            )
            raise
