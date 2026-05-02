"""Gemini LLM provider with key rotation and retry logic."""

import asyncio
import json
import re
from typing import Any

import httpx
from loguru import logger

from app.infrastructure.llm.provider import LLMProvider, LLMProviderError


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider(LLMProvider):
    """
    Google Gemini LLM provider.

    Features:
    - Round-robin key rotation across multiple API keys
    - Automatic fallback on 429/500 errors
    - Exponential backoff retry
    - JSON response parsing with text fallback extraction
    - Structured logging for observability
    """

    def __init__(
        self,
        api_keys: list[str],
        model: str = "gemini-2.0-flash",
        max_retries: int = 3,
        timeout_seconds: int = 60,
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
    ) -> None:
        """
        Initialize Gemini provider.

        Args:
            api_keys (list[str]): List of Gemini API keys for rotation.
            model (str): Gemini model name.
            max_retries (int): Maximum retry attempts per request.
            timeout_seconds (int): HTTP request timeout.
            temperature (float): LLM temperature parameter.
            max_output_tokens (int): Maximum tokens in response.

        Raises:
            ValueError: If no API keys provided.
        """
        if not api_keys:
            raise ValueError("At least one Gemini API key is required")

        self.api_keys = [key.strip() for key in api_keys if key.strip()]
        self.model = model
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._current_key_index = 0

    def _get_current_key(self) -> str:
        """Get the current API key from rotation pool."""
        return self.api_keys[self._current_key_index]

    def _rotate_key(self) -> str:
        """
        Rotate to the next API key.

        Returns:
            str: The new current API key.
        """
        old_index = self._current_key_index
        self._current_key_index = (self._current_key_index + 1) % len(self.api_keys)
        logger.warning(
            "gemini_key_rotated",
            extra={
                "from_index": old_index,
                "to_index": self._current_key_index,
                "total_keys": len(self.api_keys),
            },
        )
        return self._get_current_key()

    def _build_url(self, api_key: str) -> str:
        """
        Build the Gemini API URL.

        Args:
            api_key (str): API key to use.

        Returns:
            str: Full API URL.
        """
        return f"{GEMINI_API_BASE_URL}/{self.model}:generateContent?key={api_key}"

    def _build_payload(self, prompt: str) -> dict[str, Any]:
        """
        Build the request payload.

        Args:
            prompt (str): Input prompt text.

        Returns:
            dict: Request body for Gemini API.
        """
        return {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }

    def _build_text_payload(self, prompt: str) -> dict[str, Any]:
        """
        Build payload for plain text response.

        Args:
            prompt (str): Input prompt text.

        Returns:
            dict: Request body for Gemini API without JSON mime type.
        """
        return {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
        }

    @staticmethod
    def _extract_text_from_response(response_data: dict) -> str:
        """
        Extract text from Gemini API response.

        Args:
            response_data (dict): Raw API response.

        Returns:
            str: Extracted text content.

        Raises:
            LLMProviderError: If response structure is unexpected.
        """
        try:
            candidates = response_data.get("candidates", [])
            if not candidates:
                raise LLMProviderError(
                    "No candidates in Gemini response",
                    provider="gemini",
                )

            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            if not parts:
                raise LLMProviderError(
                    "No parts in Gemini response content",
                    provider="gemini",
                )

            return parts[0].get("text", "")
        except (KeyError, IndexError) as exc:
            raise LLMProviderError(
                f"Failed to parse Gemini response structure: {exc}",
                provider="gemini",
            )

    @staticmethod
    def _parse_json_response(text: str) -> dict:
        """
        Parse JSON from LLM response text with fallback extraction.

        Handles cases where LLM wraps JSON in markdown code blocks or
        includes extra text around the JSON object.

        Args:
            text (str): Raw text from LLM response.

        Returns:
            dict: Parsed JSON object.

        Raises:
            LLMProviderError: If JSON cannot be extracted.
        """
        cleaned = text.strip()

        # Direct JSON parse attempt
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strip markdown code blocks
        code_block_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)
        match = code_block_pattern.search(cleaned)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Find first JSON object in text
        brace_pattern = re.compile(r"\{.*\}", re.DOTALL)
        match = brace_pattern.search(cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMProviderError(
            f"Failed to parse JSON from LLM response: {cleaned[:200]}",
            provider="gemini",
        )

    async def _call_api(self, payload: dict) -> dict:
        """
        Call Gemini API with retry and key rotation.

        Args:
            payload (dict): Request payload.

        Returns:
            dict: Raw API response.

        Raises:
            LLMProviderError: If all retries and keys exhausted.
        """
        last_error = None
        keys_tried = 0
        total_keys = len(self.api_keys)

        for attempt in range(self.max_retries):
            api_key = self._get_current_key()
            url = self._build_url(api_key)

            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={"Content-Type": "application/json"},
                    )

                if response.status_code == 200:
                    logger.debug(
                        "gemini_api_success",
                        extra={
                            "attempt": attempt + 1,
                            "model": self.model,
                        },
                    )
                    return response.json()

                # Rate limit or server error — rotate key and retry
                if response.status_code in (429, 500, 503):
                    logger.warning(
                        "gemini_api_retryable_error",
                        extra={
                            "status_code": response.status_code,
                            "attempt": attempt + 1,
                            "key_index": self._current_key_index,
                        },
                    )
                    self._rotate_key()
                    keys_tried += 1

                    # Exponential backoff
                    backoff = min(2 ** attempt, 30)
                    await asyncio.sleep(backoff)
                    continue

                # Non-retryable error
                error_body = response.text[:500]
                last_error = LLMProviderError(
                    f"Gemini API error {response.status_code}: {error_body}",
                    provider="gemini",
                    attempts=attempt + 1,
                )
                logger.error(
                    "gemini_api_non_retryable_error",
                    extra={
                        "status_code": response.status_code,
                        "body": error_body,
                    },
                )
                break

            except httpx.TimeoutException:
                last_error = LLMProviderError(
                    f"Gemini API timeout after {self.timeout_seconds}s",
                    provider="gemini",
                    attempts=attempt + 1,
                )
                logger.warning(
                    "gemini_api_timeout",
                    extra={"attempt": attempt + 1},
                )
                # Try rotating key on timeout too
                if keys_tried < total_keys:
                    self._rotate_key()
                    keys_tried += 1

                backoff = min(2 ** attempt, 30)
                await asyncio.sleep(backoff)

            except httpx.HTTPError as exc:
                last_error = LLMProviderError(
                    f"Gemini HTTP error: {exc}",
                    provider="gemini",
                    attempts=attempt + 1,
                )
                logger.error(
                    "gemini_api_http_error",
                    extra={
                        "error": str(exc),
                        "attempt": attempt + 1,
                    },
                )
                backoff = min(2 ** attempt, 30)
                await asyncio.sleep(backoff)

        raise last_error or LLMProviderError(
            "All Gemini API attempts exhausted",
            provider="gemini",
            attempts=self.max_retries,
        )

    async def generate(self, prompt: str, response_format: str = "json") -> dict:
        """
        Generate a structured JSON response from Gemini.

        Args:
            prompt (str): The input prompt.
            response_format (str): Expected response format (currently only "json").

        Returns:
            dict: Parsed JSON response.

        Raises:
            LLMProviderError: If generation fails.
        """
        logger.info(
            "gemini_generate_start",
            extra={
                "prompt_length": len(prompt),
                "model": self.model,
                "format": response_format,
            },
        )

        payload = self._build_payload(prompt)
        response_data = await self._call_api(payload)
        text = self._extract_text_from_response(response_data)
        result = self._parse_json_response(text)

        logger.info(
            "gemini_generate_complete",
            extra={
                "response_keys": list(result.keys()) if isinstance(result, dict) else "non-dict",
            },
        )
        return result

    async def generate_text(self, prompt: str) -> str:
        """
        Generate a plain text response from Gemini.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: Text response.

        Raises:
            LLMProviderError: If generation fails.
        """
        logger.info(
            "gemini_generate_text_start",
            extra={
                "prompt_length": len(prompt),
                "model": self.model,
            },
        )

        payload = self._build_text_payload(prompt)
        response_data = await self._call_api(payload)
        text = self._extract_text_from_response(response_data)

        logger.info(
            "gemini_generate_text_complete",
            extra={"response_length": len(text)},
        )
        return text
