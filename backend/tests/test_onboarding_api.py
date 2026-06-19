"""Onboarding API tests."""

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
NEW_STUDENT_EMAIL = "new@example.com"
NEW_STUDENT_PASS = "new-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "onboarding.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    new_student_id = uuid.uuid4()

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
                    User(
                        id=new_student_id,
                        email=NEW_STUDENT_EMAIL,
                        password_hash=hash_password(NEW_STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            from datetime import datetime, timezone

            session.add_all(
                [
                    StudentProfile(
                        user_id=student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                        onboarding_completed_at=datetime.now(timezone.utc),
                        onboarding_checklist={
                            "login": True,
                            "first_action": True,
                            "lecture": True,
                        },
                    ),
                    StudentProfile(
                        user_id=new_student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                    ),
                ]
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

    app.dependency_overrides.clear()
    get_settings.cache_clear()
    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert response.status_code == 200


def test_onboarding_needs_welcome_for_new_student(client: TestClient) -> None:
    _login(client, NEW_STUDENT_EMAIL, NEW_STUDENT_PASS)
    response = client.get("/api/students/me/onboarding")
    assert response.status_code == 200
    body = response.json()
    assert body["needs_welcome"] is True
    assert body["checklist"]["login"] is True
    assert body["first_login_at"] is not None


def test_onboarding_completed_for_existing_student(client: TestClient) -> None:
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.get("/api/students/me/onboarding")
    assert response.status_code == 200
    body = response.json()
    assert body["needs_welcome"] is False


def test_complete_welcome(client: TestClient) -> None:
    _login(client, NEW_STUDENT_EMAIL, NEW_STUDENT_PASS)
    response = client.patch(
        "/api/students/me/onboarding",
        json={"complete_welcome": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["needs_welcome"] is False
    assert body["onboarding_completed_at"] is not None


def test_mark_lecture_step(client: TestClient) -> None:
    _login(client, NEW_STUDENT_EMAIL, NEW_STUDENT_PASS)
    response = client.patch(
        "/api/students/me/onboarding",
        json={"mark_step": "lecture"},
    )
    assert response.status_code == 200
    assert response.json()["checklist"]["lecture"] is True


def test_teacher_sees_activation_status(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.get("/api/students")
    assert response.status_code == 200
    students = {item["email"]: item for item in response.json()}
    assert students[STUDENT_EMAIL]["is_activated"] is True
    assert students[NEW_STUDENT_EMAIL]["is_activated"] is False


def test_complete_welcome_records_analytics(client: TestClient) -> None:
    _login(client, NEW_STUDENT_EMAIL, NEW_STUDENT_PASS)
    client.get("/api/students/me/onboarding/welcome")
    response = client.patch(
        "/api/students/me/onboarding",
        json={"complete_welcome": True, "mark_step": "first_action"},
    )
    assert response.status_code == 200

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    students = {s["email"]: s for s in client.get("/api/students").json()}
    assert students[NEW_STUDENT_EMAIL]["is_activated"] is True


def test_onboarding_forbidden_for_teacher(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.get("/api/students/me/onboarding")
    assert response.status_code == 403
