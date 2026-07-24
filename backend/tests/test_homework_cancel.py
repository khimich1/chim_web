"""Homework cancel / restore API (single + wave, TTL)."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, HomeworkAssignment, StudentProfile, User, UserRole
from app.models.enums import HomeworkStatus

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
OTHER_TEACHER_EMAIL = "other-teacher@example.com"
OTHER_TEACHER_PASS = "other-teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"
STUDENT_B_EMAIL = "student-b@example.com"
STUDENT_B_PASS = "student-b-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "homework_cancel.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
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
                        password_hash=hash_password(TEACHER_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=other_teacher_id,
                        email=OTHER_TEACHER_EMAIL,
                        password_hash=hash_password(OTHER_TEACHER_PASS),
                        role=UserRole.TEACHER,
                    ),
                    User(
                        id=student_id,
                        email=STUDENT_EMAIL,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=student_b_id,
                        email=STUDENT_B_EMAIL,
                        password_hash=hash_password(STUDENT_B_PASS),
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
                        user_id=student_b_id,
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
    app = create_app(settings=Settings())
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        test_client.db_url = db_url  # type: ignore[attr-defined]
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _student_id(client: TestClient, email: str) -> str:
    students = client.get("/api/students").json()
    return next(s["id"] for s in students if s["email"] == email)


def _assign_lecture(client: TestClient, student_id: str) -> dict:
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Отзыв тест",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    )
    assert response.status_code == 201
    return response.json()


async def _backdate_cancelled_at(
    db_url: str,
    assignment_ids: list[uuid.UUID],
    *,
    seconds_ago: int = 31,
) -> None:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    past = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    async with session_maker() as session:
        rows = await session.scalars(
            select(HomeworkAssignment).where(HomeworkAssignment.id.in_(assignment_ids))
        )
        for row in rows:
            row.cancelled_at = past
        await session.commit()
    await engine.dispose()


def test_cancel_single_active_assignment(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _student_id(client, STUDENT_EMAIL)
    assignment = _assign_lecture(client, student_id)

    cancelled = client.post(f"/api/homework/{assignment['id']}/cancel", json={})
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["cancelled_ids"] == [assignment["id"]]
    assert body["skipped_submitted_count"] == 0
    assert body["cancelled_at"] is not None

    detail = client.get(f"/api/homework/{assignment['id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "cancelled"
    assert detail.json()["cancelled_at"] is not None

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert client.get("/api/homework").json() == []


def test_cancel_submitted_skips_without_status_change(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _student_id(client, STUDENT_EMAIL)
    assignment = _assign_lecture(client, student_id)

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert (
        client.post(f"/api/homework/{assignment['id']}/submit", json={}).status_code
        == 200
    )

    client.post("/api/auth/logout")
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    cancelled = client.post(f"/api/homework/{assignment['id']}/cancel", json={})
    assert cancelled.status_code == 200
    body = cancelled.json()
    assert body["cancelled_ids"] == []
    assert body["skipped_submitted_count"] == 1

    detail = client.get(f"/api/homework/{assignment['id']}")
    assert detail.json()["status"] == "submitted"


def test_restore_within_ttl_and_after_ttl(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _student_id(client, STUDENT_EMAIL)
    assignment = _assign_lecture(client, student_id)
    assignment_id = assignment["id"]

    assert (
        client.post(f"/api/homework/{assignment_id}/cancel", json={}).status_code == 200
    )

    restored = client.post(f"/api/homework/{assignment_id}/restore", json={})
    assert restored.status_code == 200
    assert restored.json()["restored_ids"] == [assignment_id]
    assert client.get(f"/api/homework/{assignment_id}").json()["status"] == "assigned"
    assert client.get(f"/api/homework/{assignment_id}").json()["cancelled_at"] is None

    assert (
        client.post(f"/api/homework/{assignment_id}/cancel", json={}).status_code == 200
    )
    asyncio.run(
        _backdate_cancelled_at(
            client.db_url,  # type: ignore[attr-defined]
            [uuid.UUID(assignment_id)],
            seconds_ago=31,
        )
    )
    expired = client.post(f"/api/homework/{assignment_id}/restore", json={})
    assert expired.status_code == 409


def test_other_teacher_cannot_cancel(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _student_id(client, STUDENT_EMAIL)
    assignment = _assign_lecture(client, student_id)

    client.post("/api/auth/logout")
    assert _login(client, OTHER_TEACHER_EMAIL, OTHER_TEACHER_PASS).status_code == 200
    response = client.post(f"/api/homework/{assignment['id']}/cancel", json={})
    assert response.status_code in (403, 404)


def test_wave_cancel_and_partial_submitted(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    a_id = _student_id(client, STUDENT_EMAIL)
    b_id = _student_id(client, STUDENT_B_EMAIL)

    group = client.post("/api/teacher/groups", json={"name": "Wave"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [a_id, b_id]},
        ).status_code
        == 200
    )
    template = client.post(
        "/api/homework/templates",
        json={
            "title": "Волна",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    ).json()
    assigned = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    )
    assert assigned.status_code == 201
    rows = assigned.json()
    assert len(rows) == 2
    batch_id = rows[0]["assign_batch_id"]
    assert batch_id is not None
    assert rows[1]["assign_batch_id"] == batch_id

    by_student = {row["student_id"]: row for row in rows}
    # Submit student B's copy
    client.post("/api/auth/logout")
    assert _login(client, STUDENT_B_EMAIL, STUDENT_B_PASS).status_code == 200
    assert (
        client.post(
            f"/api/homework/{by_student[b_id]['id']}/submit",
            json={},
        ).status_code
        == 200
    )

    client.post("/api/auth/logout")
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    wave = client.post(
        f"/api/homework/{by_student[a_id]['id']}/cancel",
        json={"scope": "wave"},
    )
    assert wave.status_code == 200
    body = wave.json()
    assert body["cancelled_ids"] == [by_student[a_id]["id"]]
    assert body["skipped_submitted_count"] == 1

    assert (
        client.get(f"/api/homework/{by_student[a_id]['id']}").json()["status"]
        == "cancelled"
    )
    assert (
        client.get(f"/api/homework/{by_student[b_id]['id']}").json()["status"]
        == "submitted"
    )

    # Full wave cancel (2 active) in a fresh wave
    template2 = client.post(
        "/api/homework/templates",
        json={
            "title": "Волна 2",
            "items": [{"kind": "lecture", "topic": "Алкены"}],
        },
    ).json()
    wave2 = client.post(
        f"/api/homework/templates/{template2['id']}/assign",
        json={"group_id": group["id"]},
    ).json()
    anchor = wave2[0]["id"]
    full = client.post(f"/api/homework/{anchor}/cancel", json={"scope": "wave"})
    assert full.status_code == 200
    assert len(full.json()["cancelled_ids"]) == 2
    assert full.json()["skipped_submitted_count"] == 0


def test_wave_restore_within_ttl(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    a_id = _student_id(client, STUDENT_EMAIL)
    b_id = _student_id(client, STUDENT_B_EMAIL)
    group = client.post("/api/teacher/groups", json={"name": "Undo"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [a_id, b_id]},
        ).status_code
        == 200
    )
    template = client.post(
        "/api/homework/templates",
        json={
            "title": "Undo wave",
            "items": [{"kind": "lecture", "topic": "Алканы"}],
        },
    ).json()
    rows = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    ).json()
    anchor = rows[0]["id"]
    assert (
        client.post(f"/api/homework/{anchor}/cancel", json={"scope": "wave"}).status_code
        == 200
    )

    restored = client.post(
        f"/api/homework/{anchor}/restore",
        json={"scope": "wave"},
    )
    assert restored.status_code == 200
    assert set(restored.json()["restored_ids"]) == {row["id"] for row in rows}
    for row in rows:
        detail = client.get(f"/api/homework/{row['id']}").json()
        assert detail["status"] == "assigned"
        assert detail["cancelled_at"] is None


def test_wave_on_individual_returns_422(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _student_id(client, STUDENT_EMAIL)
    assignment = _assign_lecture(client, student_id)
    response = client.post(
        f"/api/homework/{assignment['id']}/cancel",
        json={"scope": "wave"},
    )
    assert response.status_code == 422
