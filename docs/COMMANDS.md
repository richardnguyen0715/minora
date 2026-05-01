# Command System Documentation

## Overview

The bot now supports a **configuration-driven command system** that allows users to execute commands like `/help`, `/find`, `/update`, etc.

### Key Features

✅ **Configuration-Driven**: Commands defined in `configs/commands.yaml`
✅ **Short Aliases**: Every command has short versions (e.g., `/h` for `/help`)
✅ **Concept Level**: Commands acknowledge receipt and indicate what would be done
✅ **Easy to Extend**: Add new commands by updating YAML
✅ **Automatic Routing**: Messages starting with `/` are routed to command handler

---

## Available Commands

### Built-in Commands

| Command | Aliases | Usage | Description |
|---------|---------|-------|-------------|
| `/help` | `/h`, `/?` | `/help` | Show all available commands |
| `/update` | `/u`, `/upd` | `/update <args>` | Update or modify something |
| `/find` | `/f`, `/search` | `/find <query>` | Search for something |
| `/status` | `/s`, `/info` | `/status` | Show bot status and statistics |
| `/list` | `/ls`, `/l` | `/list` | List saved links or data |
| `/delete` | `/del`, `/d`, `/rm` | `/delete <id>` | Delete a saved link |
| `/settings` | `/config`, `/cfg` | `/settings` | Show or modify settings |
| `/export` | `/exp`, `/save` | `/export` | Export saved data |
| `/import` | `/imp`, `/load` | `/import <data>` | Import data |
| `/clear` | `/clr`, `/reset` | `/clear` | Clear data or cache |

### Example Usage

```
User: /help
Bot: 📋 **Available Commands:**
     • /help /h /?
       Show all available commands
     • /update /u /upd
       Update or modify something
     ...

User: /find my link
Bot: ✓ Find command received with query: my link
     Searching...

User: /u data to update
Bot: ✓ Update command received with args: data to update
     Processing your request...
```

---

## Architecture

### Components

```
Message Received
    ↓
CommandParser.is_command()  (Check if starts with /)
    ↓
    ├─ YES → CommandParser.find_matching_command()
    │         ↓
    │         CommandRegistry.get_command()
    │         ↓
    │         HandleCommandUseCase.execute()
    │         ↓
    │         Send response
    │
    └─ NO → Handle as regular message (links, etc.)
```

### Key Classes

1. **Command** (`app/domain/entities/command.py`)
   - Represents a single command
   - Properties: name, command, aliases, description, usage, response_template
   - Methods: matches(), format_response()

2. **CommandParser** (`app/domain/services/command_parser.py`)
   - Parses messages to extract commands
   - Methods: is_command(), extract_command(), find_matching_command()

3. **CommandRegistry** (`app/infrastructure/commands/registry.py`)
   - Loads commands from YAML configuration
   - Provides command lookup and formatting
   - Methods: get_command(), get_all_commands(), format_help_message()

4. **HandleCommandUseCase** (`app/application/use_cases/handle_command.py`)
   - Executes command logic
   - Concept level: acknowledges receipt and simulates processing
   - Methods: execute(), _handle_help(), _handle_update(), etc.

---

## Configuration

### Command Config File: `configs/commands.yaml`

```yaml
commands:
  - name: "Help"                    # Display name
    command: "help"                 # Main command (without slash)
    aliases: ["h", "?"]             # Short versions
    description: "Show all commands"
    usage: "/help or /h"
    response_template: "..."        # Response with {placeholders}

  - name: "Find"
    command: "find"
    aliases: ["f", "search"]
    description: "Search for something"
    usage: "/find <query> or /f <query>"
    response_template: "✓ Find command received with query: {args}\nSearching..."
```

### Template Variables

Available variables for response templates:

| Variable | Description |
|----------|-------------|
| `{args}` | Command arguments passed by user |
| `{user}` | User identifier |
| `{timestamp}` | Current timestamp |
| `{link_count}` | Number of saved links (if implemented) |
| `{settings_info}` | Settings information (if implemented) |
| `{command_list}` | Formatted list of all commands (for help) |

---

## Adding New Commands

### Method 1: Edit YAML Configuration

1. Open `configs/commands.yaml`
2. Add a new command entry:

```yaml
  - name: "MyCommand"
    command: "mycommand"
    aliases: ["mc", "my"]
    description: "What this command does"
    usage: "/mycommand or /mc"
    response_template: "✓ MyCommand received with args: {args}"
```

