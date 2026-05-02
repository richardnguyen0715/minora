from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Attributes:
        telegram_token (str): Telegram Bot API token.
        telegram_webhook_url (str): URL where Telegram will send updates.
        telegram_chat_id (str, optional): Telegram Chat ID to filter/restrict messages.
        gemini_api_keys (list[str]): Gemini API keys for rotation (comma-separated).
        agents_config_path (str): Path to agents pipeline YAML config.
        redis_url (str): Redis connection URL for queue.
        log_level (str): Logging level.
        app_host (str): Application host for FastAPI.
        app_port (int): Application port for FastAPI.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    telegram_token: str
    telegram_webhook_url: str
    telegram_chat_id: str | None = Field(default=None)
    gemini_api_keys: str = Field(default="")
    agents_config_path: str = Field(default="configs/agents.yaml")
    redis_url: str = Field(default="redis://localhost:6379")
    log_level: str = Field(default="INFO")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    def get_gemini_keys(self) -> list[str]:
        """
        Parse comma-separated Gemini API keys.

        Returns:
            list[str]: List of non-empty API keys.
        """
        if not self.gemini_api_keys:
            return []
        return [key.strip() for key in self.gemini_api_keys.split(",") if key.strip()]

    def get_agents_config(self) -> dict:
        """
        Load agents pipeline configuration from YAML.

        Returns:
            dict: Parsed YAML configuration.
        """
        import yaml

        config_path = Path(self.agents_config_path)
        if not config_path.exists():
            return {}
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}


settings = Settings()
