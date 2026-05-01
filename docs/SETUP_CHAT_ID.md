# How to Get Your Telegram Chat ID

After the recent update, you can now configure which Telegram chat the bot listens to using the `TELEGRAM_CHAT_ID` setting.

## Step 1: Send a Message to the Bot

1. Open the Telegram group where you added the bot (the one shared with BotFather)
2. Send any message to the group

## Step 2: Check the Application Logs

When the message arrives, the bot will log information including the **chat_id**. Check your application logs:

```bash
python -m app.main
```

You'll see something like:

```
2026-05-01 09:34:57,789 | INFO     | app.interface.api.webhook:116 - Webhook received
  extra={'update_id': 123456789}
```

Or check the logs directory:

```bash
tail -f logs/app.log
```

Search for "Webhook received" to find recent messages with their chat information.

## Step 3: Get Your Chat ID

Use one of these methods:

### Method A: Use @userinfobot (Easiest)
1. In Telegram, search for and message `@userinfobot`
2. Send `/start` command
3. It will show you your chat ID
4. For group chats, the ID will be **negative** (e.g., `-1001234567890`)

### Method B: Check Bot Logs
When you send a message, the bot processes it. To see the chat_id in logs:

1. Update your `.env` temporarily to enable DEBUG logging:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Restart the application

3. Send a message to the group

4. Check the logs - you'll see the chat_id extracted from the message

## Step 4: Update Your `.env` File

Edit `.env` and add/update:

```bash
# Your Telegram Chat ID
# Example for a group: -1001234567890
# Example for a private chat: 123456789
TELEGRAM_CHAT_ID=-1001234567890
```

## Important Notes

- **Group Chat IDs** start with `-100` (e.g., `-1001234567890`)
- **Private Chat IDs** are positive numbers (e.g., `123456789`)
- **Channels** also have negative IDs starting with `-100`
- If you don't set `TELEGRAM_CHAT_ID`, the bot will process messages from ANY chat

## Configuration Behavior

### Without TELEGRAM_CHAT_ID
```
TELEGRAM_CHAT_ID=  # (empty or not set)
↓
Bot responds to messages from ANY chat
```

### With TELEGRAM_CHAT_ID
```
TELEGRAM_CHAT_ID=-1001234567890
↓
Bot only responds to messages from this chat
Bot ignores messages from other chats
```

## Restart the Application

After updating `.env`, restart your application:

On macOS/Linux, find and kill the process:
```bash
ps aux | grep "python -m app.main"
kill -9 <PID>
python -m app.main
```

Or with Docker:

```bash
docker-compose restart
```

## Verify It Works

1. Send a message with a link to your configured chat group
2. The bot should respond with confirmation
3. The link should be saved to the database

If it doesn't work, check the logs:

```bash
tail -f logs/app.log | grep -i "chat"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot doesn't respond | Check that `TELEGRAM_CHAT_ID` in `.env` matches the actual chat ID |
| Wrong chat ID | Use `@userinfobot` to confirm the correct ID |
| Still getting all messages | Restart the app after updating `.env` |
| Can't find logs | Logs are in `logs/app.log` - make sure `data/` and `logs/` directories exist |

## Example `.env` Setup

```bash
# Your token from BotFather
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Your group chat ID
TELEGRAM_CHAT_ID=-1001234567890

# Webhook URL pointing to your server
TELEGRAM_WEBHOOK_URL=https://your-domain.com/webhook

# Other settings
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
APP_HOST=0.0.0.0
APP_PORT=8000
```

Done! Your bot will now only listen to messages in the configured chat.
