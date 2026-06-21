"""Rate limiting on auth login and tutor chat (Task 98 / Phase 17e)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import User, UserRole

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"


@pytest.fixture
def login_client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "rate_limit_auth.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add(
                User(
                    id=uuid.uuid4(),
                    email=TEACHER_EMAIL,
                    password_hash=hash_password(TEACHER_PASS),
                    role=UserRole.TEACHER,
                )
            )
            await session.commit()
        await engine.dispose()

    asyncio.run(_setup())

    request_engine = create_async_engine(db_url, poolclass=NullPool)
    request_sessions = async_sessionmaker(request_engine, expire_on_commit=False)

    async def _override_get_db():
        async with request_sessions() as session:
            yield session

    get_settings.cache_clear()
    app = create_app(
        settings=Settings(
            auth_login_rate_limit="5/minute",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def test_login_burst_returns_429(login_client: TestClient) -> None:
    payload = {"email": TEACHER_EMAIL, "password": "wrong-pass"}

    for _ in range(5):
        response = login_client.post("/api/auth/login", json=payload)
        assert response.status_code == 401

    blocked = login_client.post("/api/auth/login", json=payload)
    assert blocked.status_code == 429
    assert blocked.json()["error"] == "Rate limit exceeded: 5 per 1 minute"


def test_default_access_token_ttl_is_sixty_minutes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ACCESS_TOKEN_EXPIRE_MINUTES", raising=False)
    get_settings.cache_clear()
    settings = Settings(_env_file=None)
    assert settings.access_token_expire_minutes == 60
