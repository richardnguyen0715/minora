"""
Link extraction and processing service.
"""
import re
from typing import Optional


class LinkService:
    """
    Service for extracting and validating links from message text.

    Provides pure business logic independent of any framework.
    """

    # Regex pattern for URL detection (comprehensive but practical)
    URL_PATTERN = re.compile(
        r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
    )

    @staticmethod
    def extract_links(text: Optional[str]) -> list[str]:
        """
        Extract all URLs from message text.

        Args:
            text (Optional[str]): Message text to search for URLs.

        Returns:
            list[str]: List of unique URLs found.
        """
        if not text:
            return []

        matches = LinkService.URL_PATTERN.findall(text)
        return list(dict.fromkeys(matches))  # Remove duplicates while preserving order

    @staticmethod
    def has_links(text: Optional[str]) -> bool:
        """
        Check if text contains any links.

        Args:
            text (Optional[str]): Message text to check.

        Returns:
            bool: True if text contains links.
        """
        if not text:
            return False

        return bool(LinkService.URL_PATTERN.search(text))

    @staticmethod
    def extract_domain(url: str) -> str:
        """
        Extract domain from URL.

        Args:
            url (str): The URL to extract domain from.

        Returns:
            str: The domain name.
        """
        try:
            # Remove protocol
            domain = url.replace("https://", "").replace("http://", "")
            # Remove www
            domain = domain.replace("www.", "")
            # Get domain only
            domain = domain.split("/")[0].split("?")[0]
            return domain
        except Exception:
            return url

    @staticmethod
    def generate_link_response(url: str) -> str:
        """
        Generate a response message for a received link.

        Args:
            url (str): The received URL.

        Returns:
            str: Response message to send back to user.
        """
        domain = LinkService.extract_domain(url)
        return f"I got this link from {domain}: {url}"
