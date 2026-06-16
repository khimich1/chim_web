"""Students API tests (teacher CRUD, RBAC)."""

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
from app.models import ExamTrack, StudentProfile, User, UserRole

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "students.db"
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


def test_teacher_lists_own_students(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.get("/api/students")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["email"] == STUDENT_EMAIL
    assert body[0]["track"] == "oge"
    assert "id" in body[0]
    assert "created_at" in body[0]


def test_teacher_creates_student(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.post(
        "/api/students",
        json={
            "email": "new-student@example.com",
            "password": "temp-pass",
            "track": "ege",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-student@example.com"
    assert body["track"] == "ege"

    list_response = client.get("/api/students")
    emails = [item["email"] for item in list_response.json()]
    assert "new-student@example.com" in emails


def test_created_student_can_login(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    assert (
        client.post(
            "/api/students",
            json={
                "email": "login-test@example.com",
                "password": "login-pass",
                "track": "oge",
            },
        ).status_code
        == 201
    )

    client.post("/api/auth/logout")
    login_response = _login(client, "login-test@example.com", "login-pass")
    assert login_response.status_code == 200
    body = login_response.json()
    assert body["role"] == "student"
    assert body["track"] == "oge"


def test_student_cannot_list_students(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    assert client.get("/api/students").status_code == 403


def test_student_cannot_create_student(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.post(
        "/api/students",
        json={
            "email": "hacker@example.com",
            "password": "temp-pass",
            "track": "ege",
        },
    )
    assert response.status_code == 403


def test_unauthenticated_returns_401(client: TestClient) -> None:
    assert client.get("/api/students").status_code == 401
    assert (
        client.post(
            "/api/students",
            json={
                "email": "x@example.com",
                "password": "temp-pass",
                "track": "ege",
            },
        ).status_code
        == 401
    )


def test_duplicate_email_returns_409(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.post(
        "/api/students",
        json={
            "email": STUDENT_EMAIL,
            "password": "temp-pass",
            "track": "ege",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"
