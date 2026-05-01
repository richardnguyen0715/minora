from enum import Enum


class MessageType(Enum):
    """Enum representing different types of messages received from Telegram."""

    TEXT = "text"
    MEDIA = "media"
    EMPTY = "empty"
