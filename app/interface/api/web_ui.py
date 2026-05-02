"""REST API routes for the Web UI knowledge management interface."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.web_knowledge import WebKnowledgeUseCase
from app.infrastructure.database import get_session

router = APIRouter(prefix="/api", tags=["web-ui"])


# ------------------------------------------------------------------ #
#  Request / Response schemas                                         #
# ------------------------------------------------------------------ #


class NodeCreateRequest(BaseModel):
    """Schema for creating a new knowledge node."""

    id: str = Field(..., description="Unique node identifier (e.g. src_20260501_001)")
    type: str = Field(..., description="Node type: source, concept, insight, summary, entity, task")
    title: str = Field(..., description="Human-readable title")
    content: str = Field(default="", description="Markdown body content")
    slug: str | None = Field(default=None, description="URL-friendly slug")
    status: str = Field(default="draft", description="Status: draft, processed, imported, archived")
    confidence: float | None = Field(default=None, description="Confidence score 0.0 to 1.0")
    tags: list[str] = Field(default_factory=list, description="List of tag names")
    aliases: list[str] = Field(default_factory=list, description="Alternative names")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Type-specific metadata")


class NodeUpdateRequest(BaseModel):
    """Schema for updating an existing knowledge node."""

    title: str | None = None
    content: str | None = None
    slug: str | None = None
    status: str | None = None
    confidence: float | None = None
    tags: list[str] | None = None
    aliases: list[str] | None = None
    metadata: dict[str, Any] | None = None


class ContentReplaceRequest(BaseModel):
    """Schema for replacing markdown content only."""

    content: str = Field(..., description="New markdown content")


class EdgeCreateRequest(BaseModel):
    """Schema for creating a relationship edge."""

    from_id: str = Field(..., description="Source node ID")
    to_id: str = Field(..., description="Target node ID")
    type: str = Field(default="references", description="Edge type")
    weight: float = Field(default=1.0, description="Relationship weight")


class LinkUpdateRequest(BaseModel):
    """Schema for updating a link."""

    url: str | None = None
    title: str | None = None
    status: str | None = None
    source_type: str | None = None


# ------------------------------------------------------------------ #
#  Dependency                                                         #
# ------------------------------------------------------------------ #


async def _get_use_case(session: AsyncSession = Depends(get_session)):
    """Dependency injection for WebKnowledgeUseCase."""
    return WebKnowledgeUseCase(session)


# ------------------------------------------------------------------ #
#  Statistics                                                         #
# ------------------------------------------------------------------ #


@router.get("/stats")
async def get_stats(
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Get dashboard statistics."""
    return await use_case.get_stats()


# ------------------------------------------------------------------ #
#  Nodes                                                              #
# ------------------------------------------------------------------ #


@router.get("/nodes")
async def list_nodes(
    type: str | None = Query(default=None, description="Filter by node type"),
    status: str | None = Query(default=None, description="Filter by status"),
    search: str | None = Query(default=None, description="Search query"),
    sort_by: str = Query(default="updated_at", description="Sort column"),
    sort_order: str = Query(default="desc", description="Sort direction"),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """List knowledge nodes with filtering, search, sorting, and pagination."""
    return await use_case.list_nodes(
        node_type=type,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )


@router.get("/nodes/{node_id}")
async def get_node(
    node_id: str,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Get full detail for a specific knowledge node."""
    result = await use_case.get_node(node_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return result


@router.post("/nodes", status_code=201)
async def create_node(
    request: NodeCreateRequest,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Create a new knowledge node."""
    return await use_case.create_node(request.model_dump())


@router.put("/nodes/{node_id}")
async def update_node(
    node_id: str,
    request: NodeUpdateRequest,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Update an existing knowledge node."""
    updates = {key: value for key, value in request.model_dump().items() if value is not None}
    result = await use_case.update_node(node_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return result


@router.delete("/nodes/{node_id}")
async def delete_node(
    node_id: str,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Delete a knowledge node."""
    deleted = await use_case.delete_node(node_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return {"deleted": True, "id": node_id}


@router.put("/nodes/{node_id}/content")
async def replace_content(
    node_id: str,
    request: ContentReplaceRequest,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Replace only the markdown content of a node."""
    result = await use_case.replace_content(node_id, request.content)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return result


# ------------------------------------------------------------------ #
#  Edges                                                              #
# ------------------------------------------------------------------ #


@router.get("/edges")
async def list_edges(
    node_id: str | None = Query(default=None, description="Filter by node ID"),
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """List relationship edges."""
    return await use_case.list_edges(node_id=node_id)


@router.post("/edges", status_code=201)
async def create_edge(
    request: EdgeCreateRequest,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Create a new relationship edge."""
    return await use_case.create_edge(request.model_dump())


@router.delete("/edges/{edge_id}")
async def delete_edge(
    edge_id: int,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Delete a relationship edge."""
    deleted = await use_case.delete_edge(edge_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Edge '{edge_id}' not found")
    return {"deleted": True, "id": edge_id}


# ------------------------------------------------------------------ #
#  Tags                                                               #
# ------------------------------------------------------------------ #


@router.get("/tags")
async def list_tags(
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """List all tags with usage counts."""
    return await use_case.list_tags()


# ------------------------------------------------------------------ #
#  Links                                                              #
# ------------------------------------------------------------------ #


@router.get("/links")
async def list_links(
    status: str | None = Query(default=None, description="Filter by status"),
    search: str | None = Query(default=None, description="Search URL or title"),
    sort_by: str = Query(default="created_at", description="Sort column"),
    sort_order: str = Query(default="desc", description="Sort direction"),
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """List saved links with filtering, search, sorting, and pagination."""
    return await use_case.list_links(
        status=status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        per_page=per_page,
    )


@router.get("/links/{link_id}")
async def get_link(
    link_id: str,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Get a specific link."""
    result = await use_case.get_link(link_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")
    return result


@router.put("/links/{link_id}")
async def update_link(
    link_id: str,
    request: LinkUpdateRequest,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Update a link."""
    updates = {key: value for key, value in request.model_dump().items() if value is not None}
    result = await use_case.update_link(link_id, updates)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")
    return result


@router.delete("/links/{link_id}")
async def delete_link(
    link_id: str,
    use_case: WebKnowledgeUseCase = Depends(_get_use_case),
):
    """Delete a link."""
    deleted = await use_case.delete_link(link_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Link '{link_id}' not found")
    return {"deleted": True, "id": link_id}
