from typing import Optional

from fastapi import APIRouter, Request
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.handle_message import HandleMessageUseCase
from app.domain.entities.message import Message
from app.domain.enums.message_type import MessageType
from app.infrastructure.database import get_session_maker
from app.infrastructure.telegram.telegram_messenger import TelegramMessenger

router = APIRouter()

# Initialize messenger and use case
# These will be set by the main application
_messenger: Optional[TelegramMessenger] = None
_use_case: Optional[HandleMessageUseCase] = None
_session_maker = None


def initialize_webhook(telegram_token: str) -> None:
    """
    Initialize the webhook with necessary dependencies.

    Args:
        telegram_token (str): Telegram Bot API token.
    """
    global _messenger, _use_case, _session_maker
    _messenger = TelegramMessenger(token=telegram_token)
    _session_maker = get_session_maker()

    # Create use case with messenger and database session capability
    async def create_use_case(session: Optional[AsyncSession] = None):
        return HandleMessageUseCase(messenger=_messenger, session=session)

    # Store the factory for later use
    global _use_case_factory
    _use_case_factory = create_use_case


def normalize_message(telegram_payload: dict) -> Optional[Message]:
    """
    Map Telegram webhook payload to domain Message entity.

    Extracts relevant information from the Telegram API response
    and normalizes it into our domain model.

    Args:
        telegram_payload (dict): Raw Telegram webhook payload.

    Returns:
        Optional[Message]: Normalized message or None if invalid.
    """
    update_data = telegram_payload.get("message")

    if not update_data:
        logger.warning("Received webhook without message data")
        return None

    chat_data = update_data.get("chat")
    from_data = update_data.get("from")

    if not chat_data or not from_data:
        logger.warning("Missing chat or from data in message")
        return None

    chat_id = str(chat_data.get("id"))
    user_id = str(from_data.get("id"))

    # Determine message type
    text = update_data.get("text")
    if text:
        message_type = MessageType.TEXT
    elif update_data.get("photo") or update_data.get("document"):
        message_type = MessageType.MEDIA
        text = None
    else:
        message_type = MessageType.EMPTY
        text = None

    return Message(
        chat_id=chat_id,
        user_id=user_id,
        type=message_type,
        text=text,
    )


@router.post("/webhook")
async def telegram_webhook(request: Request) -> dict:
    """
    Handle incoming Telegram webhook updates.

    Receives updates from Telegram, normalizes them to domain entities,
    and processes them through the use case with database session.

    Args:
        request (Request): FastAPI request containing Telegram payload.

    Returns:
        dict: Webhook response.
    """
    if not _session_maker:
        logger.error("Session maker not initialized")
        return {"ok": False, "error": "Service not initialized"}

    try:
        payload = await request.json()

        logger.info(
            "Webhook received",
            extra={"update_id": payload.get("update_id")},
        )

        message = normalize_message(payload)
        message_id = payload.get("message", {}).get("message_id")

        if not message:
            logger.warning("Failed to normalize message")
            return {"ok": True}

        # Create database session for this request
        async with _session_maker() as session:
            use_case = HandleMessageUseCase(messenger=_messenger, session=session)
            await use_case.execute(message, message_id=message_id)

        return {"ok": True}

    except Exception as e:
        logger.error(
            "Webhook processing failed",
            extra={"error": str(e)},
        )
        return {"ok": False, "error": str(e)}


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for load balancers and monitoring.

    Returns:
        dict: Health status.
    """
    return {"status": "ok"}
