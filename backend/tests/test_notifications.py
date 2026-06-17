"""Notification tests (created on homework submit, mark read)."""

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
    db_file = tmp_path / "notifications.db"
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
                    track=ExamTrack.EGE,
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


def test_homework_submit_creates_notification(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = client.get("/api/students").json()[0]["id"]
    assignment_id = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Лекция",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    ).json()["id"]

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert client.post(f"/api/homework/{assignment_id}/submit", json={}).status_code == 200

    client.post("/api/auth/logout")
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    unread = client.get("/api/notifications/unread-count")
    assert unread.status_code == 200
    assert unread.json()["count"] == 1

    notifications = client.get("/api/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "homework_submitted"
    assert notifications[0]["payload"]["homework_id"] == assignment_id
    assert notifications[0]["read_at"] is None

    mark = client.patch(f"/api/notifications/{notifications[0]['id']}/read")
    assert mark.status_code == 200
    assert mark.json()["read_at"] is not None

    unread_after = client.get("/api/notifications/unread-count").json()
    assert unread_after["count"] == 0


def test_student_cannot_list_notifications(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert client.get("/api/notifications").status_code == 403
