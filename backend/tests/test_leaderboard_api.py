"""Leaderboard and student stats API tests (Task 61)."""

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
from app.models import ExamTrack, StudentProfile, StudentStats, User, UserRole
from app.services.activity_service import resolve_public_display_name

TEACHER_EMAIL = "teacher-lb@example.com"
STUDENT_A_EMAIL = "student-a-lb@example.com"
STUDENT_B_EMAIL = "student-b-lb@example.com"
PASS = "lb-pass"


@pytest.fixture
def lb_env(tmp_path: Path):
    db_file = tmp_path / "leaderboard.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
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
                        id=teacher_id,
                        email=TEACHER_EMAIL,
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
                ]
            )
            await session.flush()
            session.add_all(
                [
                    StudentProfile(
                        user_id=student_a_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                        display_name="Химик-А",
                    ),
                    StudentProfile(
                        user_id=student_b_id,
                        teacher_id=teacher_id,
                        track=ExamTrack.EGE,
                        display_name=None,
                    ),
                ]
            )
            session.add_all(
                [
                    StudentStats(
                        student_id=student_a_id,
                        total_points=120,
                        week_points=40,
                        current_streak=2,
                        longest_streak=5,
                        tasks_solved=8,
                        total_minutes=90,
                    ),
                    StudentStats(
                        student_id=student_b_id,
                        total_points=200,
                        week_points=25,
                        current_streak=1,
                        longest_streak=3,
                        tasks_solved=12,
                        total_minutes=120,
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
            JWT_SECRET="test-jwt-secret-for-leaderboard-api-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield {
            "client": test_client,
            "student_a_id": student_a_id,
            "student_b_id": student_b_id,
        }

    asyncio.run(request_engine.dispose())


@pytest.fixture
def client(lb_env) -> TestClient:
    return lb_env["client"]


def _login(client: TestClient, email: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": PASS})
    assert response.status_code == 200, response.text


def test_my_stats_returns_current_student_metrics(client: TestClient, lb_env) -> None:
    _login(client, STUDENT_A_EMAIL)

    response = client.get("/api/students/me/stats")
    assert response.status_code == 200
    body = response.json()
    assert body["student_id"] == str(lb_env["student_a_id"])
    assert body["total_points"] == 120
    assert body["week_points"] == 40
    assert body["current_streak"] == 2
    assert body["longest_streak"] == 5
    assert body["tasks_solved"] == 8
    assert body["total_minutes"] == 90


def test_my_stats_requires_student_role(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL)

    response = client.get("/api/students/me/stats")
    assert response.status_code == 403
    assert response.json()["detail"] == "Student role required"


def test_my_stats_requires_auth(client: TestClient) -> None:
    response = client.get("/api/students/me/stats")
    assert response.status_code == 401


def test_leaderboard_week_orders_by_week_points(client: TestClient) -> None:
    _login(client, STUDENT_A_EMAIL)

    response = client.get("/api/leaderboard", params={"period": "week"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0] == {"rank": 1, "display_name": "Химик-А", "points": 40}
    assert body[1]["rank"] == 2
    assert body[1]["points"] == 25
    assert "@" not in body[0]["display_name"]
    assert "@" not in body[1]["display_name"]


def test_leaderboard_all_time_orders_by_total_points(client: TestClient, lb_env) -> None:
    _login(client, STUDENT_B_EMAIL)

    response = client.get("/api/leaderboard", params={"period": "all_time"})
    assert response.status_code == 200
    body = response.json()
    assert body[0]["points"] == 200
    assert body[0]["display_name"] == resolve_public_display_name(
        None,
        lb_env["student_b_id"],
    )
    assert body[1]["points"] == 120
    assert body[1]["display_name"] == "Химик-А"


def test_leaderboard_null_display_name_fallback(client: TestClient, lb_env) -> None:
    _login(client, STUDENT_A_EMAIL)

    response = client.get("/api/leaderboard", params={"period": "all_time"})
    assert response.status_code == 200
    names = {row["display_name"] for row in response.json()}
    assert resolve_public_display_name(None, lb_env["student_b_id"]) in names
    assert STUDENT_B_EMAIL not in response.text


def test_leaderboard_empty_returns_list_not_404(tmp_path: Path) -> None:
    db_file = tmp_path / "empty_lb.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
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
                    password_hash=hash_password(PASS),
                    role=UserRole.STUDENT,
                )
            )
            await session.flush()
            session.add(
                StudentProfile(
                    user_id=student_id,
                    teacher_id=student_id,
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
            JWT_SECRET="test-jwt-secret-for-empty-leaderboard-32b",
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        _login(test_client, "solo@example.com")
        response = test_client.get("/api/leaderboard")
        assert response.status_code == 200
        assert response.json() == []

    asyncio.run(request_engine.dispose())


def test_leaderboard_requires_student_role(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL)

    response = client.get("/api/leaderboard")
    assert response.status_code == 403


def test_leaderboard_limit_validation(client: TestClient) -> None:
    _login(client, STUDENT_A_EMAIL)

    ok = client.get("/api/leaderboard", params={"limit": 100})
    assert ok.status_code == 200

    bad = client.get("/api/leaderboard", params={"limit": 101})
    assert bad.status_code == 422


def test_leaderboard_default_limit_is_50(client: TestClient) -> None:
    _login(client, STUDENT_A_EMAIL)

    response = client.get("/api/leaderboard")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_leaderboard_student_response_never_leaks_email(
    client: TestClient,
) -> None:
    """Student-facing leaderboard must expose only rank, display_name, points."""
    _login(client, STUDENT_A_EMAIL)

    for period in ("week", "all_time"):
        response = client.get("/api/leaderboard", params={"period": period})
        assert response.status_code == 200
        body = response.json()
        assert isinstance(body, list)

        for row in body:
            assert set(row.keys()) == {"rank", "display_name", "points"}
            assert "@" not in row["display_name"]
            assert STUDENT_A_EMAIL not in response.text
            assert STUDENT_B_EMAIL not in response.text
            assert "email" not in response.text.lower()
