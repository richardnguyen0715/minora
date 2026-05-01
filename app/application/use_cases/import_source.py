"""Use case for importing sources from URLs (Facebook, web, etc.)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.knowledge import KnowledgeDocument
from app.domain.services.link_service import LinkService
from app.infrastructure.knowledge.repository import KnowledgeRepository
from app.infrastructure.knowledge.markdown_storage import MarkdownStorage


class ImportSourceUseCase:
    """
    Import a source from URL and save as knowledge node.

    Workflow:
    1. Validate URL
    2. Extract platform info
    3. Generate unique source ID
    4. Create Source node
    5. Save to markdown + metadata DB
    """

    def __init__(self, session: AsyncSession, knowledge_root: str = "knowledge") -> None:
        """
        Initialize use case.

        Args:
            session (AsyncSession): Async database session.
            knowledge_root (str): Root directory for knowledge files.
        """
        self.repository = KnowledgeRepository(session)
        self.storage = MarkdownStorage(knowledge_root)
        self.session = session

    async def execute(
        self,
        url: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict:
        """
        Import a source from URL.

        Args:
            url (str): Source URL.
            user_id (Optional[str]): User ID for tracking.
            title (Optional[str]): Custom title (optional, will use URL if not provided).
            tags (Optional[list[str]]): Tags for the source.

        Returns:
            dict: Result with node info and file path.
        """
        tags = tags or []

        logger.info(
            "import_source_started",
            extra={
                "url": url,
                "user_id": user_id,
            },
        )

        try:
            # Validate URL
            if not LinkService.has_links(url):
                return {
                    "ok": False,
                    "error": "invalid_url",
                    "message": "URL is not valid",
                }

            # Extract platform info
            domain = LinkService.extract_domain(url)
            platform = self._detect_platform(url, domain)

            # Check if already imported by URL
            existing = await self.repository.get_node_by_url(url)
            if existing:
                logger.info(
                    "source_already_imported",
                    extra={"node_id": existing.id, "url": url},
                )
                return {
                    "ok": False,
                    "error": "duplicate_import",
                    "message": f"This source already imported: {existing.id}",
                    "node_id": existing.id,
                }

            # Generate unique source ID
            source_id = self._generate_source_id(platform, url)

            # Create Source document
            document = self._create_source_document(
                source_id=source_id,
                url=url,
                platform=platform,
                title=title or f"Source from {domain}",
                user_id=user_id,
                tags=tags,
            )

            # Save markdown file
            file_path = self.storage.write_document(
                self._to_markdown_document(document)
            )
            document.file_path = str(file_path)

            # Save to metadata DB
            node = await self.repository.upsert_document(document)
            await self.repository.commit()

            logger.info(
                "source_imported_successfully",
                extra={
                    "source_id": source_id,
                    "url": url,
                    "file_path": document.file_path,
                    "platform": platform,
                },
            )

            return {
                "ok": True,
                "source_id": source_id,
                "file_path": document.file_path,
                "url": url,
                "platform": platform,
                "title": document.title,
            }

        except Exception as exc:
            await self.repository.rollback()
            logger.error(
                "source_import_failed",
                extra={
                    "url": url,
                    "error": str(exc),
                    "user_id": user_id,
                },
            )
            return {
                "ok": False,
                "error": "import_failed",
                "message": f"Failed to import source: {str(exc)}",
            }

    def _detect_platform(self, url: str, domain: str) -> str:
        """
        Detect platform from URL.

        Args:
            url (str): Full URL.
            domain (str): Extracted domain.

        Returns:
            str: Platform name (facebook, twitter, web, etc.).
        """
        domain_lower = domain.lower()

        if "facebook" in domain_lower or "fb" in domain_lower:
            return "facebook"
        elif "twitter" in domain_lower or "x.com" in domain_lower:
            return "twitter"
        elif "youtube" in domain_lower or "youtu.be" in domain_lower:
            return "youtube"
        elif "reddit" in domain_lower:
            return "reddit"
        elif "medium" in domain_lower:
            return "medium"
        elif "github" in domain_lower:
            return "github"
        elif "arxiv" in domain_lower:
            return "arxiv"
        else:
            return "web"

    def _generate_source_id(self, platform: str, url: str) -> str:
        """
        Generate unique source ID.

        Args:
            platform (str): Platform name.

        Returns:
            str: Generated ID like src_20260501_facebook_001.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y%m%d")

        # Use short hash of URL to avoid collisions for same platform/day
        from hashlib import sha256

        short_hash = sha256(url.encode("utf-8")).hexdigest()[:8]
        return f"src_{date_str}_{platform}_{short_hash}"

    def _create_source_document(
        self,
        source_id: str,
        url: str,
        platform: str,
        title: str,
        user_id: Optional[str],
        tags: list[str],
    ) -> KnowledgeDocument:
        """
        Create a Source knowledge document.

        Args:
            source_id (str): Source ID.
            url (str): Source URL.
            platform (str): Platform name.
            title (str): Document title.
            user_id (Optional[str]): User ID.
            tags (list[str]): Tags.

        Returns:
            KnowledgeDocument: Source document.
        """
        now = datetime.now(timezone.utc)

        metadata = {
            "url": url,
            "platform": platform,
        }

        if user_id:
            metadata["imported_by_user"] = user_id

        return KnowledgeDocument(
            id=source_id,
            type="source",
            title=title,
            content=f"# {title}\n\nSource URL: {url}\n\nPlatform: {platform}",
            slug=source_id,
            status="imported",
            confidence=1.0,
            tags=tags,
            metadata=metadata,
            created_at=now,
            updated_at=now,
        )

    def _to_markdown_document(self, document: KnowledgeDocument):
        """Convert to markdown storage format."""
        from app.infrastructure.knowledge.markdown_storage import MarkdownDocument

        return MarkdownDocument(
            id=document.id,
            type=document.type,
            title=document.title,
            content=document.content,
            slug=document.slug,
            status=document.status,
            confidence=document.confidence,
            tags=document.tags,
            aliases=document.aliases,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
            file_path=document.file_path,
        )
