"""Custom theme TestSession API (SPEC §1.9.5, Task 69)."""

from __future__ import annotations

import asyncio
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
OTHER_TEACHER_EMAIL = "other-teacher@example.com"
STUDENT_EMAIL = "student@example.com"
PASS = "shared-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "custom_sessions.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()

    published_theme_id = uuid.uuid4()
    draft_theme_id = uuid.uuid4()
    other_teacher_theme_id = uuid.uuid4()
    auto_task_id = uuid.uuid4()
    self_check_task_id = uuid.uuid4()
    auto_task2_id = uuid.uuid4()

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
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=other_teacher_id,
                        email=OTHER_TEACHER_EMAIL,
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(PASS),
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
            session.add_all(
                [
                    TeacherTheme(
                        id=published_theme_id,
                        teacher_id=teacher_id,
                        title="ОВР",
                        description="Опубликованная тема",
                        is_published=True,
                        sort_order=1,
                    ),
                    TeacherTheme(
                        id=draft_theme_id,
                        teacher_id=teacher_id,
                        title="Черновик",
                        is_published=False,
                        sort_order=2,
                    ),
                    TeacherTheme(
                        id=other_teacher_theme_id,
                        teacher_id=other_teacher_id,
                        title="Чужая тема",
                        is_published=True,
                        sort_order=1,
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    CustomTask(
                        id=auto_task_id,
                        theme_id=published_theme_id,
                        title="Auto 1",
                        sort_order=0,
                        grading_mode=GradingMode.AUTO,
                        question_blocks=[{"type": "text", "content": "2+2=?"}],
                        correct_value="4",
                    ),
                    CustomTask(
                        id=self_check_task_id,
                        theme_id=published_theme_id,
                        title="Self check",
                        sort_order=1,
                        grading_mode=GradingMode.SELF_CHECK,
                        question_blocks=[{"type": "text", "content": "Опишите ОВР"}],
                        reference_answer=[
                            {"type": "text", "content": "Эталонный ответ"}
                        ],
                    ),
                    CustomTask(
                        id=auto_task2_id,
                        theme_id=published_theme_id,
                        title="Auto 2",
                        sort_order=2,
                        grading_mode=GradingMode.AUTO,
                        question_blocks=[{"type": "text", "content": "H2O?"}],
                        correct_value="вода",
                    ),
                    CustomTask(
                        id=uuid.uuid4(),
                        theme_id=other_teacher_theme_id,
                        sort_order=0,
                        grading_mode=GradingMode.AUTO,
                        question_blocks=[{"type": "text", "content": "x"}],
                        correct_value="1",
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
            JWT_SECRET="test-jwt-secret-for-custom-sessions-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_id = teacher_id
        test_client.student_id = student_id
        test_client.published_theme_id = published_theme_id
        test_client.draft_theme_id = draft_theme_id
        test_client.other_teacher_theme_id = other_teacher_theme_id
        test_client.auto_task_id = auto_task_id
        test_client.self_check_task_id = self_check_task_id
        test_client.auto_task2_id = auto_task2_id
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str = STUDENT_EMAIL) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": PASS}).status_code
        == 200
    )


def _create_custom_session(
    client: TestClient,
    theme_id: uuid.UUID | None = None,
    **body,
) -> dict:
    payload = {
        "custom_theme_id": str(theme_id or client.published_theme_id),
        **body,
    }
    response = client.post("/api/tests/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_student_lists_published_themes_only(client: TestClient) -> None:
    _login(client)

    response = client.get("/api/custom-themes")
    assert response.status_code == 200
    themes = response.json()
    assert len(themes) == 1
    assert themes[0]["id"] == str(client.published_theme_id)
    assert themes[0]["title"] == "ОВР"
    assert themes[0]["task_count"] == 3
    assert themes[0]["description"] == "Опубликованная тема"


def test_create_custom_session_builds_steps(client: TestClient) -> None:
    _login(client)
    body = _create_custom_session(client)

    assert body["source"] == "custom"
    assert body["custom_theme_id"] == str(client.published_theme_id)
    assert body["status"] == "in_progress"
    assert body["total_steps"] == 3
    assert body["steps"][0]["custom_task_id"] == str(client.auto_task_id)
    assert body["steps"][0]["grading_mode"] == "auto"
    assert body["steps"][0]["question_blocks"][0]["content"] == "2+2=?"
    assert body["steps"][0]["test_id"] is None
    assert "correct_value" not in body["steps"][0]
    assert body["steps"][1]["grading_mode"] == "self_check"


def test_create_custom_session_with_task_subset(client: TestClient) -> None:
    _login(client)
    body = _create_custom_session(
        client,
        task_ids=[str(client.auto_task_id)],
    )

    assert body["total_steps"] == 1
    assert body["steps"][0]["custom_task_id"] == str(client.auto_task_id)


def test_check_auto_step_correct_and_incorrect(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(client, task_ids=[str(client.auto_task_id)])
    session_id = session["id"]

    wrong = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "5"},
    )
    assert wrong.status_code == 200
    assert wrong.json()["is_correct"] is False

    right = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": " 4 "},
    )
    assert right.status_code == 200
    assert right.json()["is_correct"] is True


def test_self_check_compare_returns_reference_not_score(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(
        client,
        task_ids=[str(client.self_check_task_id)],
    )
    session_id = session["id"]

    compare = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": "мой ответ"},
    )
    assert compare.status_code == 200
    data = compare.json()
    assert data["status"] == "checked"
    assert data["reference_answer"][0]["content"] == "Эталонный ответ"
    assert "is_correct" not in data

    state = client.get(f"/api/tests/sessions/{session_id}").json()
    assert state["steps"][0]["answer"] == "мой ответ"
    assert state["steps"][0]["is_correct"] is None

    check = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "мой ответ"},
    )
    assert check.status_code == 422


