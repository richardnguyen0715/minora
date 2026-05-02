"""Fetch agent: downloads raw HTML from a URL using httpx."""

import httpx
from loguru import logger

from app.domain.entities.pipeline import FetchResult, PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent


class FetchAgent(BaseAgent):
    """
    Fetch raw HTML content from a URL.

    No LLM involved. Uses httpx for async HTTP requests.
    Handles redirects, timeouts, and basic error recovery.
    """

    name = "fetch"

    def __init__(
        self,
        timeout_seconds: int = 30,
        max_content_length: int = 100000,
        user_agent: str = "Minora/1.0 KnowledgeBot",
    ) -> None:
        """
        Initialize fetch agent.

        Args:
            timeout_seconds (int): HTTP request timeout.
            max_content_length (int): Maximum response body size in characters.
            user_agent (str): User-Agent header value.
        """
        self.timeout_seconds = timeout_seconds
        self.max_content_length = max_content_length
        self.user_agent = user_agent

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Fetch the URL and store raw HTML in context.

        Args:
            context (PipelineContext): Pipeline context with url.

        Returns:
            PipelineContext: Updated with fetch_result.
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        async with httpx.AsyncClient(
            timeout=self.timeout_seconds,
            follow_redirects=True,
            max_redirects=5,
        ) as client:
            response = await client.get(context.url, headers=headers)

        content_type = response.headers.get("content-type", "text/html")
        html = response.text

        # Truncate if too long to avoid overwhelming downstream agents
        if len(html) > self.max_content_length:
            logger.warning(
                "fetch_content_truncated",
                extra={
                    "original_length": len(html),
                    "max_length": self.max_content_length,
                    "url": context.url,
                },
            )
            html = html[: self.max_content_length]

        context.fetch_result = FetchResult(
            html=html,
            status_code=response.status_code,
            content_type=content_type,
            url=str(response.url),
        )

        logger.info(
            "fetch_complete",
            extra={
                "status_code": response.status_code,
                "content_length": len(html),
                "url": context.url,
            },
        )

        return context
