"""Image upload API tests (SPEC §1.9.7)."""

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

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"
OTHER_STUDENT_EMAIL = "other@example.com"

# Minimal 1x1 PNG
PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05"
    b"\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "uploads.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add_all(
                [
                    User(
                        id=teacher_id,
                        email=TEACHER_EMAIL,
                        password_hash=hash_password(TEACHER_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=other_student_id,
                        email=OTHER_STUDENT_EMAIL,
                        password_hash=hash_password("other-pass"),
                        role=UserRole.STUDENT,
                    ),
                ]
            )
            await session.flush()
            session.add_all(
                [
                    StudentProfile(
                        user_id=student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                    ),
                    StudentProfile(
                        user_id=other_student_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.OGE,
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
    settings = Settings()
    object.__setattr__(settings, "upload_dir", upload_dir)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def test_upload_valid_png_as_student(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.post(
        "/api/uploads/images",
        files={"file": ("test.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == f"/api/uploads/images/{body['id']}"

    get_response = client.get(f"/api/uploads/images/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.headers["content-type"].startswith("image/png")
    assert get_response.content == PNG_BYTES


def test_upload_valid_png_as_teacher(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    response = client.post(
        "/api/uploads/images",
        files={"file": ("diagram.png", PNG_BYTES, "image/png")},
    )
    assert response.status_code == 201


def test_reject_unsupported_mime(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    response = client.post(
        "/api/uploads/images",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 422
    assert "MIME" in response.json()["detail"]


def test_reject_oversize_image(client: TestClient, tmp_path: Path) -> None:
    db_file = tmp_path / "oversize.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads_oversize"
    student_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add(
                User(
                    id=student_id,
                    email="solo@example.com",
                    password_hash=hash_password("pass"),
                    role=UserRole.STUDENT,
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
    settings = Settings()
    object.__setattr__(settings, "upload_dir", upload_dir)
    object.__setattr__(settings, "upload_max_bytes", 16)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        assert (
            test_client.post(
                "/api/auth/login",
                json={"email": "solo@example.com", "password": "pass"},
            ).status_code
            == 200
        )
        response = test_client.post(
            "/api/uploads/images",
            files={"file": ("big.png", PNG_BYTES, "image/png")},
        )
        assert response.status_code == 422
        assert "size" in response.json()["detail"].lower()

    asyncio.run(request_engine.dispose())


def test_get_image_rbac_owner_only(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    upload = client.post(
        "/api/uploads/images",
        files={"file": ("mine.png", PNG_BYTES, "image/png")},
    )
    image_id = upload.json()["id"]

    client.post("/api/auth/logout")
    assert _login(client, OTHER_STUDENT_EMAIL, "other-pass").status_code == 200

    forbidden = client.get(f"/api/uploads/images/{image_id}")
    assert forbidden.status_code == 403

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    allowed = client.get(f"/api/uploads/images/{image_id}")
    assert allowed.status_code == 200
