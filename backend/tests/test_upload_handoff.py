"""QR handoff token + mobile capture API — §1.9.9 (Task 79)."""

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
from app.models import (
    CustomTask,
    ExamTrack,
    GradingMode,
    StudentProfile,
    TeacherTheme,
    User,
    UserRole,
)

TEACHER_EMAIL = "teacher-handoff@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-handoff@example.com"
STUDENT_PASS = "student-pass"
OTHER_STUDENT_EMAIL = "other-handoff@example.com"
OTHER_STUDENT_PASS = "other-pass"

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_by_type_db(path: Path) -> None:
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
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "upload_handoff.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"
    ege_db = tmp_path / "test_ege.db"
    _create_by_type_db(ege_db)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()
    theme_id = uuid.uuid4()
    self_check_task_id = uuid.uuid4()

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
                        password_hash=hash_password(OTHER_STUDENT_PASS),
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
                        track=ExamTrack.EGE,
                    ),
                ]
            )
            session.add(
                TeacherTheme(
                    id=theme_id,
                    teacher_id=teacher_id,
                    title="Письменные",
                    is_published=True,
                    sort_order=1,
                )
            )
            await session.flush()
            session.add(
                CustomTask(
                    id=self_check_task_id,
                    theme_id=theme_id,
                    title="Self check",
                    sort_order=0,
                    grading_mode=GradingMode.SELF_CHECK,
                    question_blocks=[{"type": "text", "content": "Explain reaction"}],
                    reference_answer=[{"type": "text", "content": "Ref"}],
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
            JWT_SECRET="test-jwt-secret-upload-handoff",
            UPLOAD_DIR=str(upload_dir),
            FRONTEND_URL="http://localhost:3000",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_id = teacher_id
        test_client.student_id = student_id
        test_client.other_student_id = other_student_id
        test_client.theme_id = theme_id
        test_client.self_check_task_id = self_check_task_id
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": password}).status_code
        == 200
    )


def _student_id(client: TestClient) -> str:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    students = client.get("/api/students").json()
    for row in students:
        if row["email"] == STUDENT_EMAIL:
            return row["id"]
    raise AssertionError("student not found")


def _create_homework(client: TestClient) -> str:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Handoff HW",
            "items": [{"kind": "custom_theme", "theme_id": str(client.theme_id)}],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def _homework_session(client: TestClient) -> dict:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_handoff_returns_token_and_capture_url(client: TestClient) -> None:
    session = _homework_session(client)
    response = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/handoff",
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "token" in body
    assert body["capture_url"] == f"http://localhost:3000/student/capture/{body['token']}"
    assert "expires_at" in body


def test_other_student_cannot_create_handoff(client: TestClient) -> None:
    session = _homework_session(client)
    _login(client, OTHER_STUDENT_EMAIL, OTHER_STUDENT_PASS)
    response = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/handoff",
    )
    assert response.status_code == 403


def test_new_handoff_invalidates_previous_unused_token(client: TestClient) -> None:
    session = _homework_session(client)
    session_id = session["id"]
    first = client.post(f"/api/tests/sessions/{session_id}/steps/0/handoff").json()
    second = client.post(f"/api/tests/sessions/{session_id}/steps/0/handoff").json()
    assert first["token"] != second["token"]

    expired = client.get(f"/api/capture/{first['token']}")
    assert expired.status_code == 410


def test_capture_upload_attaches_photo_and_marks_token_used(client: TestClient) -> None:
    session = _homework_session(client)
    handoff = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/handoff",
    ).json()
    token = handoff["token"]

    meta = client.get(f"/api/capture/{token}")
    assert meta.status_code == 200, meta.text
    assert meta.json()["question_preview"] == "Explain reaction"
    assert meta.json()["already_has_photo"] is False

    upload = client.post(
        f"/api/capture/{token}",
        files={"file": ("work.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    assert body["position"] == 0
    assert body["answer_image_url"].startswith("/api/uploads/images/")

    step_session = client.get(f"/api/tests/sessions/{session['id']}")
    assert step_session.status_code == 200
    step = step_session.json()["steps"][0]
    assert step["answer_image_id"] == body["answer_image_id"]

    reuse = client.post(
        f"/api/capture/{token}",
        files={"file": ("work2.png", PNG_BYTES, "image/png")},
    )
    assert reuse.status_code == 410


def test_handoff_after_checked_returns_409(client: TestClient) -> None:
    session = _homework_session(client)
    session_id = session["id"]

    image = client.post(
        "/api/uploads/images",
        files={"file": ("work.png", PNG_BYTES, "image/png")},
    ).json()
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/answer-image",
        json={"answer_image_id": image["id"]},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": "done"},
    )

    handoff = client.post(f"/api/tests/sessions/{session_id}/steps/0/handoff")
    assert handoff.status_code == 409


def test_capture_after_checked_returns_409(client: TestClient) -> None:
    session = _homework_session(client)
    session_id = session["id"]

    handoff = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/handoff",
    ).json()

    image = client.post(
        "/api/uploads/images",
        files={"file": ("work.png", PNG_BYTES, "image/png")},
    ).json()
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/answer-image",
        json={"answer_image_id": image["id"]},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": "done"},
    )

    upload = client.post(
        f"/api/capture/{handoff['token']}",
        files={"file": ("late.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 409


def test_practice_session_handoff_returns_422(client: TestClient) -> None:
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"custom_theme_id": str(client.theme_id)},
    ).json()
    response = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/handoff",
    )
    assert response.status_code == 422
