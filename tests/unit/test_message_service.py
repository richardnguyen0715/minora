import pytest

from app.domain.entities.message import Message
from app.domain.enums.message_type import MessageType
from app.domain.services.message_service import MessageService


class TestMessageService:
    """Test cases for MessageService business logic."""

    def test_generate_reply_for_text_message(self) -> None:
        """Test reply generation for text messages."""
        message = Message(
            chat_id="123",
            user_id="456",
            type=MessageType.TEXT,
            text="Hello",
        )

        reply = MessageService.generate_reply(message)

        assert reply == "I have received your message."

    def test_generate_reply_for_media_message(self) -> None:
        """Test reply generation for media messages."""
        message = Message(
            chat_id="123",
            user_id="456",
            type=MessageType.MEDIA,
            text=None,
        )

        reply = MessageService.generate_reply(message)

        assert reply == "I have received the content you sent."

    def test_generate_reply_for_empty_message(self) -> None:
        """Test reply generation for empty messages."""
        message = Message(
            chat_id="123",
            user_id="456",
            type=MessageType.EMPTY,
            text=None,
        )

        reply = MessageService.generate_reply(message)

        assert reply == "Empty message has been received."

    def test_message_entity_creation(self) -> None:
        """Test Message entity creation with all attributes."""
        message = Message(
            chat_id="chat_123",
            user_id="user_456",
            type=MessageType.TEXT,
            text="Test message",
        )

        assert message.chat_id == "chat_123"
        assert message.user_id == "user_456"
        assert message.type == MessageType.TEXT
        assert message.text == "Test message"

    def test_message_type_enum_values(self) -> None:
        """Test MessageType enum values."""
        assert MessageType.TEXT.value == "text"
        assert MessageType.MEDIA.value == "media"
        assert MessageType.EMPTY.value == "empty"
