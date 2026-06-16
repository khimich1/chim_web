"""Tests images API and placeholder substitution in questions."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from urllib.parse import quote

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

STUDENT_EMAIL = "ege-student@example.com"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "test_images_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    _create_tests_db(ege_db, with_bug=True)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()

    async def _setup() -> None:
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
                    email=STUDENT_EMAIL,
                    password_hash=hash_password(STUDENT_PASS),
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
            JWT_SECRET="test-jwt-secret-for-test-images",
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient) -> None:
    assert (
        client.post(
            "/api/auth/login",
            json={"email": STUDENT_EMAIL, "password": STUDENT_PASS},
        ).status_code
        == 200
    )


def test_questions_replace_image_placeholder(client: TestClient) -> None:
    _login(client)

    response = client.get("/api/tests/variants/001.txt/questions")
    assert response.status_code == 200
    questions = response.json()
    image_url = f"/api/tests/images/{quote('рисунок0001.png')}"
    assert image_url in questions[1]["question"]
    assert "[рисунок0001]" not in questions[1]["question"]


def test_student_can_fetch_png_image(client: TestClient) -> None:
    _login(client)

    filename = quote("рисунок0001.png")
    response = client.get(f"/api/tests/images/{filename}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"


def test_missing_image_returns_404(client: TestClient) -> None:
    _login(client)

    assert client.get("/api/tests/images/missing.png").status_code == 404
