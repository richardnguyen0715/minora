"""Tests for IngestionOrchestrator with mocked agents."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.entities.pipeline import PipelineContext


class TestIngestionOrchestrator:
    """Test orchestrator initialization and basic flow."""

    def test_detect_platform(self):
        from app.application.use_cases.ingestion_orchestrator import IngestionOrchestrator

        # Create a mock session
        mock_session = MagicMock()
        orchestrator = IngestionOrchestrator(mock_session)

        assert orchestrator._detect_platform("https://medium.com/article") == "medium"
        assert orchestrator._detect_platform("https://github.com/repo") == "github"
        assert orchestrator._detect_platform("https://example.com") == "web"
        assert orchestrator._detect_platform("https://www.youtube.com/watch") == "youtube"
        assert orchestrator._detect_platform("https://arxiv.org/abs/123") == "arxiv"

    def test_generate_source_id(self):
        from app.application.use_cases.ingestion_orchestrator import IngestionOrchestrator

        mock_session = MagicMock()
        orchestrator = IngestionOrchestrator(mock_session)

        source_id = orchestrator._generate_source_id("https://example.com", "web")
        assert source_id.startswith("src_")
        assert "_web_" in source_id
        assert len(source_id) > 15

    @pytest.mark.asyncio
    async def test_duplicate_url_returns_warning(self):
        from app.application.use_cases.ingestion_orchestrator import IngestionOrchestrator

        mock_session = MagicMock()
        orchestrator = IngestionOrchestrator(mock_session)

        # Mock existing node
        mock_node = MagicMock()
        mock_node.id = "src_existing"

        with patch.object(orchestrator.repository, "get_node_by_url", return_value=mock_node):
            result = await orchestrator.run("https://example.com", "user1", "chat1")
            assert "[WARN]" in result
            assert "already imported" in result
