# Feature Documentation

## Link Saving Feature (v0.2.0)

### Overview

The link saving feature automatically detects URLs in Telegram messages, saves them to a database, and responds to the user with a confirmation message.

### How It Works

#### 1. Link Detection

When a user sends a message containing URLs, the system:

1. Receives the message via webhook
2. Extracts all URLs using regex pattern matching
3. Validates URL format (http/https only)
4. Deduplicates links

**Supported URL formats:**
- Simple: `https://example.com`
- With path: `https://example.com/article`
- With query params: `https://example.com/search?q=test`
- With fragments: `https://example.com/docs#section`
- With subdomain: `https://api.example.com/endpoint`

#### 2. Database Storage

Each unique link is saved with:

```
id          - Unique identifier (link_xxxx)
url         - The full URL
title       - Optional description from message
chat_id     - Telegram chat ID
user_id     - Telegram user ID
source_type - Type: message_text, caption, etc.
message_id  - Telegram message ID
status      - new, processed, archived
created_at  - Timestamp when received
processed_at - Timestamp when processed (optional)
```

**Deduplication:**
- Same URL + same chat = prevented (unique constraint)
- Same URL in different chats = allowed (different context)
- Duplicate detection shown in response

#### 3. User Response

The system sends back a message for each link:

**For new links:**
```
I got this link from example.com: https://example.com/article
```

**For duplicate links:**
```
You already sent this link: https://example.com/article
```

**For links that fail to save:**
```
Error saving link: https://example.com/article
```

### Use Cases

#### Use Case 1: Save Research Links

**Scenario:** User is researching a topic and sends multiple article links

**Flow:**
1. User sends: "Found these articles: https://article1.com https://article2.com"
2. Bot extracts both URLs
3. Bot saves both to database
4. Bot responds with confirmation for each
5. User can later retrieve all links from that conversation

#### Use Case 2: Prevent Duplicates

**Scenario:** User accidentally sends the same link twice

**Flow:**
1. First message: "Check this: https://article.com"
   - Bot saves and responds: "I got this link..."
2. Second message: "Check this again: https://article.com"
   - Bot detects existing link
   - Bot responds: "You already sent this link..."

#### Use Case 3: Track Link Origins

**Scenario:** Multiple users sending links to the same group chat

**Flow:**
1. User A sends: "https://tutorial.com"
2. User B sends: "https://reference.com"
3. System saves both with user identification
4. Admin can query: "Show all links from User A in Chat 123"

### Implementation Details

#### LinkService (Domain Layer)

Handles pure link extraction logic:

```python
LinkService.extract_links(text)           # Extract URLs
LinkService.has_links(text)               # Check if text contains URLs
LinkService.extract_domain(url)           # Get domain from URL
LinkService.generate_link_response(url)   # Generate response
```

**Regex Pattern:**
- Matches http/https URLs
- Supports subdomains, ports, paths, query params, fragments
- Filters out incomplete URLs

#### SaveLinkUseCase (Application Layer)

Orchestrates link extraction and storage:

```python
result = await use_case.execute(
    chat_id="123",
    user_id="456",
    text="Check https://example.com",
    message_id=999
)

# Result contains:
# - links_found: number of links
# - links: saved link records
# - responses: messages to send user
```

#### LinkRepository (Infrastructure Layer)

Data access abstraction:

```python
# Save link
link = await repo.save_link(url, chat_id, user_id)

# Retrieve links
links = await repo.get_links_by_chat(chat_id)

# Check for duplicates
existing = await repo.get_link_by_url(url, chat_id)

# Mark as processed
await repo.mark_processed(link_id)
```

### Database Schema

```sql
CREATE TABLE links (
    id VARCHAR(64) PRIMARY KEY,          -- link_<uuid>
    url VARCHAR(2048) NOT NULL UNIQUE,   -- The URL
    title TEXT,                          -- Optional title
    chat_id VARCHAR(64) NOT NULL,        -- Telegram chat
    user_id VARCHAR(64) NOT NULL,        -- Telegram user
    source_type VARCHAR(32),             -- message_text, etc.
    message_id INTEGER,                  -- Telegram message ID
    status VARCHAR(32),                  -- new, processed, archived
    created_at DATETIME,                 -- Received timestamp
    processed_at DATETIME,               -- Processed timestamp
    
    UNIQUE (url, chat_id)                -- Prevent duplicates per chat
);
```

### Configuration

No special configuration needed. The feature activates automatically when:
- Database is initialized (automatic on startup)
- Message contains a URL