3. Restart the bot - it will automatically load the new command

### Method 2: Implement Custom Logic

1. Add command to YAML (see Method 1)
2. Add handler method in `HandleCommandUseCase`:

```python
def _handle_mycommand(self, args: str) -> str:
    """Custom logic for mycommand."""
    # Your implementation here
    return f"Processing {args}..."
```

3. Add case in `execute()` method:

```python
elif command.command == "mycommand":
    response = self._handle_mycommand(args)
```

---

## Usage Examples

### User: Request Help

```
User: /help
Bot: 📋 **Available Commands:**
     • /help /h /?
       Show all available commands
     • /update /u /upd
       Update or modify something
     ...
```

### User: Execute Command with Arguments

```
User: /find my important link
Bot: ✓ Find command received with query: my important link
     Searching...
```

### User: Execute Short Alias

```
User: /u new data
Bot: ✓ Update command received with args: new data
     Processing your request...
```

### User: Check Status

```
User: /status
Bot: 🤖 Bot Status:
     - Active: ✓
     - Ready to receive commands
     - Version: 0.3.0
```

---

## Implementation Status

### Current (Concept Level)

- ✅ Command parsing and matching
- ✅ Alias support
- ✅ Configuration file loading
- ✅ Help message generation
- ✅ Command acknowledgement responses
- ✅ Automatic routing from HandleMessageUseCase

### Future Implementation

- 🔲 Search functionality (/find)
- 🔲 Update/modify operations (/update)
- 🔲 Data export (/export)
- 🔲 Data import (/import)
- 🔲 Database clearing (/clear)
- 🔲 Settings management (/settings)
- 🔲 Link management (/list, /delete)

---

## Extending Commands

### To Customize Response Templates

Edit `configs/commands.yaml`:

```yaml
  - name: "Find"
    command: "find"
    aliases: ["f"]
    description: "Search for something"
    usage: "/find <query>"
    response_template: "🔍 Searching for: {args}...\nThis will find all matches."
```

### To Add New Command with Logic

1. Add to YAML:

```yaml
  - name: "Stats"
    command: "stats"
    aliases: ["st"]
    description: "Show statistics"
    usage: "/stats"
    response_template: "📊 Statistics loaded"
```

2. Implement in `HandleCommandUseCase`:

```python
async def execute(self, ...):
    ...
    elif command.command == "stats":
        response = self._handle_stats()
    ...

def _handle_stats(self) -> str:
    # Your custom logic here
    return "📊 Your statistics:\n- Links: 42\n- Commands: 123"
```

---

## Testing

### Run Command Parser Tests

```bash
python -m pytest tests/unit/test_command_parser.py -xvs
```

### All Tests

```bash
python -m pytest tests/ -q
```

---

## Integration with Message Handling

Commands are integrated into the main `HandleMessageUseCase`:

```python
# In HandleMessageUseCase.execute():
if message.text and CommandParser.is_command(message.text):
    # Handle command
    await self.command_use_case.execute(...)
else:
    # Handle as regular message (links, etc.)
```

This means:
- **Messages starting with `/`** → Handled by command system
- **Messages without `/`** → Normal message processing (link detection, etc.)

---

## Configuration Reload

To reload commands from YAML without restarting:

```python
from app.infrastructure.commands.registry import get_command_registry

registry = get_command_registry()
registry.reload()  # Reloads from configs/commands.yaml
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Command not recognized | Check spelling and YAML indentation |
| Response template not working | Verify variable names (case-sensitive) |
| Command not appearing in /help | Check YAML syntax and reload |
| Bot not responding to commands | Check LOG_LEVEL=DEBUG for details |

---

## File Structure

```
configs/
  └─ commands.yaml              # Command configuration

app/
  ├─ domain/
  │  ├─ entities/
  │  │  └─ command.py            # Command entity
  │  └─ services/
  │     └─ command_parser.py      # Parsing logic
  ├─ infrastructure/
  │  └─ commands/
  │     └─ registry.py            # YAML loader & registry
  └─ application/
     └─ use_cases/
        └─ handle_command.py      # Command execution

tests/
  └─ unit/
     └─ test_command_parser.py    # Tests
```

---

## Version

- **Version**: 0.3.0
- **Status**: Concept Complete
- **Commands**: 10 built-in commands
- **Aliases**: 20+ short versions
- **Test Coverage**: 9 unit tests
