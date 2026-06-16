"""Auth endpoint and RBAC dependency tests.

DB strategy: a file-based SQLite per test (tmp_path). Setup/seed runs in its own
event loop and disposes; the request-time engine uses NullPool so connections are
never shared across event loops (avoids aiosqlite cross-loop errors).
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import require_student, require_teacher
from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, StudentProfile, User, UserRole

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "auth.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add_all(
                [
                    User(
                        id=teacher_id,
                        email=TEACHER_EMAIL,
                        password_hash=hash_password(TEACHER_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add(
                StudentProfile(
                    user_id=student_id,
                    teacher_id=teacher_id,
                    track=ExamTrack.OGE,
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
    app = create_app(settings=Settings())
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_login_returns_user_and_sets_httponly_cookie(client: TestClient) -> None:
    response = _login(client, TEACHER_EMAIL, TEACHER_PASS)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == TEACHER_EMAIL
    assert body["role"] == "teacher"
    assert body["track"] is None

    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "access_token=" in set_cookie
    assert "httponly" in set_cookie


def test_login_does_not_leak_token_in_body(client: TestClient) -> None:
    body = _login(client, TEACHER_EMAIL, TEACHER_PASS).json()
    assert set(body.keys()) == {"id", "email", "role", "track"}


def test_login_with_wrong_password_returns_401(client: TestClient) -> None:
    response = _login(client, TEACHER_EMAIL, "wrong-pass")
    assert response.status_code == 401
    assert "set-cookie" not in response.headers


def test_login_unknown_email_returns_401(client: TestClient) -> None:
    assert _login(client, "nobody@example.com", "x").status_code == 401


def test_me_returns_track_for_student(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/auth/me")
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == STUDENT_EMAIL
    assert body["role"] == "student"
    assert body["track"] == "oge"


def test_me_without_cookie_returns_401(client: TestClient) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_logout_clears_cookie_and_me_then_401(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    assert client.get("/api/auth/me").status_code == 200

    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_logout_without_auth_returns_401(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 401


def _user(role: UserRole) -> User:
    return User(email="x@example.com", password_hash="x", role=role)


def test_require_teacher_allows_teacher_blocks_student() -> None:
    teacher = _user(UserRole.TEACHER)
    assert require_teacher(teacher) is teacher

    with pytest.raises(HTTPException) as exc:
        require_teacher(_user(UserRole.STUDENT))
    assert exc.value.status_code == 403


def test_require_student_allows_student_blocks_teacher() -> None:
    student = _user(UserRole.STUDENT)
    assert require_student(student) is student

    with pytest.raises(HTTPException) as exc:
        require_student(_user(UserRole.TEACHER))
    assert exc.value.status_code == 403
