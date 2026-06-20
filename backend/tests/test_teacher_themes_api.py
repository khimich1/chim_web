"""Teacher themes and custom tasks API tests (SPEC §1.9, Task 68)."""

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
OTHER_TEACHER_EMAIL = "other-teacher@example.com"
OTHER_TEACHER_PASS = "other-teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"

IMAGE_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
IMAGE_URL = f"/api/uploads/images/{IMAGE_ID}"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    db_file = tmp_path / "teacher_themes.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    other_teacher_id = uuid.uuid4()
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
    app = create_app(settings=Settings())
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _create_theme(client: TestClient, **overrides) -> dict:
    payload = {
        "title": "ОВР",
        "description": "Окислительно-восстановительные реакции",
        "is_published": False,
        "sort_order": 1,
        **overrides,
    }
    response = client.post("/api/teacher/themes", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_list_themes(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200

    created = _create_theme(client, is_published=True)
    assert created["title"] == "ОВР"
    assert created["is_published"] is True
    assert created["sort_order"] == 1

    listed = client.get("/api/teacher/themes")
    assert listed.status_code == 200
    themes = listed.json()
    assert len(themes) == 1
    assert themes[0]["id"] == created["id"]


def test_create_auto_task(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    response = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "title": "Числовой ответ",
            "sort_order": 0,
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "2+2=?"}],
            "correct_value": "4",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["grading_mode"] == "auto"
    assert body["correct_value"] == "4"
    assert body["theme_id"] == theme["id"]


def test_create_self_check_task_with_image_block(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    response = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "title": "Письменный ответ",
            "grading_mode": "self_check",
            "question_blocks": [
                {"type": "text", "content": "Опишите ОВР"},
                {"type": "image", "url": IMAGE_URL},
            ],
            "reference_answer": [{"type": "text", "content": "Эталонный ответ"}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["grading_mode"] == "self_check"
    assert body["reference_answer"][0]["content"] == "Эталонный ответ"
    assert body["question_blocks"][1]["url"] == IMAGE_URL


def test_update_theme_and_task(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    task = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "H2O?"}],
            "correct_value": "вода",
        },
    ).json()

    theme_patch = client.patch(
        f"/api/teacher/themes/{theme['id']}",
        json={"title": "Новое название", "is_published": True},
    )
    assert theme_patch.status_code == 200
    assert theme_patch.json()["title"] == "Новое название"
    assert theme_patch.json()["is_published"] is True

    task_patch = client.patch(
        f"/api/teacher/tasks/{task['id']}",
        json={"correct_value": "H2O"},
    )
    assert task_patch.status_code == 200
    assert task_patch.json()["correct_value"] == "H2O"


def test_delete_theme_and_task(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)
    task = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "1+1?"}],
            "correct_value": "2",
        },
    ).json()

    delete_task = client.delete(f"/api/teacher/tasks/{task['id']}")
    assert delete_task.status_code == 204
    assert client.get(f"/api/teacher/tasks/{task['id']}").status_code == 404

    delete_theme = client.delete(f"/api/teacher/themes/{theme['id']}")
    assert delete_theme.status_code == 204
    assert client.get(f"/api/teacher/themes/{theme['id']}").status_code == 404


def test_student_cannot_access_teacher_endpoints(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    client.post("/api/auth/logout")
    assert _login(client, STUDENT_EMAIL, STUDENT_PASS).status_code == 200

    assert client.get("/api/teacher/themes").status_code == 403
    assert client.post("/api/teacher/themes", json={"title": "X"}).status_code == 403
    assert client.get(f"/api/teacher/themes/{theme['id']}").status_code == 403


def test_teacher_cannot_access_other_teacher_theme(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)
    task = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "Q"}],
            "correct_value": "A",
        },
    ).json()

    client.post("/api/auth/logout")
    assert _login(client, OTHER_TEACHER_EMAIL, OTHER_TEACHER_PASS).status_code == 200

    assert client.get(f"/api/teacher/themes/{theme['id']}").status_code == 404
    assert client.patch(
        f"/api/teacher/themes/{theme['id']}",
        json={"title": "Hack"},
    ).status_code == 404
    assert client.delete(f"/api/teacher/themes/{theme['id']}").status_code == 404
    assert (
        client.get(f"/api/teacher/themes/{theme['id']}/tasks").status_code == 404
    )
    assert client.get(f"/api/teacher/tasks/{task['id']}").status_code == 404


def test_validation_errors(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    auto_missing = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "Q"}],
        },
    )
    assert auto_missing.status_code == 422

    self_check_missing = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "self_check",
            "question_blocks": [{"type": "text", "content": "Q"}],
        },
    )
    assert self_check_missing.status_code == 422

    bad_image_url = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "self_check",
            "question_blocks": [{"type": "image", "url": "/static/evil.png"}],
            "reference_answer": [{"type": "text", "content": "A"}],
        },
    )
    assert bad_image_url.status_code == 422

    empty_question = client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [],
            "correct_value": "1",
        },
    )
    assert empty_question.status_code == 422


def test_list_tasks_in_theme(client: TestClient) -> None:
    assert _login(client, TEACHER_EMAIL, TEACHER_PASS).status_code == 200
    theme = _create_theme(client)

    client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "A"}],
            "correct_value": "1",
            "sort_order": 0,
        },
    )
    client.post(
        f"/api/teacher/themes/{theme['id']}/tasks",
        json={
            "grading_mode": "auto",
            "question_blocks": [{"type": "text", "content": "B"}],
            "correct_value": "2",
            "sort_order": 1,
        },
    )

    listed = client.get(f"/api/teacher/themes/{theme['id']}/tasks")
    assert listed.status_code == 200
    tasks = listed.json()
    assert len(tasks) == 2
    assert tasks[0]["question_blocks"][0]["content"] == "A"
    assert tasks[1]["question_blocks"][0]["content"] == "B"
