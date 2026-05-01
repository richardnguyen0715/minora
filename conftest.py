import os
import sys

import pytest


def pytest_configure(config):
    """Configure test environment before any tests run."""
    # Set environment variables VERY EARLY, before any app imports
    os.environ["TELEGRAM_TOKEN"] = "test_token"
    os.environ["TELEGRAM_WEBHOOK_URL"] = "http://localhost:8000/webhook"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["APP_HOST"] = "localhost"
    os.environ["APP_PORT"] = "8000"


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup after pytest_configure."""
    pass
