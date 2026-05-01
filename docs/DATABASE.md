# Database Design & Implementation

This document describes the database layer implementation following the principles outlined in `@docs/database-design.md`.

## Overview

The Telegram Message Receiver system now includes link storage and tracking capabilities using SQLite as the primary database, with a clean repository pattern for data access.

## Design Principles

Following `@docs/database-design.md`, the database design implements:

1. **Structured & Normalized**: Each link has a standardized schema with metadata
2. **Atomic & Composable**: The `links` table serves a single, well-defined purpose
3. **Graph-Ready**: IDs and relationships support future knowledge graph expansion
4. **AI-Friendly**: Structured metadata enables embedding and semantic search
5. **Source Tracking**: Full traceability of where links originated

## Database Schema

### Current Tables

#### `links` Table

Stores received links from Telegram messages with full context and metadata.

```sql
CREATE TABLE links (
    id VARCHAR(64) PRIMARY KEY,              -- Unique ID: link_<12-char-uuid>
    url VARCHAR(2048) NOT NULL UNIQUE,      -- The extracted URL
    title TEXT,                              -- Optional link title/description
    chat_id VARCHAR(64) NOT NULL,           -- Telegram chat identifier
    user_id VARCHAR(64) NOT NULL,           -- Telegram user identifier
    source_type VARCHAR(32) NOT NULL,       -- Type: message_text, caption, etc.
    message_id INTEGER,                     -- Telegram message ID for reference
    status VARCHAR(32) NOT NULL,            -- new, processed, archived
    created_at DATETIME NOT NULL,           -- When link was received
    processed_at DATETIME,                  -- When link was processed
    
    UNIQUE (url, chat_id),                  -- Prevent duplicate links per chat
    INDEX (chat_id),
    INDEX (user_id),
    INDEX (created_at),
    INDEX (url)
);
```

### Schema Design Decisions

1. **ID Format**: `link_<12-char-uuid>` follows the pattern from `database-design.md` (e.g., `src_<date>_<seq>`)
   - Machine-parseable and sortable
   - Supports future sharding by date or sequence

2. **Unique Constraint**: `(url, chat_id)` prevents duplicate link saves per chat
   - Allows same link in different chats (different contexts)
   - Prevents accidental duplicates within a chat

3. **Status Field**: Supports processing pipeline
   - `new`: Just received
   - `processed`: Metadata extracted, categorized
   - `archived`: Old or no longer relevant

4. **Metadata Fields**:
   - `source_type`: Enables future support for links in captions, documents, etc.
   - `message_id`: Enables linking back to original Telegram message
   - `created_at` + `processed_at`: Timestamps for audit trail

## Data Access Layer

### Repository Pattern

The `LinkRepository` class implements the repository pattern for data access:

```python
class LinkRepository:
    """Data access layer for link records."""
    
    async def save_link(url, chat_id, user_id, ...) -> LinkRecord
    async def get_link_by_url(url, chat_id) -> Optional[LinkRecord]
    async def get_links_by_chat(chat_id) -> List[LinkRecord]
    async def mark_processed(link_id) -> LinkRecord
    async def commit() -> None
    async def rollback() -> None
```

Benefits:
- Abstraction of database operations
- Easy to mock for testing
- Supports transaction management
- Async/await for scalability

## Usage Examples

### Saving a Link

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.repository import LinkRepository

async def save_link_example():
    async with session_maker() as session:
        repository = LinkRepository(session)
        
        link = await repository.save_link(
            url="https://example.com/article",
            chat_id="123456",
            user_id="789",
            title="Example Article"
        )
        
        await repository.commit()
        print(f"Saved link: {link.id}")
```

### Retrieving Links by Chat

```python
links = await repository.get_links_by_chat(chat_id="123456")
for link in links:
    print(f"{link.url} - {link.created_at}")
```

### Checking for Duplicate Links

```python
existing = await repository.get_link_by_url(
    url="https://example.com",
    chat_id="123456"
)
if existing:
    print(f"Link already saved: {existing.id}")
else:
    print("New link")
```

## Database Initialization

The database is automatically initialized on application startup:

```python
# In app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    await init_db()  # Creates all tables
    logger.info("Database initialized")
    yield
    logger.info("Application shutting down")
```

Tables are created if they don't exist (idempotent).

## File Structure

```
app/infrastructure/database/
├── __init__.py           # Database initialization and session management
├── models.py             # SQLAlchemy ORM models (LinkRecord)
└── repository.py         # LinkRepository data access layer
```

Location: `data/minora.db` (created in application working directory)

## Future Enhancements

The current schema is designed to support:

1. **Multi-Platform Ingestion**: `source_type` field ready for non-Telegram sources
   - Could ingest links from email, Slack, Discord
   - Extensible to include API integrations

2. **Knowledge Graph Integration**: IDs and metadata support future graph database
   - Links → Concepts → Insights workflow
   - Enable semantic relationship discovery

3. **Link Categorization**: Reserved fields for:
   - Domain categorization
   - Content type detection
   - Topic/tag assignment

4. **Processing Pipeline**: Status field supports:
   - Link validation and metadata extraction
   - Content summary generation
   - AI embedding creation

5. **Analytics**: Timestamps and metadata enable:
   - Link frequency analysis
   - User behavior tracking
   - Trending topics detection

## Configuration

Database configuration via environment variables:

```env
# .env
DATABASE_URL=sqlite+aiosqlite:///data/minora.db  # Default
# Or PostgreSQL for production:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/minora
```

## Migration Strategy

Currently using SQLAlchemy's metadata.create_all() for schema creation.

For production with schema changes:
```bash
# Using Alembic (already installed)
alembic init migrations
alembic revision --autogenerate -m "Add new field"
alembic upgrade head
```

## Performance Considerations

### Indexes

- `chat_id`: Fast retrieval of user's links
- `user_id`: User-level analytics
- `url`: Duplicate detection
- `created_at`: Time-based queries

### Scalability

- **SQLite**: Good for < 1M records
- **PostgreSQL**: Recommended for production at scale
- **Connection pooling**: AsyncSession with sessionmaker handles connection management

## Testing

Database operations are tested with:
- Async/await patterns for realistic concurrency
- Transaction isolation
- Error handling and rollback scenarios

Tests in: `tests/unit/test_link_service.py` and `tests/integration/test_link_saving.py`

## Compliance

✅ Follows `@docs/code-policies.md`:
- English naming conventions
- Full type hints
- Comprehensive docstrings
- Structured logging with loguru
- No hardcoded secrets (config via env)

✅ Follows `@docs/database-design.md`:
- Structured and normalized schema
- Atomic purpose (links only)
- Graph-ready with IDs and relationships
- AI-friendly metadata
- Source traceability
