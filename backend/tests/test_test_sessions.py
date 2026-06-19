"""TestSession API: create, get, check step, complete, RBAC."""

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
    db_file = tmp_path / "sessions_app.db"
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
            JWT_SECRET="test-jwt-secret-for-sessions-32-bytes",
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


def _create_session(client: TestClient, **body) -> dict:
    payload = {"variant_ref": "001.txt", **body}
    response = client.post("/api/tests/sessions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_session_builds_steps_from_variant(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)

    assert body["track"] == "ege"
    assert body["variant_ref"] == "001.txt"
    assert body["status"] == "in_progress"
    assert body["total_steps"] == 2
    assert "created_at" in body
    assert body["created_at"] is not None
    positions = [s["position"] for s in body["steps"]]
    assert positions == [0, 1]
    # No correct answer leaks into the step view.
    assert "correct_ans" not in body["steps"][0]


def test_create_partial_session_filters_types(client: TestClient) -> None:
    _login(client)
    body = _create_session(client, types=[2])

    assert body["total_steps"] == 1
    assert body["steps"][0]["type"] == 2


def test_create_session_by_task_type_across_variants(client: TestClient) -> None:
    _login(client)
    response = client.post("/api/tests/sessions", json={"types": [1]})
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["variant_ref"] is None
    assert body["total_steps"] == 1
    assert body["steps"][0]["type"] == 1


def test_question_has_image_url_substituted(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)

    step_with_image = next(s for s in body["steps"] if s["type"] == 2)
    assert "/api/tests/images/" in step_with_image["question"]
    assert "[рисунок0001]" not in step_with_image["question"]


def test_check_step_correct_answer(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert data["status"] == "checked"


def test_check_step_wrong_answer_then_recheck(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    wrong = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "9"},
    )
    assert wrong.json()["is_correct"] is False

    right = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert right.json()["is_correct"] is True

    state = client.get(f"/api/tests/sessions/{session_id}").json()
    assert "created_at" in state
    assert state["created_at"] is not None
    step0 = state["steps"][0]
    assert step0["answer"] == "1"
    assert step0["is_correct"] is True
    assert step0["status"] == "checked"


def test_check_step_does_not_return_explanation(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_correct"] is True
    assert "detailed_explanation" not in data
    assert "hint" not in data


def test_hint_endpoint_removed(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    assert body["steps"][0]["hint_used"] is False
    assert "hint" not in body["steps"][0]
    assert "detailed_explanation" not in body["steps"][0]

    response = client.get(f"/api/tests/sessions/{session_id}/steps/0/hint")
    assert response.status_code == 404


def test_session_read_omits_hint_and_explanation(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )

    state = client.get(f"/api/tests/sessions/{session_id}").json()
    step0 = state["steps"][0]
    assert step0["status"] == "checked"
    assert "hint" not in step0
    assert "detailed_explanation" not in step0


def test_complete_session_computes_score(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check",
        json={"answer": "wrong"},
    )

    response = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert response.status_code == 200
    summary = response.json()
    assert summary["status"] == "completed"
    assert summary["score"] == 1
    assert summary["max_score"] == 2
    assert len(summary["steps"]) == 2


def test_check_after_complete_returns_409(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]
    client.post(f"/api/tests/sessions/{session_id}/complete")

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/0/check",
        json={"answer": "1"},
    )
    assert response.status_code == 409


def test_other_student_cannot_access_session(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    # Switch to a different student.
    _login(client, OTHER_EMAIL)
    assert client.get(f"/api/tests/sessions/{session_id}").status_code == 403


def test_unknown_step_returns_404(client: TestClient) -> None:
    _login(client)
    body = _create_session(client)
    session_id = body["id"]

    response = client.post(
        f"/api/tests/sessions/{session_id}/steps/99/check",
        json={"answer": "1"},
    )
    assert response.status_code == 404


def test_teacher_cannot_create_session(client: TestClient) -> None:
    _login(client, TEACHER_EMAIL)
    response = client.post(
        "/api/tests/sessions", json={"variant_ref": "001.txt"}
    )
    assert response.status_code == 403
