"""Configuration command handlers."""

import asyncio

from loguru import logger

from app.application.use_cases.ingestion_orchestrator import IngestionOrchestrator
from app.domain.entities.command_context import CommandContext
from app.infrastructure.database import get_session_maker


def handle_settings(args: dict, user_id: str) -> str:
    """Show settings."""
    subcommand = args.get("query", "")
    
    if not subcommand:
        return "[OK] Settings:\n- Polling mode: Enabled\n- Auto-save: On\n- Notifications: On"
    
    if subcommand.startswith("set"):
        return "[OK] Setting updated"
    elif subcommand.startswith("get"):
        return "[OK] Setting retrieved"
    
    return "[ERROR] Unknown settings subcommand"


def handle_export(args: dict, user_id: str) -> str:
    """Export data."""
    format_type = args.get("query", "json")
    return f"[OK] Preparing export in {format_type} format..."


async def handle_import(context: CommandContext) -> str:
    """
    Import data from URL with full ingestion pipeline.

    Runs the multi-agent pipeline asynchronously:
    1. Returns immediate "Processing..." response
    2. Runs pipeline in background
    3. Sends full report when done

    Args:
        context (CommandContext): Command context with args, user_id, chat_id, messenger.

    Returns:
        str: Immediate response message.
    """
    url = context.args.get("query", "").strip()

    if not url:
        return "[ERROR] Please provide a URL: /import <url>"

    # Validate URL
    from app.domain.services.link_service import LinkService
    if not LinkService.has_links(url):
        return "[ERROR] Invalid URL format. Please provide a valid URL."

    logger.info(
        "import_pipeline_triggered",
        extra={
            "url": url,
            "user_id": context.user_id,
            "chat_id": context.chat_id,
        },
    )

    # Launch pipeline in background
    asyncio.create_task(
        _run_import_pipeline(url, context.user_id, context.chat_id, context.messenger)
    )

    return "[OK] Processing your link... I'll send you the results when done."


async def _run_import_pipeline(url: str, user_id: str, chat_id: str, messenger) -> None:
    """
    Run the full ingestion pipeline in the background.

    Args:
        url (str): URL to import.
        user_id (str): User who triggered the import.
        chat_id (str): Chat to send results to.
        messenger: Messenger for sending the report.
    """
    try:
        session_factory = get_session_maker()
        async with session_factory() as session:
            orchestrator = IngestionOrchestrator(session)
            report = await orchestrator.run(url, user_id, chat_id)

            if messenger:
                try:
                    await messenger.send(chat_id, report)
                except Exception as send_error:
                    logger.error(
                        "import_report_send_failed",
                        extra={"chat_id": chat_id, "error": str(send_error)},
                    )
    except Exception as exc:
        logger.error(
            "import_pipeline_background_failed",
            extra={"url": url, "error": str(exc)},
        )
        if messenger:
            try:
                await messenger.send(chat_id, f"[ERROR] Import pipeline failed: {str(exc)}")
            except Exception:
                pass
