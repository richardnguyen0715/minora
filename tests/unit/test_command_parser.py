"""Tests for command parsing and handling."""

import pytest

from app.domain.entities.command import Command
from app.domain.services.command_parser import CommandParser


class TestCommandEntity:
    """Test Command domain entity."""

    def test_command_creation(self):
        """Test creating a command."""
        def handler(args, user_id):
            return "[OK] Help"
        
        cmd = Command(
            name="help",
            description="Show help",
            usage="/help",
            category="system",
            args_schema=None,
            handler=handler,
        )

        assert cmd.name == "help"
        assert cmd.description == "Show help"
        assert cmd.category == "system"
        assert cmd.handler is not None

    def test_command_validation_no_schema(self):
        """Test validation with no schema."""
        def handler(args, user_id):
            return "[OK]"
        
        cmd = Command(
            name="status",
            description="Status check",
            usage="/status",
            category="system",
            args_schema=None,
            handler=handler,
        )

        is_valid, error = cmd.validate_args({})
        assert is_valid
        assert error is None

    def test_command_validation_with_schema(self):
        """Test validation with args schema."""
        def handler(args, user_id):
            return "[OK]"
        
        cmd = Command(
            name="find",
            description="Search",
            usage="/find <query>",
            category="search",
            args_schema={"query": str},
            handler=handler,
        )

        # Valid args
        is_valid, error = cmd.validate_args({"query": "milk"})
        assert is_valid
        assert error is None

        # Missing required arg
        is_valid, error = cmd.validate_args({})
        assert not is_valid
        assert "query" in error

        # Wrong type
        is_valid, error = cmd.validate_args({"query": 123})
        assert not is_valid


class TestCommandParser:
    """Test CommandParser service."""

    def test_is_command_true(self):
        """Test recognizing commands."""
        assert CommandParser.is_command("/help")
        assert CommandParser.is_command("/ help")
        assert CommandParser.is_command("/find query")

    def test_is_command_false(self):
        """Test recognizing non-commands."""
        assert not CommandParser.is_command("help")
        assert not CommandParser.is_command("regular text")
        assert not CommandParser.is_command("")
        assert not CommandParser.is_command(None)

    def test_parse_simple_command(self):
        """Test parsing simple command without args."""
        cmd, args = CommandParser.parse("/help")
        assert cmd == "help"
        assert args == {}

    def test_parse_command_with_query(self):
        """Test parsing command with positional argument."""
        cmd, args = CommandParser.parse("/find milk")
        assert cmd == "find"
        assert args == {"query": "milk"}

        cmd, args = CommandParser.parse("/find organic milk")
        assert cmd == "find"
        assert args == {"query": "organic milk"}

    def test_parse_command_with_flags(self):
        """Test parsing command with flags."""
        cmd, args = CommandParser.parse("/find milk --limit=10")
        assert cmd == "find"
        assert args == {"query": "milk", "limit": "10"}

        cmd, args = CommandParser.parse("/status --verbose")
        assert cmd == "status"
        assert args == {"verbose": True}

    def test_parse_non_command(self):
        """Test parsing non-command text."""
        cmd, args = CommandParser.parse("regular text")
        assert cmd == ""
        assert args == {}

    def test_parse_invalid_command(self):
        """Test parsing various command formats."""
        cmd, args = CommandParser.parse("/")
        assert cmd == ""
        assert args == {}
