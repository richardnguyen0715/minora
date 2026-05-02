"""
Database initialization and connection management.
"""
from pathlib import Path

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base

# Database file location
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_DIR}/minora.db"


async def _migrate_db(engine) -> None:
    """
    Safely add new columns to existing tables.

    Uses ALTER TABLE ADD COLUMN which is idempotent-safe in SQLite
    (errors on duplicate columns are caught and ignored).
    """
    migrations = [
        ("sources", "source_type", "TEXT DEFAULT 'article'"),
        ("sources", "ingested_by", "TEXT"),
        ("sources", "title_extracted", "TEXT"),
        ("sources", "summary", "TEXT"),
        ("sources", "content_hash", "TEXT"),
    ]

    async with engine.begin() as conn:
        for table, column, col_type in migrations:
            try:
                await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                logger.info(f"migration_added_column", extra={"table": table, "column": column})
            except Exception:
                # Column already exists, safe to ignore
                pass


async def init_db() -> None:
    """
    Initialize database tables and run migrations.

    Creates all tables defined in Base.metadata and applies
    any pending column migrations for schema evolution.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _migrate_db(engine)
    await engine.dispose()


async def get_session() -> AsyncSession:
    """
    Get an async database session.

    Returns:
        AsyncSession: Database session for queries.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
    await engine.dispose()


def get_session_maker():
    """
    Get sessionmaker for dependency injection.

    Returns:
        sessionmaker: SQLAlchemy sessionmaker factory.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    return sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autocommit=False
    )

