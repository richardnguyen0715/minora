# Telegram Message Receiver System

A production-ready Telegram message receiver system built with **clean architecture** principles that automatically responds to messages and saves links to a database.

## Quick Start

Two ways to receive messages:

**🚀 Local Development (Long Polling):**
```bash
# .env
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# Run
python -m app.main
```

**🌐 Production (Webhooks):**
```bash
# .env
TELEGRAM_TOKEN=your_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# Run
python -m app.main
```

→ **[Detailed Setup Guide](docs/POLLING_SETUP.md)**

## Architecture

The system follows a layered architecture with clear separation of concerns:

```
Telegram Update
    ↓
Interface Layer (FastAPI Webhook)
    ↓
Application Layer (Use Cases)
    ↓
Domain Layer (Business Logic)
    ↓
Infrastructure Layer (Telegram API, Database)
```

### Layers

- **Domain Layer**: Pure business logic independent of frameworks
  - `entities/`: Domain models (Message, Link)
  - `enums/`: Shared enumerations (MessageType)
  - `services/`: Business logic (MessageService, LinkService)

- **Application Layer**: Use cases and interfaces
  - `use_cases/`: Application workflows (HandleMessageUseCase, SaveLinkUseCase)
  - `interfaces/`: Abstraction for external systems (Messenger, Queue)

- **Infrastructure Layer**: External system implementations
  - `telegram/`: Telegram API integration
  - `database/`: SQLite database with Repository pattern
  - `queue/`: Message queuing (Redis)
  - `config.py`: Environment configuration

- **Interface Layer**: API and entry points
  - `api/`: FastAPI webhook endpoint (for webhook mode)
  - `telegram/polling.py`: Long polling client (for local development)
  - `main.py`: Application factory with auto-detection

## Features

✨ **v0.3.0 - Long Polling Support**
- 📱 **Long Polling**: Receive messages without public URL (local development)
- 🌐 **Webhooks**: Instant delivery for production servers
- Auto-detects mode based on configuration
- Exponential backoff on connection errors

✨ **v0.2.0 - Link Saving**
- 🔗 Automatic link detection and extraction from messages
- 💾 Save links to SQLite database with metadata
- 📤 Send confirmation response: "I got this link: {url}"
- 🚫 Prevent duplicate links per chat
- 📊 Track link metadata (sender, timestamp, status)

✨ **v0.1.0 - Message Receiving**
- 📨 Receive Telegram webhook updates
- 🤖 Respond to text messages
- 📸 Support for media messages
- 🏥 Health check endpoint

## Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- SQLite (included with Python)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram-receiver
```

2. Install dependencies:
```bash
pip install fastapi uvicorn httpx loguru pydantic redis sqlalchemy aiosqlite
```

3. Create `.env` file:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`:
```env
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000
```

## Running

### Development

```bash
python -m app.main
```

The application will start on `http://localhost:8000`

### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
docker-compose up
```

## Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test module:
```bash
pytest tests/unit/test_link_service.py -v
```

Run with coverage:
```bash
pytest tests/ --cov=app
```

## API Endpoints

- **POST** `/webhook` - Telegram webhook endpoint (receives updates from Telegram)
- **GET** `/health` - Health check endpoint

## Setting Up Telegram Webhook

1. Get your bot token from [@BotFather](https://t.me/botfather)

2. Set the webhook URL:
```bash
curl -X POST https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/webhook"}'
```

3. Verify webhook is set:
```bash
curl https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo
```

## Project Structure

```
app/
├── domain/
│   ├── entities/
│   │   └── message.py
│   ├── enums/
│   │   └── message_type.py
│   └── services/
│       ├── message_service.py
│       └── link_service.py
├── application/
│   ├── use_cases/
│   │   ├── handle_message.py
│   │   └── save_link.py
│   └── interfaces/
│       ├── messenger.py
│       └── queue.py
├── infrastructure/
│   ├── telegram/
│   │   └── telegram_messenger.py
│   ├── database/
│   │   ├── models.py
│   │   └── repository.py
│   ├── queue/
│   │   └── redis_queue.py
│   └── config.py
├── interface/
│   └── api/
│       └── webhook.py
├── logging_config.py
└── main.py

