"""Parse agent: extracts clean text content from raw HTML."""

import re

from bs4 import BeautifulSoup
from loguru import logger

from app.domain.entities.pipeline import ParseResult, PipelineContext
from app.infrastructure.agents.base_agent import BaseAgent


class ParseAgent(BaseAgent):
    """
    Parse raw HTML into structured content.

    No LLM involved. Uses BeautifulSoup to:
    - Strip noise elements (scripts, styles, nav, footer)
    - Extract main content from article/main tags
    - Extract metadata (title, author, description)
    - Convert to clean text
    """

    name = "parse"

    def __init__(self, max_content_length: int = 50000) -> None:
        """
        Initialize parse agent.

        Args:
            max_content_length (int): Maximum output text length.
        """
        self.max_content_length = max_content_length

    async def _execute(self, context: PipelineContext) -> PipelineContext:
        """
        Parse HTML content into structured text.

        Args:
            context (PipelineContext): Pipeline context with fetch_result.

        Returns:
            PipelineContext: Updated with parse_result and status=parsed.
        """
        if not context.fetch_result:
            raise ValueError("No fetch result available for parsing")

        html = context.fetch_result.html
        soup = BeautifulSoup(html, "html.parser")

        # Extract metadata
        title = self._extract_title(soup)
        author = self._extract_author(soup)
        description = self._extract_description(soup)
        language = self._extract_language(soup)

        # Remove noise elements
        self._remove_noise(soup)

        # Extract main content
        content = self._extract_main_content(soup)

        # Truncate if needed
        if len(content) > self.max_content_length:
            content = content[: self.max_content_length]
            logger.warning(
                "parse_content_truncated",
                extra={
                    "max_length": self.max_content_length,
                    "source_id": context.source_id,
                },
            )

        context.parse_result = ParseResult(
            title=title,
            content=content,
            author=author,
            description=description,
            language=language,
        )
        context.status = "parsed"

        logger.info(
            "parse_complete",
            extra={
                "title": title,
                "content_length": len(content),
                "language": language,
                "source_id": context.source_id,
            },
        )

        return context

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        """Extract page title from various sources."""
        # Open Graph title
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        # Standard title tag
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()

        # First h1
        h1_tag = soup.find("h1")
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return "Untitled"

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> str | None:
        """Extract author from meta tags."""
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        author_meta = soup.find("meta", property="article:author")
        if author_meta and author_meta.get("content"):
            return author_meta["content"].strip()

        return None

    @staticmethod
    def _extract_description(soup: BeautifulSoup) -> str | None:
        """Extract description from meta tags."""
        desc_meta = soup.find("meta", attrs={"name": "description"})
        if desc_meta and desc_meta.get("content"):
            return desc_meta["content"].strip()

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            return og_desc["content"].strip()

        return None

    @staticmethod
    def _extract_language(soup: BeautifulSoup) -> str:
        """Extract language from HTML lang attribute."""
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = html_tag["lang"].strip()
            # Normalize: "en-US" -> "en"
            return lang.split("-")[0].lower() if lang else "en"
        return "en"

    @staticmethod
    def _remove_noise(soup: BeautifulSoup) -> None:
        """Remove non-content elements from the soup in place."""
        noise_tags = [
            "script", "style", "nav", "footer", "header",
            "aside", "iframe", "noscript", "form",
        ]
        for tag_name in noise_tags:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Remove common ad/tracking class patterns
        noise_classes = ["sidebar", "advertisement", "ad-", "social-share", "cookie"]
        for cls_pattern in noise_classes:
            for tag in soup.find_all(class_=re.compile(cls_pattern, re.IGNORECASE)):
                tag.decompose()

    @staticmethod
    def _extract_main_content(soup: BeautifulSoup) -> str:
        """
        Extract the main readable content from the page.

        Prioritizes article/main tags, falls back to body.
        """
        # Priority: <article>, <main>, [role="main"], <body>
        main_element = (
            soup.find("article")
            or soup.find("main")
            or soup.find(attrs={"role": "main"})
            or soup.find("body")
        )

        if not main_element:
            return soup.get_text(separator="\n", strip=True)

        # Get text with paragraph separation
        paragraphs = main_element.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "pre"])
        if paragraphs:
            lines = []
            for para in paragraphs:
                text = para.get_text(strip=True)
                if text and len(text) > 10:
                    lines.append(text)
            return "\n\n".join(lines)

        # Fallback: get all text
        return main_element.get_text(separator="\n", strip=True)
