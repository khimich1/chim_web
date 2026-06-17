"""Homework API tests (assign, list, RBAC, submit)."""

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
OTHER_STUDENT_EMAIL = "other@example.com"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "homework.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()

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
                        id=other_student_id,
                        email=OTHER_STUDENT_EMAIL,
                        password_hash=hash_password("other-pass"),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    StudentProfile(
                        user_id=student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                    ),
                    StudentProfile(
                        user_id=other_student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.OGE,
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

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_teacher_creates_lecture_homework(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    students = client.get("/api/students").json()
    student_id = students[0]["id"]

    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Прочитать Алканы",
            "description": "Глава 1",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Прочитать Алканы"
    assert body["status"] == "assigned"
    assert body["items"][0]["kind"] == "lecture"
    assert body["student_email"] == STUDENT_EMAIL


def test_student_lists_own_homework(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = client.get("/api/students").json()[0]["id"]
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Тестовое ДЗ",
            "items": [{"kind": "lecture", "topic": "Соли"}],
        },
    )
    assignment_id = create.json()["id"]

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    listed = client.get("/api/homework").json()
    assert len(listed) == 1
    assert listed[0]["id"] == assignment_id
    assert listed[0]["student_email"] is None

    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200


def test_student_submits_lecture_homework(client: TestClient) -> None:
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

    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200
    assert submit.json()["status"] == "submitted"
    assert submit.json()["submission"]["test_session_id"] is None

    again = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert again.status_code == 409


def test_student_cannot_access_other_homework(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    students = client.get("/api/students").json()
    other_id = next(item["id"] for item in students if item["email"] == OTHER_STUDENT_EMAIL)
    assignment_id = client.post(
        "/api/homework",
        json={
            "student_id": other_id,
            "title": "Чужое ДЗ",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    ).json()["id"]

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert client.get(f"/api/homework/{assignment_id}").status_code == 403


def test_teacher_cannot_create_for_unknown_student(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    response = client.post(
        "/api/homework",
        json={
            "student_id": str(uuid.uuid4()),
            "title": "Нет ученика",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert response.status_code == 404


def test_student_cannot_create_homework(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    response = client.post(
        "/api/homework",
        json={
            "student_id": str(uuid.uuid4()),
            "title": "Хак",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert response.status_code == 403
