"""Feedback QR handoff + capture staging — teacher feedback composer UX."""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
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
    HomeworkSubmissionFeedback,
    StudentProfile,
    TeacherTheme,
    TestSessionStepFeedback,
    User,
    UserRole,
)

TEACHER_EMAIL = "teacher-fb-handoff@example.com"
TEACHER_PASS = "teacher-pass"
OTHER_TEACHER_EMAIL = "other-teacher-fb-handoff@example.com"
OTHER_TEACHER_PASS = "other-teacher-pass"
STUDENT_EMAIL = "student-fb-handoff@example.com"
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
    db_file = tmp_path / "feedback_handoff.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"
    ege_db = tmp_path / "test_ege.db"
    _create_by_type_db(ege_db)

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
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
                        id=other_teacher_id,
                        email=OTHER_TEACHER_EMAIL,
                        password_hash=hash_password(OTHER_TEACHER_PASS),
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
            JWT_SECRET="test-jwt-secret-feedback-handoff",
            UPLOAD_DIR=str(upload_dir),
            FRONTEND_URL="http://localhost:3000",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_id = teacher_id
        test_client.other_teacher_id = other_teacher_id
        test_client.student_id = student_id
        test_client.theme_id = theme_id
        test_client.db_url = db_url
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": password}).status_code
        == 200
    )


def _create_homework(client: TestClient) -> str:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    students = client.get("/api/students").json()
    student_id = next(row["id"] for row in students if row["email"] == STUDENT_EMAIL)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Feedback handoff HW",
            "items": [{"kind": "custom_theme", "theme_id": str(client.theme_id)}],
        },
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


async def _count_feedback_rows(db_url: str) -> tuple[int, int]:
    engine = create_async_engine(db_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        step_count = len(
            (await session.scalars(select(TestSessionStepFeedback))).all()
        )
        submission_count = len(
            (await session.scalars(select(HomeworkSubmissionFeedback))).all()
        )
    await engine.dispose()
    return step_count, submission_count


def test_create_feedback_handoff_for_step_and_submission(client: TestClient) -> None:
    assignment_id = _create_homework(client)

    step = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    )
    assert step.status_code == 201, step.text
    step_body = step.json()
    assert "token" in step_body
    assert step_body["capture_url"].endswith(f"/student/capture/{step_body['token']}")

    submission = client.post(f"/api/homework/{assignment_id}/feedback-handoff")
    assert submission.status_code == 201, submission.text
    assert submission.json()["token"] != step_body["token"]


def test_feedback_capture_stages_image_without_publishing(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    handoff = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    ).json()
    token = handoff["token"]

    meta = client.get(f"/api/capture/{token}")
    assert meta.status_code == 200, meta.text
    assert meta.json()["purpose"] == "feedback"
    assert meta.json()["already_has_photo"] is False
    assert meta.json()["staged_image_id"] is None

    upload = client.post(
        f"/api/capture/{token}",
        files={"file": ("fb.png", PNG_BYTES, "image/png")},
    )
    assert upload.status_code == 200, upload.text
    body = upload.json()
    assert body["purpose"] == "feedback"
    assert body["staged_image_id"] is not None
    assert body["staged_image_url"].startswith("/api/uploads/images/")
    assert body["answer_image_ids"] == []

    polled = client.get(f"/api/capture/{token}")
    assert polled.status_code == 200, polled.text
    polled_body = polled.json()
    assert polled_body["already_has_photo"] is True
    assert polled_body["staged_image_id"] == body["staged_image_id"]
    assert polled_body["staged_image_url"] == body["staged_image_url"]

    reuse = client.post(
        f"/api/capture/{token}",
        files={"file": ("fb2.png", PNG_BYTES, "image/png")},
    )
    assert reuse.status_code == 410

    step_count, submission_count = asyncio.run(_count_feedback_rows(client.db_url))
    assert step_count == 0
    assert submission_count == 0


def test_feedback_capture_unauthenticated_returns_401(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    token = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    ).json()["token"]

    assert client.post("/api/auth/logout").status_code == 204

    assert client.get(f"/api/capture/{token}").status_code == 401
    assert (
        client.post(
            f"/api/capture/{token}",
            files={"file": ("fb.png", PNG_BYTES, "image/png")},
        ).status_code
        == 401
    )


def test_feedback_capture_rbac_rejects_other_teacher_and_student(
    client: TestClient,
) -> None:
    assignment_id = _create_homework(client)
    token = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    ).json()["token"]

    _login(client, OTHER_TEACHER_EMAIL, OTHER_TEACHER_PASS)
    assert client.get(f"/api/capture/{token}").status_code == 403
    assert (
        client.post(
            f"/api/capture/{token}",
            files={"file": ("fb.png", PNG_BYTES, "image/png")},
        ).status_code
        == 403
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    assert client.get(f"/api/capture/{token}").status_code == 403
    assert (
        client.post(
            f"/api/capture/{token}",
            files={"file": ("fb.png", PNG_BYTES, "image/png")},
        ).status_code
        == 403
    )


def test_feedback_handoff_invalidates_previous_unused_for_same_position(
    client: TestClient,
) -> None:
    assignment_id = _create_homework(client)
    first = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    ).json()
    second = client.post(
        f"/api/homework/{assignment_id}/feedback-handoff",
        json={"position": 0},
    ).json()
    assert first["token"] != second["token"]
    assert client.get(f"/api/capture/{first['token']}").status_code == 410
    assert client.get(f"/api/capture/{second['token']}").status_code == 200
