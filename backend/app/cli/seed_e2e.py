"""Seed teacher, student, and a one-step homework for Playwright smoke E2E (Task 99).

Prints JSON to stdout::

    python -m app.cli.seed_e2e

Idempotent for users; creates a fresh homework assignment each run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password
from app.models import ExamTrack, HomeworkAssignment, HomeworkItemProgress, HomeworkStatus, StudentProfile, User, UserRole
from app.models.enums import HomeworkItemKind
from app.services.homework_validation import validate_homework_items

TEACHER_EMAIL = "e2e-teacher@example.com"
TEACHER_PASS = "e2e-teacher-pass"
STUDENT_EMAIL = "e2e-student@example.com"
STUDENT_PASS = "e2e-student-pass"
CORRECT_ANSWER = "1"
HOMEWORK_TITLE_PREFIX = "E2E smoke"


async def _ensure_teacher(session_factory) -> uuid.UUID:
    async with session_factory() as session:
        teacher = await session.scalar(
            select(User).where(User.email == TEACHER_EMAIL)
        )
        if teacher is None:
            teacher = User(
                email=TEACHER_EMAIL,
                password_hash=hash_password(TEACHER_PASS),
                role=UserRole.TEACHER,
                is_active=True,
            )
            session.add(teacher)
            await session.commit()
            await session.refresh(teacher)
        elif teacher.role != UserRole.TEACHER:
            raise ValueError(f"{TEACHER_EMAIL} exists but is not a teacher")
        return teacher.id


async def _ensure_student(session_factory, teacher_id: uuid.UUID) -> uuid.UUID:
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        student = await session.scalar(
            select(User).where(User.email == STUDENT_EMAIL)
        )
        if student is None:
            student = User(
                email=STUDENT_EMAIL,
                password_hash=hash_password(STUDENT_PASS),
                role=UserRole.STUDENT,
                is_active=True,
            )
            session.add(student)
            await session.flush()
            session.add(
                StudentProfile(
                    user_id=student.id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                    first_login_at=now,
                    onboarding_completed_at=now,
                )
            )
            await session.commit()
            await session.refresh(student)
            return student.id

        if student.role != UserRole.STUDENT:
            raise ValueError(f"{STUDENT_EMAIL} exists but is not a student")

        profile = await session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            session.add(
                StudentProfile(
                    user_id=student.id,
                    teacher_id=teacher_id,
                    track=ExamTrack.EGE,
                    first_login_at=now,
                    onboarding_completed_at=now,
                )
            )
        else:
            profile.first_login_at = profile.first_login_at or now
            profile.onboarding_completed_at = profile.onboarding_completed_at or now
        await session.commit()
        return student.id


async def _create_homework(
    session_factory,
    *,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    settings,
) -> uuid.UUID:
    items_payload = [
        {
            "kind": HomeworkItemKind.TEST_PARTIAL.value,
            "variant": "001.txt",
            "types": [1],
        }
    ]
    from app.schemas.homework import TestPartialItem

    parsed_items = [TestPartialItem.model_validate(items_payload[0])]
    async with session_factory() as session:
        await validate_homework_items(
            parsed_items,
            track=ExamTrack.EGE,
            teacher_id=teacher_id,
            settings=settings,
            session=session,
        )
        assignment = HomeworkAssignment(
            student_id=student_id,
            teacher_id=teacher_id,
            title=f"{HOMEWORK_TITLE_PREFIX} {uuid.uuid4().hex[:8]}",
            description="Playwright smoke: one test step then submit.",
            items=items_payload,
            status=HomeworkStatus.ASSIGNED,
            item_progress=[
                HomeworkItemProgress(
                    item_index=0,
                    kind=HomeworkItemKind.TEST_PARTIAL,
                    completed=False,
                )
            ],
        )
        session.add(assignment)
        await session.commit()
        await session.refresh(assignment)
        return assignment.id


async def seed_e2e() -> dict[str, str]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        teacher_id = await _ensure_teacher(session_factory)
        student_id = await _ensure_student(session_factory, teacher_id)
        homework_id = await _create_homework(
            session_factory,
            teacher_id=teacher_id,
            student_id=student_id,
            settings=settings,
        )
        return {
            "teacherEmail": TEACHER_EMAIL,
            "teacherPassword": TEACHER_PASS,
            "studentEmail": STUDENT_EMAIL,
            "studentPassword": STUDENT_PASS,
            "homeworkId": str(homework_id),
            "correctAnswer": CORRECT_ANSWER,
        }
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed Playwright E2E users and homework")
    parser.parse_args(argv)
    try:
        payload = asyncio.run(seed_e2e())
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
