"""Knowledge data command handlers."""

from __future__ import annotations

from loguru import logger

from app.application.use_cases.knowledge_item import KnowledgeItemUseCase
from app.infrastructure.database import get_session_maker


async def _run_with_use_case(action):
    try:
        session_factory = get_session_maker()
        async with session_factory() as session:
            use_case = KnowledgeItemUseCase(session)
            return await action(use_case)
    except Exception as exc:
        logger.warning(
            "knowledge_database_unavailable",
            extra={"error": str(exc)},
        )
        return "[WARN] Knowledge database is not ready yet"


async def handle_list(args: dict, user_id: str) -> str:
    """List recent knowledge items."""

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        nodes = await use_case.repository.list_nodes(limit=10)
        if not nodes:
            return "[WARN] No knowledge items available"

        lines = ["[OK] Recent knowledge items"]
        for node in nodes:
            lines.append(f"- {node.id} | {node.type} | {node.title}")
            lines.append(f"  file: {node.file_path}")
        return "\n".join(lines)

    return await _run_with_use_case(_action)


async def handle_find(args: dict, user_id: str) -> str:
    """Search knowledge items by metadata index."""
    query = args.get("query", "").strip()
    limit = args.get("limit", 10)

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        return await use_case.find(query=query, limit=limit)

    return await _run_with_use_case(_action)


async def handle_read(args: dict, user_id: str) -> str:
    """Read a knowledge item by id."""
    node_id = args.get("query", "").strip()

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        return await use_case.get(node_id)

    return await _run_with_use_case(_action)


async def handle_update(args: dict, user_id: str) -> str:
    """Update a knowledge item by id."""
    node_id = args.get("query", "").strip()

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        return await use_case.update(node_id, args)

    return await _run_with_use_case(_action)


async def handle_delete(args: dict, user_id: str) -> str:
    """Delete a knowledge item by id."""
    node_id = args.get("query", "").strip()

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        return await use_case.delete(node_id)

    return await _run_with_use_case(_action)


async def handle_clear(args: dict, user_id: str) -> str:
    """Clear command placeholder for compatibility."""
    return (
        "[WARN] Clear is reserved for future bulk knowledge cleanup. "
        "Use /delete <id> for single-item removal."
    )


async def handle_visualize(args: dict, user_id: str) -> str:
    """Visualize metadata DB and real-file content."""
    node_id = args.get("query")
    limit = args.get("limit", 10)

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10

    async def _action(use_case: KnowledgeItemUseCase) -> str:
        return await use_case.visualize(node_id=node_id, limit=limit)

    return await _run_with_use_case(_action)


async def handle_history(args: dict, user_id: str) -> str:
    """Show recent knowledge items (compatibility command)."""
    return await handle_list(args, user_id)