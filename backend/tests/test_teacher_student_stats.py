"""Teacher student stats API tests (Task 62)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
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
from app.models import ExamTrack, StudentProfile, StudentStats, User, UserRole

TEACHER_A_EMAIL = "teacher-a-stats@example.com"
TEACHER_B_EMAIL = "teacher-b-stats@example.com"
STUDENT_A_EMAIL = "student-a-stats@example.com"
STUDENT_B_EMAIL = "student-b-stats@example.com"
STUDENT_OTHER_EMAIL = "student-other-stats@example.com"
PASS = "stats-pass"


@pytest.fixture
def stats_env(tmp_path: Path):
    db_file = tmp_path / "teacher_student_stats.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_a_id = uuid.uuid4()
    teacher_b_id = uuid.uuid4()
    student_a_id = uuid.uuid4()
    student_b_id = uuid.uuid4()
    student_other_id = uuid.uuid4()

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
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=teacher_b_id,
                        email=TEACHER_B_EMAIL,
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_a_id,
                        email=STUDENT_A_EMAIL,
                        password_hash=hash_password(PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=student_b_id,
                        email=STUDENT_B_EMAIL,
                        password_hash=hash_password(PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=student_other_id,
                        email=STUDENT_OTHER_EMAIL,
                        password_hash=hash_password(PASS),
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
                        display_name="Ученик А",
                    ),
                    StudentProfile(
                        user_id=student_b_id,
                        teacher_id=teacher_a_id,
                        track=ExamTrack.OGE,
                        display_name=None,
                    ),
                    StudentProfile(
                        user_id=student_other_id,
                        teacher_id=teacher_b_id,
                        track=ExamTrack.EGE,
                        display_name="Чужой ученик",
                    ),
                ]
            )
            session.add_all(
                [
                    StudentStats(
                        student_id=student_a_id,
                        total_points=150,
                        week_points=30,
                        current_streak=3,
                        longest_streak=7,
                        tasks_solved=10,
                        total_minutes=75,
                        last_active_date=date(2026, 6, 18),
                    ),
                    StudentStats(
                        student_id=student_b_id,
                        total_points=80,
                        week_points=15,
                        current_streak=1,
                        longest_streak=2,
                        tasks_solved=4,
                        total_minutes=40,
                        last_active_date=date(2026, 6, 17),
                    ),
                    StudentStats(
                        student_id=student_other_id,
                        total_points=999,
                        week_points=99,
                        current_streak=10,
                        tasks_solved=50,
                        total_minutes=300,
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
            JWT_SECRET="test-jwt-secret-for-teacher-stats-api-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "student_a_id": student_a_id,
            "student_b_id": student_b_id,
            "student_other_id": student_other_id,
        }

    asyncio.run(request_engine.dispose())


@pytest.fixture
def client(stats_env) -> TestClient:
    return stats_env["client"]


def _login(client: TestClient, email: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": PASS})
    assert response.status_code == 200, response.text


def test_teacher_sees_own_students_stats(client: TestClient, stats_env) -> None:
    _login(client, TEACHER_A_EMAIL)

    response = client.get("/api/teacher/students/stats")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2

    by_id = {row["id"]: row for row in body}
    student_a = by_id[str(stats_env["student_a_id"])]
    student_b = by_id[str(stats_env["student_b_id"])]

    assert student_a == {
        "id": str(stats_env["student_a_id"]),
        "email": STUDENT_A_EMAIL,
        "display_name": "Ученик А",
        "total_points": 150,
        "week_points": 30,
        "streak": 3,
        "tasks_solved": 10,
        "total_minutes": 75,
        "last_active_date": "2026-06-18",
    }
    assert student_b["email"] == STUDENT_B_EMAIL
    assert student_b["display_name"] is None
    assert student_b["total_points"] == 80
    assert student_b["week_points"] == 15
    assert student_b["streak"] == 1
    assert student_b["tasks_solved"] == 4
    assert student_b["total_minutes"] == 40
    assert student_b["last_active_date"] == "2026-06-17"


def test_teacher_does_not_see_other_teachers_students(
    client: TestClient,
    stats_env,
) -> None:
    _login(client, TEACHER_B_EMAIL)

    response = client.get("/api/teacher/students/stats")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == str(stats_env["student_other_id"])
    assert body[0]["email"] == STUDENT_OTHER_EMAIL
    assert body[0]["total_points"] == 999
    assert str(stats_env["student_a_id"]) not in response.text
    assert str(stats_env["student_b_id"]) not in response.text


def test_student_gets_403(client: TestClient) -> None:
    _login(client, STUDENT_A_EMAIL)

    response = client.get("/api/teacher/students/stats")
    assert response.status_code == 403
    assert response.json()["detail"] == "Teacher role required"


def test_requires_auth(client: TestClient) -> None:
    response = client.get("/api/teacher/students/stats")
    assert response.status_code == 401


def test_teacher_sees_student_without_stats_row(tmp_path: Path) -> None:
    db_file = tmp_path / "no_stats_row.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
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
                        email="solo-teacher@example.com",
                        password_hash=hash_password(PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email="new-student@example.com",
                        password_hash=hash_password(PASS),
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
                    display_name="Новичок",
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
            JWT_SECRET="test-jwt-secret-for-teacher-no-stats-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        _login(test_client, "solo-teacher@example.com")
        response = test_client.get("/api/teacher/students/stats")
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 1
        assert body[0] == {
            "id": str(student_id),
            "email": "new-student@example.com",
            "display_name": "Новичок",
            "total_points": 0,
            "week_points": 0,
            "streak": 0,
            "tasks_solved": 0,
            "total_minutes": 0,
            "last_active_date": None,
        }

    asyncio.run(request_engine.dispose())


def test_empty_list_when_teacher_has_no_students(tmp_path: Path) -> None:
    db_file = tmp_path / "lonely_teacher.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    teacher_id = uuid.uuid4()

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            session.add(
                User(
                    id=teacher_id,
                    email="lonely@example.com",
                    password_hash=hash_password(PASS),
                    role=UserRole.TEACHER,
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
            JWT_SECRET="test-jwt-secret-for-lonely-teacher-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        _login(test_client, "lonely@example.com")
        response = test_client.get("/api/teacher/students/stats")
        assert response.status_code == 200
        assert response.json() == []

    asyncio.run(request_engine.dispose())
