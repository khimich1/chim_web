"""Tests for settings, CORS, and database session dependency."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import dispose_engine, get_db, init_engine


def test_settings_loads_required_fields(test_settings: Settings) -> None:
    assert test_settings.database_url.startswith("sqlite+aiosqlite:")
    assert test_settings.jwt_secret == "test-jwt-secret"
    assert test_settings.cors_origins == ["http://localhost:3000"]


def test_settings_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()


def test_settings_requires_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET", raising=False)
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()


def test_settings_parses_multiple_cors_origins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    )
    get_settings.cache_clear()
    settings = Settings()
    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_cors_preflight_allows_credentials(client) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_get_db_yields_and_closes_session() -> None:
    await dispose_engine()
    init_engine("sqlite+aiosqlite:///:memory:")

    generator = get_db()
    session = await generator.__anext__()
    try:
        assert isinstance(session, AsyncSession)
        assert session.is_active
    finally:
        await generator.aclose()
        await dispose_engine()
