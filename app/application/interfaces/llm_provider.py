"""Abstract LLM provider interface for the application layer (clean architecture boundary)."""

from abc import ABC, abstractmethod


class LLMProviderInterface(ABC):
    """
    Application-layer interface for LLM providers.

    This interface lives in the application layer so that use cases
    can depend on it without knowing about infrastructure details.
    """

    @abstractmethod
    async def generate(self, prompt: str, response_format: str = "json") -> dict:
        """
        Generate a structured JSON response.

        Args:
            prompt (str): The input prompt.
            response_format (str): Expected response format hint.

        Returns:
            dict: Parsed JSON response from the LLM.
        """
        pass

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Generate a plain text response.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: Text response from the LLM.
        """
        pass
