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

    async def send(
        self,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        """
        Send a message to a Telegram chat.

        Args:
            chat_id (str): The Telegram chat ID.
            text (str): The message text to send.
            parse_mode (str | None): Optional Telegram parse mode.

        Raises:
            httpx.RequestError: If the HTTP request fails.
            ValueError: If the Telegram API returns an error.
        """
        url = f"{self.base_url}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        if parse_mode:
            payload["parse_mode"] = parse_mode

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

    async def get_updates(
        self,
        offset: int = 0,
        timeout: int = 30,
    ) -> list[dict]:
        """
        Get updates from Telegram using long polling.

        Args:
            offset (int): The update offset to start polling from.
            timeout (int): Long polling timeout in seconds.

        Returns:
            list[dict]: List of Telegram update objects.

        Raises:
            httpx.RequestError: If the HTTP request fails.
        """
        url = f"{self.base_url}/getUpdates"
        payload = {"offset": offset, "timeout": timeout}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=timeout + 5,
                )

                if response.status_code != 200:
                    logger.error(
                        "Telegram getUpdates API error",
                        extra={
                            "status_code": response.status_code,
                            "response": response.text,
                        },
                    )
                    response.raise_for_status()

                data = response.json()
                if not data.get("ok"):
                    logger.error(
                        "Telegram API returned error",
                        extra={"error_description": data.get("description")},
                    )
                    return []

                updates = data.get("result", [])
                logger.debug(
                    "Got updates from Telegram",
                    extra={"count": len(updates)},
                )
                return updates

        except httpx.RequestError as e:
            logger.error(
                "Failed to get updates from Telegram",
                extra={"error": str(e)},
            )
            raise
