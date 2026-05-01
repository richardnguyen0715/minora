from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    Attributes:
        telegram_token (str): Telegram Bot API token.
        telegram_webhook_url (str): URL where Telegram will send updates.
        telegram_chat_id (str, optional): Telegram Chat ID to filter/restrict messages.
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
    redis_url: str = Field(default="redis://localhost:6379")
    log_level: str = Field(default="INFO")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)


settings = Settings()
