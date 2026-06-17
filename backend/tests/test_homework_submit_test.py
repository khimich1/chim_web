"""Homework submission tests for test_variant and test_partial assignments."""

from __future__ import annotations

import asyncio
import sqlite3
import uuid
from collections.abc import Callable, Iterator
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

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"


def _create_multi_variant_db(path: Path) -> None:
    """EGE content DB with two distinct variants for multi-item homework tests."""
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
    conn.execute("CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)")
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("003.txt", 10, "Q003-10", "10", 0),
            ("003.txt", 11, "Q003-11", "11", 0),
            ("007.txt", 15, "Q007-15", "15", 0),
        ],
    )
    conn.commit()
    conn.close()


def _create_ege_by_type_db(path: Path) -> None:
    """EGE DB: type 10 appears in three variants (for test_by_type)."""
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
    conn.execute("CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)")
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("003.txt", 10, "Q003-10", "10", 0),
            ("007.txt", 10, "Q007-10", "10", 0),
            ("008.txt", 10, "Q008-10", "10", 0),
        ],
    )
    conn.commit()
    conn.close()


def _create_oversized_ege_db(path: Path) -> None:
    """EGE DB where test_by_type expands beyond the 60-question cap."""
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
    conn.execute("CREATE TABLE images (filename TEXT PRIMARY KEY, data BLOB NOT NULL)")
    rows = [
        (variant, type_num, f"Q{variant}-{type_num}", str(type_num), 0)
        for variant in ("001.txt", "002.txt", "003.txt")
        for type_num in range(1, 22)
    ]
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()


def _build_client(
    tmp_path: Path,
    build_ege: Callable[[Path], None],
) -> Iterator[TestClient]:
    db_file = tmp_path / "homework_submit_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    build_ege(ege_db)

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
    app = create_app(
        settings=Settings(
            DATABASE_URL=db_url,
            JWT_SECRET="test-jwt-secret-for-homework-submit",
            CONTENT_EGE_DB_PATH=str(ege_db),
        )
    )
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    yield from _build_client(
        tmp_path, lambda path: _create_tests_db(path, with_bug=True)
    )


@pytest.fixture
def multi_client(tmp_path: Path) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, _create_multi_variant_db)


@pytest.fixture
def by_type_client(tmp_path: Path) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, _create_ege_by_type_db)


@pytest.fixture
def oversized_client(tmp_path: Path) -> Iterator[TestClient]:
    yield from _build_client(tmp_path, _create_oversized_ege_db)


def _login(client: TestClient, email: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text


def _create_test_homework(client: TestClient, item: dict[str, object]) -> str:
    return _create_homework(client, [item])


def _create_homework(client: TestClient, items: list[dict[str, object]]) -> str:
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_id = client.get("/api/students").json()[0]["id"]
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Тестовое ДЗ",
            "items": items,
        },
    )
    assert response.status_code == 201, response.text
    client.post("/api/auth/logout")
    return response.json()["id"]


