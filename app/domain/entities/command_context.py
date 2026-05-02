"""Command context for context-aware command handlers."""

from dataclasses import dataclass
from typing import Any


@dataclass
class CommandContext:
    """
    Extended context passed to commands that need access to messenger and chat.

    Used by commands like /import that need to send async follow-up messages.

    Attributes:
        args (dict): Parsed command arguments.
        user_id (str): User who issued the command.
        chat_id (str): Chat where command was issued.
        messenger (Any): Messenger interface for sending replies.
    """

    args: dict
    user_id: str
    chat_id: str
    messenger: Any = None
