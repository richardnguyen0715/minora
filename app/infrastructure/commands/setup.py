"""Command setup: register all commands with their handlers."""

from loguru import logger

from app.domain.entities.command import Command
from app.infrastructure.commands.registry import CommandRegistry
from app.infrastructure.commands.handlers.system import (
    build_help_handler,
    handle_status,
    handle_ping,
    handle_start,
    handle_whoami,
    handle_version,
)
from app.infrastructure.commands.handlers.data import (
    handle_list,
    handle_find,
    handle_read,
    handle_update,
    handle_delete,
    handle_visualize,
    handle_clear,
    handle_history,
)
from app.infrastructure.commands.handlers.config import (
    handle_settings,
    handle_export,
    handle_import,
)


def build_registry() -> CommandRegistry:
    """
    Build command registry with all handlers.
    
    Returns:
        CommandRegistry: Initialized registry.
    """
    registry = CommandRegistry()
    help_handler = build_help_handler(registry)

    # ============ SYSTEM COMMANDS ============

    registry.register(Command(
        name="help",
        description="List all commands or show command details",
        usage="/help [command]",
        category="system",
        examples=["/help", "/help find"],
        args_schema=None,
        is_visible=True,
        aliases=["h"],
        handler=help_handler,
    ))

    registry.register(Command(
        name="status",
        description="System health check",
        usage="/status",
        category="system",
        examples=["/status"],
        args_schema=None,
        is_visible=True,
        aliases=["health"],
        handler=handle_status,
    ))

    registry.register(Command(
        name="ping",
        description="Test latency",
        usage="/ping",
        category="system",
        examples=["/ping"],
        args_schema=None,
        is_visible=True,
        aliases=["latency"],
        handler=handle_ping,
    ))

    registry.register(Command(
        name="start",
        description="Start/onboard user",
        usage="/start",
        category="system",
        examples=["/start"],
        args_schema=None,
        is_visible=True,
        handler=handle_start,
    ))

    registry.register(Command(
        name="whoami",
        description="Show user context (debug)",
        usage="/whoami",
        category="system",
        examples=["/whoami"],
        args_schema=None,
        is_visible=False,
        handler=handle_whoami,
    ))

    registry.register(Command(
        name="version",
        description="Show system version",
        usage="/version",
        category="system",
        examples=["/version"],
        args_schema=None,
        is_visible=True,
        handler=handle_version,
    ))

    # ============ DATA COMMANDS ============

    registry.register(Command(
        name="list",
        description="List recent knowledge items",
        usage="/list",
        category="knowledge",
        examples=["/list"],
        args_schema=None,
        is_visible=True,
        aliases=["ls"],
        handler=handle_list,
    ))

    registry.register(Command(
        name="find",
        description="Search knowledge metadata and file index",
        usage="/find <query> [--limit=10]",
        category="knowledge",
        examples=["/find llm", "/find ai --limit=5"],
        args_schema={"query": str},
        is_visible=True,
        aliases=["search"],
        handler=handle_find,
    ))

    registry.register(Command(
        name="read",
        description="Read a knowledge item by id",
        usage="/read <id>",
        category="knowledge",
        examples=["/read concept_llm"],
        args_schema={"query": str},
        is_visible=True,
        aliases=["get", "show"],
        handler=handle_read,
    ))

    registry.register(Command(
        name="update",
        description="Update a knowledge item by id",
        usage="/update <id> [title=...] [content=...] [status=...]",
        category="knowledge",
        examples=["/update concept_llm title=LLM content=Updated text", "/update src_20260430_001 status=processed"],
        args_schema={"query": str},
        is_visible=True,
        aliases=["edit"],
        handler=handle_update,
    ))

    registry.register(Command(
        name="delete",
        description="Delete a knowledge item by id",
        usage="/delete <id>",
        category="knowledge",
        examples=["/delete concept_llm"],
        args_schema={"query": str},
        is_visible=True,
        aliases=["remove"],
        handler=handle_delete,
    ))

    registry.register(Command(
        name="visualize",
        description="Visualize metadata DB and real-file contents",
        usage="/visualize [id] [--limit=10]",
        category="knowledge",
        examples=["/visualize", "/visualize concept_llm", "/visualize --limit=5"],
        args_schema=None,
        is_visible=True,
        aliases=["inspect", "dump"],
        handler=handle_visualize,
    ))

    registry.register(Command(
        name="clear",
        description="Clear a knowledge item shortcut",
        usage="/clear confirm",
        category="knowledge",
        examples=["/clear confirm"],
        args_schema=None,
        is_visible=True,
        handler=handle_clear,
    ))

    registry.register(Command(
        name="history",
        description="Show recent knowledge items",
        usage="/history [limit]",
        category="knowledge",
        examples=["/history", "/history 10"],
        args_schema=None,
        is_visible=True,
        handler=handle_history,
    ))

    # ============ SEARCH COMMANDS ============

    # Note: "find" is already in data commands

    # ============ CONFIG COMMANDS ============

    registry.register(Command(
        name="settings",
        description="Manage settings",
        usage="/settings [set <key> <value>]",
        category="config",
        examples=["/settings", "/settings get theme", "/settings set theme dark"],
        args_schema=None,
        is_visible=True,
        handler=handle_settings,
    ))

    registry.register(Command(
        name="export",
        description="Export data",
        usage="/export [json|csv]",
        category="config",
        examples=["/export json", "/export csv"],
        args_schema=None,
        is_visible=True,
        handler=handle_export,
    ))

    registry.register(Command(
        name="import",
        description="Import source from URL (full AI pipeline)",
        usage="/import <url>",
        category="config",
        examples=["/import https://example.com/article"],
        args_schema=None,
        is_visible=True,
        requires_context=True,
        handler=handle_import,
    ))

    logger.info(
        "command_registry_built",
        extra={"command_count": len(registry.all())},
    )

    return registry


# Global registry instance
_registry = None


def get_command_registry() -> CommandRegistry:
    """
    Get or create the global command registry.
    
    Returns:
        CommandRegistry: Global registry instance.
    """
    global _registry
    if _registry is None:
        _registry = build_registry()
    return _registry
