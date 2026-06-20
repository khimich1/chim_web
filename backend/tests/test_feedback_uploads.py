"""Audio upload API tests (SPEC §1.9.9, Task 81)."""

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

TEACHER_EMAIL = "teacher-audio@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student-audio@example.com"
STUDENT_PASS = "student-pass"

# Minimal fake webm bytes (duration validated via form field in tests)
WEBM_BYTES = b"\x1a\x45\xdf\xa3" + b"\x00" * 64


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "audio_uploads.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    upload_dir = tmp_path / "uploads"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()

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
    object.__setattr__(settings, "upload_audio_max_duration_sec", 600)
    app = create_app(settings=settings)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    assert (
        client.post("/api/auth/login", json={"email": email, "password": password}).status_code
        == 200
    )


def test_teacher_can_upload_audio(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.post(
        "/api/uploads/audio",
        files={"file": ("voice.webm", WEBM_BYTES, "audio/webm")},
        data={"duration_sec": "12.5"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["url"] == f"/api/uploads/audio/{body['id']}"
    assert body["duration_sec"] == 12.5

    get_response = client.get(f"/api/uploads/audio/{body['id']}")
    assert get_response.status_code == 200
    assert get_response.headers["content-type"].startswith("audio/webm")


def test_student_cannot_upload_audio(client: TestClient) -> None:
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.post(
        "/api/uploads/audio",
        files={"file": ("voice.webm", WEBM_BYTES, "audio/webm")},
        data={"duration_sec": "5"},
    )
    assert response.status_code == 403


def test_reject_unsupported_audio_mime(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.post(
        "/api/uploads/audio",
        files={"file": ("voice.mp3", WEBM_BYTES, "audio/mpeg")},
        data={"duration_sec": "5"},
    )
    assert response.status_code == 422


def test_reject_audio_over_duration_limit(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    response = client.post(
        "/api/uploads/audio",
        files={"file": ("long.webm", WEBM_BYTES, "audio/webm")},
        data={"duration_sec": "601"},
    )
    assert response.status_code == 422
    assert "duration" in response.json()["detail"].lower()


def test_audio_rbac_owner_only(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    upload = client.post(
        "/api/uploads/audio",
        files={"file": ("voice.webm", WEBM_BYTES, "audio/webm")},
        data={"duration_sec": "3"},
    )
    audio_id = upload.json()["id"]

    client.post("/api/auth/logout")
    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    forbidden = client.get(f"/api/uploads/audio/{audio_id}")
    assert forbidden.status_code == 403
