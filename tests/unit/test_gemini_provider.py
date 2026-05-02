"""Tests for GeminiProvider with mocked API calls."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.llm.gemini_provider import GeminiProvider
from app.infrastructure.llm.provider import LLMProviderError


class TestGeminiProviderInit:
    """Test GeminiProvider initialization."""

    def test_init_with_valid_keys(self):
        provider = GeminiProvider(api_keys=["key1", "key2"])
        assert len(provider.api_keys) == 2
        assert provider.model == "gemini-2.0-flash"

    def test_init_with_empty_keys_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            GeminiProvider(api_keys=[])

    def test_init_strips_whitespace_keys(self):
        provider = GeminiProvider(api_keys=["  key1  ", " key2 "])
        assert provider.api_keys == ["key1", "key2"]

    def test_init_filters_empty_keys(self):
        provider = GeminiProvider(api_keys=["key1", "", "  ", "key2"])
        assert provider.api_keys == ["key1", "key2"]


class TestKeyRotation:
    """Test API key rotation logic."""

    def test_initial_key_index(self):
        provider = GeminiProvider(api_keys=["a", "b", "c"])
        assert provider._get_current_key() == "a"

    def test_rotate_key_cycles(self):
        provider = GeminiProvider(api_keys=["a", "b", "c"])
        provider._rotate_key()
        assert provider._get_current_key() == "b"
        provider._rotate_key()
        assert provider._get_current_key() == "c"
        provider._rotate_key()
        assert provider._get_current_key() == "a"


class TestJsonParsing:
    """Test JSON response parsing."""

    def test_parse_clean_json(self):
        text = '{"summary": "test", "concepts": ["a"]}'
        result = GeminiProvider._parse_json_response(text)
        assert result["summary"] == "test"

    def test_parse_json_in_code_block(self):
        text = '```json\n{"summary": "test"}\n```'
        result = GeminiProvider._parse_json_response(text)
        assert result["summary"] == "test"

    def test_parse_json_with_extra_text(self):
        text = 'Here is the result:\n{"summary": "test"}\nDone.'
        result = GeminiProvider._parse_json_response(text)
        assert result["summary"] == "test"

    def test_parse_invalid_json_raises(self):
        with pytest.raises(LLMProviderError):
            GeminiProvider._parse_json_response("not json at all")


class TestExtractText:
    """Test response text extraction."""

    def test_extract_from_valid_response(self):
        response = {
            "candidates": [{"content": {"parts": [{"text": "hello"}]}}]
        }
        assert GeminiProvider._extract_text_from_response(response) == "hello"

    def test_extract_from_empty_candidates_raises(self):
        with pytest.raises(LLMProviderError):
            GeminiProvider._extract_text_from_response({"candidates": []})


class TestGenerate:
    """Test generate methods with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_generate_success(self):
        provider = GeminiProvider(api_keys=["test_key"], max_retries=1)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": '{"summary": "test"}'}]}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.generate("test prompt")
            assert result["summary"] == "test"

    @pytest.mark.asyncio
    async def test_generate_text_success(self):
        provider = GeminiProvider(api_keys=["test_key"], max_retries=1)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "hello world"}]}}]
        }

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await provider.generate_text("test prompt")
            assert result == "hello world"
