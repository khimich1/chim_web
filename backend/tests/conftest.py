"""Shared pytest fixtures.

TestClient usage:
https://fastapi.tiangolo.com/tutorial/testing/
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Defaults for tests — no live PostgreSQL required (sqlite+aiosqlite in-memory).
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-at-least-32-bytes-long")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.core.config import Settings, get_settings  # noqa: E402
from app.core.rate_limit import reset_limiter_storage  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Prevent slowapi counter bleed between tests."""
    reset_limiter_storage()
    yield
    reset_limiter_storage()


@pytest.fixture
def test_settings() -> Settings:
    get_settings.cache_clear()
    return Settings()


@pytest.fixture
def app(test_settings: Settings):
    get_settings.cache_clear()
    return create_app(settings=test_settings)


@pytest.fixture
def client(app) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
