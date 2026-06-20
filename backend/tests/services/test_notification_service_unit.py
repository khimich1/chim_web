"""Direct NotificationService unit tests."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException

from app.models import Notification, NotificationType, User, UserRole
from app.services.notification_service import NotificationService


@pytest.mark.asyncio
async def test_list_notifications_teacher(db_session, teacher_student_users) -> None:
    teacher, _, _ = teacher_student_users
    db_session.add(
        Notification(
            user_id=teacher.id,
            type=NotificationType.HOMEWORK_SUBMITTED,
            payload={"homework_id": str(uuid.uuid4())},
        )
    )
    await db_session.commit()

    service = NotificationService(db_session)
    items = await service.list_notifications(teacher)
    assert len(items) == 1
    assert items[0].type == NotificationType.HOMEWORK_SUBMITTED


@pytest.mark.asyncio
async def test_list_notifications_student_forbidden(
    db_session, teacher_student_users
) -> None:
    _, student, _ = teacher_student_users
    service = NotificationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.list_notifications(student)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_unread_count_teacher(db_session, teacher_student_users) -> None:
    teacher, _, _ = teacher_student_users
    db_session.add(
        Notification(
            user_id=teacher.id,
            type=NotificationType.HOMEWORK_SUBMITTED,
            payload={},
        )
    )
    await db_session.commit()

    service = NotificationService(db_session)
    assert (await service.unread_count(teacher)).count == 1


@pytest.mark.asyncio
async def test_unread_count_student_forbidden(
    db_session, teacher_student_users
) -> None:
    _, student, _ = teacher_student_users
    service = NotificationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.unread_count(student)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_mark_read_success(db_session, teacher_student_users) -> None:
    teacher, _, _ = teacher_student_users
    notification = Notification(
        user_id=teacher.id,
        type=NotificationType.HOMEWORK_SUBMITTED,
        payload={},
    )
    db_session.add(notification)
    await db_session.commit()

    service = NotificationService(db_session)
    read = await service.mark_read(teacher, notification.id)
    assert read.read_at is not None


@pytest.mark.asyncio
async def test_mark_read_not_found(db_session, teacher_student_users) -> None:
    teacher, _, _ = teacher_student_users
    service = NotificationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.mark_read(teacher, uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_mark_read_other_teacher_forbidden(
    db_session, teacher_student_users
) -> None:
    teacher, _, _ = teacher_student_users
    intruder = User(
        email="intruder@example.com",
        password_hash="x",
        role=UserRole.TEACHER,
    )
    db_session.add(intruder)
    await db_session.flush()
    notification = Notification(
        user_id=teacher.id,
        type=NotificationType.HOMEWORK_SUBMITTED,
        payload={},
    )
    db_session.add(notification)
    await db_session.commit()

    service = NotificationService(db_session)
    with pytest.raises(HTTPException) as exc:
        await service.mark_read(intruder, notification.id)
    assert exc.value.status_code == 403
