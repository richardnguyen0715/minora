from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.interface.api.webhook import normalize_message
from app.domain.enums.message_type import MessageType


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_app()
    return TestClient(app)


class TestWebhook:
    """Test cases for Telegram webhook endpoint."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @patch("app.infrastructure.telegram.telegram_messenger.httpx.AsyncClient")
    def test_webhook_with_text_message(self, mock_client_class, client):
        """Test webhook receiving text message with mocked HTTP."""
        mock_instance = AsyncMock()
        mock_post_method = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post_method.return_value = mock_response
        mock_instance.post = mock_post_method
        mock_instance.__aenter__.return_value = mock_instance
        mock_client_class.return_value = mock_instance

        payload = {
            "update_id": 123,
            "message": {
                "message_id": 1,
                "from": {"id": 456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567890,
                "text": "Hello bot",
            },
        }

        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

    @patch("app.infrastructure.telegram.telegram_messenger.httpx.AsyncClient")
    def test_webhook_with_media_message(self, mock_client_class, client):
        """Test webhook receiving media message with mocked HTTP."""
        mock_instance = AsyncMock()
        mock_post_method = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post_method.return_value = mock_response
        mock_instance.post = mock_post_method
        mock_instance.__aenter__.return_value = mock_instance
        mock_client_class.return_value = mock_instance

        payload = {
            "update_id": 124,
            "message": {
                "message_id": 2,
                "from": {"id": 456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567891,
                "photo": [{"file_id": "xyz"}],
            },
        }

        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_webhook_with_invalid_payload(self, client):
        """Test webhook with invalid payload."""
        response = client.post("/webhook", json={})
        assert response.status_code == 200
        assert response.json()["ok"] is True


class TestNormalizeMessage:
    """Test cases for message normalization."""

    def test_normalize_text_message(self):
        """Test normalizing text message from Telegram payload."""
        payload = {
            "message": {
                "text": "Hello",
                "from": {"id": 123},
                "chat": {"id": 456},
            }
        }

        message = normalize_message(payload)

        assert message is not None
        assert message.chat_id == "456"
        assert message.user_id == "123"
        assert message.type == MessageType.TEXT
        assert message.text == "Hello"

    def test_normalize_media_message(self):
        """Test normalizing media message from Telegram payload."""
        payload = {
            "message": {
                "photo": [{"file_id": "xyz"}],
                "from": {"id": 123},
                "chat": {"id": 456},
            }
        }

        message = normalize_message(payload)

        assert message is not None
        assert message.chat_id == "456"
        assert message.user_id == "123"
        assert message.type == MessageType.MEDIA
        assert message.text is None

    def test_normalize_empty_message(self):
        """Test normalizing empty message from Telegram payload."""
        payload = {
            "message": {
                "from": {"id": 123},
                "chat": {"id": 456},
            }
        }

        message = normalize_message(payload)

        assert message is not None
        assert message.chat_id == "456"
        assert message.user_id == "123"
        assert message.type == MessageType.EMPTY
        assert message.text is None

    def test_normalize_missing_message_data(self):
        """Test normalizing payload without message data."""
        payload = {}

        message = normalize_message(payload)

        assert message is None

    def test_normalize_missing_chat_data(self):
        """Test normalizing message without chat data."""
        payload = {
            "message": {
                "text": "Hello",
                "from": {"id": 123},
            }
        }

        message = normalize_message(payload)

        assert message is None
