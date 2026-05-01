"""Command domain model."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Command:
    """
    Represents a Telegram bot command.

    Attributes:
        name (str): Display name of the command (e.g., "Help").
        command (str): Full command name (e.g., "help").
        aliases (list[str]): Short versions (e.g., ["h", "?"]).
        description (str): What this command does.
        usage (str): How to use it (e.g., "/help or /h").
        response_template (str): Response message template.
    """

    name: str
    command: str
    aliases: list[str]
    description: str
    usage: str
    response_template: str

    @property
    def all_versions(self) -> list[str]:
        """Get all versions of this command (main + aliases)."""
        return [self.command] + self.aliases

    def matches(self, text: str) -> bool:
        """
        Check if a command text matches this command.

        Args:
            text (str): Command text (without leading slash).

        Returns:
            bool: True if text matches this command or any alias.
        """
        return text.lower() in [v.lower() for v in self.all_versions]

    def format_response(
        self,
        args: str = "",
        user: str = "User",
        timestamp: str = "",
        link_count: int = 0,
        settings_info: str = "",
        command_list: str = "",
    ) -> str:
        """
        Format the response template with actual values.

        Args:
            args (str): Command arguments.
            user (str): Username or user identifier.
            timestamp (str): Current timestamp.
            link_count (int): Number of saved links.
            settings_info (str): Settings information.
            command_list (str): List of commands for help.

        Returns:
            str: Formatted response message.
        """
        return self.response_template.format(
            args=args,
            user=user,
            timestamp=timestamp,
            link_count=link_count,
            settings_info=settings_info,
            command_list=command_list,
        )
