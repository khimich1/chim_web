"""Cross-user RBAC tests for homework and test sessions."""

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

TEACHER_A_EMAIL = "teacher-a@example.com"
TEACHER_B_EMAIL = "teacher-b@example.com"
STUDENT_A_EMAIL = "student-a@example.com"
STUDENT_B_EMAIL = "student-b@example.com"
PASSWORD = "test-password"
JWT_SECRET = "test-jwt-secret-for-rbac-suite-32-bytes"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "rbac.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET=JWT_SECRET,
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text


def _logout(client: TestClient) -> None:
    response = client.post("/api/auth/logout")
    assert response.status_code == 204, response.text


def _current_teacher_student_id(client: TestClient) -> str:
    response = client.get("/api/students")
    assert response.status_code == 200, response.text
    return response.json()[0]["id"]


def _create_homework(client: TestClient, item: dict[str, object]) -> str:
    student_id = _current_teacher_student_id(client)
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "RBAC homework",
            "items": [item],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_test_session(client: TestClient, assignment_id: str) -> str:
    response = client.post(
        "/api/tests/sessions",
        json={
            "variant_ref": "001.txt",
            "homework_assignment_id": assignment_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _complete_first_step(client: TestClient, session_id: str) -> None:
    check = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert check.status_code == 200, check.text
    complete = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert complete.status_code == 200, complete.text


def test_teacher_cannot_read_other_teachers_homework(client: TestClient) -> None:
    _login(client, TEACHER_B_EMAIL)
    assignment_id = _create_homework(
        client,
        {"kind": "lecture", "topic": "Алканы"},
    )

    _logout(client)
    _login(client, TEACHER_A_EMAIL)

    assert client.get(f"/api/homework/{assignment_id}").status_code == 403
    listed_ids = {item["id"] for item in client.get("/api/homework").json()}
    assert assignment_id not in listed_ids


def test_student_cannot_start_session_for_other_students_homework(
    client: TestClient,
) -> None:
    _login(client, TEACHER_B_EMAIL)
    assignment_id = _create_homework(
        client,
        {"kind": "test_variant", "variant": "001.txt"},
    )

    _logout(client)
    _login(client, STUDENT_A_EMAIL)

    response = client.post(
        "/api/tests/sessions",
        json={
            "variant_ref": "001.txt",
            "homework_assignment_id": assignment_id,
        },
    )
    assert response.status_code == 403


def test_student_cannot_submit_session_for_different_homework(
    client: TestClient,
) -> None:
    _login(client, TEACHER_A_EMAIL)
    first_assignment_id = _create_homework(
        client,
        {"kind": "test_variant", "variant": "001.txt"},
    )
    second_assignment_id = _create_homework(
        client,
        {"kind": "test_variant", "variant": "001.txt"},
    )

    _logout(client)
    _login(client, STUDENT_A_EMAIL)
    session_id = _create_test_session(client, first_assignment_id)
    _complete_first_step(client, session_id)

    submit = client.post(
        f"/api/homework/{second_assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 422
    assert submit.json()["detail"] == "Test session is not linked to this homework"
