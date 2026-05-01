"""
Unit tests for link extraction and processing.
"""
import pytest

from app.domain.services.link_service import LinkService


class TestLinkService:
    """Test cases for LinkService."""

    def test_extract_single_link(self) -> None:
        """Test extracting a single link from text."""
        text = "Check this out: https://example.com/article"
        links = LinkService.extract_links(text)

        assert len(links) == 1
        assert links[0] == "https://example.com/article"

    def test_extract_multiple_links(self) -> None:
        """Test extracting multiple links from text."""
        text = "Visit https://example.com and http://test.org for more info"
        links = LinkService.extract_links(text)

        assert len(links) == 2
        assert "https://example.com" in links
        assert "http://test.org" in links

    def test_extract_links_with_query_params(self) -> None:
        """Test extracting links with query parameters."""
        text = "https://example.com/page?id=123&name=test"
        links = LinkService.extract_links(text)

        assert len(links) == 1
        assert "id=123" in links[0]

    def test_extract_links_with_fragments(self) -> None:
        """Test extracting links with URL fragments."""
        text = "https://example.com/docs#section-1"
        links = LinkService.extract_links(text)

        assert len(links) == 1
        assert links[0] == "https://example.com/docs#section-1"

    def test_no_links_in_text(self) -> None:
        """Test text with no links."""
        text = "This is just plain text without any links"
        links = LinkService.extract_links(text)

        assert len(links) == 0

    def test_extract_links_empty_text(self) -> None:
        """Test extracting links from empty text."""
        links = LinkService.extract_links("")

        assert len(links) == 0

    def test_extract_links_none(self) -> None:
        """Test extracting links from None."""
        links = LinkService.extract_links(None)

        assert len(links) == 0

    def test_has_links_true(self) -> None:
        """Test link detection when links exist."""
        text = "Check https://example.com"
        assert LinkService.has_links(text) is True

    def test_has_links_false(self) -> None:
        """Test link detection when no links exist."""
        text = "No links here"
        assert LinkService.has_links(text) is False

    def test_has_links_empty_text(self) -> None:
        """Test link detection on empty text."""
        assert LinkService.has_links("") is False

    def test_extract_domain_simple(self) -> None:
        """Test domain extraction from simple URL."""
        url = "https://example.com"
        domain = LinkService.extract_domain(url)

        assert domain == "example.com"

    def test_extract_domain_with_www(self) -> None:
        """Test domain extraction with www."""
        url = "https://www.example.com"
        domain = LinkService.extract_domain(url)

        assert domain == "example.com"

    def test_extract_domain_with_path(self) -> None:
        """Test domain extraction with path."""
        url = "https://example.com/article/page"
        domain = LinkService.extract_domain(url)

        assert domain == "example.com"

    def test_generate_link_response(self) -> None:
        """Test response generation for link."""
        url = "https://example.com"
        response = LinkService.generate_link_response(url)

        assert "I got this link" in response
        assert "example.com" in response
        assert url in response

    def test_duplicate_links_removed(self) -> None:
        """Test that duplicate links are removed."""
        text = "Check https://example.com and https://example.com again"
        links = LinkService.extract_links(text)

        assert len(links) == 1
