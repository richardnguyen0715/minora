"""Tests for pipeline agents with mocked dependencies."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.entities.pipeline import (
    PipelineContext, FetchResult, ParseResult, ExtractResult,
)


class TestFetchAgent:
    """Test FetchAgent."""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        from app.infrastructure.agents.fetch_agent import FetchAgent

        agent = FetchAgent(timeout_seconds=10)
        context = PipelineContext(
            url="https://example.com",
            user_id="test", chat_id="test", source_id="src_test",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Hello</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://example.com"

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client

            result = await agent.run(context)
            assert result.fetch_result is not None
            assert result.fetch_result.status_code == 200


class TestParseAgent:
    """Test ParseAgent."""

    @pytest.mark.asyncio
    async def test_parse_extracts_title(self):
        from app.infrastructure.agents.parse_agent import ParseAgent

        agent = ParseAgent()
        html = "<html><head><title>Test Title</title></head><body><article><p>Some content here that is long enough.</p></article></body></html>"
        context = PipelineContext(
            url="https://example.com",
            user_id="test", chat_id="test", source_id="src_test",
        )
        context.fetch_result = FetchResult(html=html, status_code=200)

        result = await agent.run(context)
        assert result.parse_result is not None
        assert result.parse_result.title == "Test Title"
        assert result.status == "parsed"


class TestExtractAgent:
    """Test ExtractAgent with mocked LLM."""

    @pytest.mark.asyncio
    async def test_extract_with_mocked_llm(self):
        from app.infrastructure.agents.extract_agent import ExtractAgent

        mock_llm = AsyncMock()
        mock_llm.generate.return_value = {
            "summary": "A test summary",
            "key_points": ["Point 1", "Point 2"],
            "concepts": ["concept_a"],
            "entities": ["Entity1"],
            "topics": ["tech"],
        }

        agent = ExtractAgent(llm=mock_llm)
        context = PipelineContext(
            url="https://example.com",
            user_id="test", chat_id="test", source_id="src_test",
        )
        context.parse_result = ParseResult(title="Test", content="Test content")

        result = await agent.run(context)
        assert result.extract_result is not None
        assert result.extract_result.summary == "A test summary"
        assert len(result.extract_result.key_points) == 2
        assert result.status == "extracted"


class TestReportAgent:
    """Test ReportAgent formatting."""

    def test_format_completed_report(self):
        from app.infrastructure.agents.report_agent import ReportAgent

        agent = ReportAgent()
        context = PipelineContext(
            url="https://example.com",
            user_id="test", chat_id="test", source_id="src_test",
            status="completed",
        )
        context.parse_result = ParseResult(title="Test Article", content="...")
        context.extract_result = ExtractResult(
            summary="A summary", key_points=["P1"], concepts=["llm"], entities=[], topics=[],
        )

        report = agent.format_report(context)
        assert "[OK] Import complete" in report
        assert "A summary" in report

    def test_format_failed_report(self):
        from app.infrastructure.agents.report_agent import ReportAgent

        agent = ReportAgent()
        context = PipelineContext(
            url="https://example.com",
            user_id="test", chat_id="test", source_id="src_test",
            status="failed",
        )
        context.error = "Network error"
        context.error_stage = "fetch"

        report = agent.format_report(context)
        assert "[ERROR]" in report
        assert "fetch" in report


class TestPipelineEntities:
    """Test pipeline data transfer objects."""

    def test_pipeline_context_defaults(self):
        ctx = PipelineContext(url="http://x.com", user_id="u", chat_id="c", source_id="s")
        assert ctx.status == "pending"
        assert ctx.fetch_result is None
        assert ctx.error is None

    def test_fetch_result(self):
        fr = FetchResult(html="<html>", status_code=200)
        assert fr.html == "<html>"

    def test_extract_result_defaults(self):
        er = ExtractResult()
        assert er.summary == ""
        assert er.key_points == []
