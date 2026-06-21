"""End-to-end backend path for EGE written self_check steps (types 29–34) — Task 91."""

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

TEACHER_EMAIL = "teacher-ege-e2e@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-ege-e2e@example.com"
STUDENT_PASS = "student-pass"

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

WRITTEN_TYPES = list(range(29, 35))


def _create_ege_db_full_variant(path: Path) -> None:
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
    rows = [
        ("001.txt", 1, "Q exact", "1", 0),
        ("001.txt", 28, "Q28 exact", "28", 0),
    ]
    for type_num in WRITTEN_TYPES:
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
    for type_num in WRITTEN_TYPES:
        conn.execute(
            "INSERT INTO images (filename, data) VALUES (?, ?)",
            (f"ответ{type_num:04d}.png", PNG_BYTES),
        )
    conn.commit()
    conn.close()


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "ege_written_integration.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"
    ege_db = tmp_path / "test_ege.db"
    _create_ege_db_full_variant(ege_db)

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
            JWT_SECRET="test-jwt-secret-ege-written-integration",
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


def _steps_by_type(session: dict) -> dict[int, dict]:
    return {step["type"]: step for step in session["steps"]}


def test_full_ege_written_path_variant_compare_homework_submit_feedback(
    client: TestClient,
) -> None:
    """Fixture 29–34 → practice compare → homework photo → submit → teacher feedback."""
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    practice = client.post(
        "/api/tests/sessions",
        json={"variant_ref": "001.txt"},
    )
    assert practice.status_code == 201, practice.text
    practice_body = practice.json()
    practice_id = practice_body["id"]
    practice_steps = _steps_by_type(practice_body)

    assert len(practice_body["steps"]) == 8
    for type_num in WRITTEN_TYPES:
        assert practice_steps[type_num]["grading_mode"] == "self_check"

    for exact_type in (1, 28):
        step = practice_steps[exact_type]
        check = client.post(
            f"/api/tests/sessions/{practice_id}/steps/{step['position']}/check",
            json={"answer": str(exact_type)},
        )
        assert check.status_code == 200, check.text

    for type_num in WRITTEN_TYPES:
        step = practice_steps[type_num]
        compare = client.post(
            f"/api/tests/sessions/{practice_id}/steps/{step['position']}/compare",
            json={"answer": f"разбор {type_num}"},
        )
        assert compare.status_code == 200, compare.text
        ref = compare.json()["reference_answer"]
        assert ref[0]["content"] == "Разбор "
        assert ref[1]["url"] == f"/api/tests/images/{quote(f'ответ{type_num:04d}.png')}"

    practice_summary = client.post(f"/api/tests/sessions/{practice_id}/complete").json()
    assert practice_summary["max_score"] == 8
    assert practice_summary["score"] == 8

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_id = _student_id(client)
    homework = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "EGE full variant written",
            "items": [{"kind": "test_variant", "variant": "001.txt"}],
        },
    )
    assert homework.status_code == 201, homework.text
    assignment_id = homework.json()["id"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    hw_session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    )
    assert hw_session.status_code == 201, hw_session.text
    hw_body = hw_session.json()
    hw_id = hw_body["id"]
    hw_steps = _steps_by_type(hw_body)

    for exact_type in (1, 28):
        step = hw_steps[exact_type]
        assert (
            client.post(
                f"/api/tests/sessions/{hw_id}/steps/{step['position']}/check",
                json={"answer": str(exact_type)},
            ).status_code
            == 200
        )

    for type_num in WRITTEN_TYPES:
        step = hw_steps[type_num]
        image_id = _upload_image(client)
        attach = client.post(
            f"/api/tests/sessions/{hw_id}/steps/{step['position']}/answer-image",
            json={"answer_image_id": image_id},
        )
        assert attach.status_code == 200, attach.text
        compare = client.post(
            f"/api/tests/sessions/{hw_id}/steps/{step['position']}/compare",
            json={"answer": f"домашний разбор {type_num}"},
        )
        assert compare.status_code == 200, compare.text

    hw_summary = client.post(f"/api/tests/sessions/{hw_id}/complete").json()
    assert hw_summary["max_score"] == 8
    assert hw_summary["score"] == 8

    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    submission = submit.json()["submission"]
    assert submission["score"] == 8
    assert submission["max_score"] == 8

    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200, detail.text
    written_steps = [
        step
        for step in detail.json()["submission_steps"]
        if step.get("grading_mode") == "self_check"
    ]
    assert len(written_steps) == 6
    assert all(step["answer_image_url"] for step in written_steps)

    feedback_pos = hw_steps[30]["position"]
    feedback = client.put(
        f"/api/homework/{assignment_id}/steps/{feedback_pos}/feedback",
        json={"teacher_text": "Отличный разбор задания 30"},
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["teacher_text"] == "Отличный разбор задания 30"

    list_resp = client.get("/api/homework")
    row = next(item for item in list_resp.json() if item["id"] == assignment_id)
    assert row["has_teacher_feedback"] is True

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    student_fb = client.get(f"/api/student/homework/{assignment_id}/feedback")
    assert student_fb.status_code == 200, student_fb.text
    fb_steps = student_fb.json()["steps"]
    assert len(fb_steps) == 1
    assert fb_steps[0]["title"] == "Задание 30"
    assert fb_steps[0]["teacher_text"] == "Отличный разбор задания 30"


def test_test_by_type_written_step_in_homework_flow(client: TestClient) -> None:
    """Regression: test_by_type item with a single written type still works end-to-end."""
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_id = _student_id(client)
    create = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "EGE by type 33",
            "items": [{"kind": "test_by_type", "types": [33]}],
        },
    )
    assert create.status_code == 201, create.text
    assignment_id = create.json()["id"]

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    assert len(session["steps"]) == 1
    step = session["steps"][0]
    assert step["type"] == 33
    assert step["grading_mode"] == "self_check"

    image_id = _upload_image(client)
    client.post(
        f"/api/tests/sessions/{session['id']}/steps/{step['position']}/answer-image",
        json={"answer_image_id": image_id},
    )
    client.post(
        f"/api/tests/sessions/{session['id']}/steps/{step['position']}/compare",
        json={"answer": "разбор 33"},
    )
    summary = client.post(f"/api/tests/sessions/{session['id']}/complete").json()
    assert summary["score"] == 1
    assert summary["max_score"] == 1

    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    assert submit.json()["submission"]["score"] == 1
