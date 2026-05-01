"""Tests for markdown file storage in the real-file layer."""

from app.domain.entities.knowledge import KnowledgeDocument
from app.infrastructure.knowledge.markdown_storage import MarkdownStorage


def test_markdown_storage_roundtrip(tmp_path):
    storage = MarkdownStorage(tmp_path / "knowledge")
    document = KnowledgeDocument(
        id="src_20260430_001",
        type="source",
        title="Telegram source note",
        content="## Summary\nA source document body.",
        tags=["telegram", "source"],
        aliases=["telegram-source"],
        metadata={
            "url": "https://example.com/article",
            "platform": "web",
            "author": "alice",
            "language": "en",
        },
    )

    file_path = storage.write_document(document)
    assert file_path.exists()

    loaded = storage.read_document(file_path)
    assert loaded is not None
    assert loaded.id == document.id
    assert loaded.type == "source"
    assert loaded.title == document.title
    assert loaded.tags == ["telegram", "source"]
    assert loaded.aliases == ["telegram-source"]
    assert loaded.metadata["url"] == "https://example.com/article"
    assert "A source document body." in loaded.content

    assert storage.delete_document(file_path) is True
    assert not file_path.exists()


def test_markdown_storage_replace_preserves_path(tmp_path):
    storage = MarkdownStorage(tmp_path / "knowledge")
    document = KnowledgeDocument(
        id="concept_llm",
        type="concept",
        title="LLM",
        content="Initial content",
        metadata={"domain": "ai"},
    )

    first_path = storage.write_document(document)
    document.content = "Updated content"
    second_path = storage.replace_document(document)

    assert first_path == second_path
    loaded = storage.read_document(second_path)
    assert loaded is not None
    assert loaded.content == "Updated content"
