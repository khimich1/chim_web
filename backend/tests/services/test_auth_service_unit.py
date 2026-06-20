"""Direct AuthService unit tests (async) for accurate coverage measurement."""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.db.base import Base
from app.models import ExamTrack, StudentProfile, User, UserRole
from app.services.auth_service import AuthService


@pytest.fixture
async def auth_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        teacher_id = uuid.uuid4()
        student_id = uuid.uuid4()
        session.add_all(
            [
                User(
                    id=teacher_id,
                    email="teacher@example.com",
                    password_hash=hash_password("secret"),
                    role=UserRole.TEACHER,
                ),
                User(
                    id=student_id,
                    email="student@example.com",
                    password_hash=hash_password("secret"),
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
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_authenticate_success(auth_session) -> None:
    service = AuthService(auth_session)
    user = await service.authenticate("teacher@example.com", "secret")
    assert user is not None
    assert user.role == UserRole.TEACHER


@pytest.mark.asyncio
async def test_authenticate_unknown_email(auth_session) -> None:
    service = AuthService(auth_session)
    assert await service.authenticate("missing@example.com", "secret") is None


@pytest.mark.asyncio
async def test_authenticate_wrong_password(auth_session) -> None:
    service = AuthService(auth_session)
    assert await service.authenticate("teacher@example.com", "wrong") is None


@pytest.mark.asyncio
async def test_get_user_track_student(auth_session) -> None:
    service = AuthService(auth_session)
    user = await service.authenticate("student@example.com", "secret")
    assert user is not None
    assert await service.get_user_track(user) == ExamTrack.EGE


@pytest.mark.asyncio
async def test_authenticate_inactive_user(auth_session) -> None:
    inactive = User(
        email="inactive@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.TEACHER,
        is_active=False,
    )
    auth_session.add(inactive)
    await auth_session.commit()

    service = AuthService(auth_session)
    assert await service.authenticate("inactive@example.com", "secret") is None


@pytest.mark.asyncio
async def test_get_user_track_orphan_student(auth_session) -> None:
    orphan = User(
        email="orphan@example.com",
        password_hash=hash_password("secret"),
        role=UserRole.STUDENT,
    )
    auth_session.add(orphan)
    await auth_session.commit()

    service = AuthService(auth_session)
    assert await service.get_user_track(orphan) is None


@pytest.mark.asyncio
async def test_get_user_track_teacher_returns_none(auth_session) -> None:
    service = AuthService(auth_session)
    user = await service.authenticate("teacher@example.com", "secret")
    assert user is not None
    assert await service.get_user_track(user) is None
