"""Active in_progress test session lookup (SPEC §1.3.2)."""

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

STUDENT_EMAIL = "student@example.com"
OTHER_EMAIL = "other@example.com"
TEACHER_EMAIL = "teacher@example.com"
PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "active_sessions_app.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    _create_tests_db(ege_db, with_bug=True)

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_id = uuid.uuid4()

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
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=other_id,
                        email=OTHER_EMAIL,
                        password_hash=hash_password(PASS),
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
                        user_id=other_id,
                        teacher_id=teacher_id,
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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-active-sessions-32b",
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str = STUDENT_EMAIL) -> None:
    assert (
        client.post(
            "/api/auth/login", json={"email": email, "password": PASS}
        ).status_code
        == 200
    )


def _create_free_session(client: TestClient, variant_ref: str = "001.txt") -> dict:
    response = client.post(
        "/api/tests/sessions", json={"variant_ref": variant_ref}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_test_homework(client: TestClient) -> str:
    assert (
        client.post(
            "/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": PASS},
        ).status_code
        == 200
    )
    student_id = next(
        item["id"]
        for item in client.get("/api/students").json()
        if item["email"] == STUDENT_EMAIL
    )
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Тестовое ДЗ",
            "items": [{"kind": "test_variant", "variant": "001.txt"}],
        },
    )
    assert response.status_code == 201, response.text
    client.post("/api/auth/logout")
    _login(client)
    return response.json()["id"]


def test_active_session_by_variant_ref(client: TestClient) -> None:
    _login(client)
    created = _create_free_session(client)
    session_id = created["id"]

    active = client.get(
        "/api/tests/sessions/active", params={"variant_ref": "001.txt"}
    )
    assert active.status_code == 200
    assert active.json()["session_id"] == session_id


def test_active_session_null_when_none(client: TestClient) -> None:
    _login(client)
    response = client.get(
        "/api/tests/sessions/active", params={"variant_ref": "001.txt"}
    )
    assert response.status_code == 200
    assert response.json()["session_id"] is None


def test_completed_session_not_active(client: TestClient) -> None:
    _login(client)
    body = _create_free_session(client)
    session_id = body["id"]
    client.post(f"/api/tests/sessions/{session_id}/complete")

    response = client.get(
        "/api/tests/sessions/active", params={"variant_ref": "001.txt"}
    )
    assert response.status_code == 200
    assert response.json()["session_id"] is None


def test_active_session_latest_by_created_at(client: TestClient) -> None:
    _login(client)
    first = _create_free_session(client)
    second = _create_free_session(client)

    response = client.get(
        "/api/tests/sessions/active", params={"variant_ref": "001.txt"}
    )
    assert response.status_code == 200
    assert response.json()["session_id"] == second["id"]
    assert response.json()["session_id"] != first["id"]


def test_active_session_by_homework_assignment_id(client: TestClient) -> None:
    _login(client)
    homework_id = _create_test_homework(client)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": homework_id},
    )
    assert session.status_code == 201, session.text
    session_id = session.json()["id"]

    active = client.get(
        "/api/tests/sessions/active",
        params={"homework_assignment_id": homework_id},
    )
    assert active.status_code == 200
    assert active.json()["session_id"] == session_id


def test_active_session_rejects_both_query_params(client: TestClient) -> None:
    _login(client)
    response = client.get(
        "/api/tests/sessions/active",
        params={
            "variant_ref": "001.txt",
            "homework_assignment_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 422


def test_active_session_rejects_neither_query_param(client: TestClient) -> None:
    _login(client)
    response = client.get("/api/tests/sessions/active")
    assert response.status_code == 422


def test_active_session_other_students_homework_forbidden(
    client: TestClient,
) -> None:
    _login(client)
    homework_id = _create_test_homework(client)

    _login(client, OTHER_EMAIL)
    response = client.get(
        "/api/tests/sessions/active",
        params={"homework_assignment_id": homework_id},
    )
    assert response.status_code == 403


def test_homework_detail_includes_active_test_session_id(
    client: TestClient,
) -> None:
    _login(client)
    homework_id = _create_test_homework(client)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": homework_id},
    )
    assert session.status_code == 201
    session_id = session.json()["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )

    detail = client.get(f"/api/homework/{homework_id}")
    assert detail.status_code == 200
    assert detail.json()["active_test_session_id"] == session_id


def test_teacher_homework_detail_has_null_active_session(
    client: TestClient,
) -> None:
    homework_id = _create_test_homework(client)
    _login(client)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": homework_id},
    )
    assert session.status_code == 201

    client.post("/api/auth/logout")
    assert (
        client.post(
            "/api/auth/login",
            json={"email": TEACHER_EMAIL, "password": PASS},
        ).status_code
        == 200
    )
    detail = client.get(f"/api/homework/{homework_id}")
    assert detail.status_code == 200
    assert detail.json()["active_test_session_id"] is None
