"""Tests for explain_incorrect_step server-side gating (SPEC §1.3.4)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import (
    ExamTrack,
    StudentProfile,
    TestSession,
    TestSessionStep,
    User,
    UserRole,
)
from app.models.enums import StepStatus, TestSessionStatus
from app.services.tutor.solve_gating import resolve_incorrect_step_gate


@pytest.fixture
def gating_db(tmp_path):
    db_file = tmp_path / "solve_gating.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    session_id = uuid.uuid4()

    async def _setup() -> dict[str, uuid.UUID]:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add(
                User(
                    id=teacher_id,
                    email="teacher@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.TEACHER,
                )
            )
            session.add(
                User(
                    id=student_id,
                    email="student@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.STUDENT,
                )
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
                TestSession(
                    id=session_id,
                    student_id=student_id,
                    track=ExamTrack.EGE,
                    variant_ref="001.txt",
                    status=TestSessionStatus.IN_PROGRESS,
                    steps=[
                        TestSessionStep(
                            position=0,
                            test_id=42,
                            answer="99",
                            is_correct=False,
                            status=StepStatus.CHECKED,
                            checked_at=datetime.now(timezone.utc),
                        ),
                        TestSessionStep(
                            position=1,
                            test_id=43,
                            answer=None,
                            is_correct=None,
                            status=StepStatus.UNSEEN,
                        ),
                    ],
                )
            )
            await session.commit()
        await engine.dispose()
        return {
            "student_id": student_id,
            "session_id": session_id,
            "db_url": db_url,
        }

    return asyncio.run(_setup())


@pytest.mark.asyncio
async def test_resolve_gate_for_checked_incorrect_step(gating_db) -> None:
    engine = create_async_engine(gating_db["db_url"])
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        gate = await resolve_incorrect_step_gate(
            session,
            student_id=gating_db["student_id"],
            page_context={
                "solve_mode": "explain_incorrect_step",
                "test_session_id": str(gating_db["session_id"]),
                "step_position": 0,
                "test_id": 42,
            },
        )
    await engine.dispose()

    assert gate is not None
    assert gate.test_id == 42
    assert gate.step_position == 0
    assert gate.student_answer == "99"


@pytest.mark.asyncio
async def test_resolve_gate_rejects_wrong_test_id(gating_db) -> None:
    engine = create_async_engine(gating_db["db_url"])
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        gate = await resolve_incorrect_step_gate(
            session,
            student_id=gating_db["student_id"],
            page_context={
                "solve_mode": "explain_incorrect_step",
                "test_session_id": str(gating_db["session_id"]),
                "step_position": 0,
                "test_id": 99,
            },
        )
    await engine.dispose()
    assert gate is None


@pytest.mark.asyncio
async def test_resolve_gate_rejects_unseen_step(gating_db) -> None:
    engine = create_async_engine(gating_db["db_url"])
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        gate = await resolve_incorrect_step_gate(
            session,
            student_id=gating_db["student_id"],
            page_context={
                "solve_mode": "explain_incorrect_step",
                "test_session_id": str(gating_db["session_id"]),
                "step_position": 1,
                "test_id": 43,
            },
        )
    await engine.dispose()
    assert gate is None
