import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.infrastructure.config import settings
from app.infrastructure.database import init_db
from app.infrastructure.telegram.polling import TelegramPoller
from app.interface.api.webhook import initialize_webhook, router
from app.logging_config import setup_logging

# Global polling task for long polling mode
_polling_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan (startup and shutdown).

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    global _polling_task
    logger.info("Application starting up")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(
            "Failed to initialize database",
            extra={"error": str(e)},
        )
        raise

    # Determine if using polling or webhook based on configuration
    # If TELEGRAM_WEBHOOK_URL is set, use webhook mode
    # If not set or empty, use long polling for local development
    is_webhook_mode = bool(settings.telegram_webhook_url)

    if is_webhook_mode:
        logger.info("Webhook mode configured")
        initialize_webhook(
            telegram_token=settings.telegram_token,
            allowed_chat_id=settings.telegram_chat_id,
        )
    else:
        logger.info("Starting Telegram long polling mode")
        import asyncio

        poller = TelegramPoller(
            telegram_token=settings.telegram_token,
            allowed_chat_id=settings.telegram_chat_id,
        )
        _polling_task = asyncio.create_task(poller.poll())

    logger.info("Application started successfully")
    yield

    # Stop polling if running
    if _polling_task:
        _polling_task.cancel()
        try:
            await _polling_task
        except asyncio.CancelledError:
            pass
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Sets up logging, routes, database, and initializes dependencies.
    Automatically detects polling vs webhook mode based on configuration.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    # Setup logging
    setup_logging(settings.log_level)

    logger.info(
        "Starting Telegram receiver application",
        extra={
            "host": settings.app_host,
            "port": settings.app_port,
            "log_level": settings.log_level,
        },
    )

    # Create logs and data directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    os.makedirs("knowledge", exist_ok=True)

    # Create FastAPI app with lifespan context manager
    app = FastAPI(
        title="Telegram Message Receiver",
        description="Clean architecture Telegram message receiver with link saving (Polling & Webhook)",
        version="0.3.0",
        lifespan=lifespan,
    )

    # Include webhook router (optional, only used if webhook configured)
    app.include_router(router)

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
        log_config=None,
    )
