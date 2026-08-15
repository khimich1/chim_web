"""CLI reconcile_activity: dry-run by default, --apply writes, no PII."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ActivityEventType,
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    HomeworkSubmission,
    StudentActivityEvent,
    StudentProfile,
    User,
    UserRole,
)


def _utc() -> datetime:
    return datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)


async def _prepare_db(
    db_url: str,
    *,
    with_hole: bool = True,
    extra_student: bool = False,
) -> dict[str, uuid.UUID]:
    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_id = uuid.uuid4()
    assignment_id = uuid.uuid4()

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        users = [
            User(
                id=teacher_id,
                email="cli-teacher@example.com",
                password_hash=hash_password("secret-pass"),
                role=UserRole.TEACHER,
            ),
            User(
                id=student_id,
                email="cli-student@example.com",
                password_hash=hash_password("secret-pass"),
                role=UserRole.STUDENT,
            ),
        ]
        if extra_student:
            users.append(
                User(
                    id=other_id,
                    email="cli-other@example.com",
                    password_hash=hash_password("secret-pass"),
                    role=UserRole.STUDENT,
                )
            )
        session.add_all(users)
        await session.flush()
        session.add(
            StudentProfile(
                user_id=student_id,
                teacher_id=teacher_id,
                track=ExamTrack.EGE,
            )
        )
        if extra_student:
            session.add(
                StudentProfile(
                    user_id=other_id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                )
            )
        if with_hole:
            session.add(
                HomeworkAssignment(
                    id=assignment_id,
                    student_id=student_id,
                    teacher_id=teacher_id,
                    title="CLI hole",
                    items=[{"kind": "lecture", "topic": "x"}],
                    status=HomeworkStatus.SUBMITTED,
                )
            )
            await session.flush()
            session.add(
                HomeworkSubmission(
                    assignment_id=assignment_id,
                    submitted_at=_utc(),
                    answered_steps=2,
                    total_steps=2,
                    completion_percent=100,
                )
            )
        await session.commit()
    await engine.dispose()
    return {
        "teacher_id": teacher_id,
        "student_id": student_id,
        "other_id": other_id,
        "assignment_id": assignment_id,
    }


async def _count_events(db_url: str, student_id: uuid.UUID) -> dict[str, int]:
    engine = create_async_engine(db_url)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_maker() as session:
            rows = (
                await session.execute(
                    select(
                        StudentActivityEvent.event_type,
                        func.count(),
                    )
                    .where(StudentActivityEvent.student_id == student_id)
                    .group_by(StudentActivityEvent.event_type)
                )
            ).all()
            return {event_type.value: count for event_type, count in rows}
    finally:
        await engine.dispose()


@pytest.fixture
def cli_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "reconcile_cli.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ids = asyncio.run(_prepare_db(db_url, with_hole=True, extra_student=True))
    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-reconcile-cli-32b")
    get_settings.cache_clear()
    yield {"db_url": db_url, **ids}
    get_settings.cache_clear()


def test_main_dry_run_does_not_write(cli_db, capsys) -> None:
    from app.cli.reconcile_activity import main

    code = main([])
    captured = capsys.readouterr()

    assert code == 0
    assert str(cli_db["student_id"]) in captured.out
    assert "1" in captured.out
    assert "cli-student@example.com" not in captured.out
    assert "cli-teacher@example.com" not in captured.out
    assert "secret" not in captured.out.lower()
    counts = asyncio.run(_count_events(cli_db["db_url"], cli_db["student_id"]))
    assert counts.get(ActivityEventType.HOMEWORK_COMPLETE.value, 0) == 0


def test_main_apply_creates_only_two_event_types_and_is_idempotent(
    cli_db, capsys
) -> None:
    from app.cli.reconcile_activity import main

    first = main(["--apply"])
    out1 = capsys.readouterr().out
    assert first == 0
    assert str(cli_db["student_id"]) in out1
    assert "cli-student@example.com" not in out1

    counts = asyncio.run(_count_events(cli_db["db_url"], cli_db["student_id"]))
    assert counts == {ActivityEventType.HOMEWORK_COMPLETE.value: 1}
    assert ActivityEventType.HOMEWORK_COMPLETE_DELTA.value not in counts
    assert ActivityEventType.STREAK_DAILY.value not in counts

    second = main(["--apply"])
    out2 = capsys.readouterr().out
    assert second == 0
    counts_again = asyncio.run(_count_events(cli_db["db_url"], cli_db["student_id"]))
    assert counts_again == {ActivityEventType.HOMEWORK_COMPLETE.value: 1}
    assert str(cli_db["student_id"]) in out2


def test_main_student_id_limits_scope(cli_db, capsys) -> None:
    from app.cli.reconcile_activity import main

    other_id = cli_db["other_id"]
    code = main(["--apply", "--student-id", str(other_id)])
    captured = capsys.readouterr()

    assert code == 0
    assert str(other_id) in captured.out
    assert str(cli_db["student_id"]) not in captured.out
    hole_counts = asyncio.run(
        _count_events(cli_db["db_url"], cli_db["student_id"])
    )
    other_counts = asyncio.run(_count_events(cli_db["db_url"], other_id))
    assert hole_counts.get(ActivityEventType.HOMEWORK_COMPLETE.value, 0) == 0
    assert other_counts.get(ActivityEventType.HOMEWORK_COMPLETE.value, 0) == 0


def test_main_unknown_student_id_exits_nonzero_without_traceback(
    cli_db, capsys
) -> None:
    from app.cli.reconcile_activity import main

    missing = uuid.uuid4()
    code = main(["--student-id", str(missing)])
    captured = capsys.readouterr()

    assert code != 0
    assert "Traceback" not in captured.out
    assert str(missing) in captured.err
    assert "Traceback" not in captured.err
