"""Command dispatcher for routing and execution."""

import inspect

from loguru import logger

from app.domain.entities.command_context import CommandContext
from app.infrastructure.commands.registry import CommandRegistry


class CommandDispatcher:
    """
    Dispatch commands to their handlers.

    Eliminates if-else branching and provides registry-driven execution.
    Supports context-aware handlers for commands that need messenger access.
    """

    def __init__(self, registry: CommandRegistry):
        """
        Initialize dispatcher.

        Args:
            registry (CommandRegistry): Command registry.
        """
        self.registry = registry

    async def dispatch(
        self,
        command_name: str,
        args: dict,
        user_id: str,
        chat_id: str = "",
        messenger=None,
    ) -> tuple:
        """
        Dispatch command to its handler.

        Args:
            command_name (str): Command name.
            args (dict): Parsed arguments.
            user_id (str): User identifier.
            chat_id (str): Chat identifier (for context-aware commands).
            messenger: Messenger instance (for context-aware commands).

        Returns:
            tuple: (command, response) or (None, None) if not found.
        """
        command = self.registry.get(command_name)

        if not command:
            logger.warning(
                "command_not_found",
                extra={"command": command_name},
            )
            return None, None

        # Validate args if schema exists
        if command.args_schema:
            is_valid, error = command.validate_args(args)
            if not is_valid:
                logger.warning(
                    "args_validation_failed",
                    extra={
                        "command": command_name,
                        "error": error,
                    },
                )
                return command, f"[ERROR] {error}"

        try:
            if command.requires_context:
                context = CommandContext(
                    args=args,
                    user_id=user_id,
                    chat_id=chat_id,
                    messenger=messenger,
                )
                response = command.handler(context)
            else:
                response = command.handler(args, user_id)

            if inspect.isawaitable(response):
                response = await response
            logger.info(
                "command_executed",
                extra={
                    "command": command_name,
                    "user_id": user_id,
                },
            )
            return command, response
        except Exception as e:
            logger.error(
                "command_execution_failed",
                extra={
                    "command": command_name,
                    "error": str(e),
                },
            )
            return command, f"[ERROR] Command execution failed: {str(e)}"

