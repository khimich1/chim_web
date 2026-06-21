"""Homework layer for exam content self_check steps (EGE 29–34) — §1.10 Task 89."""

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

TEACHER_EMAIL = "teacher-hw-written@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-hw-written@example.com"
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
    db_file = tmp_path / "homework_content_written_app.db"
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
            JWT_SECRET="test-jwt-secret-hw-content-written",
            UPLOAD_DIR=str(upload_dir),
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
            "title": "EGE written HW",
            "items": [
                {"kind": "test_partial", "variant": "001.txt", "types": [1, 29]},
            ],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def _written_step_position(session: dict) -> int:
    return next(step["position"] for step in session["steps"] if step["type"] == 29)


def test_partial_submit_allows_unchecked_exam_self_check_without_photo(
    client: TestClient,
) -> None:
    """Task 100: photo required only on checked self_check steps (§1.7 partial submit)."""
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    written_pos = _written_step_position(session)

    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)
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
            json={"answer": "мой разбор"},
        ).status_code
        == 422
    )

    client.post(f"/api/tests/sessions/{session_id}/complete")
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["submission"]["answered_steps"] == 1
    assert body["submission"]["total_steps"] == 2
    assert body["can_reopen"] is True


def test_submit_score_includes_written_step(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    written_pos = _written_step_position(session)
    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{exact_pos}/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/compare",
        json={"answer": "мой разбор"},
    )

    summary = client.post(f"/api/tests/sessions/{session_id}/complete").json()
    assert summary["max_score"] == 2
    assert summary["score"] == 2

    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["submission"]["score"] == 2
    assert body["submission"]["max_score"] == 2


def test_teacher_detail_includes_reference_and_photo(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    written_pos = _written_step_position(session)
    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{exact_pos}/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/compare",
        json={"answer": "мой разбор"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    client.post(f"/api/homework/{assignment_id}/submit", json={})

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()

    written_steps = [
        step
        for step in body["submission_steps"]
        if step.get("grading_mode") == "self_check"
    ]
    assert len(written_steps) == 1
    step = written_steps[0]
    assert step["title"] == "Задание 29"
    assert step["answer_image_url"] == f"/api/uploads/images/{image_id}"
    assert step["answer"] == "мой разбор"
    assert step["question_blocks"][0]["content"] == "Written Q29"
    assert step["reference_answer"][0]["content"] == "Разбор "
    image_url = f"/api/tests/images/{quote('ответ0001.png')}"
    assert step["reference_answer"][1]["url"] == image_url


def test_teacher_feedback_on_content_exam_step(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    written_pos = _written_step_position(session)
    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{exact_pos}/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/compare",
        json={"answer": "мой разбор"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    client.post(f"/api/homework/{assignment_id}/submit", json={})

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    feedback = client.put(
        f"/api/homework/{assignment_id}/steps/{written_pos}/feedback",
        json={"teacher_text": "Хороший разбор уравнения"},
    )
    assert feedback.status_code == 200, feedback.text
    fb = feedback.json()
    assert fb["position"] == written_pos
    assert fb["title"] == "Задание 29"
    assert fb["teacher_text"] == "Хороший разбор уравнения"

    list_resp = client.get("/api/homework")
    row = next(item for item in list_resp.json() if item["id"] == assignment_id)
    assert row["has_teacher_feedback"] is True

    detail = client.get(f"/api/homework/{assignment_id}")
    written_step = next(
        s for s in detail.json()["submission_steps"] if s["title"] == "Задание 29"
    )
    assert written_step["feedback"]["teacher_text"] == "Хороший разбор уравнения"

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    student_fb = client.get(f"/api/student/homework/{assignment_id}/feedback")
    assert student_fb.status_code == 200, student_fb.text
    steps = student_fb.json()["steps"]
    assert len(steps) == 1
    assert steps[0]["title"] == "Задание 29"
    assert steps[0]["teacher_text"] == "Хороший разбор уравнения"


def test_feedback_rejected_on_exact_exam_step(client: TestClient) -> None:
    assignment_id = _create_homework_partial(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    written_pos = _written_step_position(session)
    exact_pos = next(step["position"] for step in session["steps"] if step["type"] == 1)

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{exact_pos}/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/{written_pos}/compare",
        json={"answer": "мой разбор"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    client.post(f"/api/homework/{assignment_id}/submit", json={})

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.put(
        f"/api/homework/{assignment_id}/steps/{exact_pos}/feedback",
        json={"teacher_text": "not allowed"},
    )
    assert response.status_code == 422
    assert "self_check" in response.json()["detail"].lower()
