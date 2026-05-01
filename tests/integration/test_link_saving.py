"""
Integration tests for link saving functionality.
"""
import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    from app.infrastructure.config import settings
    from app.interface.api.webhook import initialize_webhook

    app = create_app()

    # Manually initialize webhook since TestClient doesn't trigger async lifespan
    initialize_webhook(
        telegram_token=settings.telegram_token,
        allowed_chat_id=settings.telegram_chat_id,
    )

    return TestClient(app)


class TestLinkSavingWebhook:
    """Test cases for link saving webhook integration."""

    @patch("app.infrastructure.telegram.telegram_messenger.httpx.AsyncClient")
    @patch("app.infrastructure.database.get_session_maker")
    def test_webhook_with_link_message(self, mock_session_maker, mock_client_class, client):
        """Test webhook receiving message with link."""
        # Setup mock database session
        mock_session = AsyncMock()
        mock_session_maker = AsyncMock()
        mock_session_maker.__aenter__.return_value = mock_session
        mock_session_maker.__aexit__.return_value = None
        mock_session_maker.return_value = mock_session_maker

        # Setup mock Telegram client
        mock_instance = AsyncMock()
        mock_post_method = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_post_method.return_value = mock_response
        mock_instance.post = mock_post_method
        mock_instance.__aenter__.return_value = mock_instance
        mock_client_class.return_value = mock_instance

        payload = {
            "update_id": 125,
            "message": {
                "message_id": 3,
                "from": {"id": 456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567892,
                "text": "Check this link: https://example.com/article",
            },
        }

        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["ok"] is True

    def test_webhook_with_multiple_links(self, client):
        """Test webhook receiving message with multiple links."""
        payload = {
            "update_id": 126,
            "message": {
                "message_id": 4,
                "from": {"id": 456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567893,
                "text": "Links: https://example.com and https://test.org",
            },
        }

        with patch(
            "app.infrastructure.telegram.telegram_messenger.httpx.AsyncClient"
        ) as mock_client_class:
            mock_instance = AsyncMock()
            mock_post_method = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_post_method.return_value = mock_response
            mock_instance.post = mock_post_method
            mock_instance.__aenter__.return_value = mock_instance
            mock_client_class.return_value = mock_instance

            response = client.post("/webhook", json=payload)
            assert response.status_code == 200

    def test_webhook_with_no_links(self, client):
        """Test webhook receiving message with no links."""
        payload = {
            "update_id": 127,
            "message": {
                "message_id": 5,
                "from": {"id": 456, "is_bot": False, "first_name": "Test"},
                "chat": {"id": 789, "type": "private"},
                "date": 1234567894,
                "text": "Just a regular message",
            },
        }

        with patch(
            "app.infrastructure.telegram.telegram_messenger.httpx.AsyncClient"
        ) as mock_client_class:
            mock_instance = AsyncMock()
            mock_post_method = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_post_method.return_value = mock_response
            mock_instance.post = mock_post_method
            mock_instance.__aenter__.return_value = mock_instance
            mock_client_class.return_value = mock_instance

            response = client.post("/webhook", json=payload)
            assert response.status_code == 200
