from dataclasses import dataclass
from typing import Optional

from app.domain.enums.message_type import MessageType


@dataclass
class Message:
    """
    Domain entity representing a normalized message from Telegram.

    Attributes:
        chat_id (str): Unique identifier for the chat.
        user_id (str): Unique identifier for the user who sent the message.
        type (MessageType): Type of message (text, media, or empty).
        text (Optional[str]): Text content of the message if available.
    """

    chat_id: str
    user_id: str
    type: MessageType
    text: Optional[str] = None
