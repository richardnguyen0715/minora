# 1. Tổng thể kiến trúc

```
┌──────────────────────────────┐
│        Interface Layer       │  (FastAPI, Webhook)
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│      Application Layer       │  (Use Cases)
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│         Domain Layer         │  (Entities, Rules)
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│     Infrastructure Layer     │  (Telegram API, Queue, DB)
└──────────────────────────────┘
```

---

# 2. Folder structure

```bash
app/
├── domain/
│   ├── entities/
│   │   └── message.py
│   ├── enums/
│   │   └── message_type.py
│   └── services/
│       └── message_service.py
│
├── application/
│   ├── use_cases/
│   │   └── handle_message.py
│   └── interfaces/
│       ├── messenger.py
│       └── queue.py
│
├── infrastructure/
│   ├── telegram/
│   │   └── telegram_messenger.py
│   ├── queue/
│   │   └── redis_queue.py
│   └── config.py
│
├── interface/
│   └── api/
│       └── webhook.py
│
└── main.py
```

---

# 3. Domain layer (business logic thuần)

### `message_type.py`

```python
from enum import Enum

class MessageType(Enum):
    TEXT = "text"
    MEDIA = "media"
    EMPTY = "empty"
```

---

### `message.py`

```python
from dataclasses import dataclass
from domain.enums.message_type import MessageType

@dataclass
class Message:
    chat_id: str
    user_id: str
    type: MessageType
    text: str | None
```

---

### `message_service.py`

```python
class MessageService:

    @staticmethod
    def generate_reply(message):
        if message.type == "text":
            return "Tôi đã nhận được tin nhắn của bạn."
        elif message.type == "media":
            return "Tôi đã nhận được nội dung bạn gửi."
        else:
            return "Tin nhắn trống đã được nhận."
```

→ Domain không biết Telegram, không biết HTTP.

---

# 4. Application layer (use case)

### `messenger.py` (interface)

```python
from abc import ABC, abstractmethod

class Messenger(ABC):

    @abstractmethod
    async def send(self, chat_id: str, text: str):
        pass
```

---

### `handle_message.py`

```python
from domain.services.message_service import MessageService

class HandleMessageUseCase:

    def __init__(self, messenger):
        self.messenger = messenger

    async def execute(self, message):
        reply = MessageService.generate_reply(message)
        await self.messenger.send(message.chat_id, reply)
```

---

# 5. Infrastructure layer

### Telegram adapter

```python
import httpx
from application.interfaces.messenger import Messenger

class TelegramMessenger(Messenger):

    def __init__(self, token: str):
        self.base_url = f"https://api.telegram.org/bot{token}"

    async def send(self, chat_id: str, text: str):
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text}
            )
```

---

# 6. Interface layer (FastAPI)

### `webhook.py`

```python
from fastapi import APIRouter, Request
from domain.entities.message import Message
from domain.enums.message_type import MessageType
from application.use_cases.handle_message import HandleMessageUseCase
from infrastructure.telegram.telegram_messenger import TelegramMessenger

router = APIRouter()

messenger = TelegramMessenger(token="YOUR_TOKEN")
use_case = HandleMessageUseCase(messenger)

def map_message(data):
    msg = data.get("message", {})
    text = msg.get("text")

    if text:
        mtype = MessageType.TEXT
    elif msg.get("photo") or msg.get("document"):
        mtype = MessageType.MEDIA
    else:
        mtype = MessageType.EMPTY

    return Message(
        chat_id=str(msg["chat"]["id"]),
        user_id=str(msg["from"]["id"]),
        type=mtype,
        text=text
    )

@router.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()

    message = map_message(data)

    await use_case.execute(message)

    return {"ok": True}
```

---

# 7. Entry point

### `main.py`

```python
from fastapi import FastAPI
from interface.api.webhook import router

app = FastAPI()
app.include_router(router)
```

---

# 8. Thêm Queue (production-ready)

Interface:

```python
class Queue(ABC):
    async def publish(self, event): pass
    async def consume(self): pass
```

Flow:

* Webhook → publish event
* Worker → consume → run use case