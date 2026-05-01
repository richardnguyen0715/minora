"""Tests for command parsing and handling."""

import pytest

from app.domain.entities.command import Command
from app.domain.services.command_parser import CommandParser


class TestCommandEntity:
    """Test Command domain entity."""

    def test_command_creation(self):
        """Test creating a command."""
        cmd = Command(
            name="Help",
            command="help",
            aliases=["h", "?"],
            description="Show help",
            usage="/help or /h",
            response_template="Here are commands:\n{command_list}",
        )

        assert cmd.name == "Help"
        assert cmd.command == "help"
        assert cmd.aliases == ["h", "?"]

    def test_command_all_versions(self):
        """Test getting all command versions."""
        cmd = Command(
            name="Help",
            command="help",
            aliases=["h", "?"],
            description="Show help",
            usage="/help or /h",
            response_template="Help",
        )

        assert cmd.all_versions == ["help", "h", "?"]

    def test_command_matches(self):
        """Test command matching."""
        cmd = Command(
            name="Help",
            command="help",
            aliases=["h", "?"],
            description="Show help",
            usage="/help or /h",
            response_template="Help",
        )

        assert cmd.matches("help")
        assert cmd.matches("h")
        assert cmd.matches("?")
        assert cmd.matches("HELP")  # Case insensitive
        assert not cmd.matches("update")

    def test_command_format_response(self):
        """Test formatting response with template."""
        cmd = Command(
            name="Update",
            command="update",
            aliases=["u"],
            description="Update",
            usage="/update <args>",
            response_template="Update received: {args}",
        )

        response = cmd.format_response(args="test data")
        assert response == "Update received: test data"


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

    def test_extract_command(self):
        """Test extracting command and arguments."""
        cmd, args = CommandParser.extract_command("/help")
        assert cmd == "help"
        assert args == ""

        cmd, args = CommandParser.extract_command("/find test query")
        assert cmd == "find"
        assert args == "test query"

        cmd, args = CommandParser.extract_command("/update arg1 arg2 arg3")
        assert cmd == "update"
        assert args == "arg1 arg2 arg3"

    def test_extract_command_none(self):
        """Test extracting command from non-command."""
        result = CommandParser.extract_command("regular text")
        assert result is None

    def test_find_matching_command(self):
        """Test finding matching command."""
        commands = [
            Command(
                name="Help",
                command="help",
                aliases=["h"],
                description="Help",
                usage="/help",
                response_template="Help",
            ),
            Command(
                name="Find",
                command="find",
                aliases=["f", "search"],
                description="Find",
                usage="/find",
                response_template="Finding",
            ),
        ]

        # Match main command
        match = CommandParser.find_matching_command("/help", commands)
        assert match is not None
        cmd, args = match
        assert cmd.command == "help"
        assert args == ""

        # Match alias
        match = CommandParser.find_matching_command("/h", commands)
        assert match is not None
        cmd, args = match
        assert cmd.command == "help"

        # Match with arguments
        match = CommandParser.find_matching_command("/find test", commands)
        assert match is not None
        cmd, args = match
        assert cmd.command == "find"
        assert args == "test"

        # No match
        match = CommandParser.find_matching_command("/unknown", commands)
        assert match is None
