"""Service for parsing commands with structured arguments."""

import shlex
from loguru import logger


class CommandParser:
    """Parse command text into structured (command_name, args_dict)."""

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
    def parse(text: str) -> tuple[str, dict]:
        """
        Parse command text into (command_name, args_dict).
        
        Supports:
        - /help
        - /find milk
        - /find milk --limit=10
        - /update key value
        
        Args:
            text (str): Raw command text.
            
        Returns:
            tuple[str, dict]: (command_name, args_dict)
            
        Example:
            >>> parse("/find milk --limit=10")
            ("find", {"query": "milk", "limit": "10"})
            >>> parse("/status")
            ("status", {})
        """
        if not CommandParser.is_command(text):
            return "", {}

        # Remove leading slash and parse tokens
        text = text.lstrip("/").strip()
        
        if not text:
            return "", {}

        try:
            tokens = shlex.split(text)
        except ValueError:
            logger.warning("Failed to parse command tokens", extra={"text": text})
            return "", {}

        if not tokens:
            return "", {}

        command = tokens[0]
        args = {}
        positional = []

        # Parse remaining tokens
        for token in tokens[1:]:
            if token.startswith("--"):
                # Flag format: --key=value or --key
                flag = token[2:]
                if "=" in flag:
                    key, value = flag.split("=", 1)
                    args[key] = value
                else:
                    args[flag] = True
            elif token.startswith("-"):
                # Short flag format: -k value
                key = token[1:]
                args[key] = True
            else:
                # Positional argument
                positional.append(token)

        # Store positional args as "query"
        if positional:
            args["query"] = " ".join(positional)

        logger.debug(
            "command_parsed",
            extra={
                "command": command,
                "args": args,
            },
        )

        return command, args
