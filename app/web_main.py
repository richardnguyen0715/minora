"""Standalone Web UI entry point for the knowledge management interface.

This module provides a separate FastAPI application that serves the Web UI
without requiring Telegram bot configuration. It initializes only the database
and mounts static files for the frontend.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.infrastructure.database import init_db
from app.interface.api.web_ui import router as web_router
from app.logging_config import setup_logging

# Load web configuration
WEB_CONFIG_PATH = Path("configs/web_config.yaml")
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080


def _load_web_config() -> dict:
    """
    Load web configuration from YAML file.

    Returns:
        dict: Web configuration with defaults applied.
    """
    defaults = {
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "knowledge_root": "knowledge",
        "items_per_page": 20,
    }

    if not WEB_CONFIG_PATH.exists():
        logger.warning(
            "Web config file not found, using defaults",
            extra={"path": str(WEB_CONFIG_PATH)},
        )
        return defaults

    with open(WEB_CONFIG_PATH, "r", encoding="utf-8") as config_file:
        raw = yaml.safe_load(config_file)

    web_section = raw.get("web", {})
    defaults.update(web_section)
    return defaults


@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    Manage Web UI application lifespan.

    Initializes the database on startup and performs cleanup on shutdown.

    Args:
        application (FastAPI): The FastAPI application instance.
    """
    logger.info("Web UI application starting up")

    try:
        await init_db()
        logger.info("Database initialized for Web UI")
    except Exception as error:
        logger.error(
            "Failed to initialize database for Web UI",
            extra={"error": str(error)},
        )
        raise

    logger.info("Web UI application started successfully")
    yield
    logger.info("Web UI application shutting down")


def create_web_app() -> FastAPI:
    """
    Create and configure the Web UI FastAPI application.

    Returns:
        FastAPI: Configured application instance with API routes and static files.
    """
    setup_logging("INFO")

    application = FastAPI(
        title="Minora Knowledge Base",
        description="Web UI for managing the 2-layer knowledge store",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Include API routes
    application.include_router(web_router)

    # Mount static files for the frontend
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    application.mount(
        "/static",
        StaticFiles(directory=str(static_dir)),
        name="static",
    )

    # Serve index.html at root
    @application.get("/")
    async def serve_index():
        """Serve the main Web UI page."""
        index_path = static_dir / "index.html"
        if not index_path.exists():
            return {"error": "Frontend not built. Place index.html in app/static/"}
        return FileResponse(str(index_path))

    return application


# Create the application instance
app = create_web_app()


if __name__ == "__main__":
    import uvicorn

    config = _load_web_config()
    uvicorn.run(
        "app.web_main:app",
        host=config["host"],
        port=config["port"],
        reload=False,
        log_config=None,
    )
