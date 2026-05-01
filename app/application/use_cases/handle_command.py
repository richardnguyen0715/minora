"""Use case for handling command execution."""

from loguru import logger

from app.application.interfaces.messenger import Messenger
from app.domain.entities.command import Command
from app.domain.services.command_parser import CommandParser
from app.infrastructure.commands.registry import get_command_registry


class HandleCommandUseCase:
    """
    Execute command logic.

    Handles command parsing, registry lookup, and response generation.
    At concept level - just acknowledges commands received.
    """

    def __init__(self, messenger: Messenger):
        """
        Initialize the use case.

        Args:
            messenger (Messenger): Messenger for sending responses.
        """
        self.messenger = messenger
        self.registry = get_command_registry()

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
            dict: Command execution result with keys:
                - executed (bool): Whether command was found and executed.
                - command_name (str): Name of executed command.
                - response (str): Response message.
        """
        logger.info(
            "Processing command",
            extra={
                "chat_id": chat_id,
                "user_id": user_id,
                "text": text,
            },
        )

        # Parse command
        match = CommandParser.find_matching_command(text, self.registry.get_all_commands())

        if not match:
            logger.debug(
                "No command matched in text",
                extra={"text": text},
            )
            return {
                "executed": False,
                "command_name": None,
                "response": None,
            }

        command, args = match

        logger.info(
            "Command matched",
            extra={
                "command": command.command,
                "args": args,
            },
        )

        # Generate response (concept level - just acknowledge)
        if command.command == "help":
            response = self._handle_help()
        elif command.command == "update":
            response = self._handle_update(args)
        elif command.command == "find":
            response = self._handle_find(args)
        elif command.command == "status":
            response = self._handle_status()
        elif command.command == "list":
            response = self._handle_list()
        elif command.command == "delete":
            response = self._handle_delete(args)
        elif command.command == "settings":
            response = self._handle_settings()
        elif command.command == "export":
            response = self._handle_export()
        elif command.command == "import":
            response = self._handle_import(args)
        elif command.command == "clear":
            response = self._handle_clear(args)
        else:
            # Fallback - use template
            response = command.format_response(args=args, user=user_id)

        # Send response
        try:
            await self.messenger.send(chat_id, response)
            logger.info(
                "Command executed successfully",
                extra={
                    "command": command.command,
                    "chat_id": chat_id,
                },
            )
        except Exception as e:
            logger.error(
                "Failed to send command response",
                extra={
                    "command": command.command,
                    "error": str(e),
                },
            )

        return {
            "executed": True,
            "command_name": command.command,
            "response": response,
        }

    def _handle_help(self) -> str:
        """Generate help response."""
        return self.registry.format_help_message()

    def _handle_update(self, args: str) -> str:
        """Generate update command response."""
        return f"✓ Update command received with args: {args}\nProcessing your request..."

    def _handle_find(self, args: str) -> str:
        """Generate find command response."""
        return f"✓ Find command received with query: {args}\nSearching..."

    def _handle_status(self) -> str:
        """Generate status command response."""
        return "🤖 Bot Status:\n- Active: ✓\n- Ready to receive commands\n- Version: 0.3.0"

    def _handle_list(self) -> str:
        """Generate list command response."""
        return "✓ List command received\nRetrieving your saved items..."

    def _handle_delete(self, args: str) -> str:
        """Generate delete command response."""
        return f"✓ Delete command received for: {args}\nDeleting..."

    def _handle_settings(self) -> str:
        """Generate settings command response."""
        return "⚙️ Settings:\n- Polling mode: Enabled\n- Auto-save: On\n- Notifications: On"

    def _handle_export(self) -> str:
        """Generate export command response."""
        return "✓ Export command received\nPreparing your data export..."

    def _handle_import(self, args: str) -> str:
        """Generate import command response."""
        return f"✓ Import command received\nProcessing your import data..."

    def _handle_clear(self, args: str) -> str:
        """Generate clear command response."""
        if "confirm" in args.lower():
            return "⚠️ Data cleared successfully!"
        return "⚠️ Clear command received\nThis will clear data. Use /clear confirm to proceed."
