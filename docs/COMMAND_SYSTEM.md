# Production-Grade Command System Refactor

## Overview

The command system has been completely refactored following clean architecture and SOLID principles. The new design eliminates if-else branching and provides plugin-based command registration.

## Architecture

### 1. **Command Domain Model** (`app/domain/entities/command.py`)

```python
@dataclass
class Command:
    name: str                          # Unique name
    description: str                   # Human-readable description
    usage: str                         # Usage example: "/find <query>"
    category: str                      # system|data|search|config|admin
    args_schema: dict[str, type] | None  # Type validation schema
    handler: Callable                  # Handler function
```

**Key features:**
- Structured semantics (not just strings)
- Args schema for validation
- Handler reference (not string templates)

### 2. **Command Parser** (`app/domain/services/command_parser.py`)

**Before:** Returns `(command, args_string)`
**After:** Returns `(command, args_dict)` with structured parsing

```python
parse("/find milk --limit=10")
# → ("find", {"query": "milk", "limit": "10"})
```

**Features:**
- Uses `shlex` for proper shell-like parsing
- Supports positional arguments (`/find milk`)
- Supports flags (`--limit=10`, `--flag`, `-k value`)
- No more string concatenation or splitting

### 3. **Command Registry** (`app/infrastructure/commands/registry.py`)

**Before:** YAML-based registry with template responses
**After:** Plugin-based registry with handler references

```python
registry.register(Command(...))
registry.get(name: str) -> Command | None
registry.all() -> list[Command]
registry.by_category(category: str) -> list[Command]
```

**No YAML needed** — commands defined in Python code.

### 4. **Command Handlers** (`app/infrastructure/commands/handlers/`)

Organized by domain:
- `system.py`: help, status, ping, start, whoami, version
- `data.py`: list, find, update, delete, clear, history
- `config.py`: settings, export, import

Each handler is a pure function:
```python
def handle_find(args: dict, user_id: str) -> str:
    query = args.get("query", "")
    limit = args.get("limit", 10)
    return f"[OK] Searching for: '{query}' (limit: {limit})"
```

### 5. **Command Dispatcher** (`app/application/services/command_dispatcher.py`)

Routes commands to handlers without if-else:

```python
dispatcher = CommandDispatcher(registry)
command, response = dispatcher.dispatch(cmd_name, args, user_id)
```

**Responsibilities:**
- Lookup command in registry
- Validate arguments
- Call handler
- Handle errors

### 6. **UseCase** (`app/application/use_cases/handle_command.py`)

Clean and focused:

```python
async def execute(self, chat_id, text, user_id):
    # 1. Parse
    cmd_name, args = CommandParser.parse(text)
    
    # 2. Dispatch
    command, response = dispatcher.dispatch(cmd_name, args, user_id)
    
    # 3. Send
    await messenger.send(chat_id, response)
    
    # That's it! No command-specific logic.
```

## Execution Flow

```
Input: "/find milk --limit=5"
    ↓
CommandParser.parse()
    ↓
(command_name="find", args={"query": "milk", "limit": "5"})
    ↓
CommandDispatcher.dispatch()
    ↓
CommandRegistry.get("find")
    ↓
Command(name="find", handler=handle_find, ...)
    ↓
handle_find({"query": "milk", "limit": "5"}, user_id)
    ↓
Response sent to user
```

## Available Commands (15 Total)

### System (6)
- `/help` — List commands
- `/status` — Health check
- `/ping` — Latency test
- `/start` — Onboarding
- `/whoami` — User context
- `/version` — Show version

### Data (6)
- `/list` — List items
- `/find <query>` — Search items
- `/update <key> <value>` — Update data
- `/delete <id>` — Delete item
- `/clear confirm` — Clear all data
- `/history [limit]` — Show history

### Config (3)
- `/settings [set <key> <value>]` — Manage settings
- `/export [format]` — Export data
- `/import <source>` — Import data

## How to Add a New Command

### 1. Create handler in `handlers/`

```python
# app/infrastructure/commands/handlers/system.py

def handle_echo(args: dict, user_id: str) -> str:
    msg = args.get("query", "")
    return f"[OK] Echo: {msg}"
```

### 2. Register in `setup.py`

```python
# app/infrastructure/commands/setup.py

registry.register(Command(
    name="echo",
    description="Echo your message",
    usage="/echo <message>",
    category="system",
    args_schema=None,
    handler=handle_echo,
))
```

**That's it!** No need to modify UseCase or any routing logic.

## Design Principles

### 1. **Open/Closed Principle**
- Open for extension (add commands)
- Closed for modification (don't touch existing code)

### 2. **Single Responsibility**
- Parser: Parse text into structured data
- Dispatcher: Route to handlers
- Handlers: Execute command logic
- UseCase: Orchestrate

### 3. **Dependency Inversion**
- UseCase depends on abstractions (Messenger, Dispatcher)
- Not on concrete implementations

### 4. **Plugin Architecture**
- Commands are plugins registered at startup
- No hardcoded command routing

## Testing

```python
# Test parsing
cmd_name, args = CommandParser.parse("/find milk --limit=10")
assert cmd_name == "find"
assert args == {"query": "milk", "limit": "10"}

# Test dispatcher
dispatcher = CommandDispatcher(registry)
command, response = dispatcher.dispatch("find", {"query": "milk"}, "user1")
assert command is not None
assert "[OK]" in response
```

## Future Enhancements

1. **Argument Validation with Pydantic**
   ```python
   args_schema={
       "query": {"type": str, "min_length": 1},
       "limit": {"type": int, "ge": 1, "le": 100}
   }
   ```

2. **Permission System**
   ```python
   Command(..., permissions=["user", "admin"])
   ```

3. **Middleware**
   ```python
   dispatcher.use(LoggingMiddleware())
   dispatcher.use(RateLimitMiddleware())
   dispatcher.use(AuthMiddleware())
   ```

4. **Async Handlers**
   ```python
   async def handle_async_find(args, user_id):
       # Can call async database, APIs, etc.
   ```

5. **Multi-step Workflows**
   ```python
   /start_backup
   "Confirm backup? Reply: yes or no"
   # State machine handling user response
   ```

## Key Files

- `app/domain/entities/command.py` — Command contract
- `app/domain/services/command_parser.py` — Structured parsing
- `app/application/services/command_dispatcher.py` — Routing
- `app/infrastructure/commands/registry.py` — Command storage
- `app/infrastructure/commands/setup.py` — Command registration
- `app/infrastructure/commands/handlers/` — Handlers by domain
- `app/application/use_cases/handle_command.py` — Clean orchestration

## Demo

Run the demo:
```bash
python tools/demo_command_system.py
```

View database:
```bash
python tools/view_db.py
```
