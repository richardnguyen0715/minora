import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from app.infrastructure.config import settings
from app.interface.api.webhook import initialize_webhook, router
from app.logging_config import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan (startup and shutdown).

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    logger.info("Application started successfully")
    yield
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Sets up logging, routes, and initializes dependencies.

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

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Create FastAPI app with lifespan context manager
    app = FastAPI(
        title="Telegram Message Receiver",
        description="Clean architecture Telegram message receiver system",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Initialize webhook dependencies
    initialize_webhook(telegram_token=settings.telegram_token)

    # Include routes
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
