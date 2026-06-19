"""Tests catalog API (variants, questions, track isolation, RBAC)."""

from __future__ import annotations

import asyncio
import sqlite3
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
from tests.content.conftest import _create_tests_db

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
EGE_STUDENT_EMAIL = "ege-student@example.com"
OGE_STUDENT_EMAIL = "oge-student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "tests_api_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    oge_db = tmp_path / "test_oge.db"
    _create_tests_db(ege_db, with_bug=True)

    conn_oge = sqlite3.connect(oge_db)
    conn_oge.executescript(
        """
        CREATE TABLE tests (
            filename TEXT, type INTEGER, question TEXT, options TEXT,
            correct_ans TEXT, hint TEXT, detailed_explanation TEXT,
            has_issue INTEGER DEFAULT 0
        );
        CREATE TABLE tests_bug (filename TEXT);
        """
    )
    conn_oge.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("001.txt", 1, "OGE Q1", "1", 0),
            ("019.txt", 1, "OGE Q19", "4", 0),
        ],
    )
    conn_oge.commit()
    conn_oge.close()

    teacher_id = uuid.uuid4()
    ege_student_id = uuid.uuid4()
    oge_student_id = uuid.uuid4()

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
                        id=ege_student_id,
                        email=EGE_STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=oge_student_id,
                        email=OGE_STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    StudentProfile(
                        user_id=ege_student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                    ),
                    StudentProfile(
                        user_id=oge_student_id,
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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-tests-api-32-bytes",
            CONTENT_EGE_DB_PATH=str(ege_db),
            CONTENT_OGE_DB_PATH=str(oge_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str = STUDENT_PASS):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_ege_student_lists_task_types(client: TestClient) -> None:
    assert _login(client, EGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/task-types")
    assert response.status_code == 200
    assert response.json() == [
        {"type": 1, "variant_count": 1},
        {"type": 2, "variant_count": 1},
    ]


def test_ege_student_lists_variants(client: TestClient) -> None:
    assert _login(client, EGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/variants")
    assert response.status_code == 200
    assert response.json() == [{"filename": "001.txt"}]


def test_oge_student_lists_oge_variants(client: TestClient) -> None:
    assert _login(client, OGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/variants")
    assert response.status_code == 200
    filenames = [item["filename"] for item in response.json()]
    assert filenames == ["001.txt", "019.txt"]


def test_track_isolation_ege_student_does_not_see_oge_only_variant(
    client: TestClient,
) -> None:
    assert _login(client, EGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/variants/019.txt/questions")
    assert response.status_code == 404


def test_ege_student_lists_questions_without_sensitive_fields(
    client: TestClient,
) -> None:
    assert _login(client, EGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/variants/001.txt/questions")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["type"] == 1
    assert body[0]["question"] == "Q1"
    assert "correct_ans" not in body[0]
    assert "hint" not in body[0]
    assert "detailed_explanation" not in body[0]
    assert "hint" not in body[0]
    assert "detailed_explanation" not in body[0]


def test_has_issue_questions_excluded(client: TestClient) -> None:
    assert _login(client, EGE_STUDENT_EMAIL).status_code == 200

    response = client.get("/api/tests/variants/002.txt/questions")
    assert response.status_code == 404


def test_teacher_lists_variants_with_track(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.get("/api/tests/variants", params={"track": "ege"})
    assert response.status_code == 200
    assert response.json() == [{"filename": "001.txt"}]


def test_teacher_variants_requires_track(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    assert client.get("/api/tests/variants").status_code == 422


def test_unauthenticated_returns_401(client: TestClient) -> None:
    assert client.get("/api/tests/variants").status_code == 401
