"""Production-grade command registry with plugin-based architecture."""

from typing import Dict, Optional
from loguru import logger

from app.domain.entities.command import Command


class CommandRegistry:
    """
    Plugin-based command registry.
    
    Supports:
    - Dynamic command registration
    - Lookup by name
    - No if-else branching
    - Easy extension
    """

    def __init__(self):
        """Initialize empty registry."""
        self._commands: Dict[str, Command] = {}
        self._aliases: Dict[str, str] = {}

    def register(self, command: Command) -> None:
        """
        Register a command.
        
        Args:
            command (Command): Command to register.
            
        Raises:
            ValueError: If command name already registered.
        """
        if command.name in self._commands:
            raise ValueError(f"Command '{command.name}' already registered")
        
        self._commands[command.name] = command

        for alias in command.aliases:
            if alias in self._commands or alias in self._aliases:
                raise ValueError(f"Command alias '{alias}' already registered")
            self._aliases[alias] = command.name

        logger.debug(
            "command_registered",
            extra={
                "name": command.name,
                "category": command.category,
            },
        )

    def get(self, name: str) -> Optional[Command]:
        """
        Get command by name.
        
        Args:
            name (str): Command name.
            
        Returns:
            Optional[Command]: Command or None.
        """
        command = self._commands.get(name)
        if command is not None:
            return command

        alias_target = self._aliases.get(name)
        if alias_target is None:
            return None

        return self._commands.get(alias_target)

    def all(self) -> list[Command]:
        """
        Get all registered commands.
        
        Returns:
            list[Command]: List of commands.
        """
        return list(self._commands.values())

    def visible(self) -> list[Command]:
        """Get only commands marked as visible."""
        return [cmd for cmd in self._commands.values() if cmd.is_visible]

    def by_category(self, category: str) -> list[Command]:
        """
        Get commands by category.
        
        Args:
            category (str): Category name.
            
        Returns:
            list[Command]: List of commands in category.
        """
        return [cmd for cmd in self._commands.values() if cmd.category == category]

    def format_help_message(self) -> str:
        """
        Format help message with all commands.
        
        Returns:
            str: Formatted help message.
        """
        if not self._commands:
            return "[OK] No commands available."

        lines = ["[OK] Available Commands:\n"]

        # Group by category
        categories = {}
        for cmd in self._commands.values():
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)

        for category in sorted(categories.keys()):
            lines.append(f"\n{category.upper()}:")
            for cmd in sorted(categories[category], key=lambda c: c.name):
                lines.append(f"  {cmd.usage:<25} - {cmd.description}")

        return "\n".join(lines)
