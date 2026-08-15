"""Activity hooks via TestClient: check_step, complete, homework submit (Task 60)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    HomeworkSubmission,
    Notification,
    NotificationType,
    StepStatus,
    StudentActivityEvent,
    StudentProfile,
    StudentStats,
    User,
    UserRole,
)
from app.models.enums import ActivityEventType
from app.models.test_session import TestSession as TestSessionModel
from app.models.test_session import TestSessionStep as SessionStepRow
from app.services.activity_service import (
    POINTS_HOMEWORK_COMPLETE,
    POINTS_STEP_CORRECT,
    POINTS_STREAK_DAILY,
    ActivityService,
)
from app.services.homework_submit_service import HomeworkSubmitService
from app.services.test_session.common import SessionAdapterBase
from tests.content.conftest import _create_tests_db

TEACHER_EMAIL = "teacher-hooks@example.com"
STUDENT_EMAIL = "student-hooks@example.com"
PASS = "hooks-pass"


@pytest.fixture
def hooks_env(tmp_path: Path):
    db_file = tmp_path / "activity_hooks.db"
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
            JWT_SECRET="test-jwt-secret-for-activity-hooks-32b",
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "db_url": db_url,
            "student_id": student_id,
            "sessions": request_sessions,
        }

    asyncio.run(request_engine.dispose())


@pytest.fixture
def client(hooks_env) -> TestClient:
    return hooks_env["client"]


def _login(client: TestClient, email: str = STUDENT_EMAIL) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": PASS}).status_code
        == 200
    )


def _create_session(client: TestClient, **body) -> dict:
    payload = {"variant_ref": "001.txt", **body}
    response = client.post("/api/tests/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_homework(client: TestClient) -> str:
    _login(client, TEACHER_EMAIL)
    student_id = client.get("/api/students").json()[0]["id"]
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Hooks HW",
            "items": [{"kind": "test_variant", "variant": "001.txt"}],
        },
    )
    assert response.status_code == 201, response.text
    client.post("/api/auth/logout")
    return response.json()["id"]


async def _load_stats(db_url: str, student_id: uuid.UUID) -> StudentStats:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            stats = await session.get(StudentStats, student_id)
            assert stats is not None
            return stats
    finally:
        await engine.dispose()


async def _backdate_session(
    sessions,
    session_id: str,
    *,
    minutes_ago: int,
) -> None:
    created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    async with sessions() as session:
        await session.execute(
            update(TestSessionModel)
            .where(TestSessionModel.id == uuid.UUID(session_id))
            .values(created_at=created_at)
        )
        await session.commit()


def _mock_session_for_hook() -> AsyncMock:
    session = AsyncMock()
    nested = AsyncMock()
    nested.__aenter__ = AsyncMock(return_value=None)
    nested.__aexit__ = AsyncMock(return_value=False)
    session.begin_nested = MagicMock(return_value=nested)
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


async def _load_assignment(db_url: str, assignment_id: str) -> HomeworkAssignment:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            assignment = await session.get(HomeworkAssignment, uuid.UUID(assignment_id))
            assert assignment is not None
            return assignment
    finally:
        await engine.dispose()


async def _load_submission(
    db_url: str, assignment_id: str
) -> HomeworkSubmission | None:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            return await session.scalar(
                select(HomeworkSubmission).where(
                    HomeworkSubmission.assignment_id == uuid.UUID(assignment_id)
                )
            )
    finally:
        await engine.dispose()


async def _count_notifications(
    db_url: str, *, notification_type: NotificationType
) -> int:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            rows = (
                await session.scalars(
                    select(Notification).where(Notification.type == notification_type)
                )
            ).all()
            return len(list(rows))
    finally:
        await engine.dispose()


async def _count_events(
    db_url: str,
    student_id: uuid.UUID,
    event_type: ActivityEventType,
) -> int:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            rows = (
                await session.scalars(
                    select(StudentActivityEvent).where(
                        StudentActivityEvent.student_id == student_id,
                        StudentActivityEvent.event_type == event_type,
                    )
                )
            ).all()
            return len(list(rows))
    finally:
        await engine.dispose()


async def _load_step(
    db_url: str, session_id: str, *, position: int = 0
) -> SessionStepRow:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            step = await session.scalar(
                select(SessionStepRow).where(
                    SessionStepRow.session_id == uuid.UUID(session_id),
                    SessionStepRow.position == position,
                )
            )
            assert step is not None
            return step
    finally:
        await engine.dispose()


def test_check_step_correct_updates_stats(client: TestClient, hooks_env) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert response.status_code == 200
    assert response.json()["is_correct"] is True

    stats = asyncio.run(_load_stats(hooks_env["db_url"], hooks_env["student_id"]))
    assert stats.total_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.tasks_solved == 1


def test_check_step_wrong_then_correct_awards_once(client: TestClient, hooks_env) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    wrong = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "9"},
    )
    assert wrong.json()["is_correct"] is False

    right = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert right.json()["is_correct"] is True

    stats = asyncio.run(_load_stats(hooks_env["db_url"], hooks_env["student_id"]))
    assert stats.total_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.tasks_solved == 1


def test_check_step_recheck_correct_does_not_double_award(
    client: TestClient, hooks_env
) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )

    stats = asyncio.run(_load_stats(hooks_env["db_url"], hooks_env["student_id"]))
    assert stats.total_points == POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.tasks_solved == 1


def test_complete_session_records_duration_minutes(client: TestClient, hooks_env) -> None:
    _login(client)
    session_id = _create_session(client)["id"]
    asyncio.run(
        _backdate_session(hooks_env["sessions"], session_id, minutes_ago=90)
    )

    response = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert response.status_code == 200

    stats = asyncio.run(_load_stats(hooks_env["db_url"], hooks_env["student_id"]))
    assert stats.total_minutes == 90


def test_complete_session_score_unchanged_by_activity(client: TestClient) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check",
        json={"answer": "wrong"},
    )

    summary = client.post(f"/api/tests/sessions/{session_id}/complete").json()
    assert summary["score"] == 1
    assert summary["max_score"] == 2


def test_homework_submit_awards_completion_bonus(client: TestClient, hooks_env) -> None:
    assignment_id = _create_homework(client)

    _login(client)
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
    assert client.post(f"/api/tests/sessions/{session_id}/complete").status_code == 200

    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 200

    stats = asyncio.run(_load_stats(hooks_env["db_url"], hooks_env["student_id"]))
    expected_step_points = 2 * POINTS_STEP_CORRECT + POINTS_STREAK_DAILY
    assert stats.total_points == expected_step_points + POINTS_HOMEWORK_COMPLETE
    assert stats.tasks_solved == 2


def test_activity_failure_does_not_break_check_step(client: TestClient) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    with patch.object(
        ActivityService,
        "record_step_correct",
        AsyncMock(side_effect=RuntimeError("activity down")),
    ):
        response = client.post(
            f"/api/tests/sessions/{session_id}/steps/0/check",
            json={"answer": "1"},
        )

    assert response.status_code == 200
    assert response.json()["is_correct"] is True

    state = client.get(f"/api/tests/sessions/{session_id}").json()
    assert state["steps"][0]["is_correct"] is True


async def test_run_activity_hook_does_not_commit_or_rollback() -> None:
    settings = MagicMock()
    settings.content_ege_db_path = ":memory:"
    settings.content_oge_db_path = ":memory:"

    async def boom() -> None:
        raise RuntimeError("activity down")

    adapter_session = _mock_session_for_hook()
    adapter = SessionAdapterBase(adapter_session, settings, activity=MagicMock())
    await adapter.run_activity_hook("record_step_correct", boom)
    adapter_session.commit.assert_not_called()
    adapter_session.rollback.assert_not_called()
    adapter_session.begin_nested.assert_called()

    submit_session = _mock_session_for_hook()
    submit_service = HomeworkSubmitService(
        submit_session, activity=MagicMock(), settings=settings
    )
    await submit_service._run_activity_hook("record_homework_complete", boom)
    submit_session.commit.assert_not_called()
    submit_session.rollback.assert_not_called()
    submit_session.begin_nested.assert_called()


def test_homework_submit_keeps_assignment_when_activity_raises(
    client: TestClient, hooks_env
) -> None:
    assignment_id = _create_homework(client)

    _login(client)
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
    assert client.post(f"/api/tests/sessions/{session_id}/complete").status_code == 200

    with patch.object(
        ActivityService,
        "record_homework_complete",
        AsyncMock(side_effect=RuntimeError("activity down")),
    ):
        submit = client.post(
            f"/api/homework/{assignment_id}/submit",
            json={"test_session_id": session_id},
        )

    assert submit.status_code < 500
    assignment = asyncio.run(_load_assignment(hooks_env["db_url"], assignment_id))
    assert assignment.status == HomeworkStatus.SUBMITTED
    submission = asyncio.run(_load_submission(hooks_env["db_url"], assignment_id))
    assert submission is not None
    assert (
        asyncio.run(
            _count_notifications(
                hooks_env["db_url"],
                notification_type=NotificationType.HOMEWORK_SUBMITTED,
            )
        )
        == 1
    )
    assert (
        asyncio.run(
            _count_events(
                hooks_env["db_url"],
                hooks_env["student_id"],
                ActivityEventType.HOMEWORK_COMPLETE,
            )
        )
        == 0
    )


def test_check_step_keeps_checked_when_activity_raises(
    client: TestClient, hooks_env
) -> None:
    _login(client)
    session_id = _create_session(client)["id"]

    with patch.object(
        ActivityService,
        "record_step_correct",
        AsyncMock(side_effect=RuntimeError("activity down")),
    ):
        response = client.post(
            f"/api/tests/sessions/{session_id}/steps/0/check",
            json={"answer": "1"},
        )

    assert response.status_code < 500
    step = asyncio.run(_load_step(hooks_env["db_url"], session_id, position=0))
    assert step.status == StepStatus.CHECKED
    assert step.is_correct is True
