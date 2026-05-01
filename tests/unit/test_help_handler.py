"""Tests for dynamic help handler."""

from app.infrastructure.commands.handlers.system import build_help_handler
from app.infrastructure.commands.registry import CommandRegistry
from app.domain.entities.command import Command


def _handler(args, user_id):
    return "[OK]"


def test_help_lists_commands_by_category():
    registry = CommandRegistry()
    registry.register(
        Command(
            name="status",
            description="System health check",
            usage="/status",
            category="system",
            examples=["/status"],
            handler=_handler,
        )
    )
    registry.register(
        Command(
            name="find",
            description="Search stored items",
            usage="/find <query>",
            category="data",
            aliases=["search"],
            examples=["/find milk", "/find milk --limit=10"],
            args_schema={"query": str},
            handler=_handler,
        )
    )
    registry.register(
        Command(
            name="whoami",
            description="Show user context",
            usage="/whoami",
            category="system",
            examples=["/whoami"],
            handler=_handler,
            is_visible=False,
        )
    )

    help_handler = build_help_handler(registry)
    response = help_handler({}, "user1")

    assert "*Available Commands*" in response
    assert "*SYSTEM*" in response
    assert "`/status` - System health check" in response
    assert "*DATA*" in response
    assert "`/find` - Search stored items _(aliases: /search)_" in response
    assert "/whoami" not in response
    assert "Use `/help <command>` for details" in response


def test_help_shows_command_details():
    registry = CommandRegistry()
    registry.register(
        Command(
            name="find",
            description="Search stored items",
            usage="/find <query>",
            category="data",
            aliases=["search"],
            examples=["/find milk", "/find milk --limit=10"],
            args_schema={"query": str},
            handler=_handler,
        )
    )

    help_handler = build_help_handler(registry)
    response = help_handler({"query": "find"}, "user1")

    assert response == (
        "*Command Details*\n\n"
        "*Name:* `/find`\n"
        "*Category:* `data`\n"
        "*Description:* Search stored items\n"
        "*Usage:* `/find <query>`\n"
        "Aliases: /search\n"
        "*Examples:*\n"
        "• `/find milk`\n"
        "• `/find milk --limit=10`"
    )


def test_help_resolves_alias():
    registry = CommandRegistry()
    registry.register(
        Command(
            name="find",
            description="Search stored items",
            usage="/find <query>",
            category="data",
            aliases=["search"],
            examples=["/find milk"],
            args_schema={"query": str},
            handler=_handler,
        )
    )

    help_handler = build_help_handler(registry)
    response = help_handler({"query": "search"}, "user1")

    assert "*Command Details*" in response
    assert "`/find`" in response


def test_help_returns_error_for_missing_command():
    registry = CommandRegistry()
    help_handler = build_help_handler(registry)

    response = help_handler({"query": "unknown"}, "user1")

    assert response == "[ERROR] Command 'unknown' not found"
