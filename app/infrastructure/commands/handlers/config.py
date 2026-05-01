"""Configuration command handlers."""

from loguru import logger

from app.application.use_cases.import_source import ImportSourceUseCase
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


async def handle_import(args: dict, user_id: str) -> str:
    """
    Import data from URL (Facebook, web, etc.).

    Args:
        args (dict): Arguments containing 'query' with URL.
        user_id (str): User ID making the import.

    Returns:
        str: Response message.
    """
    url = args.get("query", "").strip()

    if not url:
        return "[ERROR] Please provide a URL: /import <url>"

    logger.info(
        "import_command_received",
        extra={
            "url": url,
            "user_id": user_id,
        },
    )

    try:
        session_factory = get_session_maker()
        async with session_factory() as session:
            use_case = ImportSourceUseCase(session)
            result = await use_case.execute(
                url=url,
                user_id=user_id,
                tags=["imported"],
            )

            if result.get("ok"):
                return (
                    f"[OK] Source imported successfully!\n"
                    f"- ID: {result['source_id']}\n"
                    f"- Platform: {result['platform']}\n"
                    f"- File: {result['file_path']}"
                )
            else:
                error_msg = result.get("message", result.get("error", "Unknown error"))
                return f"[WARN] {error_msg}"

    except Exception as exc:
        logger.error(
            "import_command_failed",
            extra={
                "url": url,
                "user_id": user_id,
                "error": str(exc),
            },
        )
        return f"[ERROR] Import failed: {str(exc)}"
