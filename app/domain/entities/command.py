"""Command domain model following production-grade design."""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Command:
    """
    Production-grade command contract.
    
    Represents a bot command with structured semantics, validation, and execution.
    
    Attributes:
        name (str): Unique command name (e.g., "find").
        description (str): Human-readable description.
        usage (str): Usage example (e.g., "/find <query>").
        examples (list[str]): Example invocations shown in help output.
        category (str): Command category (system|data|search|config|admin).
        aliases (list[str]): Alternate command names.
        args_schema (dict[str, type] | None): Arguments validation schema.
        is_visible (bool): Whether the command should appear in help output.
        handler (Callable): Handler function signature: (args: dict, user_id: str) -> str
    """

    name: str
    description: str
    usage: str
    category: str
    handler: Callable[[dict[str, Any], str], str]
    examples: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    args_schema: dict[str, type] | None = None
    is_visible: bool = True

    def validate_args(self, args: dict) -> tuple[bool, str | None]:
        """
        Validate arguments against schema.
        
        Args:
            args (dict): Arguments to validate.
            
        Returns:
            tuple[bool, str | None]: (is_valid, error_message)
        """
        if self.args_schema is None:
            return True, None
        
        for key, expected_type in self.args_schema.items():
            if key not in args:
                return False, f"Missing required argument: {key}"
            
            if not isinstance(args[key], expected_type):
                return False, f"Invalid type for {key}: expected {expected_type.__name__}"
        
        return True, None
