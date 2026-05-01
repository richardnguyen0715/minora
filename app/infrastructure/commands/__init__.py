"""Commands infrastructure module."""

from app.infrastructure.commands.setup import get_command_registry
from app.infrastructure.commands.registry import CommandRegistry

__all__ = ["get_command_registry", "CommandRegistry"]
