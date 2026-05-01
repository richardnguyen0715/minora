# Telegram Message Receiver System

A production-ready Telegram message receiver system built with **clean architecture** principles.

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
Infrastructure Layer (Telegram API, Redis)
```

### Layers

- **Domain Layer**: Pure business logic independent of frameworks
  - `entities/`: Domain models (Message)
  - `enums/`: Shared enumerations (MessageType)
  - `services/`: Business logic (MessageService)

- **Application Layer**: Use cases and interfaces
  - `use_cases/`: Application workflows (HandleMessageUseCase)
  - `interfaces/`: Abstraction for external systems (Messenger, Queue)

- **Infrastructure Layer**: External system implementations
  - `telegram/`: Telegram API integration
  - `queue/`: Message queuing (Redis)
  - `config.py`: Environment configuration

- **Interface Layer**: API and entry points
  - `api/`: FastAPI webhook endpoint
  - `main.py`: Application factory and entry point

## Prerequisites

- Python 3.10+
- Redis (optional, for queue functionality)
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram-receiver
```

2. Install dependencies with Poetry:
```bash
poetry install
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
poetry run python -m app.main
```

The application will start on `http://localhost:8000`

### Production

```bash
poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker

```bash
docker build -t telegram-receiver .
docker run -p 8000:8000 --env-file .env telegram-receiver
```

## Testing

Run all tests:
```bash
poetry run pytest
```

Run with coverage:
```bash
poetry run pytest --cov=app --cov-report=html
```

Run specific test file:
```bash
poetry run pytest tests/unit/test_message_service.py
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

## Code Policies

This project follows strict code policies:

- ✅ English naming conventions (variables, functions, classes)
- ✅ PEP 257 docstrings for all public functions
- ✅ Structured logging with loguru
- ✅ No hardcoded secrets (use environment variables)
- ✅ Clean code principles (small functions, early returns)
- ✅ Comprehensive error handling
- ✅ Type hints throughout
- ✅ Black code formatting
- ✅ Conventional commits

## Project Structure

```
app/
├── domain/
│   ├── entities/
│   │   └── message.py
│   ├── enums/
│   │   └── message_type.py
│   └── services/
│       └── message_service.py
├── application/
│   ├── use_cases/
│   │   └── handle_message.py
│   └── interfaces/
│       ├── messenger.py
│       └── queue.py
├── infrastructure/
│   ├── telegram/
│   │   └── telegram_messenger.py
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
│   └── test_handle_message_use_case.py
└── integration/
    └── test_webhook.py
```

## Dependencies

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **httpx**: Async HTTP client
- **loguru**: Logging library
- **pydantic**: Data validation
- **redis**: Message queue
- **pytest**: Testing framework

## Message Flow

1. User sends message to Telegram bot
2. Telegram sends webhook update to `/webhook`
3. Webhook normalizes Telegram payload to domain `Message` entity
4. `HandleMessageUseCase` is executed
5. `MessageService` generates appropriate reply
6. Reply is sent back to user via `TelegramMessenger`

## Example Message Types

- **Text**: Regular text messages
- **Media**: Photos, documents, videos
- **Empty**: Messages with no recognized content

## Future Enhancements

- [ ] Redis queue for async message processing
- [ ] Worker service for consuming queue events
- [ ] Message persistence layer
- [ ] User authentication
- [ ] Advanced logging and monitoring
- [ ] Kubernetes deployment manifests
- [ ] CI/CD pipeline

## Contributing

Please follow the code policies defined in `docs/code-policies.md`.

## License

MIT
