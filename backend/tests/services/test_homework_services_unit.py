"""Direct HomeworkService and HomeworkSubmitService unit tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models.enums import HomeworkItemKind
from app.models import User, UserRole
from app.schemas.homework import HomeworkCreate, HomeworkSubmitRequest
from app.services.homework_service import HomeworkService
from app.services.homework_submit_service import HomeworkSubmitService


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
