"""Written homework photo submit — §1.9.8 (Tasks 72 + 75)."""

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

TEACHER_EMAIL = "teacher-photo@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-photo@example.com"
STUDENT_PASS = "student-pass"

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
    db_file = tmp_path / "homework_written_photo.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"
    ege_db = tmp_path / "test_ege.db"
    _create_by_type_db(ege_db)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
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
                    question_blocks=[{"type": "text", "content": "Explain"}],
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
            JWT_SECRET="test-jwt-secret-written-photo",
            UPLOAD_DIR=str(upload_dir),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_id = teacher_id
        test_client.student_id = student_id
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
    return client.get("/api/students").json()[0]["id"]


def _upload_image(client: TestClient) -> str:
    response = client.post(
        "/api/uploads/images",
        files={"file": ("work.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_homework(client: TestClient) -> str:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Written HW",
            "items": [{"kind": "custom_theme", "theme_id": str(client.theme_id)}],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def test_homework_compare_without_photo_returns_422(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()

    compare = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/compare",
        json={"answer": "text only"},
    )
    assert compare.status_code == 422
    assert "image" in compare.json()["detail"].lower()


def test_attach_photo_after_checked_returns_409(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]

    image_id = _upload_image(client)
    attach = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/answer-image",
        json={"answer_image_id": image_id},
    )
    assert attach.status_code == 200, attach.text

    compare = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": ""},
    )
    assert compare.status_code == 200, compare.text

    replace = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/answer-image",
        json={"answer_image_id": image_id},
    )
    assert replace.status_code == 409


def test_submit_blocked_without_self_check_photo(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]

    client.post(f"/api/tests/sessions/{session_id}/complete")
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 422
    assert "photo" in submit.json()["detail"].lower()


def test_teacher_homework_detail_includes_photo_urls(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": "written"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    client.post(f"/api/homework/{assignment_id}/submit", json={})

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert len(body["submission_steps"]) == 1
    assert body["submission_steps"][0]["answer_image_url"] == f"/api/uploads/images/{image_id}"
    assert body["submission_steps"][0]["answer"] == "written"
    assert body["submission_steps"][0]["title"] == "Self check"
    assert body["submission_steps"][0]["question_blocks"] == [
        {"type": "text", "content": "Explain"}
    ]
    assert body["submission_steps"][0]["reference_answer"] == [
        {"type": "text", "content": "Ref"}
    ]

    image_get = client.get(f"/api/uploads/images/{image_id}")
    assert image_get.status_code == 200


def test_practice_self_check_compare_without_photo_ok(client: TestClient) -> None:
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"custom_theme_id": str(client.theme_id)},
    ).json()

    compare = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/compare",
        json={"answer": "practice"},
    )
    assert compare.status_code == 200, compare.text

    image_id = _upload_image(client)
    attach = client.post(
        f"/api/tests/sessions/{session['id']}/steps/0/answer-image",
        json={"answer_image_id": image_id},
    )
    assert attach.status_code == 422
    assert "homework" in attach.json()["detail"].lower()
