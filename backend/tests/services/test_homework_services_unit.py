"""Direct HomeworkService and HomeworkSubmitService unit tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models.enums import HomeworkItemKind
from app.models import User, UserRole
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.schemas.homework import HomeworkCreate, HomeworkSubmitRequest
from app.schemas.test_session import SessionCreate
from app.services.homework_service import HomeworkService
from app.services.homework_submit_service import (
    HomeworkSubmitService,
    compute_homework_points,
    count_lecture_progress,
    count_session_progress,
)
from app.services.test_session_service import TestSessionService as SessionService
from app.services.activity_service import POINTS_HOMEWORK_COMPLETE


@pytest.mark.asyncio
async def test_create_assignment_success(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    service = HomeworkService(db_session, service_settings)
    created = await service.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )
    assert created.title == "Лекция"
    assert created.student_email == student.email


@pytest.mark.asyncio
async def test_create_assignment_unknown_student(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, _, _ = teacher_student_users
    service = HomeworkService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_assignment(
            teacher,
            HomeworkCreate(
                student_id=uuid.uuid4(),
                title="Нет ученика",
                items=[{"kind": "lecture", "topic": "Алканы"}],
            ),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_assignments_teacher_and_student(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    service = HomeworkService(db_session, service_settings)
    await service.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="ДЗ",
            items=[{"kind": "lecture", "topic": "Соли"}],
        ),
    )

    teacher_list = await service.list_assignments(teacher)
    assert len(teacher_list) == 1
    assert teacher_list[0].student_email == student.email

    student_list = await service.list_assignments(student)
    assert len(student_list) == 1
    assert student_list[0].student_email is None


@pytest.mark.asyncio
async def test_get_assignment_rbac(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, other = teacher_student_users
    service = HomeworkService(db_session, service_settings)
    created = await service.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=other.id,
            title="Чужое",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_assignment(student, created.id)
    assert exc.value.status_code == 403

    detail = await service.get_assignment(teacher, created.id)
    assert detail.id == created.id


@pytest.mark.asyncio
async def test_submit_lecture_homework(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    submitted = await submit.submit(student, created.id, HomeworkSubmitRequest())
    assert submitted.status == "submitted"
    assert submitted.submission is not None

    with pytest.raises(HTTPException) as exc:
        await submit.submit(student, created.id, HomeworkSubmitRequest())
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_complete_lecture_item(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    updated = await submit.complete_item(student, created.id, 0)
    assert updated.status == "in_progress"
    assert updated.progress[0].completed is True


@pytest.mark.asyncio
async def test_get_assignment_not_found(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, _, _ = teacher_student_users
    service = HomeworkService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.get_assignment(teacher, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_assignment_teacher_forbidden(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, _, other_teacher = teacher_student_users
    intruder = User(
        email="intruder@example.com",
        password_hash="x",
        role=UserRole.TEACHER,
    )
    db_session.add(intruder)
    await db_session.flush()

    service = HomeworkService(db_session, service_settings)
    created = await service.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=other_teacher.id,
            title="ДЗ",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_assignment(intruder, created.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_submit_lecture_rejects_test_session_id(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await submit.submit(
            student,
            created.id,
            HomeworkSubmitRequest(test_session_id=uuid.uuid4()),
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_mark_in_progress(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    await submit.mark_in_progress(student, created.id)
    detail = await homework.get_assignment(student, created.id)
    assert detail.status == "in_progress"


@pytest.mark.asyncio
async def test_complete_item_rejects_test_kind(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Тест",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await submit.complete_item(student, created.id, 0)
    assert exc.value.status_code == 422
    assert HomeworkItemKind.TEST_VARIANT.value == "test_variant"


def test_compute_homework_points_zero_total_uses_full_points() -> None:
    assert compute_homework_points(0, 0) == POINTS_HOMEWORK_COMPLETE


@pytest.mark.asyncio
async def test_count_progress_helpers(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Progress",
            items=[
                {"kind": "lecture", "topic": "A"},
                {"kind": "test_variant", "variant": "001.txt"},
            ],
        ),
    )
    sessions = SessionService(db_session, service_settings)
    test_session = await sessions.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    orm_session = await TestSessionRepository(db_session).get_with_steps(test_session.id)
    assert orm_session is not None
    session_progress = count_session_progress(orm_session)
    assert session_progress.total_steps == 2
    assert session_progress.answered_steps == 0

    orm = await HomeworkRepository(db_session).get_by_id(assignment.id)
    assert orm is not None
    lecture_progress = count_lecture_progress(orm)
    assert lecture_progress.total_steps == 2


async def _partial_test_homework_flow(
    db_session,
    teacher_student_users,
    service_settings,
):
    """Create HW, answer one of two steps, complete session — ready to partial submit."""
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)
    sessions = SessionService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Partial",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )
    session = await sessions.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    await sessions.check_step(student, session.id, 0, "1")
    await sessions.complete_session(student, session.id)
    return homework, submit, sessions, student, assignment, session


@pytest.mark.asyncio
async def test_partial_submit_reopen_and_resubmit_via_service(
    db_session, teacher_student_users, service_settings
) -> None:
    homework, submit, sessions, student, assignment, session = await _partial_test_homework_flow(
        db_session, teacher_student_users, service_settings
    )

    partial = await submit.submit(
        student,
        assignment.id,
        HomeworkSubmitRequest(test_session_id=session.id),
    )
    assert partial.status == "submitted"
    assert partial.submission is not None
    assert partial.submission.completion_percent == 50
    assert partial.can_reopen is True

    reopened = await submit.reopen(student, assignment.id)
    assert reopened.status == "in_progress"
    assert reopened.can_reopen is False

    await sessions.check_step(student, session.id, 1, "2")
    await sessions.complete_session(student, session.id)
    final = await submit.submit(
        student,
        assignment.id,
        HomeworkSubmitRequest(test_session_id=session.id),
    )
    assert final.submission is not None
    assert final.submission.completion_percent == 100
    assert final.can_reopen is False


@pytest.mark.asyncio
async def test_submit_without_test_session_id_uses_latest_completed(
    db_session, teacher_student_users, service_settings
) -> None:
    _, submit, _, student, assignment, session = await _partial_test_homework_flow(
        db_session, teacher_student_users, service_settings
    )

    submitted = await submit.submit(student, assignment.id, HomeworkSubmitRequest())
    assert submitted.submission is not None
    assert submitted.submission.answered_steps == 1


@pytest.mark.asyncio
async def test_submit_requires_at_least_one_answered_step(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)
    sessions = SessionService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Empty answers",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )
    session = await sessions.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    await sessions.complete_session(student, session.id)

    with pytest.raises(HTTPException) as exc:
        await submit.submit(
            student,
            assignment.id,
            HomeworkSubmitRequest(test_session_id=session.id),
        )
    assert exc.value.status_code == 422
    assert "at least one answered step" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_reopen_errors(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)
    sessions = SessionService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Reopen errors",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await submit.reopen(student, assignment.id)
    assert exc.value.status_code == 422
    assert "not been submitted" in exc.value.detail.lower()

    full_session = await sessions.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    await sessions.check_step(student, full_session.id, 0, "1")
    await sessions.check_step(student, full_session.id, 1, "2")
    await sessions.complete_session(student, full_session.id)
    await submit.submit(
        student,
        assignment.id,
        HomeworkSubmitRequest(test_session_id=full_session.id),
    )

    with pytest.raises(HTTPException) as exc2:
        await submit.reopen(student, assignment.id)
    assert exc2.value.status_code == 422
    assert "fully completed" in exc2.value.detail.lower()


@pytest.mark.asyncio
async def test_resolve_test_session_errors(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, other = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)
    sessions = SessionService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Resolve errors",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )
    session = await sessions.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    await sessions.check_step(student, session.id, 0, "1")

    with pytest.raises(HTTPException) as exc:
        await submit.submit(
            student,
            assignment.id,
            HomeworkSubmitRequest(test_session_id=session.id),
        )
    assert exc.value.status_code == 422
    assert "complete the test session" in exc.value.detail.lower()

    with pytest.raises(HTTPException) as exc2:
        await submit.submit(
            student,
            assignment.id,
            HomeworkSubmitRequest(test_session_id=uuid.uuid4()),
        )
    assert exc2.value.status_code == 404

    other_assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=other.id,
            title="Other",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )
    other_session = await sessions.create_session(
        other,
        SessionCreate(homework_assignment_id=other_assignment.id),
    )
    await sessions.check_step(other, other_session.id, 0, "1")
    await sessions.complete_session(other, other_session.id)

    with pytest.raises(HTTPException) as exc3:
        await submit.submit(
            student,
            assignment.id,
            HomeworkSubmitRequest(test_session_id=other_session.id),
        )
    assert exc3.value.status_code == 403


@pytest.mark.asyncio
async def test_complete_item_guardrails(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    teacher_id = teacher.id
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)

    created = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Lecture guards",
            items=[{"kind": "lecture", "topic": "A"}],
        ),
    )
    await submit.submit(student, created.id, HomeworkSubmitRequest())

    with pytest.raises(HTTPException) as exc:
        await submit.complete_item(student, created.id, 0)
    assert exc.value.status_code == 409

    teacher_refreshed = await db_session.get(User, teacher_id)
    assert teacher_refreshed is not None
    in_progress = await homework.create_assignment(
        teacher_refreshed,
        HomeworkCreate(
            student_id=student.id,
            title="Bad index",
            items=[{"kind": "lecture", "topic": "B"}],
        ),
    )
    with pytest.raises(HTTPException) as exc2:
        await submit.complete_item(student, in_progress.id, 5)
    assert exc2.value.status_code == 404


@pytest.mark.asyncio
async def test_load_owned_assignment_rbac(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, other = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session, settings=service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="RBAC",
            items=[{"kind": "lecture", "topic": "A"}],
        ),
    )

    with pytest.raises(HTTPException) as exc:
        await submit.submit(other, assignment.id, HomeworkSubmitRequest())
    assert exc.value.status_code == 403

    with pytest.raises(HTTPException) as exc2:
        await submit.submit(student, uuid.uuid4(), HomeworkSubmitRequest())
    assert exc2.value.status_code == 404
