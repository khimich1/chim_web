"""Homework teacher/student feedback API — §1.9.9 (Tasks 82)."""

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

TEACHER_EMAIL = "teacher-fb@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-fb@example.com"
STUDENT_PASS = "student-pass"

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 64


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
    db_file = tmp_path / "homework_feedback.db"
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
            JWT_SECRET="test-jwt-secret-feedback",
            UPLOAD_DIR=str(upload_dir),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.theme_id = theme_id
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


def _upload_audio(client: TestClient) -> str:
    response = client.post(
        "/api/uploads/audio",
        files={"file": ("voice.webm", WEBM_BYTES, "audio/webm")},
        data={"duration_sec": "8"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _submit_written_homework(client: TestClient) -> str:
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
    assignment_id = create.json()["id"]

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
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    return assignment_id


def test_step_feedback_requires_content(client: TestClient) -> None:
    assignment_id = _submit_written_homework(client)
    _login(client, TEACHER_EMAIL, TEACHER_PASS)

    empty = client.put(
        f"/api/homework/{assignment_id}/steps/0/feedback",
        json={},
    )
    assert empty.status_code == 422

    saved = client.put(
        f"/api/homework/{assignment_id}/steps/0/feedback",
        json={"teacher_text": "Хорошо, но проверьте коэффициенты"},
    )
    assert saved.status_code == 200, saved.text
    body = saved.json()
    assert body["position"] == 0
    assert body["teacher_text"] == "Хорошо, но проверьте коэффициенты"
    assert body["published_at"] is not None


def test_step_feedback_upsert_and_student_read(client: TestClient) -> None:
    assignment_id = _submit_written_homework(client)
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    audio_id = _upload_audio(client)
    image_id = _upload_image(client)

    save = client.put(
        f"/api/homework/{assignment_id}/steps/0/feedback",
        json={
            "teacher_text": "Разбор шага",
            "teacher_voice_id": audio_id,
            "teacher_image_ids": [image_id],
        },
    )
    assert save.status_code == 200, save.text
    assert save.json()["teacher_voice_url"] == f"/api/uploads/audio/{audio_id}"
    assert save.json()["teacher_image_urls"] == [f"/api/uploads/images/{image_id}"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    audio_get = client.get(f"/api/uploads/audio/{audio_id}")
    assert audio_get.status_code == 200

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    update = client.put(
        f"/api/homework/{assignment_id}/steps/0/feedback",
        json={"teacher_text": "Обновлённый разбор"},
    )
    assert update.status_code == 200
    assert update.json()["teacher_text"] == "Обновлённый разбор"

    list_resp = client.get("/api/homework")
    assert list_resp.status_code == 200
    row = next(item for item in list_resp.json() if item["id"] == assignment_id)
    assert row["has_teacher_feedback"] is True

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    student_list = client.get("/api/homework")
    student_row = next(item for item in student_list.json() if item["id"] == assignment_id)
    assert student_row["has_teacher_feedback"] is True

    feedback = client.get(f"/api/student/homework/{assignment_id}/feedback")
    assert feedback.status_code == 200, feedback.text
    fb = feedback.json()
    assert fb["has_feedback"] is True
    assert len(fb["steps"]) == 1
    assert fb["steps"][0]["teacher_text"] == "Обновлённый разбор"


def test_submission_feedback_optional(client: TestClient) -> None:
    assignment_id = _submit_written_homework(client)
    _login(client, TEACHER_EMAIL, TEACHER_PASS)

    save = client.put(
        f"/api/homework/{assignment_id}/submission-feedback",
        json={"teacher_text": "Общий комментарий к сдаче"},
    )
    assert save.status_code == 200, save.text
    assert save.json()["teacher_text"] == "Общий комментарий к сдаче"

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    feedback = client.get(f"/api/student/homework/{assignment_id}/feedback")
    assert feedback.status_code == 200
    assert feedback.json()["submission"]["teacher_text"] == "Общий комментарий к сдаче"


def test_student_feedback_before_submit_returns_404(client: TestClient) -> None:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Not submitted",
            "items": [{"kind": "custom_theme", "theme_id": str(client.theme_id)}],
        },
    )
    assignment_id = create.json()["id"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.get(f"/api/student/homework/{assignment_id}/feedback")
    assert response.status_code == 404


def test_student_cannot_save_feedback(client: TestClient) -> None:
    assignment_id = _submit_written_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.put(
        f"/api/homework/{assignment_id}/steps/0/feedback",
        json={"teacher_text": "hack"},
    )
    assert response.status_code == 403
