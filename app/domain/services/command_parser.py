"""Service for parsing and executing commands."""

from typing import Optional
from loguru import logger

from app.domain.entities.command import Command


class CommandParser:
    """Parse and extract commands from text messages."""

    @staticmethod
    def is_command(text: str) -> bool:
        """
        Check if text is a command (starts with /).

        Args:
            text (str): Message text.

        Returns:
            bool: True if text starts with /.
        """
        return text.strip().startswith("/") if text else False

    @staticmethod
    def extract_command(text: str) -> Optional[tuple[str, str]]:
        """
        Extract command and arguments from text.

        Args:
            text (str): Message text (e.g., "/help" or "/find query").

        Returns:
            Optional[tuple[str, str]]: Tuple of (command, args) or None if invalid.

        Example:
            >>> extract_command("/help")
            ("help", "")
            >>> extract_command("/find test query")
            ("find", "test query")
        """
        if not CommandParser.is_command(text):
            return None

        # Remove leading slash and strip whitespace
        text = text.lstrip("/").strip()

        # Split into command and args
        parts = text.split(maxsplit=1)
        command = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        return (command, args)

    @staticmethod
    def find_matching_command(
        text: str,
        commands: list[Command],
    ) -> Optional[tuple[Command, str]]:
        """
        Find matching command from list of commands.

        Args:
            text (str): Message text (e.g., "/help").
            commands (list[Command]): Available commands.

        Returns:
            Optional[tuple[Command, str]]: Tuple of (command, args) or None.
        """
        extracted = CommandParser.extract_command(text)
        if not extracted:
            return None

        command_text, args = extracted

        # Find matching command
        for command in commands:
            if command.matches(command_text):
                logger.debug(
                    "Command matched",
                    extra={
                        "command": command.command,
                        "text": command_text,
                        "args": args,
                    },
                )
                return (command, args)

        logger.debug(
            "No command matched",
            extra={"text": command_text},
        )
        return None
