"""
Command System Demo - Production-Grade Architecture

This demonstrates the refactored command system that follows:
- Clean Architecture principles
- Plugin-based registry (no if-else)
- Structured argument parsing
- Domain-driven command definitions
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.infrastructure.commands import get_command_registry
from app.domain.services.command_parser import CommandParser
from app.application.services.command_dispatcher import CommandDispatcher


def demo():
    """Run interactive command system demo."""
    
    # Initialize components
    registry = get_command_registry()
    dispatcher = CommandDispatcher(registry)
    
    print("\n" + "=" * 70)
    print("PRODUCTION-GRADE COMMAND SYSTEM DEMO")
    print("=" * 70)
    
    # 1. Show all registered commands
    print("\n1. REGISTRY CONTENTS:")
    print(f"   Total commands: {len(registry.all())}")
    
    for category in sorted(set(cmd.category for cmd in registry.all())):
        commands = registry.by_category(category)
        print(f"\n   {category.upper()} ({len(commands)}):")
        for cmd in sorted(commands, key=lambda c: c.name):
            print(f"     - {cmd.name:12} | {cmd.usage:30} | {cmd.description}")
    
    # 2. Test command parsing with structured arguments
    print("\n\n2. COMMAND PARSING (Structured Arguments):")
    test_inputs = [
        "/help",
        "/find milk",
        "/find milk --limit=5",
        "/status",
        "/clear confirm",
    ]
    
    for text in test_inputs:
        cmd_name, args = CommandParser.parse(text)
        print(f"\n   Input:  {text}")
        print(f"   Output: command='{cmd_name}', args={args}")
    
    # 3. End-to-end execution
    print("\n\n3. END-TO-END EXECUTION (Parse -> Dispatch -> Handle):")
    test_commands = [
        "/help",
        "/find pizza --limit=20",
        "/status",
        "/delete 123",
    ]
    
    for text in test_commands:
        cmd_name, args = CommandParser.parse(text)
        command, response = dispatcher.dispatch(cmd_name, args, "alice@example.com")
        
        print(f"\n   Input:    {text}")
        print(f"   Matched:  {command.name if command else 'NONE'}")
        print(f"   Response: {response}")
    
    # 4. Show how to add a new command
    print("\n\n4. HOW TO ADD A NEW COMMAND:")
    print("""
   Step 1: Create handler in app/infrastructure/commands/handlers/
   
       def handle_echo(args: dict, user_id: str) -> str:
           msg = args.get("query", "")
           return f"[OK] Echo: {msg}"
   
   Step 2: Register in app/infrastructure/commands/setup.py
   
       registry.register(Command(
           name="echo",
           description="Echo your message",
           usage="/echo <message>",
           category="system",
           args_schema=None,
           handler=handle_echo,
       ))
   
   That's it! No need to touch UseCase or any if-else branching.
    """)
    
    # 5. Show registry-driven benefits
    print("\n5. KEY BENEFITS OF THIS DESIGN:")
    print("""
   ✓ Open/Closed Principle: Add commands without modifying existing code
   ✓ No if-else branching: Using registry pattern instead
   ✓ Structured arguments: Parsing with shlex (supports --flag=value format)
   ✓ Clean separation: Handlers, Parser, Dispatcher, UseCase are separate
   ✓ Scalable: Easy to add middleware, validation, permissions later
   ✓ Testable: Each component can be tested independently
   ✓ Type-safe: Args have schema with validation
    """)
    
    print("\n" + "=" * 70)
    print("END OF DEMO")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo()
