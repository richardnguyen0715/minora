import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.use_cases.handle_message import HandleMessageUseCase
from app.domain.entities.message import Message
from app.domain.enums.message_type import MessageType


class TestHandleMessageUseCase:
    """Test cases for HandleMessageUseCase."""

    @pytest.mark.asyncio
    async def test_execute_with_text_message(self) -> None:
        """Test executing use case with text message."""
        # Arrange
        mock_messenger = AsyncMock()
        use_case = HandleMessageUseCase(messenger=mock_messenger)

        message = Message(
            chat_id="123",
            user_id="456",
            type=MessageType.TEXT,
            text="Hello",
        )

        # Act
        await use_case.execute(message)

        # Assert
        mock_messenger.send.assert_called_once()
        call_args = mock_messenger.send.call_args
        assert call_args[0][0] == "123"
        assert call_args[0][1] == "I have received your message."

    @pytest.mark.asyncio
    async def test_execute_with_media_message(self) -> None:
        """Test executing use case with media message."""
        # Arrange
        mock_messenger = AsyncMock()
        use_case = HandleMessageUseCase(messenger=mock_messenger)

        message = Message(
            chat_id="789",
            user_id="101",
            type=MessageType.MEDIA,
            text=None,
        )

        # Act
        await use_case.execute(message)

        # Assert
        mock_messenger.send.assert_called_once()
        call_args = mock_messenger.send.call_args
        assert call_args[0][0] == "789"
        assert call_args[0][1] == "I have received the content you sent."

    @pytest.mark.asyncio
    async def test_execute_sends_reply(self) -> None:
        """Test that execute sends the generated reply via messenger."""
        # Arrange
        mock_messenger = AsyncMock()
        use_case = HandleMessageUseCase(messenger=mock_messenger)

        message = Message(
            chat_id="chat_123",
            user_id="user_123",
            type=MessageType.TEXT,
            text="Test",
        )

        # Act
        await use_case.execute(message)

        # Assert
        assert mock_messenger.send.called
