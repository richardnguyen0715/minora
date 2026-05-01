# Getting Started: Long Polling vs Webhooks

The Telegram bot now supports **two modes** for receiving messages:

1. **Long Polling** (for local development) - ✅ What you need
2. **Webhooks** (for production) - for public servers

---

## Quick Start: Long Polling

### Step 1: Get Your Telegram Chat ID

1. Use `@userinfobot` in Telegram to get your chat ID
2. Or send a message to the bot and it will appear in the logs

### Step 2: Update `.env` File

```bash
# Your bot token from BotFather
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Your chat ID (to filter messages to only this chat)
# Leave empty to respond to all chats
TELEGRAM_CHAT_ID=your_chat_id_here

# Optional: Don't set webhook URL, or leave it empty
# TELEGRAM_WEBHOOK_URL=

# Other settings
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000
```

### Step 3: Run the Bot

```bash
python -m app.main
```

You should see:

```
INFO     | app.main:lifespan:32 - Starting Telegram long polling mode
INFO     | app.main:lifespan:34 - Application started successfully
INFO     | app.infrastructure.telegram.polling:poll:100 - Starting Telegram long polling
```

### Step 4: Test It

1. Send a message with a link to your Telegram group:
   ```
   Check this: https://example.com/article
   ```

2. The bot should respond immediately:
   ```
   I got this link from example.com: https://example.com/article
   ```

3. The link is saved to `data/minora.db`

---

## How It Works

### Long Polling Flow

```
┌─────────────────────────────────┐
│   Your Application Running      │
│  (python -m app.main)          │
└────────────┬────────────────────┘
             │
             ├─→ Continuously polls Telegram every second
             │
             ├─→ "Any new messages for me?"
             │
             ├─→ Gets updates using getUpdates API
             │
             ├─→ Processes links in messages
             │
             └─→ Saves to database & responds
```

### Webhook Flow (Production)

```
┌──────────────────────┐
│  Your Server (public)│
│  Running bot app     │
└──────────┬───────────┘
           ▲
           │ (Telegram pushes messages)
           │
    ┌──────┴──────┐
    │  Telegram   │
    │    API      │
    └─────────────┘
```

---

## Configuration

### Polling Mode (Default if no webhook)

```bash
# .env
TELEGRAM_TOKEN=your_token
# Don't set TELEGRAM_WEBHOOK_URL (leave empty or remove)
TELEGRAM_CHAT_ID=your_chat_id  # Optional
```

**Pros:**
- ✅ Works locally
- ✅ No need for public URL
- ✅ Simple setup
- ✅ Perfect for development/testing

**Cons:**
- ⚠ Slight delay (polls every second)
- ⚠ More API calls to Telegram

### Webhook Mode (Production)

```bash
# .env
TELEGRAM_TOKEN=your_token
TELEGRAM_WEBHOOK_URL=https://yourdomain.com/webhook
TELEGRAM_CHAT_ID=your_chat_id  # Optional
```

**Pros:**
- ✅ Instant message delivery
- ✅ Fewer API calls
- ✅ Production-ready

**Cons:**
- ⚠ Requires public HTTPS URL
- ⚠ Must configure with BotFather
- ⚠ More complex setup

---

## Switching Modes

### To Use Polling (Local Development)

```bash
# Edit .env
TELEGRAM_WEBHOOK_URL=  # Leave empty or remove the line
```

Then restart:

```bash
# Kill the running app
Ctrl+C

# Restart in polling mode
python -m app.main
```

### To Use Webhook (Production)

1. Set your public HTTPS URL:
   ```bash
   TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook
   ```

2. Configure with BotFather:
   ```
   /setwebhook https://your-domain.com/webhook
   ```

3. Restart the app

---

## Logging & Debugging

### View Polling Activity

Set log level to DEBUG:

```bash
# .env
LOG_LEVEL=DEBUG
```

Then restart and send a message. You'll see:

```
DEBUG | app.infrastructure.telegram.polling:_process_update:95 - Processing message via long polling
DEBUG | app.infrastructure.telegram.polling:poll:107 - Received 1 updates
```

### Check Database

After sending messages with links:

```bash
ls -lh data/minora.db
sqlite3 data/minora.db "SELECT url, chat_id, created_at FROM links LIMIT 5;"
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Bot not responding | Check `TELEGRAM_CHAT_ID` matches your actual chat |
| No polling logs | Set `LOG_LEVEL=DEBUG` in `.env` |
| Database not created | Make sure `data/` directory exists |
| Settings not updating | Restart the app after editing `.env` |

---

## Polling Configuration

The poller automatically:
- Polls Telegram every second
- Uses exponential backoff on errors (max 60 seconds)
- Handles disconnections gracefully
- Continues polling even if errors occur
- Resets backoff on successful updates

### Advanced: Custom Timeout

In `app/infrastructure/telegram/polling.py`:

```python
poller = TelegramPoller(...)
await poller.poll(timeout=30)  # Telegram long polling timeout
```

---

## Example `.env` Setup

```bash
# Telegram
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=-1001234567890

# Local development (polling)
TELEGRAM_WEBHOOK_URL=

# Database
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
```

---

## Next Steps

Once polling works locally, you can:

1. **Deploy to production:**
   - Use webhooks with a public HTTPS URL
   - Configure domain and SSL certificate
   - Set up monitoring

2. **Add more features:**
   - Extract metadata from links
   - Categorize links by domain
   - Search saved links
   - Web UI for viewing links

3. **Scale:**
   - Move to PostgreSQL
   - Add caching layer
   - Set up knowledge graph

---

## Support

- **Question:** How do I get my chat ID?
  - **Answer:** Use `@userinfobot` in Telegram, or check logs with `LOG_LEVEL=DEBUG`

- **Question:** Why is polling slower than webhooks?
  - **Answer:** Polling checks for updates every ~1 second, webhooks are instant

- **Question:** Can I use both polling and webhooks?
  - **Answer:** No, only one mode at a time. The app auto-detects based on `TELEGRAM_WEBHOOK_URL`

---

Done! Your bot is now receiving messages via long polling. 🎉
