"""Exam content self_check steps (EGE types 29–34) — §1.10 Task 88."""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import quote

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

TEACHER_EMAIL = "teacher-exam-written@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-exam-written@example.com"
STUDENT_PASS = "student-pass"

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_ege_db_with_written(path: Path) -> None:
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
    conn.execute(
        "CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)"
    )
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("001.txt", 1, "Q exact", "1", 0),
            (
                "001.txt",
                29,
                "Written Q29",
                "Разбор [ответ0001]",
                0,
            ),
        ],
    )
    conn.execute(
        "INSERT INTO images (filename, data) VALUES (?, ?)",
        ("ответ0001.png", PNG_BYTES),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "exam_self_check_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"
    ege_db = tmp_path / "test_ege.db"
    _create_ege_db_with_written(ege_db)

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
            CONTENT_EGE_DB_PATH=str(ege_db),
            JWT_SECRET="test-jwt-secret-exam-self-check-32b",
            UPLOAD_DIR=str(upload_dir),
            FRONTEND_URL="http://localhost:3000",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": password}).status_code
        == 200
    )


def _student_id(client: TestClient) -> str:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    return client.get("/api/students").json()[0]["id"]


def _upload_image(client: TestClient) -> str:
    response = client.post(
        "/api/uploads/images",
        files={"file": ("work.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_homework_partial(client: TestClient) -> str:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "EGE written",
            "items": [
                {"kind": "test_partial", "variant": "001.txt", "types": [1, 29]},
            ],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def _practice_session(client: TestClient) -> dict:
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.post(
        "/api/tests/sessions",
        json={"variant_ref": "001.txt"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_step_read_marks_type_29_as_self_check(client: TestClient) -> None:
    session = _practice_session(client)
    written = next(step for step in session["steps"] if step["type"] == 29)
    exact = next(step for step in session["steps"] if step["type"] == 1)
    assert written["grading_mode"] == "self_check"
    assert exact.get("grading_mode") is None


def test_check_rejects_self_check_step(client: TestClient) -> None:
    session = _practice_session(client)
    position = next(step["position"] for step in session["steps"] if step["type"] == 29)
    response = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/check",
        json={"answer": "мой ответ"},
    )
    assert response.status_code == 422
    assert "compare" in response.json()["detail"].lower()


def test_compare_rejects_exact_step(client: TestClient) -> None:
    session = _practice_session(client)
    position = next(step["position"] for step in session["steps"] if step["type"] == 1)
    response = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/compare",
        json={"answer": "1"},
    )
    assert response.status_code == 422
    assert "check" in response.json()["detail"].lower()


def test_practice_compare_without_photo_ok(client: TestClient) -> None:
    session = _practice_session(client)
    position = next(step["position"] for step in session["steps"] if step["type"] == 29)
    compare = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/compare",
        json={"answer": "мой разбор"},
    )
    assert compare.status_code == 200, compare.text
    data = compare.json()
    assert data["status"] == "checked"
    assert data["reference_answer"][0]["content"] == "Разбор "
    image_url = f"/api/tests/images/{quote('ответ0001.png')}"
    assert data["reference_answer"][1]["url"] == image_url


def test_homework_compare_without_photo_returns_422(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    position = next(step["position"] for step in session["steps"] if step["type"] == 29)

    compare = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/compare",
        json={"answer": "мой разбор"},
    )
    assert compare.status_code == 422
    assert "image" in compare.json()["detail"].lower()


def test_homework_attach_and_compare_with_photo(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    position = next(step["position"] for step in session["steps"] if step["type"] == 29)
    image_id = _upload_image(client)

    attach = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/answer-image",
        json={"answer_image_id": image_id},
    )
    assert attach.status_code == 200, attach.text
    assert attach.json()["answer_image_id"] == image_id

    compare = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/compare",
        json={"answer": "мой разбор"},
    )
    assert compare.status_code == 200, compare.text

    attach_again = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/answer-image",
        json={"answer_image_id": image_id},
    )
    assert attach_again.status_code == 409


def test_homework_handoff_for_exam_self_check_step(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    position = next(step["position"] for step in session["steps"] if step["type"] == 29)

    handoff = client.post(
        f"/api/tests/sessions/{session['id']}/steps/{position}/handoff",
    )
    assert handoff.status_code == 200, handoff.text
    body = handoff.json()
    assert body["token"]
    assert "/student/capture/" in body["capture_url"]

    meta = client.get(f"/api/capture/{body['token']}")
    assert meta.status_code == 200, meta.text
    assert meta.json()["question_preview"] == "Written Q29"


def test_complete_session_score_includes_written_steps(client: TestClient) -> None:
    session = _practice_session(client)
    session_id = session["id"]
    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)
    written_pos = next(step["position"] for step in session["steps"] if step["type"] == 29)

    assert (
        client.post(
            f"/api/tests/sessions/{session_id}/steps/{exact_pos}/check",
            json={"answer": "1"},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/tests/sessions/{session_id}/steps/{written_pos}/compare",
            json={"answer": "разбор"},
        ).status_code
        == 200
    )

    summary = client.post(f"/api/tests/sessions/{session_id}/complete").json()
    assert summary["max_score"] == 2
    assert summary["score"] == 2
    written_summary = next(
        step for step in summary["steps"] if step.get("type") == 29
    )
    assert written_summary["grading_mode"] == "self_check"
