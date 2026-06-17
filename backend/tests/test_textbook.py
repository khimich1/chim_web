"""Textbook API tests (student RBAC, topics, chunks, audio)."""

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
from tests.content.conftest import _create_lectures_db

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "textbook_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    lectures_db = tmp_path / "prepared_lectures.db"
    _create_lectures_db(lectures_db)

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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-textbook",
            CONTENT_LECTURES_DB_PATH=str(lectures_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_student_lists_topics_in_db_order(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/topics")
    assert response.status_code == 200
    body = response.json()
    assert [item["topic"] for item in body] == ["Соли", "Алканы"]
    assert body[0]["chunk_count"] == 2


def test_student_lists_chunk_summaries_without_lecture_body(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/topics/Соли/chunks")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0] == {
        "chunk_idx": 0,
        "chunk_title": "Введение",
        "has_audio": False,
    }
    assert body[1]["has_audio"] is True
    assert "lecture" not in body[0]


def test_student_gets_chunk_with_lecture_markdown(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/topics/Соли/chunks/0")
    assert response.status_code == 200
    body = response.json()
    assert body["topic"] == "Соли"
    assert body["chunk_idx"] == 0
    assert body["chunk_title"] == "Введение"
    assert body["lecture"] == "# Соли"
    assert body["has_audio"] is False


def test_student_streams_audio_for_chunk_with_tts(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.get("/api/textbook/topics/Соли/chunks/1/audio")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/ogg")
    assert response.content == b"audio"


def test_audio_returns_404_when_missing(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    assert client.get("/api/textbook/topics/Соли/chunks/0/audio").status_code == 404


def test_teacher_can_list_topics(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.get("/api/textbook/topics")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_teacher_cannot_access_textbook_chunks(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    assert client.get("/api/textbook/topics/Соли/chunks").status_code == 403


def test_unauthenticated_returns_401(client: TestClient) -> None:
    assert client.get("/api/textbook/topics").status_code == 401


def test_unknown_topic_returns_404(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    assert client.get("/api/textbook/topics/Нет такой/chunks").status_code == 404


def test_unknown_chunk_returns_404(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    assert client.get("/api/textbook/topics/Соли/chunks/99").status_code == 404