tests/
├── unit/
│   ├── test_message_service.py
│   ├── test_handle_message_use_case.py
│   └── test_link_service.py
└── integration/
    ├── test_webhook.py
    └── test_link_saving.py

docs/
├── clean-architechture.md
├── code-policies.md
├── database-design.md
└── DATABASE.md
```

## Message Flow

### Text Message Processing

1. User sends message to Telegram bot
2. Telegram sends webhook update to `/webhook`
3. Webhook normalizes Telegram payload to domain `Message` entity
4. `HandleMessageUseCase` is executed
5. System extracts links if present using `LinkService`
6. If links found:
   - Each link is saved to database via `SaveLinkUseCase`
   - Response generated: "I got this link: {domain}"
7. If no links:
   - `MessageService` generates generic response
8. Response sent back to user via `TelegramMessenger`

### Database Operations

- Links are stored with metadata (sender, timestamp, URL, domain)
- Duplicate links per chat are prevented via unique constraint
- Links can be marked as processed
- Full audit trail with timestamps

## Code Policies

This project follows strict code policies from `@docs/code-policies.md`:

✅ **English Naming**: All variables, functions, classes use English snake_case/PascalCase
✅ **Docstrings**: PEP 257 Google-style docstrings on all public functions
✅ **Logging**: Structured logging with loguru (not print statements)
✅ **No Hardcoded Secrets**: All config via environment variables
✅ **Type Hints**: Full type annotations throughout codebase
✅ **Clean Code**: Small functions (<30 lines), early returns, no magic numbers
✅ **Error Handling**: Proper exception handling with context logging
✅ **Modern Python**: Pydantic V2, async/await, context managers

## Database

The system uses SQLite for persistent storage of links. Database schema and details are in `@docs/DATABASE.md`.

### Key Features

- **Repository Pattern**: Clean data access abstraction
- **Async Operations**: All database operations support async/await
- **Transaction Support**: Proper commit/rollback handling
- **Structured Schema**: Normalized with full metadata tracking

### Example: Retrieve Links

```python
from app.infrastructure.database import get_session_maker
from app.infrastructure.database.repository import LinkRepository

async def get_my_links(chat_id: str):
    async with session_maker() as session:
        repository = LinkRepository(session)
        links = await repository.get_links_by_chat(chat_id)
        return links
```

## Example: Sending a Message with Link

1. Open your Telegram bot
2. Send a message with a link:
   ```
   Check this out: https://example.com/article
   ```
3. Bot responds:
   ```
   I got this link from example.com: https://example.com/article
   ```
4. Link is saved to database with metadata

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **httpx**: Async HTTP client for Telegram API
- **loguru**: Structured logging
- **pydantic**: Data validation
- **sqlalchemy**: ORM and database abstraction
- **aiosqlite**: Async SQLite driver
- **redis**: Message queue support
- **pytest**: Testing framework

## Deployment Options

### Development
```bash
python -m app.main
```

### Docker
```bash
docker-compose up
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Performance Metrics

- **Test Coverage**: 32+ comprehensive tests (link + message features)
- **Code Lines**: ~1500 lines of application code
- **Response Time**: <100ms per message (typical)
- **Database Queries**: 1-2 per message with links

## Future Enhancements

- [ ] Link metadata extraction (title, description, preview image)
- [ ] Link categorization and tagging
- [ ] Search functionality
- [ ] Web UI for viewing saved links
- [ ] Advanced analytics dashboard
- [ ] Knowledge graph integration
- [ ] PostgreSQL support for scale
- [ ] Kubernetes deployment

## Contributing

Please follow the code policies defined in `@docs/code-policies.md`.

## License

MIT