Database location: `data/minora.db`

### Error Handling

The system gracefully handles:

1. **Database Errors**: Logged and reported to user
2. **Malformed URLs**: Skipped with error response
3. **Duplicate URLs**: Detected and reported
4. **Connection Issues**: Logged with retry capability
5. **Transaction Failures**: Automatic rollback

### Performance

- **Link Extraction**: <1ms per message
- **URL Regex**: Efficient pattern matching
- **Database Save**: <10ms with async/await
- **Response Generation**: <5ms

### Monitoring

All operations logged with structured logging:

```
INFO: Links detected in message
     chat_id=123, user_id=456, link_count=2

INFO: Link saved to database
     link_id=link_abc123, url=https://example.com, chat_id=123

DEBUG: Link marked as processed
      link_id=link_abc123
```

### Testing

15 unit tests for LinkService:
- Single and multiple link extraction
- Query parameters and fragments
- Domain extraction
- Response generation
- Edge cases (empty text, duplicates, etc.)

Integration tests verify:
- Webhook receives link messages
- Database operations complete
- Responses sent correctly
- Error handling works

### Future Enhancements

1. **Link Metadata Extraction**
   - Fetch and store page title
   - Extract description
   - Download preview image

2. **Link Categorization**
   - Detect link type (article, video, image, etc.)
   - Auto-tag by domain
   - Topic detection

3. **Advanced Search**
   - Search saved links by keyword
   - Filter by date range
   - Filter by user

4. **Analytics**
   - Most shared links
   - Most active users
   - Trending topics

5. **Link Validation**
   - Check if URL is still valid
   - Detect broken links
   - Track redirects

### Example: Complete Flow

```
User: "Check these resources: https://tutorial.com and https://docs.org/api"

System Processing:
1. Receive webhook update
2. Extract messages: ["https://tutorial.com", "https://docs.org/api"]
3. For each URL:
   a. Check if duplicate in chat
   b. Save to database
   c. Generate response
4. Send responses to user:
   - "I got this link from tutorial.com: https://tutorial.com"
   - "I got this link from docs.org: https://docs.org/api"
5. Log operation

Database State:
- link_abc123: https://tutorial.com, chat_id=123, user_id=456, status=new
- link_def456: https://docs.org/api, chat_id=123, user_id=456, status=new
```

### Troubleshooting

**Q: Links not being saved**
- Check database path: `data/minora.db`
- Check logs for database errors
- Verify URL format (must start with http/https)

**Q: Duplicate link responses not working**
- Check unique constraint on (url, chat_id)
- Verify database connection
- Check logs for constraint violations

**Q: No response from bot**
- Check Telegram API token in `.env`
- Verify webhook URL configuration
- Check error logs for Telegram API errors

**Q: Database too large**
- Archive old links: `UPDATE links SET status='archived' WHERE created_at < ...`
- Implement periodic cleanup
- Consider PostgreSQL for scale

### API Reference

#### SaveLinkUseCase.execute()

```python
result = await save_link_use_case.execute(
    chat_id: str,              # Telegram chat ID
    user_id: str,              # Telegram user ID
    text: str,                 # Message text containing links
    message_id: int            # Telegram message ID
) -> dict                      # Result with links and responses
```

**Returns:**
```python
{
    "links_found": 2,
    "links": [
        {
            "id": "link_abc123",
            "url": "https://example.com",
            "status": "new"
        },
        ...
    ],
    "responses": [
        "I got this link from example.com: https://example.com",
        "I got this link from docs.org: https://docs.org/api",
        ...
    ]
}
```

#### LinkRepository Methods

```python
# Save a new link
link = await repository.save_link(
    url: str,                     # Required: URL
    chat_id: str,                 # Required: Telegram chat
    user_id: str,                 # Required: Telegram user
    title: Optional[str],         # Optional: Link title
    source_type: str = "message_text",  # Default: message_text
    message_id: Optional[int]     # Optional: Telegram message ID
) -> LinkRecord                   # The saved link

# Get links by chat
links = await repository.get_links_by_chat(
    chat_id: str                  # Telegram chat ID
) -> List[LinkRecord]             # All links in chat

# Check for duplicate
existing = await repository.get_link_by_url(
    url: str,                     # URL to check
    chat_id: str                  # Chat context
) -> Optional[LinkRecord]         # Existing link or None

# Mark as processed
link = await repository.mark_processed(
    link_id: str                  # Link ID to mark
) -> LinkRecord                   # Updated link
```
