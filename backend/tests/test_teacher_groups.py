"""Teacher student groups API tests (HT-6)."""

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
from app.models import (
    ExamTrack,
    HomeworkAssignment,
    HomeworkStatus,
    StudentProfile,
    User,
    UserRole,
)

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
OTHER_TEACHER_EMAIL = "other-teacher@example.com"
OTHER_TEACHER_PASS = "other-teacher-pass"
STUDENT_A = "student-a"
STUDENT_B = "student-b"
STUDENT_PASS = "student-pass"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "teacher_groups.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
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
                        id=student_a_id,
                        email=STUDENT_A,
                        password_hash=hash_password(STUDENT_PASS),
                        role=UserRole.STUDENT,
                    ),
                    User(
                        id=student_b_id,
                        email=STUDENT_B,
                        password_hash=hash_password(STUDENT_PASS),
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
        test_client.teacher_id = teacher_id  # type: ignore[attr-defined]
        test_client.student_a_id = student_a_id  # type: ignore[attr-defined]
        test_client.student_b_id = student_b_id  # type: ignore[attr-defined]
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _student_id(client: TestClient, email: str) -> str:
    students = client.get("/api/students").json()
    return next(s["id"] for s in students if s["email"] == email)


async def _seed_group_assignment(
    db_url: str,
    *,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    group_id: uuid.UUID,
    status: HomeworkStatus = HomeworkStatus.ASSIGNED,
) -> uuid.UUID:
    engine = create_async_engine(db_url, poolclass=NullPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    assignment_id = uuid.uuid4()
    async with session_maker() as session:
        session.add(
            HomeworkAssignment(
                id=assignment_id,
                teacher_id=teacher_id,
                student_id=student_id,
                title="Group HW",
                items=[{"kind": "lecture", "topic": "Алканы"}],
                status=status,
                source_group_id=group_id,
            )
        )
        await session.commit()
    await engine.dispose()
    return assignment_id


def test_create_group_default_names(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    first = client.post("/api/teacher/groups", json={})
    assert first.status_code == 201
    assert first.json()["name"] == "Группа 1"
    assert first.json()["member_count"] == 0

    second = client.post("/api/teacher/groups", json={"name": ""})
    assert second.status_code == 201
    assert second.json()["name"] == "Группа 2"

    named = client.post("/api/teacher/groups", json={"name": "Олимпиадники"})
    assert named.status_code == 201
    assert named.json()["name"] == "Олимпиадники"

    third_default = client.post("/api/teacher/groups", json={})
    assert third_default.status_code == 201
    assert third_default.json()["name"] == "Группа 3"


def test_list_and_get_group_with_members(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={"name": "A"}).json()
    student_a = _student_id(client, STUDENT_A)

    put = client.put(
        f"/api/teacher/groups/{group['id']}/members",
        json={"student_ids": [student_a]},
    )
    assert put.status_code == 200
    assert put.json()["member_count"] == 1
    assert len(put.json()["members"]) == 1
    assert put.json()["members"][0]["id"] == student_a

    listed = client.get("/api/teacher/groups")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["member_count"] == 1

    detail = client.get(f"/api/teacher/groups/{group['id']}")
    assert detail.status_code == 200
    assert detail.json()["members"][0]["email"] == STUDENT_A


def test_rename_group(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={}).json()

    patched = client.patch(
        f"/api/teacher/groups/{group['id']}",
        json={"name": "Переименованная"},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "Переименованная"


def test_student_cannot_belong_to_two_groups(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    g1 = client.post("/api/teacher/groups", json={"name": "G1"}).json()
    g2 = client.post("/api/teacher/groups", json={"name": "G2"}).json()
    student_a = _student_id(client, STUDENT_A)

    assert (
        client.put(
            f"/api/teacher/groups/{g1['id']}/members",
            json={"student_ids": [student_a]},
        ).status_code
        == 200
    )

    conflict = client.put(
        f"/api/teacher/groups/{g2['id']}/members",
        json={"student_ids": [student_a]},
    )
    assert conflict.status_code == 422


def test_remove_member_cancels_unsubmitted_group_homework(
    client: TestClient,
) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={"name": "G"}).json()
    student_a = _student_id(client, STUDENT_A)
    student_b = _student_id(client, STUDENT_B)

    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [student_a, student_b]},
        ).status_code
        == 200
    )

    assignment_id = asyncio.run(
        _seed_group_assignment(
            client.db_url,  # type: ignore[attr-defined]
            teacher_id=client.teacher_id,  # type: ignore[attr-defined]
            student_id=uuid.UUID(student_a),
            group_id=uuid.UUID(group["id"]),
        )
    )
    submitted_id = asyncio.run(
        _seed_group_assignment(
            client.db_url,  # type: ignore[attr-defined]
            teacher_id=client.teacher_id,  # type: ignore[attr-defined]
            student_id=uuid.UUID(student_b),
            group_id=uuid.UUID(group["id"]),
            status=HomeworkStatus.SUBMITTED,
        )
    )

    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [student_b]},
        ).status_code
        == 200
    )

    detail_a = client.get(f"/api/homework/{assignment_id}")
    assert detail_a.status_code == 200
    assert detail_a.json()["status"] == "cancelled"
    assert detail_a.json()["cancelled_at"] is not None

    detail_b = client.get(f"/api/homework/{submitted_id}")
    assert detail_b.status_code == 200
    assert detail_b.json()["status"] == "submitted"


def test_delete_group_revokes_and_removes(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={"name": "Del"}).json()
    student_a = _student_id(client, STUDENT_A)
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [student_a]},
        ).status_code
        == 200
    )
    assignment_id = asyncio.run(
        _seed_group_assignment(
            client.db_url,  # type: ignore[attr-defined]
            teacher_id=client.teacher_id,  # type: ignore[attr-defined]
            student_id=uuid.UUID(student_a),
            group_id=uuid.UUID(group["id"]),
            status=HomeworkStatus.IN_PROGRESS,
        )
    )

    deleted = client.delete(f"/api/teacher/groups/{group['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/teacher/groups/{group['id']}").status_code == 404
    assert client.get("/api/teacher/groups").json() == []

    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "cancelled"
    assert detail.json()["cancelled_at"] is not None


def test_other_teacher_cannot_access_group(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={"name": "Private"}).json()

    assert _login(client, OTHER_TEACHER_EMAIL, OTHER_TEACHER_PASS).status_code == 200
    assert client.get(f"/api/teacher/groups/{group['id']}").status_code == 404
    assert (
        client.patch(
            f"/api/teacher/groups/{group['id']}",
            json={"name": "Hijack"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/teacher/groups/{group['id']}").status_code == 404
    assert client.get("/api/teacher/groups").json() == []
