"""Homework template API tests (HT-2 / HT-3)."""

from __future__ import annotations

import asyncio
import sqlite3
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
OTHER_TEACHER_EMAIL = "other-teacher@example.com"
OTHER_TEACHER_PASS = "other-teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"
OGE_STUDENT_EMAIL = "oge-student@example.com"
OGE_STUDENT_PASS = "oge-student-pass"


def _create_track_dbs(tmp_path: Path) -> tuple[Path, Path]:
    """EGE has 003.txt only; OGE has 001.txt only — for track mismatch tests."""
    ege_db = tmp_path / "test_ege.db"
    oge_db = tmp_path / "test_oge.db"
    for path, filename in ((ege_db, "003.txt"), (oge_db, "001.txt")):
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE tests (
                filename TEXT, type INTEGER, question TEXT, options TEXT,
                correct_ans TEXT, hint TEXT, detailed_explanation TEXT,
                has_issue INTEGER DEFAULT 0
            )
            """
        )
        conn.execute("CREATE TABLE tests_bug (filename TEXT)")
        conn.execute(
            "CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)"
        )
        conn.execute(
            """
            INSERT INTO tests (filename, type, question, correct_ans, has_issue)
            VALUES (?, ?, ?, ?, ?)
            """,
            (filename, 1, f"Q-{filename}", "1", 0),
        )
        conn.commit()
        conn.close()
    return ege_db, oge_db


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "homework_templates.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db, oge_db = _create_track_dbs(tmp_path)

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    oge_student_id = uuid.uuid4()

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
                        id=oge_student_id,
                        email=OGE_STUDENT_EMAIL,
                        password_hash=hash_password(OGE_STUDENT_PASS),
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
                        user_id=oge_student_id,
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
    app = create_app(
        settings=Settings(
            CONTENT_EGE_DB_PATH=str(ege_db),
            CONTENT_OGE_DB_PATH=str(oge_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _template_payload(**overrides) -> dict:
    payload = {
        "title": "Шаблон: алканы",
        "description": "Прочитать тему",
        "items": [{"kind": "lecture", "topic": "Алканы"}],
    }
    payload.update(overrides)
    return payload


def _ege_student_id(client: TestClient) -> str:
    students = client.get("/api/students").json()
    return next(s["id"] for s in students if s["email"] == STUDENT_EMAIL)


def _oge_student_id(client: TestClient) -> str:
    students = client.get("/api/students").json()
    return next(s["id"] for s in students if s["email"] == OGE_STUDENT_EMAIL)


def test_teacher_creates_and_lists_templates(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    created = client.post("/api/homework/templates", json=_template_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Шаблон: алканы"
    assert body["description"] == "Прочитать тему"
    assert body["items"] == [{"kind": "lecture", "topic": "Алканы"}]
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body

    listed = client.get("/api/homework/templates")
    assert listed.status_code == 200
    templates = listed.json()
    assert len(templates) == 1
    assert templates[0]["id"] == body["id"]


def test_teacher_gets_patches_and_deletes_template(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    created = client.post("/api/homework/templates", json=_template_payload()).json()
    template_id = created["id"]

    detail = client.get(f"/api/homework/templates/{template_id}")
    assert detail.status_code == 200
    assert detail.json()["id"] == template_id

    patched = client.patch(
        f"/api/homework/templates/{template_id}",
        json={
            "title": "Обновлённый шаблон",
            "items": [{"kind": "lecture", "topic": "Алкены"}],
        },
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "Обновлённый шаблон"
    assert patched.json()["items"][0]["topic"] == "Алкены"

    deleted = client.delete(f"/api/homework/templates/{template_id}")
    assert deleted.status_code == 204

    assert client.get(f"/api/homework/templates/{template_id}").status_code == 404
    assert client.get("/api/homework/templates").json() == []


def test_template_items_must_be_1_to_10(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    empty = client.post(
        "/api/homework/templates",
        json=_template_payload(items=[]),
    )
    assert empty.status_code == 422

    too_many = client.post(
        "/api/homework/templates",
        json=_template_payload(
            items=[{"kind": "lecture", "topic": f"T{i}"} for i in range(11)]
        ),
    )
    assert too_many.status_code == 422


def test_student_cannot_access_templates(client: TestClient) -> None:
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert client.get("/api/homework/templates").status_code == 403
    assert (
        client.post("/api/homework/templates", json=_template_payload()).status_code
        == 403
    )


def test_other_teacher_cannot_access_template(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    created = client.post("/api/homework/templates", json=_template_payload()).json()
    template_id = created["id"]

    assert _login(client, OTHER_TEACHER_EMAIL, OTHER_TEACHER_PASS).status_code == 200
    assert client.get(f"/api/homework/templates/{template_id}").status_code == 404
    assert (
        client.patch(
            f"/api/homework/templates/{template_id}",
            json={"title": "Hijack"},
        ).status_code
        == 404
    )
    assert client.delete(f"/api/homework/templates/{template_id}").status_code == 404
    assert client.get("/api/homework/templates").json() == []


def test_assign_template_to_student_creates_assignment(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _ege_student_id(client)
    template = client.post("/api/homework/templates", json=_template_payload()).json()

    assigned = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"student_id": student_id},
    )
    assert assigned.status_code == 201
    body = assigned.json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["student_id"] == student_id
    assert body[0]["title"] == template["title"]
    assert body[0]["items"] == template["items"]
    assert body[0]["status"] == "assigned"
    assert body[0]["student_email"] == STUDENT_EMAIL
    assert body[0]["assign_batch_id"] is None
    assert body[0]["cancelled_at"] is None

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    listed = client.get("/api/homework").json()
    assert len(listed) == 1
    assert listed[0]["id"] == body[0]["id"]
    assert listed[0]["items"] == [{"kind": "lecture", "topic": "Алканы"}]


def test_patch_template_does_not_mutate_existing_assignment(
    client: TestClient,
) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _ege_student_id(client)
    template = client.post("/api/homework/templates", json=_template_payload()).json()
    assignment_id = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"student_id": student_id},
    ).json()[0]["id"]

    patched = client.patch(
        f"/api/homework/templates/{template['id']}",
        json={
            "title": "Другой шаблон",
            "items": [{"kind": "lecture", "topic": "Алкены"}],
        },
    )
    assert patched.status_code == 200
    assert patched.json()["items"][0]["topic"] == "Алкены"

    detail = client.get(f"/api/homework/{assignment_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Шаблон: алканы"
    assert detail.json()["items"] == [{"kind": "lecture", "topic": "Алканы"}]


def test_assign_ege_variant_to_oge_student_returns_422(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    oge_student_id = _oge_student_id(client)
    template = client.post(
        "/api/homework/templates",
        json=_template_payload(
            title="ЕГЭ вариант",
            items=[{"kind": "test_variant", "variant": "003.txt"}],
        ),
    ).json()

    response = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"student_id": oge_student_id},
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    detail_text = detail if isinstance(detail, str) else str(detail).lower()
    assert any(
        token in detail_text.lower()
        for token in ("track", "ege", "oge", "несовмест", "совмест")
    )


def test_assign_then_submit_creates_homework_submitted_notification(
    client: TestClient,
) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    student_id = _ege_student_id(client)
    template = client.post("/api/homework/templates", json=_template_payload()).json()
    assignment_id = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"student_id": student_id},
    ).json()[0]["id"]

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    assert (
        client.post(f"/api/homework/{assignment_id}/submit", json={}).status_code
        == 200
    )

    client.post("/api/auth/logout")
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    notifications = client.get("/api/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "homework_submitted"
    assert notifications[0]["payload"]["homework_id"] == assignment_id


def test_assign_template_to_group_fan_out(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    # Three EGE students: seeded + two created
    ege_id = _ege_student_id(client)
    created_ids = [ege_id]
    for login in ("ege-b", "ege-c"):
        created = client.post(
            "/api/students",
            json={"email": login, "password": "temp-pass", "track": "ege"},
        )
        assert created.status_code == 201
        created_ids.append(created.json()["id"])

    group = client.post("/api/teacher/groups", json={"name": "Fan"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": created_ids},
        ).status_code
        == 200
    )

    template = client.post("/api/homework/templates", json=_template_payload()).json()
    assigned = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    )
    assert assigned.status_code == 201
    body = assigned.json()
    assert len(body) == 3
    student_ids = {row["student_id"] for row in body}
    assert student_ids == set(created_ids)
    assert all(row["title"] == template["title"] for row in body)
    assert all(row["items"] == template["items"] for row in body)
    assert all(row["template_id"] == template["id"] for row in body)
    assert all(row["source_group_id"] == group["id"] for row in body)
    assert len({row["source_group_id"] for row in body}) == 1
    batch_ids = {row["assign_batch_id"] for row in body}
    assert len(batch_ids) == 1
    assert batch_ids.pop() is not None

    listed = client.get("/api/homework").json()
    assert len(listed) == 3


def test_assign_template_to_empty_group_returns_422(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    group = client.post("/api/teacher/groups", json={}).json()
    template = client.post("/api/homework/templates", json=_template_payload()).json()

    response = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    )
    assert response.status_code == 422
    assert "empty" in str(response.json()["detail"]).lower()


def test_assign_group_track_mismatch_creates_zero_assignments(
    client: TestClient,
) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    ege_id = _ege_student_id(client)
    oge_id = _oge_student_id(client)
    group = client.post("/api/teacher/groups", json={"name": "Mixed"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [ege_id, oge_id]},
        ).status_code
        == 200
    )
    template = client.post(
        "/api/homework/templates",
        json=_template_payload(
            title="ЕГЭ вариант",
            items=[{"kind": "test_variant", "variant": "003.txt"}],
        ),
    ).json()

    response = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    )
    assert response.status_code == 422
    assert client.get("/api/homework").json() == []


def test_assign_group_then_remove_member_cancels_homework(
    client: TestClient,
) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    ege_id = _ege_student_id(client)
    other = client.post(
        "/api/students",
        json={"email": "ege-peer", "password": "temp-pass", "track": "ege"},
    ).json()
    group = client.post("/api/teacher/groups", json={"name": "Revoke"}).json()
    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [ege_id, other["id"]]},
        ).status_code
        == 200
    )
    template = client.post("/api/homework/templates", json=_template_payload()).json()
    assigned = client.post(
        f"/api/homework/templates/{template['id']}/assign",
        json={"group_id": group["id"]},
    ).json()
    assert len(assigned) == 2
    removed_hw = next(row for row in assigned if row["student_id"] == ege_id)

    assert (
        client.put(
            f"/api/teacher/groups/{group['id']}/members",
            json={"student_ids": [other["id"]]},
        ).status_code
        == 200
    )

    detail = client.get(f"/api/homework/{removed_hw['id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "cancelled"

    kept = next(row for row in assigned if row["student_id"] == other["id"])
    assert client.get(f"/api/homework/{kept['id']}").json()["status"] == "assigned"

    # Student list excludes cancelled; direct GET is 404 for the student.
    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200
    listed = client.get("/api/homework").json()
    assert all(row["id"] != removed_hw["id"] for row in listed)
    assert client.get(f"/api/homework/{removed_hw['id']}").status_code == 404