def _create_homework_session(client: TestClient, assignment_id: str) -> dict:
    response = client.post(
        "/api/tests/sessions",
        json={
            "variant_ref": "001.txt",
            "homework_assignment_id": assignment_id,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_student_submits_test_variant_homework_after_completed_session(
    client: TestClient,
) -> None:
    assignment_id = _create_test_homework(
        client,
        {"kind": "test_variant", "variant": "001.txt"},
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = _create_homework_session(client, assignment_id)
    session_id = session["id"]
    assert session["homework_assignment_id"] == assignment_id
    assert session["total_steps"] == 2

    client.post(f"/api/tests/sessions/{session_id}/steps/0/check", json={"answer": "1"})
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check",
        json={"answer": "wrong"},
    )
    complete = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert complete.status_code == 200, complete.text

    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["status"] == "submitted"
    assert body["submission"]["test_session_id"] == session_id
    assert body["submission"]["score"] == 1
    assert body["submission"]["max_score"] == 2

    client.post("/api/auth/logout")
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    teacher_detail = client.get(f"/api/homework/{assignment_id}").json()
    assert teacher_detail["submission"]["score"] == 1
    assert teacher_detail["submission"]["max_score"] == 2


def test_student_submits_test_partial_homework_with_assigned_types(
    client: TestClient,
) -> None:
    assignment_id = _create_test_homework(
        client,
        {"kind": "test_partial", "variant": "001.txt", "types": [2]},
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = _create_homework_session(client, assignment_id)
    session_id = session["id"]
    assert session["total_steps"] == 1
    assert session["steps"][0]["type"] == 2

    client.post(f"/api/tests/sessions/{session_id}/steps/0/check", json={"answer": "2"})
    complete = client.post(f"/api/tests/sessions/{session_id}/complete")
    assert complete.status_code == 200, complete.text

    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 200, submit.text
    submission = submit.json()["submission"]
    assert submission["score"] == 1
    assert submission["max_score"] == 1


def test_student_cannot_submit_test_homework_before_session_complete(
    client: TestClient,
) -> None:
    assignment_id = _create_test_homework(
        client,
        {"kind": "test_variant", "variant": "001.txt"},
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = _create_homework_session(client, assignment_id)["id"]

    submit = client.post(
        f"/api/homework/{assignment_id}/submit",
        json={"test_session_id": session_id},
    )
    assert submit.status_code == 422
    assert submit.json()["detail"] == "Complete the test session before submitting homework"


def test_multi_item_homework_aggregates_lecture_and_two_variants(
    multi_client: TestClient,
) -> None:
    client = multi_client
    assignment_id = _create_homework(
        client,
        [
            {"kind": "lecture", "topic": "Алканы"},
            {"kind": "test_partial", "variant": "003.txt", "types": [10, 11]},
            {"kind": "test_partial", "variant": "007.txt", "types": [15]},
        ],
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    # One aggregated session spans both variants; variant_ref is null (SPEC §1.7).
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    session_id = session["id"]
    assert session["total_steps"] == 3
    assert session["variant_ref"] is None
    assert [step["type"] for step in session["steps"]] == [10, 11, 15]

    client.post(f"/api/tests/sessions/{session_id}/steps/0/check", json={"answer": "10"})
    client.post(
        f"/api/tests/sessions/{session_id}/steps/1/check", json={"answer": "wrong"}
    )
    client.post(f"/api/tests/sessions/{session_id}/steps/2/check", json={"answer": "15"})
    assert (
        client.post(f"/api/tests/sessions/{session_id}/complete").status_code == 200
    )

    # Submit without an explicit session id: the server finds the completed one.
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["status"] == "submitted"
    assert body["submission"]["score"] == 2
    assert body["submission"]["max_score"] == 3
    assert body["submission"]["test_session_id"] == session_id
    # All three items (lecture auto-confirmed + both test items) are complete.
    assert {p["item_index"]: p["completed"] for p in body["progress"]} == {
        0: True,
        1: True,
        2: True,
    }

    client.post("/api/auth/logout")
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    notifications = client.get("/api/notifications").json()
    assert len(notifications) == 1


def test_lecture_complete_tracks_partial_progress(multi_client: TestClient) -> None:
    client = multi_client
    assignment_id = _create_homework(
        client,
        [
            {"kind": "lecture", "topic": "Алканы"},
            {"kind": "test_partial", "variant": "003.txt", "types": [10]},
        ],
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    marked = client.post(f"/api/homework/{assignment_id}/items/0/complete", json={})
    assert marked.status_code == 200, marked.text
    body = marked.json()
    assert body["status"] == "in_progress"
    assert {p["item_index"]: p["completed"] for p in body["progress"]} == {
        0: True,
        1: False,
    }

    # Test item still pending → cannot finalize yet.
    blocked = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert blocked.status_code == 422
    assert blocked.json()["detail"] == (
        "Complete the test session before submitting homework"
    )


def test_complete_item_rejects_test_item(multi_client: TestClient) -> None:
    client = multi_client
    assignment_id = _create_homework(
        client,
        [
            {"kind": "lecture", "topic": "Алканы"},
            {"kind": "test_partial", "variant": "003.txt", "types": [10]},
        ],
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    response = client.post(f"/api/homework/{assignment_id}/items/1/complete", json={})
    assert response.status_code == 422
    assert response.json()["detail"] == "Only lecture items can be marked read directly"


def test_lecture_only_multi_item_autocompletes_on_submit(
    multi_client: TestClient,
) -> None:
    client = multi_client
    assignment_id = _create_homework(
        client,
        [
            {"kind": "lecture", "topic": "Алканы"},
            {"kind": "lecture", "topic": "Соли"},
        ],
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    submit = client.post(f"/api/homework/{assignment_id}/submit", json={})
    assert submit.status_code == 200, submit.text
    body = submit.json()
    assert body["status"] == "submitted"
    assert body["submission"]["test_session_id"] is None
    assert all(p["completed"] for p in body["progress"])


def test_test_by_type_homework_aggregates_across_variants(
    by_type_client: TestClient,
) -> None:
    client = by_type_client
    assignment_id = _create_test_homework(
        client,
        {"kind": "test_by_type", "types": [10]},
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    assert session["total_steps"] == 3
    assert session["variant_ref"] is None
    assert [step["type"] for step in session["steps"]] == [10, 10, 10]


def test_mixed_homework_with_test_by_type_and_partial(
    multi_client: TestClient,
) -> None:
    client = multi_client
    assignment_id = _create_homework(
        client,
        [
            {"kind": "lecture", "topic": "Алканы"},
            {"kind": "test_by_type", "types": [10]},
            {"kind": "test_partial", "variant": "003.txt", "types": [11]},
        ],
    )

    _login(client, STUDENT_EMAIL, STUDENT_PASS)
    session = client.post(
        "/api/tests/sessions",
        json={"homework_assignment_id": assignment_id},
    ).json()
    # test_by_type [10] -> 003 only (007 has 15 not 10 in multi db)
    # test_partial 003 [11] -> deduped with above
    assert session["total_steps"] == 2
    assert sorted(step["type"] for step in session["steps"]) == [10, 11]


def test_create_homework_rejects_oversized_test_by_type(
    oversized_client: TestClient,
) -> None:
    client = oversized_client
    _login(client, TEACHER_EMAIL, TEACHER_PASS)
    student_id = client.get("/api/students").json()[0]["id"]
    response = client.post(
        "/api/homework",
        json={
            "student_id": student_id,
            "title": "Too large",
            "items": [{"kind": "test_by_type", "types": list(range(1, 22))}],
        },
    )
    assert response.status_code == 422
    assert "maximum is 60" in response.json()["detail"]
