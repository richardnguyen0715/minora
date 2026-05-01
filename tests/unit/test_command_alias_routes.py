"""Tests for alias-based command routing."""

import pytest

from app.application.services.command_dispatcher import CommandDispatcher
from app.infrastructure.commands.setup import build_registry


@pytest.mark.asyncio
async def test_dispatch_routes_alias_to_find_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = await dispatcher.dispatch("search", {"query": "milk"}, "user1")

    assert command is not None
    assert command.name == "find"
    assert isinstance(response, str)
    assert "knowledge" in response.lower() or "warn" in response.lower()


@pytest.mark.asyncio
async def test_dispatch_routes_alias_to_status_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = await dispatcher.dispatch("health", {}, "user1")

    assert command is not None
    assert command.name == "status"
    assert response == "[OK] System is running. Version: 0.3.0"


@pytest.mark.asyncio
async def test_dispatch_routes_alias_to_read_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = await dispatcher.dispatch("get", {"query": "concept_llm"}, "user1")

    assert command is not None
    assert command.name == "read"
    assert (
        "Knowledge item: concept_llm" in response
        or "not found" in response.lower()
        or "not ready" in response.lower()
    )


@pytest.mark.asyncio
async def test_dispatch_routes_alias_to_visualize_command():
    registry = build_registry()
    dispatcher = CommandDispatcher(registry)

    command, response = await dispatcher.dispatch("inspect", {}, "user1")

    assert command is not None
    assert command.name == "visualize"
    assert (
        "Knowledge database overview" in response
        or "No knowledge items available" in response
        or "not ready" in response.lower()
    )
