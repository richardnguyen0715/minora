from abc import ABC, abstractmethod


class Messenger(ABC):
    """
    Abstract interface for sending messages to external services.

    Implementations should handle platform-specific message sending logic
    (e.g., Telegram, SMS, Email).
    """

    @abstractmethod
    async def send(
        self,
        chat_id: str,
        text: str,
        parse_mode: str | None = None,
    ) -> None:
        """
        Send a message to a specific chat.

        Args:
            chat_id (str): The unique identifier of the chat recipient.
            text (str): The message text to send.
            parse_mode (str | None): Optional Telegram parse mode.

        Raises:
            Exception: If the message cannot be sent.
        """
        pass
