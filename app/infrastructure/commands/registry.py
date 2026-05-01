"""Command registry that loads commands from configuration."""

import os
from typing import Optional

import yaml
from loguru import logger

from app.domain.entities.command import Command


class CommandRegistry:
    """
    Registry for managing available commands.

    Loads commands from YAML configuration file and provides
    lookup and formatting capabilities.
    """

    def __init__(self, config_path: str = "configs/commands.yaml"):
        """
        Initialize the registry with commands from config file.

        Args:
            config_path (str): Path to commands.yaml configuration file.
        """
        self.commands: list[Command] = []
        self.config_path = config_path
        self.load_commands()

    def load_commands(self) -> None:
        """Load commands from YAML configuration file."""
        if not os.path.exists(self.config_path):
            logger.warning(
                f"Commands config file not found: {self.config_path}",
            )
            return

        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            if not config or "commands" not in config:
                logger.warning("No commands found in config")
                return

            for cmd_config in config["commands"]:
                try:
                    command = Command(
                        name=cmd_config.get("name", ""),
                        command=cmd_config.get("command", ""),
                        aliases=cmd_config.get("aliases", []),
                        description=cmd_config.get("description", ""),
                        usage=cmd_config.get("usage", ""),
                        response_template=cmd_config.get("response_template", ""),
                    )
                    self.commands.append(command)

                    logger.debug(
                        f"Loaded command: {command.command}",
                        extra={
                            "name": command.name,
                            "aliases": command.aliases,
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to load command from config",
                        extra={"error": str(e), "config": cmd_config},
                    )

            logger.info(
                f"Loaded {len(self.commands)} commands from config",
                extra={"config_path": self.config_path},
            )

        except Exception as e:
            logger.error(
                f"Failed to load commands configuration",
                extra={"error": str(e), "config_path": self.config_path},
            )

    def get_command(self, text: str) -> Optional[Command]:
        """
        Get command by text (matches command or aliases).

        Args:
            text (str): Command text (without slash, e.g., "help" or "h").

        Returns:
            Optional[Command]: Matching command or None.
        """
        text_lower = text.lower()
        for command in self.commands:
            if command.matches(text_lower):
                return command
        return None

    def get_all_commands(self) -> list[Command]:
        """
        Get all registered commands.

        Returns:
            list[Command]: List of all commands.
        """
        return self.commands

    def format_help_message(self) -> str:
        """
        Format help message with all commands.

        Returns:
            str: Formatted help message.
        """
        if not self.commands:
            return "No commands available."

        lines = ["📋 **Available Commands:**\n"]

        for cmd in self.commands:
            # Format: /command (aliases) - description
            aliases_str = f"/{'/'.join(cmd.aliases)}" if cmd.aliases else ""
            line = f"• /{cmd.command} {aliases_str}\n  {cmd.description}"
            lines.append(line)

        return "\n".join(lines)

    def reload(self) -> None:
        """Reload commands from configuration file."""
        self.commands = []
        self.load_commands()
        logger.info("Commands reloaded")


# Global registry instance
_registry: Optional[CommandRegistry] = None


def get_command_registry() -> CommandRegistry:
    """Get or create the global command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
    return _registry