def test_complete_session_score_excludes_self_check(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(client)
    session_id = session["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "4"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/compare",
        json={"answer": "черновик"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/2/check",
        json={"answer": "wrong"},
    )

    summary = client.post(f"/api/tests/sessions/{session_id}/complete").json()
    assert summary["score"] == 1
    assert summary["max_score"] == 2
    assert len(summary["steps"]) == 3
    assert summary["steps"][1]["grading_mode"] == "self_check"
    assert summary["steps"][1]["is_correct"] is None


def test_unpublished_theme_returns_404(client: TestClient) -> None:
    _login(client)
    response = client.post(
        "/api/tests/sessions",
        json={"custom_theme_id": str(client.draft_theme_id)},
    )
    assert response.status_code == 404


def test_other_teacher_theme_returns_404(client: TestClient) -> None:
    _login(client)
    response = client.post(
        "/api/tests/sessions",
        json={"custom_theme_id": str(client.other_teacher_theme_id)},
    )
    assert response.status_code == 404


def test_resume_active_custom_session(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(client)
    session_id = session["id"]

    active = client.get(
        "/api/tests/sessions/active",
        params={"custom_theme_id": str(client.published_theme_id)},
    )
    assert active.status_code == 200
    assert active.json()["session_id"] == session_id


def test_completed_custom_session_not_active(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(client, task_ids=[str(client.auto_task_id)])
    session_id = session["id"]
    client.post(f"/api/tests/sessions/{session_id}/complete")

    active = client.get(
        "/api/tests/sessions/active",
        params={"custom_theme_id": str(client.published_theme_id)},
    )
    assert active.status_code == 200
    assert active.json()["session_id"] is None


def test_auto_step_rejects_compare(client: TestClient) -> None:
    _login(client)
    session = _create_custom_session(client, task_ids=[str(client.auto_task_id)])
    session_id = session["id"]

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/compare",
        json={"answer": "4"},
    )
    assert response.status_code == 422


def test_teacher_cannot_list_custom_themes(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL)
    assert client.get("/api/custom-themes").status_code == 403
