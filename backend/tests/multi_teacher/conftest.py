"""Shared two-teacher fixture for multi-tenant isolation tests (Variant A)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, StudentProfile, User, UserRole
from tests.content.conftest import _create_tests_db

TEACHER_A_EMAIL = "mt-teacher-a@example.com"
TEACHER_B_EMAIL = "mt-teacher-b@example.com"
STUDENT_A_EMAIL = "mt-student-a@example.com"
STUDENT_B_EMAIL = "mt-student-b@example.com"
PASSWORD = "test-password"
JWT_SECRET = "test-jwt-secret-for-multi-teacher-32b"

# Minimal 1x1 PNG
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
    b"\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def multi_teacher_client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "multi_teacher.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    upload_dir = tmp_path / "uploads"
    _create_tests_db(ege_db, with_bug=True)

    teacher_a_id = uuid.uuid4()
    teacher_b_id = uuid.uuid4()
    student_a_id = uuid.uuid4()
    student_b_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add_all(
                [
                    User(
                        id=teacher_a_id,
                        email=TEACHER_A_EMAIL,
                        password_hash=hash_password(PASSWORD),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=teacher_b_id,
                        email=TEACHER_B_EMAIL,
                        password_hash=hash_password(PASSWORD),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_a_id,
                        email=STUDENT_A_EMAIL,
                        password_hash=hash_password(PASSWORD),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=student_b_id,
                        email=STUDENT_B_EMAIL,
                        password_hash=hash_password(PASSWORD),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    StudentProfile(
                        user_id=student_a_id,
                        teacher_id=teacher_a_id,
                        track=ExamTrack.EGE,
                    ),
                    StudentProfile(
                        user_id=student_b_id,
                        teacher_id=teacher_b_id,
                        track=ExamTrack.EGE,
                    ),
                ]
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
    settings = Settings(
        DATABASE_URL=db_url,
        JWT_SECRET=JWT_SECRET,
        CONTENT_EGE_DB_PATH=str(ege_db),
    )
    object.__setattr__(settings, "upload_dir", upload_dir)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.teacher_a_email = TEACHER_A_EMAIL  # type: ignore[attr-defined]
        test_client.teacher_b_email = TEACHER_B_EMAIL  # type: ignore[attr-defined]
        test_client.student_a_id = str(student_a_id)  # type: ignore[attr-defined]
        test_client.student_b_id = str(student_b_id)  # type: ignore[attr-defined]
        yield test_client

    asyncio.run(request_engine.dispose())


def mt_login(client: TestClient, email: str) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    assert response.status_code == 200, response.text


def mt_logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text
