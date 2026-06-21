"""Partial homework submit, reopen, and resubmit (SPEC §1.7 partial submit)."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Iterator
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
    ExamTrack,
    HomeworkStatus,
    StudentActivityEvent,
    StudentProfile,
    StudentStats,
    User,
    UserRole,
)
from app.models.enums import ActivityEventType
from app.services.activity_service import (
    POINTS_HOMEWORK_COMPLETE,
    POINTS_STEP_CORRECT,
    POINTS_STREAK_DAILY,
)
from tests.content.conftest import _create_tests_db

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    db_file = tmp_path / "homework_partial_submit.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    _create_tests_db(ege_db, with_bug=True)

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
            JWT_SECRET="test-jwt-secret-partial-homework",
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.env = {"db_url": db_url, "student_id": student_id}
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    assert client.post("/api/auth/login", json={"email": email, "password": password}).status_code == 200


def _create_homework(client: TestClient) -> str:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_id = client.get("/api/students").json()[0]["id"]
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Partial HW",
            "items": [{"kind": "test_variant", "variant": "001.txt"}],
        },
    )
    assert response.status_code == 201, response.text
    client.post("/api/auth/logout")
    return response.json()["id"]


async def _load_stats(db_url: str, student_id: uuid.UUID) -> StudentStats:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        stats = await session.get(StudentStats, student_id)
        assert stats is not None
        return stats
    await engine.dispose()


async def _count_events(
    db_url: str,
    student_id: uuid.UUID,
    event_type: ActivityEventType,
) -> int:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        stmt = select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student_id,
            StudentActivityEvent.event_type == event_type,
        )
        result = await session.scalars(stmt)
        return len(list(result.all()))
    await engine.dispose()


def test_partial_submit_one_of_two_steps_succeeds(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    assert session["total_steps"] == 2

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["status"] == "submitted"
    assert body["submission"]["answered_steps"] == 1
    assert body["submission"]["total_steps"] == 2
    assert body["submission"]["completion_percent"] == 50
    assert body["can_reopen"] is True


def test_submit_blocked_with_zero_answered_steps(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    client.post(f"/api/tests/sessions/{session_id}/complete")

    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 422
    assert "at least one answered step" in submit.json()["detail"].lower()


def test_reopen_and_resubmit_updates_progress_and_points(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    db_url = client.env["db_url"]
    student_id = client.env["student_id"]
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    first = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert first.status_code == 200
    partial_points = round(POINTS_HOMEWORK_COMPLETE * 1 / 2)
    stats_after_first = asyncio.run(_load_stats(db_url, student_id))
    assert stats_after_first.total_points == (
        POINTS_STEP_CORRECT + partial_points + POINTS_STREAK_DAILY
    )

    reopen = client.post(f"/api/homework/{assignment_id}/reopen", json={})
    assert reopen.status_code == 200, reopen.text
    reopened = reopen.json()
    assert reopened["status"] == "in_progress"
    assert reopened["can_reopen"] is False
    assert reopened["active_test_session_id"] == session_id

    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check",
        json={"answer": "2"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    resubmit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert resubmit.status_code == 200, resubmit.text
    final = resubmit.json()
    assert final["submission"]["answered_steps"] == 2
    assert final["submission"]["completion_percent"] == 100
    assert final["can_reopen"] is False

    stats_after_resubmit = asyncio.run(_load_stats(db_url, student_id))
    assert stats_after_resubmit.total_points == (
        2 * POINTS_STEP_CORRECT + POINTS_HOMEWORK_COMPLETE + POINTS_STREAK_DAILY
    )
    assert asyncio.run(
        _count_events(db_url, student_id, ActivityEventType.HOMEWORK_COMPLETE)
    ) == 1
    assert asyncio.run(
        _count_events(db_url, student_id, ActivityEventType.HOMEWORK_COMPLETE_DELTA)
    ) == 1


def test_teacher_notification_includes_progress(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    assert client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    ).status_code == 200

    client.post("/api/auth/logout")
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    notifications = client.get("/api/notifications").json()
    assert len(notifications) == 1
    payload = notifications[0]["payload"]
    assert payload["answered_steps"] == 1
    assert payload["total_steps"] == 2
    assert payload["completion_percent"] == 50


def test_cannot_reopen_fully_completed_homework(client: TestClient) -> None:
    assignment_id = _create_homework(client)
    _login(client, STUDENT_EMAIL, STUDENT_PASS)

    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check",
        json={"answer": "2"},
    )
    client.post(f"/api/tests/sessions/{session_id}/complete")
    assert client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    ).status_code == 200

    reopen = client.post(f"/api/homework/{assignment_id}/reopen", json={})
    assert reopen.status_code == 422
    assert "fully completed" in reopen.json()["detail"].lower()
