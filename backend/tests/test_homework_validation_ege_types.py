"""Homework validation for EGE task types 1–34 (Task 90)."""

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

TEACHER_EMAIL = "teacher-hw-val@example.com"
TEACHER_PASS = "teacher-pass"
EGE_STUDENT_EMAIL = "ege-student@example.com"
OGE_STUDENT_EMAIL = "oge-student@example.com"
STUDENT_PASS = "student-pass"


def _create_ege_db_with_written_types(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tests (
            filename TEXT, type INTEGER, question TEXT, options TEXT,
            correct_ans TEXT, hint TEXT, detailed_explanation TEXT,
            has_issue INTEGER DEFAULT 0
        )
        """
    )
    conn.execute("CREATE TABLE tests_bug (filename TEXT)")
    conn.execute("CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)")
    rows = [
        ("001.txt", 1, "Q1", "1", 0),
        ("001.txt", 28, "Q28", "28", 0),
    ]
    for type_num in range(29, 35):
        rows.append(
            (
                "001.txt",
                type_num,
                f"Written Q{type_num}",
                f"Разбор [ответ{type_num:04d}]",
                0,
            )
        )
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()


def _create_oge_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tests (
            filename TEXT, type INTEGER, question TEXT, options TEXT,
            correct_ans TEXT, hint TEXT, detailed_explanation TEXT,
            has_issue INTEGER DEFAULT 0
        )
        """
    )
    conn.execute("CREATE TABLE tests_bug (filename TEXT)")
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("001.txt", 1, "OGE Q1", "1", 0),
            ("019.txt", 1, "OGE Q19", "4", 0),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "homework_validation_ege.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    oge_db = tmp_path / "test_oge.db"
    _create_ege_db_with_written_types(ege_db)
    _create_oge_db(oge_db)

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
            CONTENT_EGE_DB_PATH=str(ege_db),
            CONTENT_OGE_DB_PATH=str(oge_db),
            JWT_SECRET="test-jwt-secret-hw-validation-ege-types",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient) -> None:
    assert (
        client.post(
            "/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": TEACHER_PASS},
        ).status_code
        == 200
    )


def _student_id(client: TestClient, track: ExamTrack) -> str:
    email = EGE_STUDENT_EMAIL if track == ExamTrack.EGE else OGE_STUDENT_EMAIL
    students = client.get("/api/students").json()
    return next(student["id"] for student in students if student["email"] == email)


def _create_homework(client: TestClient, *, track: ExamTrack, items: list[dict]) -> dict:
    student_id = _student_id(client, track)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Validation test",
            "items": items,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.parametrize("type_num", [29, 30, 31, 32, 33, 34])
def test_ege_test_by_type_accepts_written_types(
    client: TestClient,
    type_num: int,
) -> None:
    _login(client)
    body = _create_homework(
        client,
        track=ExamTrack.EGE,
        items=[{"kind": "test_by_type", "types": [type_num]}],
    )
    assert body["items"][0]["types"] == [type_num]


@pytest.mark.parametrize("type_num", [29, 34])
def test_ege_test_partial_accepts_written_types(
    client: TestClient,
    type_num: int,
) -> None:
    _login(client)
    body = _create_homework(
        client,
        track=ExamTrack.EGE,
        items=[
            {
                "kind": "test_partial",
                "variant": "001.txt",
                "types": [1, type_num],
            }
        ],
    )
    assert body["items"][0]["types"] == [1, type_num]


def test_ege_test_variant_accepts_variant_with_written_types(client: TestClient) -> None:
    _login(client)
    body = _create_homework(
        client,
        track=ExamTrack.EGE,
        items=[{"kind": "test_variant", "variant": "001.txt"}],
    )
    assert body["items"][0]["variant"] == "001.txt"


def test_ege_rejects_type_35_for_test_by_type(client: TestClient) -> None:
    _login(client)
    student_id = _student_id(client, ExamTrack.EGE)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Out of range",
            "items": [{"kind": "test_by_type", "types": [35]}],
        },
    )
    assert response.status_code == 422
    assert "out of range" in response.json()["detail"]


def test_ege_rejects_type_35_for_test_partial(client: TestClient) -> None:
    _login(client)
    student_id = _student_id(client, ExamTrack.EGE)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Out of range partial",
            "items": [
                {
                    "kind": "test_partial",
                    "variant": "001.txt",
                    "types": [35],
                }
            ],
        },
    )
    assert response.status_code == 422
    assert "out of range" in response.json()["detail"]


def test_oge_rejects_type_29_for_test_by_type(client: TestClient) -> None:
    _login(client)
    student_id = _student_id(client, ExamTrack.OGE)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "OGE out of range",
            "items": [{"kind": "test_by_type", "types": [29]}],
        },
    )
    assert response.status_code == 422
    assert "out of range" in response.json()["detail"]


def test_oge_test_by_type_still_accepts_type_19(client: TestClient) -> None:
    _login(client)
    body = _create_homework(
        client,
        track=ExamTrack.OGE,
        items=[{"kind": "test_by_type", "types": [19]}],
    )
    assert body["items"][0]["types"] == [19]


@pytest.mark.parametrize(
    ("kind", "payload"),
    [
        (
            "test_by_type",
            {"kind": "test_by_type", "types": [1], "variants": ["missing.txt"]},
        ),
        (
            "test_partial",
            {
                "kind": "test_partial",
                "variant": "missing.txt",
                "types": [1],
            },
        ),
        ("test_variant", {"kind": "test_variant", "variant": "missing.txt"}),
    ],
)
def test_rejects_unknown_variant(
    client: TestClient,
    kind: str,
    payload: dict,
) -> None:
    _login(client)
    student_id = _student_id(client, ExamTrack.EGE)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": f"Unknown variant for {kind}",
            "items": [payload],
        },
    )
    assert response.status_code == 422
    assert "Unknown variant" in response.json()["detail"]


def test_rejects_missing_content_type_for_test_by_type(client: TestClient) -> None:
    _login(client)
    student_id = _student_id(client, ExamTrack.EGE)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Missing type in content",
            "items": [{"kind": "test_by_type", "types": [27]}],
        },
    )
    assert response.status_code == 422
    assert "No questions found" in response.json()["detail"]
