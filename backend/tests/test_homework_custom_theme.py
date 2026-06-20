"""Homework with custom_theme items and test_by_type variants (Task 73)."""

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

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


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
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("003.txt", 10, "Q003-10", "10", 0),
            ("007.txt", 10, "Q007-10", "10", 0),
            ("008.txt", 10, "Q008-10", "10", 0),
        ],
    )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "homework_custom_theme.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    _create_by_type_db(ege_db)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    theme_id = uuid.uuid4()
    auto_task_id = uuid.uuid4()
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
                    title="ОВР",
                    is_published=True,
                    sort_order=1,
                )
            )
            await session.flush()
            session.add_all(
                [
                    CustomTask(
                        id=auto_task_id,
                        theme_id=theme_id,
                        title="Auto 1",
                        sort_order=0,
                        grading_mode=GradingMode.AUTO,
                        question_blocks=[{"type": "text", "content": "2+2=?"}],
                        correct_value="4",
                    ),
                    CustomTask(
                        id=self_check_task_id,
                        theme_id=theme_id,
                        title="Self check",
                        sort_order=1,
                        grading_mode=GradingMode.SELF_CHECK,
                        question_blocks=[{"type": "text", "content": "Explain OVR"}],
                        reference_answer=[{"type": "text", "content": "Ref"}],
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
            JWT_SECRET="test-jwt-secret-for-homework-custom-theme",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_id = teacher_id
        test_client.student_id = student_id
        test_client.theme_id = theme_id
        test_client.auto_task_id = auto_task_id
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


def _complete_custom_session(client: TestClient, session_id: str, body: dict) -> None:
    for index, step in enumerate(body["steps"]):
        if step.get("grading_mode") == "self_check":
            upload = client.post(
                "/api/uploads/images",
                files={"file": ("answer.png", _PNG_BYTES, "image/png")},
            )
            assert upload.status_code == 201, upload.text
            image_id = upload.json()["id"]
            attach = client.post(
                f"/api/tests/sessions/{session_id}/steps/{index}/answer-image",
                json={"answer_image_id": image_id},
            )
            assert attach.status_code == 200, attach.text
            client.post(
                f"/api/tests/sessions/{session_id}/steps/{index}/compare",
                json={"answer": "my answer"},
            )
        else:
            client.post(
                f"/api/tests/sessions/{session_id}/steps/{index}/check",
                json={"answer": "4"},
            )
    complete = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert complete.status_code == 200, complete.text


_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_create_homework_with_custom_theme(client: TestClient) -> None:
    student_id = _student_id(client)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Custom theme HW",
            "items": [
                {
                    "kind": "custom_theme",
                    "theme_id": str(client.theme_id),
                    "task_ids": [str(client.auto_task_id)],
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    item = response.json()["items"][0]
    assert item["kind"] == "custom_theme"
    assert item["theme_id"] == str(client.theme_id)


def test_create_homework_rejects_foreign_theme(client: TestClient) -> None:
    student_id = _student_id(client)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Bad theme",
            "items": [
                {"kind": "custom_theme", "theme_id": str(uuid.uuid4())},
            ],
        },
    )
    assert response.status_code == 422


def test_test_by_type_homework_with_selected_variants(client: TestClient) -> None:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Filtered variants",
            "items": [
                {
                    "kind": "test_by_type",
                    "types": [10],
                    "variants": ["003.txt", "007.txt"],
                }
            ],
        },
    )
    assert create.status_code == 201, create.text
    assignment_id = create.json()["id"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    assert session["total_steps"] == 2


def test_create_homework_rejects_unknown_variants(client: TestClient) -> None:
    student_id = _student_id(client)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Bad variants",
            "items": [
                {
                    "kind": "test_by_type",
                    "types": [10],
                    "variants": ["missing.txt"],
                }
            ],
        },
    )
    assert response.status_code == 422
    assert "Unknown variant" in response.json()["detail"]


def test_student_submits_custom_theme_homework(client: TestClient) -> None:
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Submit custom",
            "items": [
                {"kind": "custom_theme", "theme_id": str(client.theme_id)},
            ],
        },
    )
    assert create.status_code == 201, create.text
    assignment_id = create.json()["id"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session_resp = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    )
    assert session_resp.status_code == 201, session_resp.text
    body = session_resp.json()
    assert body["source"] == "custom"
    assert body["total_steps"] == 2
    assert body["homework_assignment_id"] == assignment_id

    _complete_custom_session(client, body["id"], body)

    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    assert submit.json()["status"] == "submitted"
    assert submit.json()["submission"]["score"] == 1
    assert submit.json()["submission"]["max_score"] == 1
