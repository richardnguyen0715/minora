"""Use case for handling command execution (clean, registry-driven)."""

from loguru import logger

from app.application.interfaces.messenger import Messenger
from app.application.services.command_dispatcher import CommandDispatcher
from app.domain.services.command_parser import CommandParser
from app.infrastructure.commands.setup import get_command_registry


class HandleCommandUseCase:
    """
    Execute commands with clean, registry-driven architecture.
    
    Responsibilities:
    - Parse command text
    - Dispatch to handler
    - Send response
    - Log execution
    
    No if-else branching or command-specific logic.
    """

    def __init__(self, messenger: Messenger):
        """
        Initialize the use case.

        Args:
            messenger (Messenger): Messenger for sending responses.
        """
        self.messenger = messenger
        registry = get_command_registry()
        self.dispatcher = CommandDispatcher(registry)

    async def execute(
        self,
        chat_id: str,
        text: str,
        user_id: str = "User",
    ) -> dict:
        """
        Execute a command.

        Args:
            chat_id (str): Telegram chat ID.
            text (str): Message text containing command.
            user_id (str): User identifier.

        Returns:
            dict: Execution result with keys:
                - executed (bool): Whether command was found and executed.
                - command_name (str): Name of executed command or None.
                - response (str): Response message or None.
        """
        # Parse command text into structured format
        command_name, args = CommandParser.parse(text)

        logger.info(
            "command_received",
            extra={
                "command": command_name,
                "args": args,
                "chat_id": chat_id,
                "user_id": user_id,
            },
        )

        # Dispatch to handler (registry-driven, no if-else)
        command, response = await self.dispatcher.dispatch(
            command_name, args, user_id,
            chat_id=chat_id, messenger=self.messenger,
        )

        if not command:
            logger.debug(
                "command_not_found",
                extra={"command": command_name},
            )
            return {
                "executed": False,
                "command_name": None,
                "response": None,
            }

        # Send response
        try:
            parse_mode = "Markdown" if command.name == "help" else None
            await self.messenger.send(chat_id, response, parse_mode=parse_mode)
            logger.info(
                "command_response_sent",
                extra={
                    "command": command.name,
                    "chat_id": chat_id,
                    "user_id": user_id,
                },
            )
        except Exception as e:
            logger.error(
                "send_response_failed",
                extra={
                    "command": command.name,
                    "chat_id": chat_id,
                    "error": str(e),
                },
            )
            return {
                "executed": True,
                "command_name": command.name,
                "response": None,  # Response failed to send
            }

        return {
            "executed": True,
            "command_name": command.name,
            "response": response,
        }
