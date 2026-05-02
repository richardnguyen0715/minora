"""Pipeline data transfer objects for multi-agent ingestion."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.knowledge import KnowledgeEdge


@dataclass
class FetchResult:
    """Result of fetching a URL."""

    html: str
    status_code: int
    content_type: str = "text/html"
    url: str = ""


@dataclass
class ParseResult:
    """Result of parsing raw HTML into structured content."""

    title: str
    content: str
    author: str | None = None
    published_at: str | None = None
    language: str = "en"
    description: str | None = None


@dataclass
class ExtractResult:
    """Result of LLM-based content extraction."""

    summary: str = ""
    key_points: list[str] = field(default_factory=list)
    concepts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)


@dataclass
class ConceptResult:
    """Result of concept mapping and creation."""

    created: list[str] = field(default_factory=list)
    linked: list[str] = field(default_factory=list)
    edges: list[KnowledgeEdge] = field(default_factory=list)


@dataclass
class InsightEntry:
    """A single insight from the insight agent."""

    text: str
    impact: str = "medium"


@dataclass
class InsightResult:
    """Result of insight generation."""

    insights: list[InsightEntry] = field(default_factory=list)


@dataclass
class PipelineContext:
    """
    Shared context passed through the ingestion pipeline.

    Each agent reads from and writes to this context.
    Status tracks pipeline progress for observability and resume capability.
    """

    url: str
    user_id: str
    chat_id: str
    source_id: str
    platform: str = "web"
    status: str = "pending"

    fetch_result: FetchResult | None = None
    parse_result: ParseResult | None = None
    extract_result: ExtractResult | None = None
    concept_result: ConceptResult | None = None
    insight_result: InsightResult | None = None

    error: str | None = None
    error_stage: str | None = None
