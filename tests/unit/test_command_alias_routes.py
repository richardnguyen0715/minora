"""Tests for alias-based command routing."""

from app.application.services.command_dispatcher import CommandDispatcher
from app.infrastructure.commands.setup import build_registry


def test_dispatch_routes_alias_to_find_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = dispatcher.dispatch("search", {"query": "milk"}, "user1")

    assert command is not None
    assert command.name == "find"
    assert response == "[OK] Searching for: 'milk' (limit: 10)"


def test_dispatch_routes_alias_to_status_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = dispatcher.dispatch("health", {}, "user1")

    assert command is not None
    assert command.name == "status"
    assert response == "[OK] System is running. Version: 0.3.0"
