"""ActivityService.reconcile_student: heal missing HOMEWORK_COMPLETE / STEP_CORRECT."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import (
    ActivityEventType,
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    HomeworkSubmission,
    StudentActivityEvent,
    StudentProfile,
    StudentStats,
    User,
    UserRole,
)
from app.models.enums import StepStatus
from app.models.test_session import TestSession as TestSessionModel
from app.models.test_session import TestSessionStep as SessionStepRow
from app.models.enums import TestSessionStatus as SessionStatus
from app.services.activity_service import (
    POINTS_STEP_CORRECT,
    ActivityService,
)
from app.services.homework_submit_service import compute_homework_points


def _utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, 12, 0, tzinfo=timezone.utc)


async def _event_count(
    db_session,
    student_id: uuid.UUID,
    event_type: ActivityEventType,
) -> int:
    return await db_session.scalar(
        select(func.count())
        .select_from(StudentActivityEvent)
        .where(
            StudentActivityEvent.student_id == student_id,
            StudentActivityEvent.event_type == event_type,
        )
    )


async def _add_homework_hole(
    db_session,
    *,
    student,
    teacher,
    answered_steps: int,
    total_steps: int,
    submitted_at: datetime,
) -> HomeworkAssignment:
    assignment = HomeworkAssignment(
        student_id=student.id,
        teacher_id=teacher.id,
        title="Reconcile HW",
        items=[{"kind": "test_variant", "variant": "001.txt"}],
        status=HomeworkStatus.SUBMITTED,
    )
    db_session.add(assignment)
    await db_session.flush()
    db_session.add(
        HomeworkSubmission(
            assignment_id=assignment.id,
            submitted_at=submitted_at,
            answered_steps=answered_steps,
            total_steps=total_steps,
            completion_percent=round(100 * answered_steps / total_steps)
            if total_steps
            else 100,
        )
    )
    await db_session.flush()
    return assignment


async def _add_step_hole(
    db_session,
    *,
    student,
    is_correct: bool | None,
    checked_at: datetime | None,
    created_at: datetime,
) -> SessionStepRow:
    test_session = TestSessionModel(
        student_id=student.id,
        track=ExamTrack.EGE,
        variant_ref="001.txt",
        status=SessionStatus.COMPLETED,
        created_at=created_at,
    )
    db_session.add(test_session)
    await db_session.flush()
    step = SessionStepRow(
        session_id=test_session.id,
        position=0,
        test_id=1,
        is_correct=is_correct,
        status=StepStatus.CHECKED if is_correct is not None else StepStatus.UNSEEN,
        checked_at=checked_at,
    )
    db_session.add(step)
    await db_session.flush()
    return step


@pytest.mark.asyncio
async def test_reconcile_homework_hole_creates_one_event(
    db_session, teacher_student_users
) -> None:
    teacher, student, _ = teacher_student_users
    submitted_at = _utc(2026, 8, 10)
    assignment = await _add_homework_hole(
        db_session,
        student=student,
        teacher=teacher,
        answered_steps=1,
        total_steps=2,
        submitted_at=submitted_at,
    )

    created = await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    assert created == 1
    event = await db_session.scalar(
        select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student.id,
            StudentActivityEvent.event_type == ActivityEventType.HOMEWORK_COMPLETE,
            StudentActivityEvent.ref_id == str(assignment.id),
        )
    )
    assert event is not None
    assert event.points == compute_homework_points(1, 2)
    assert await _event_count(
        db_session, student.id, ActivityEventType.HOMEWORK_COMPLETE
    ) == 1
    assert await _event_count(
        db_session, student.id, ActivityEventType.HOMEWORK_COMPLETE_DELTA
    ) == 0


@pytest.mark.asyncio
async def test_reconcile_step_hole_uses_checked_at_not_now(
    db_session, teacher_student_users
) -> None:
    _, student, _ = teacher_student_users
    checked_at = _utc(2026, 6, 19)
    step = await _add_step_hole(
        db_session,
        student=student,
        is_correct=True,
        checked_at=checked_at,
        created_at=_utc(2026, 6, 18),
    )

    created = await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    assert created == 1
    event = await db_session.scalar(
        select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student.id,
            StudentActivityEvent.event_type == ActivityEventType.STEP_CORRECT,
            StudentActivityEvent.ref_id == str(step.id),
        )
    )
    assert event is not None
    assert event.points == POINTS_STEP_CORRECT
    stats = await db_session.get(StudentStats, student.id)
    assert stats is not None
    assert stats.last_active_date == date(2026, 6, 19)
    assert stats.tasks_solved == 1


@pytest.mark.asyncio
async def test_reconcile_step_falls_back_to_session_created_at(
    db_session, teacher_student_users
) -> None:
    _, student, _ = teacher_student_users
    created_at = _utc(2026, 6, 10)
    await _add_step_hole(
        db_session,
        student=student,
        is_correct=True,
        checked_at=None,
        created_at=created_at,
    )

    await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    stats = await db_session.get(StudentStats, student.id)
    assert stats is not None
    assert stats.last_active_date == date(2026, 6, 10)


@pytest.mark.asyncio
async def test_reconcile_is_idempotent(db_session, teacher_student_users) -> None:
    teacher, student, _ = teacher_student_users
    await _add_homework_hole(
        db_session,
        student=student,
        teacher=teacher,
        answered_steps=2,
        total_steps=2,
        submitted_at=_utc(2026, 8, 10),
    )
    await _add_step_hole(
        db_session,
        student=student,
        is_correct=True,
        checked_at=_utc(2026, 8, 10),
        created_at=_utc(2026, 8, 10),
    )
    service = ActivityService(db_session)

    first = await service.reconcile_student(student.id)
    second = await service.reconcile_student(student.id)
    await db_session.commit()

    assert first == 2
    assert second == 0
    assert await _event_count(
        db_session, student.id, ActivityEventType.HOMEWORK_COMPLETE
    ) == 1
    assert await _event_count(
        db_session, student.id, ActivityEventType.STEP_CORRECT
    ) == 1


@pytest.mark.asyncio
async def test_reconcile_does_not_create_delta_when_complete_exists(
    db_session, teacher_student_users
) -> None:
    teacher, student, _ = teacher_student_users
    assignment = await _add_homework_hole(
        db_session,
        student=student,
        teacher=teacher,
        answered_steps=2,
        total_steps=2,
        submitted_at=_utc(2026, 8, 10),
    )
    db_session.add(
        StudentActivityEvent(
            student_id=student.id,
            event_type=ActivityEventType.HOMEWORK_COMPLETE,
            ref_id=str(assignment.id),
            points=compute_homework_points(2, 2),
            payload={},
        )
    )
    await db_session.flush()

    created = await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    assert created == 0
    assert await _event_count(
        db_session, student.id, ActivityEventType.HOMEWORK_COMPLETE_DELTA
    ) == 0


@pytest.mark.asyncio
async def test_reconcile_historical_hole_does_not_rewind_streak_or_week(
    db_session, teacher_student_users
) -> None:
    teacher, student, _ = teacher_student_users
    stats = StudentStats(
        student_id=student.id,
        total_points=100,
        week_points=40,
        current_streak=5,
        longest_streak=5,
        last_active_date=date(2026, 8, 15),
        tasks_solved=3,
        total_minutes=20,
    )
    db_session.add(stats)
    await _add_homework_hole(
        db_session,
        student=student,
        teacher=teacher,
        answered_steps=1,
        total_steps=2,
        submitted_at=_utc(2026, 8, 1),
    )
    await _add_step_hole(
        db_session,
        student=student,
        is_correct=True,
        checked_at=_utc(2026, 7, 20),
        created_at=_utc(2026, 7, 20),
    )
    await db_session.flush()

    created = await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    assert created == 2
    reloaded = await db_session.get(StudentStats, student.id)
    assert reloaded is not None
    assert reloaded.current_streak == 5
    assert reloaded.week_points == 40
    assert reloaded.last_active_date == date(2026, 8, 15)
    assert reloaded.total_minutes == 20
    expected_hw = compute_homework_points(1, 2)
    assert reloaded.total_points == 100 + expected_hw + POINTS_STEP_CORRECT
    assert reloaded.tasks_solved == 4
    assert await _event_count(
        db_session, student.id, ActivityEventType.STREAK_DAILY
    ) == 0
    assert await _event_count(
        db_session, student.id, ActivityEventType.STREAK_WEEKLY
    ) == 0
    assert await _event_count(
        db_session, student.id, ActivityEventType.HOMEWORK_COMPLETE_DELTA
    ) == 0


@pytest.mark.asyncio
async def test_reconcile_ignores_incorrect_steps(
    db_session, teacher_student_users
) -> None:
    _, student, _ = teacher_student_users
    await _add_step_hole(
        db_session,
        student=student,
        is_correct=False,
        checked_at=_utc(2026, 8, 10),
        created_at=_utc(2026, 8, 10),
    )
    await _add_step_hole(
        db_session,
        student=student,
        is_correct=None,
        checked_at=_utc(2026, 8, 10),
        created_at=_utc(2026, 8, 10),
    )

    created = await ActivityService(db_session).reconcile_student(student.id)
    await db_session.commit()

    assert created == 0
    assert await _event_count(
        db_session, student.id, ActivityEventType.STEP_CORRECT
    ) == 0


_STATS_STUDENT_EMAIL = "student-stats-heal@example.com"
_STATS_TEACHER_EMAIL = "teacher-stats-heal@example.com"
_STATS_PASS = "stats-heal-pass"


@pytest.fixture
def stats_heal_env(tmp_path: Path):
    db_file = tmp_path / "student_stats_heal.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    assignment_id = uuid.uuid4()
    submitted_at = _utc(2026, 8, 10)

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
                        email=_STATS_TEACHER_EMAIL,
                        password_hash=hash_password(_STATS_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=_STATS_STUDENT_EMAIL,
                        password_hash=hash_password(_STATS_PASS),
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
                HomeworkAssignment(
                    id=assignment_id,
                    student_id=student_id,
                    teacher_id=teacher_id,
                    title="Heal HW",
                    items=[{"kind": "test_variant", "variant": "001.txt"}],
                    status=HomeworkStatus.SUBMITTED,
                )
            )
            await session.flush()
            session.add(
                HomeworkSubmission(
                    assignment_id=assignment_id,
                    submitted_at=submitted_at,
                    answered_steps=2,
                    total_steps=2,
                    completion_percent=100,
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
            JWT_SECRET="test-jwt-secret-for-student-stats-heal-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "db_url": db_url,
            "student_id": student_id,
            "assignment_id": assignment_id,
        }

    asyncio.run(request_engine.dispose())


async def _count_hw_complete(db_url: str, student_id: uuid.UUID) -> int:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            return await session.scalar(
                select(func.count())
                .select_from(StudentActivityEvent)
                .where(
                    StudentActivityEvent.student_id == student_id,
                    StudentActivityEvent.event_type
                    == ActivityEventType.HOMEWORK_COMPLETE,
                )
            )
    finally:
        await engine.dispose()


def test_student_stats_heals_homework_hole_and_is_idempotent(stats_heal_env) -> None:
    client = stats_heal_env["client"]
    student_id = stats_heal_env["student_id"]
    db_url = stats_heal_env["db_url"]
    expected = compute_homework_points(2, 2)

    assert asyncio.run(_count_hw_complete(db_url, student_id)) == 0

    login = client.post(
        "/api/auth/login",
        json={"email": _STATS_STUDENT_EMAIL, "password": _STATS_PASS},
    )
    assert login.status_code == 200

    # Leaderboard must not heal (A4).
    lb = client.get("/api/leaderboard")
    assert lb.status_code == 200
    assert asyncio.run(_count_hw_complete(db_url, student_id)) == 0

    first = client.get("/api/students/me/stats")
    assert first.status_code == 200
    body = first.json()
    assert body["student_id"] == str(student_id)
    assert body["total_points"] == expected
    assert asyncio.run(_count_hw_complete(db_url, student_id)) == 1

    second = client.get("/api/students/me/stats")
    assert second.status_code == 200
    assert second.json()["total_points"] == expected
    assert asyncio.run(_count_hw_complete(db_url, student_id)) == 1


def test_student_stats_requires_auth(stats_heal_env) -> None:
    response = stats_heal_env["client"].get("/api/students/me/stats")
    assert response.status_code == 401


def test_student_stats_requires_student_role(stats_heal_env) -> None:
    client = stats_heal_env["client"]
    login = client.post(
        "/api/auth/login",
        json={"email": _STATS_TEACHER_EMAIL, "password": _STATS_PASS},
    )
    assert login.status_code == 200
    response = client.get("/api/students/me/stats")
    assert response.status_code == 403
