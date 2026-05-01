"""System command handlers."""


def build_help_handler(registry):
    """
    Build a help handler bound to a registry.

    Args:
        registry: Command registry used for introspection.
    """

    def handle_help(args: dict, user_id: str) -> str:
        """List commands or show details for a specific command."""
        command_name = args.get("query")

        if command_name:
            command = registry.get(command_name)

            if not command:
                return f"[ERROR] Command '{command_name}' not found"

            aliases = f"\nAliases: {', '.join(f'/{alias}' for alias in command.aliases)}" if command.aliases else ""
            examples = ""
            if command.examples:
                example_lines = "\n".join(f"• `{example}`" for example in command.examples)
                examples = f"\n*Examples:*\n{example_lines}"
            return (
                "*Command Details*\n\n"
                f"*Name:* `/{command.name}`\n"
                f"*Category:* `{command.category}`\n"
                f"*Description:* {command.description}\n"
                f"*Usage:* `{command.usage}`"
                f"{aliases}"
                f"{examples}"
            )

        commands_by_category = {}
        for command in registry.visible():
            commands_by_category.setdefault(command.category, []).append(command)

        lines = ["*Available Commands*", ""]

        for category in sorted(commands_by_category.keys()):
            lines.append(f"*{category.upper()}*")
            for command in sorted(commands_by_category[category], key=lambda item: item.name):
                alias_text = (
                    f" _(aliases: {', '.join(f'/{alias}' for alias in command.aliases)})_"
                    if command.aliases
                    else ""
                )
                lines.append(f"`/{command.name}` - {command.description}{alias_text}")
            lines.append("")

        lines.append("Use `/help <command>` for details")
        return "\n".join(lines)

    return handle_help


def handle_status(args: dict, user_id: str) -> str:
    """System health check."""
    return "[OK] System is running. Version: 0.3.0"


def handle_ping(args: dict, user_id: str) -> str:
    """Ping test for latency."""
    return "[OK] pong"


def handle_start(args: dict, user_id: str) -> str:
    """Onboarding command."""
    return f"[OK] Welcome {user_id}! Use /help to see available commands."


def handle_whoami(args: dict, user_id: str) -> str:
    """Show user context (debug)."""
    return f"[OK] You are: {user_id}"


def handle_version(args: dict, user_id: str) -> str:
    """Show system version."""
    return "[OK] Minora v0.3.0 - Message Receiver System"
