"""Test for import source functionality."""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.use_cases.import_source import ImportSourceUseCase
from app.infrastructure.database.models import Base
from app.infrastructure.knowledge.markdown_storage import MarkdownStorage
from pathlib import Path
import tempfile


@pytest.fixture
async def async_session():
    """Create in-memory SQLite session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
def temp_knowledge_dir():
    """Create temporary knowledge directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.mark.asyncio
async def test_import_facebook_url(async_session, temp_knowledge_dir):
    """Test importing a Facebook URL."""
    use_case = ImportSourceUseCase(async_session, temp_knowledge_dir)
    
    url = "https://www.facebook.com/share/p/1DJys3DVKH/"
    result = await use_case.execute(
        url=url,
        user_id="test_user",
        tags=["test", "facebook"]
    )
    
    assert result["ok"] is True
    assert result["source_id"].startswith("src_")
    assert result["platform"] == "facebook"
    assert "file_path" in result
    
    # Check file was created
    file_path = Path(result["file_path"])
    assert file_path.exists()
    
    # Check file contains URL
    content = file_path.read_text()
    assert url in content
    assert "facebook" in content.lower()


@pytest.mark.asyncio
async def test_import_web_url(async_session, temp_knowledge_dir):
    """Test importing a generic web URL."""
    use_case = ImportSourceUseCase(async_session, temp_knowledge_dir)
    
    url = "https://example.com/article/interesting-stuff"
    result = await use_case.execute(
        url=url,
        user_id="test_user",
        title="My Article"
    )
    
    assert result["ok"] is True
    assert result["platform"] == "web"
    assert result["title"] == "My Article"


@pytest.mark.asyncio
async def test_import_duplicate_url(async_session, temp_knowledge_dir):
    """Test importing same URL twice."""
    use_case = ImportSourceUseCase(async_session, temp_knowledge_dir)
    
    url = "https://www.facebook.com/share/p/1DJys3DVKH/"
    
    # First import
    result1 = await use_case.execute(url=url, user_id="user1")
    assert result1["ok"] is True
    
    # Second import (should fail)
    result2 = await use_case.execute(url=url, user_id="user2")
    assert result2["ok"] is False
    assert "duplicate_import" in result2["error"]


@pytest.mark.asyncio
async def test_import_invalid_url(async_session, temp_knowledge_dir):
    """Test importing invalid URL."""
    use_case = ImportSourceUseCase(async_session, temp_knowledge_dir)
    
    result = await use_case.execute(
        url="not_a_valid_url",
        user_id="test_user"
    )
    
    assert result["ok"] is False
    assert "invalid_url" in result["error"]


@pytest.mark.asyncio
async def test_import_no_url(async_session, temp_knowledge_dir):
    """Test importing with empty URL."""
    use_case = ImportSourceUseCase(async_session, temp_knowledge_dir)
    
    result = await use_case.execute(
        url="",
        user_id="test_user"
    )
    
    assert result["ok"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
