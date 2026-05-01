"""
Database initialization and connection management.
"""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.models import Base

# Database file location
DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DB_DIR}/minora.db"


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in Base.metadata.
    """
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
