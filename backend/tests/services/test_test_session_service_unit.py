"""Direct TestSessionService unit tests for core session lifecycle."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from app.models import CustomTask, GradingMode, TeacherTheme
from app.core.security import hash_password
from app.models import User, UserRole
from app.schemas.homework import HomeworkCreate, HomeworkSubmitRequest
from app.schemas.test_session import SessionCreate
from app.services.homework_service import HomeworkService
from app.services.homework_submit_service import HomeworkSubmitService
from app.services.test_session_service import (
    TestSessionService as SessionService,
    _session_duration_minutes,
)


async def _seed_custom_theme(
    db_session, teacher, *, title: str = "ОВР"
) -> tuple[uuid.UUID, uuid.UUID]:
    theme_id = uuid.uuid4()
    task_id = uuid.uuid4()
    db_session.add(
        TeacherTheme(
            id=theme_id,
            teacher_id=teacher.id,
            title=title,
            is_published=True,
            sort_order=0,
        )
    )
    await db_session.flush()
    db_session.add(
        CustomTask(
            id=task_id,
            theme_id=theme_id,
            title="Задача",
            sort_order=0,
            grading_mode=GradingMode.AUTO,
            question_blocks=[{"type": "text", "content": "2+2=?"}],
            correct_value="4",
        )
    )
    await db_session.commit()
    return theme_id, task_id


@pytest.mark.asyncio
async def test_create_session_from_variant(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    session = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )
    assert session.track == "ege"
    assert session.variant_ref == "001.txt"
    assert session.total_steps == 2
    assert "correct_ans" not in session.steps[0].model_dump()


@pytest.mark.asyncio
async def test_create_session_by_type_across_variants(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    session = await service.create_session(student, SessionCreate(types=[1]))
    assert session.variant_ref is None
    assert session.total_steps == 1


@pytest.mark.asyncio
async def test_check_and_complete_session(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )

    checked = await service.check_step(student, created.id, 0, "1")
    assert checked.is_correct is True

    wrong = await service.check_step(student, created.id, 1, "wrong")
    assert wrong.is_correct is False

    summary = await service.complete_session(student, created.id)
    assert summary.status == "completed"
    assert summary.score == 1
    assert summary.max_score == 2


@pytest.mark.asyncio
async def test_get_session_forbidden_for_other_student(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, other = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )

    with pytest.raises(HTTPException) as exc:
        await service.get_session(other, created.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_get_session_not_found(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    with pytest.raises(HTTPException) as exc:
        await service.get_session(student, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_partial_session_filters_types(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    session = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt", types=[2]),
    )
    assert session.total_steps == 1
    assert session.steps[0].type == 2


@pytest.mark.asyncio
async def test_get_active_session_by_variant(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )

    active = await service.get_active_session(
        student,
        variant_ref="001.txt",
    )
    assert active.session_id == created.id
    assert active.session_id is not None


@pytest.mark.asyncio
async def test_get_active_session_requires_single_scope(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    with pytest.raises(HTTPException) as exc:
        await service.get_active_session(student)
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_check_after_complete_returns_409(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )
    await service.check_step(student, created.id, 0, "1")
    await service.check_step(student, created.id, 1, "wrong")
    await service.complete_session(student, created.id)

    with pytest.raises(HTTPException) as exc:
        await service.check_step(student, created.id, 0, "1")
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_create_session_no_questions_returns_404(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            student,
            SessionCreate(variant_ref="missing-variant.txt"),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_session_for_homework_assignment(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Тестовое ДЗ",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )

    service = SessionService(db_session, service_settings)
    session = await service.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    assert session.homework_assignment_id == assignment.id
    assert session.total_steps >= 1

    active = await service.get_active_session(
        student,
        homework_assignment_id=assignment.id,
    )
    assert active.session_id == session.id


@pytest.mark.asyncio
async def test_complete_session_twice_is_idempotent(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )
    await service.check_step(student, created.id, 0, "1")
    await service.check_step(student, created.id, 1, "wrong")

    first = await service.complete_session(student, created.id)
    second = await service.complete_session(student, created.id)
    assert first.score == second.score == 1
    assert first.status == second.status == "completed"


@pytest.mark.asyncio
async def test_create_homework_session_with_partial_variant(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Частичный тест",
            items=[
                {
                    "kind": "test_partial",
                    "variant": "001.txt",
                    "types": [2],
                }
            ],
        ),
    )

    service = SessionService(db_session, service_settings)
    session = await service.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    assert session.total_steps == 1
    assert session.steps[0].type == 2


@pytest.mark.asyncio
async def test_get_active_session_by_task_type(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(student, SessionCreate(types=[1]))
    active = await service.get_active_session(student, task_type=1)
    assert active.session_id == created.id


@pytest.mark.asyncio
async def test_homework_session_rejects_other_student(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, other = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="ДЗ",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            other,
            SessionCreate(homework_assignment_id=assignment.id),
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_homework_session_rejects_submitted_assignment(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    submit = HomeworkSubmitService(db_session)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )
    await submit.submit(student, assignment.id, HomeworkSubmitRequest())

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            student,
            SessionCreate(homework_assignment_id=assignment.id),
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_get_active_homework_not_found(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    with pytest.raises(HTTPException) as exc:
        await service.get_active_session(
            student,
            homework_assignment_id=uuid.uuid4(),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_session_requires_student_profile(
    db_session, service_settings
) -> None:
    orphan = User(
        email="orphan@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.STUDENT,
    )
    db_session.add(orphan)
    await db_session.commit()

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            orphan,
            SessionCreate(variant_ref="001.txt"),
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_session_returns_step_view(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )
    loaded = await service.get_session(student, created.id)
    assert loaded.id == created.id
    assert "correct_ans" not in loaded.steps[0].model_dump()


@pytest.mark.asyncio
async def test_attach_answer_image_rejects_exam_step(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )
    with pytest.raises(HTTPException) as exc:
        await service.attach_answer_image(
            student,
            created.id,
            0,
            uuid.uuid4(),
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_homework_without_test_items_returns_422(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Только лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            student,
            SessionCreate(homework_assignment_id=assignment.id),
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_get_active_homework_forbidden_for_other_student(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, other = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="ДЗ",
            items=[{"kind": "test_variant", "variant": "001.txt"}],
        ),
    )

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.get_active_session(
            other,
            homework_assignment_id=assignment.id,
        )
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_check_step_position_not_found(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )

    with pytest.raises(HTTPException) as exc:
        await service.check_step(student, created.id, 99, "1")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_homework_test_by_type_item(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="По типу",
            items=[{"kind": "test_by_type", "types": [1]}],
        ),
    )

    service = SessionService(db_session, service_settings)
    session = await service.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    assert session.total_steps >= 1
    assert session.steps[0].type == 1


@pytest.mark.asyncio
async def test_homework_custom_theme_only_session(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    theme_id, _ = await _seed_custom_theme(db_session, teacher)
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Кастом",
            items=[{"kind": "custom_theme", "theme_id": str(theme_id)}],
        ),
    )

    service = SessionService(db_session, service_settings)
    created = await service.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    assert created.total_steps == 1
    assert created.steps[0].custom_task_id is not None

    loaded = await service.get_session(student, created.id)
    assert loaded.steps[0].grading_mode == GradingMode.AUTO

    checked = await service.check_step(student, created.id, 0, "4")
    assert checked.is_correct is True

    summary = await service.complete_session(student, created.id)
    assert summary.status == "completed"
    assert summary.score == 1


@pytest.mark.asyncio
async def test_homework_mixed_exam_and_custom_session(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    theme_id, _ = await _seed_custom_theme(db_session, teacher)
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Смешанное",
            items=[
                {"kind": "test_variant", "variant": "001.txt"},
                {"kind": "custom_theme", "theme_id": str(theme_id)},
            ],
        ),
    )

    service = SessionService(db_session, service_settings)
    created = await service.create_session(
        student,
        SessionCreate(homework_assignment_id=assignment.id),
    )
    assert created.total_steps == 3

    loaded = await service.get_session(student, created.id)
    assert len(loaded.steps) == 3

    await service.check_step(student, created.id, 0, "1")
    await service.check_step(student, created.id, 1, "wrong")
    await service.check_step(student, created.id, 2, "4")

    summary = await service.complete_session(student, created.id)
    assert summary.max_score == 3
    assert summary.score == 2


@pytest.mark.asyncio
async def test_homework_no_test_items_raises_422(
    db_session, teacher_student_users, service_settings
) -> None:
    teacher, student, _ = teacher_student_users
    homework = HomeworkService(db_session, service_settings)
    assignment = await homework.create_assignment(
        teacher,
        HomeworkCreate(
            student_id=student.id,
            title="Только лекция",
            items=[{"kind": "lecture", "topic": "Алканы"}],
        ),
    )

    service = SessionService(db_session, service_settings)
    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            student,
            SessionCreate(homework_assignment_id=assignment.id),
        )
    assert exc.value.status_code == 422


@pytest.mark.asyncio
async def test_attach_answer_image_rejects_exam_step(
    db_session, teacher_student_users, service_settings
) -> None:
    _, student, _ = teacher_student_users
    service = SessionService(db_session, service_settings)

    created = await service.create_session(
        student,
        SessionCreate(variant_ref="001.txt"),
    )

    with pytest.raises(HTTPException) as exc:
        await service.attach_answer_image(
            student,
            created.id,
            0,
            uuid.uuid4(),
        )
    assert exc.value.status_code == 422


def test_session_duration_minutes_zero_when_instant() -> None:
    now = datetime.now(timezone.utc)
    assert _session_duration_minutes(now, now) == 0
