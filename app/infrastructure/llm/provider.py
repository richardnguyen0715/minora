"""Abstract LLM provider interface for infrastructure layer."""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract base for LLM service providers.

    Implementations must handle API communication, retries, and response parsing.
    The interface is kept minimal to allow easy swapping of providers
    (Gemini, OpenAI, local models, etc.).
    """

    @abstractmethod
    async def generate(self, prompt: str, response_format: str = "json") -> dict:
        """
        Generate a structured JSON response from a prompt.

        Args:
            prompt (str): The input prompt.
            response_format (str): Expected response format hint.

        Returns:
            dict: Parsed JSON response from the LLM.

        Raises:
            LLMProviderError: If generation fails after all retries.
        """
        pass

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Generate a plain text response from a prompt.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: Text response from the LLM.

        Raises:
            LLMProviderError: If generation fails after all retries.
        """
        pass


class LLMProviderError(Exception):
    """Raised when LLM provider fails after exhausting retries."""

    def __init__(self, message: str, provider: str = "unknown", attempts: int = 0):
        """
        Initialize LLM provider error.

        Args:
            message (str): Error description.
            provider (str): Provider name that failed.
            attempts (int): Number of attempts made before failure.
        """
        self.provider = provider
        self.attempts = attempts
        super().__init__(f"[{provider}] {message} (attempts={attempts})")
