"""Integration tests for tutor API (mock LLM, no OpenAI)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Annotated

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.routers.tutor import get_tutor_service

from app.core.config import Settings, get_settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models import ExamTrack, StudentProfile, User, UserRole
from app.services.tutor_service import TutorService

TEACHER_EMAIL = "teacher@example.com"
TEACHER_PASS = "teacher-pass"
STUDENT_EMAIL = "student@example.com"
STUDENT_PASS = "student-pass"
OTHER_STUDENT_EMAIL = "other@example.com"


class FakeLLM:
    """Minimal LLM double for offline tutor API tests."""

    def bind_tools(self, tools, parallel_tool_calls=False):  # noqa: ANN001
        return self

    def invoke(self, messages):  # noqa: ANN001
        system_text = ""
        if messages:
            first = messages[0]
            system_text = str(getattr(first, "content", ""))
        if "классификатор" in system_text.lower():
            return AIMessage(content="да")
        return AIMessage(content="Алканы — предельные углеводороды (мок-ответ).")


class RecordingLLM(FakeLLM):
    """FakeLLM that records the message lists passed to each invoke()."""

    def __init__(self) -> None:
        self.invocations: list[list] = []

    def invoke(self, messages):  # noqa: ANN001
        self.invocations.append(list(messages))
        return super().invoke(messages)

    def agent_invocations(self) -> list[list]:
        """Invocations that are the agent step (not the off-topic classifier)."""
        result = []
        for messages in self.invocations:
            system_text = str(getattr(messages[0], "content", "")) if messages else ""
            if "классификатор" not in system_text.lower():
                result.append(messages)
        return result


class RaisingLLM(FakeLLM):
    """FakeLLM whose agent step raises to simulate an agent/LLM failure."""

    def invoke(self, messages):  # noqa: ANN001
        system_text = str(getattr(messages[0], "content", "")) if messages else ""
        if "классификатор" in system_text.lower():
            return AIMessage(content="да")
        raise RuntimeError("simulated agent failure")


@pytest.fixture
def tutor_client(tmp_path: Path, rag_retriever, monkeypatch) -> TestClient:
    db_file = tmp_path / "tutor_api.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    teacher_id = uuid.uuid4()
    student_id = uuid.uuid4()
    other_student_id = uuid.uuid4()

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
                    User(
                        id=other_student_id,
                        email=OTHER_STUDENT_EMAIL,
                        password_hash=hash_password("other-pass"),
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
                        user_id=other_student_id,
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

    def _override_tutor_service(
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> TutorService:
        return TutorService(db, llm=FakeLLM())

    monkeypatch.setattr(
        "app.services.rag.theory.Retriever.from_settings",
        lambda settings=None: rag_retriever,
    )

    get_settings.cache_clear()
    app = create_app(settings=Settings())
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_tutor_service] = _override_tutor_service

    with TestClient(app) as test_client:
        yield test_client

    asyncio.run(request_engine.dispose())


def _login(client: TestClient, email: str, password: str) -> None:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200


def test_create_session_serializes_explain_incorrect_page_context(
    tutor_client: TestClient,
) -> None:
    """page_context with solve gating fields must round-trip through API."""
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    test_session_id = str(uuid.uuid4())

    create = tutor_client.post(
        "/api/tutor/sessions",
        json={
            "page_context": {
                "test_session_id": test_session_id,
                "step_position": 2,
                "test_id": 42,
                "solve_mode": "explain_incorrect_step",
            }
        },
    )
    assert create.status_code == 201
    body = create.json()["page_context"]
    assert body["test_session_id"] == test_session_id
    assert body["step_position"] == 2
    assert body["test_id"] == 42
    assert body["solve_mode"] == "explain_incorrect_step"


def test_create_session_serializes_test_session_id_in_page_context(
    tutor_client: TestClient,
) -> None:
    """Prove-It: UUID in page_context must be JSON-serializable when persisted."""
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    test_session_id = str(uuid.uuid4())

    create = tutor_client.post(
        "/api/tutor/sessions",
        json={"page_context": {"test_session_id": test_session_id}},
    )
    assert create.status_code == 201
    body = create.json()
    assert body["page_context"] is not None
    assert body["page_context"]["test_session_id"] == test_session_id


def test_create_session_and_send_message(tutor_client: TestClient) -> None:
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)

    create = tutor_client.post(
        "/api/tutor/sessions",
        json={"page_context": {"topic": "Алканы"}},
    )
    assert create.status_code == 201
    session_id = create.json()["id"]

    reply = tutor_client.post(
        f"/api/tutor/sessions/{session_id}/messages",
        json={"content": "Что такое алканы?"},
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["role"] == "assistant"
    assert "алкан" in body["content"].lower()
    assert "message_id" in body

    detail = tutor_client.get(f"/api/tutor/sessions/{session_id}")
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_teacher_lists_student_sessions(tutor_client: TestClient) -> None:
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post("/api/tutor/sessions", json={}).json()["id"]
    tutor_client.post(
        f"/api/tutor/sessions/{session_id}/messages",
        json={"content": "Привет"},
    )

    _login(tutor_client, TEACHER_EMAIL, TEACHER_PASS)
    students = tutor_client.get("/api/students").json()
    student_id = students[0]["id"]

    sessions = tutor_client.get(f"/api/tutor/students/{student_id}/sessions")
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 1


def test_teacher_cannot_read_other_teacher_student_sessions(
    tutor_client: TestClient,
) -> None:
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post("/api/tutor/sessions", json={}).json()["id"]

    _login(tutor_client, TEACHER_EMAIL, TEACHER_PASS)
    fake_student_id = str(uuid.uuid4())
    response = tutor_client.get(f"/api/tutor/students/{fake_student_id}/sessions")
    assert response.status_code == 403


def test_cross_user_session_forbidden(tutor_client: TestClient) -> None:
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post("/api/tutor/sessions", json={}).json()["id"]

    _login(tutor_client, OTHER_STUDENT_EMAIL, "other-pass")
    response = tutor_client.get(f"/api/tutor/sessions/{session_id}")
    assert response.status_code == 403


def test_tutor_health_endpoint(tutor_client: TestClient) -> None:
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    response = tutor_client.get("/api/tutor/health/tutor")
    assert response.status_code == 200
    body = response.json()
    assert "rag_index_exists" in body
    assert "openai_configured" in body
    assert isinstance(body["rag_index_exists"], bool)
    assert isinstance(body["openai_configured"], bool)


def test_tutor_health_requires_auth(tutor_client: TestClient) -> None:
    """B4: readiness flags must not be exposed to anonymous callers."""
    response = tutor_client.get("/api/tutor/health/tutor")
    assert response.status_code == 401


def test_session_transcript_ordered_by_created_at(tutor_client: TestClient) -> None:
    """B2: messages come back in chronological order."""
    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post(
        "/api/tutor/sessions", json={"page_context": {"topic": "Алканы"}}
    ).json()["id"]

    for text in ("Первый вопрос", "Второй вопрос", "Третий вопрос"):
        reply = tutor_client.post(
            f"/api/tutor/sessions/{session_id}/messages",
            json={"content": text},
        )
        assert reply.status_code == 200

    messages = tutor_client.get(f"/api/tutor/sessions/{session_id}").json()["messages"]
    user_messages = [m["content"] for m in messages if m["role"] == "user"]
    assert user_messages == ["Первый вопрос", "Второй вопрос", "Третий вопрос"]
    timestamps = [m["created_at"] for m in messages]
    assert timestamps == sorted(timestamps)


def test_multi_turn_history_replayed_into_agent(
    tutor_client: TestClient,
) -> None:
    """B1: prior transcript from PostgreSQL is replayed into the agent."""
    recording = RecordingLLM()
    tutor_client.app.dependency_overrides[get_tutor_service] = (
        lambda db=Depends(get_db): TutorService(db, llm=recording)
    )

    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post("/api/tutor/sessions", json={}).json()["id"]

    tutor_client.post(
        f"/api/tutor/sessions/{session_id}/messages",
        json={"content": "Что такое алканы?"},
    )
    tutor_client.post(
        f"/api/tutor/sessions/{session_id}/messages",
        json={"content": "А алкены?"},
    )

    agent_calls = recording.agent_invocations()
    assert agent_calls, "agent step never invoked"
    last_call_text = " ".join(
        str(getattr(message, "content", "")) for message in agent_calls[-1]
    )
    # The second turn's agent invocation must contain the first user question.
    assert "Что такое алканы?" in last_call_text


def test_send_message_agent_error_returns_503_and_rolls_back(
    tutor_client: TestClient,
) -> None:
    """I5: agent failure → 503 and the user turn is rolled back (no orphan)."""
    tutor_client.app.dependency_overrides[get_tutor_service] = (
        lambda db=Depends(get_db): TutorService(db, llm=RaisingLLM())
    )

    _login(tutor_client, STUDENT_EMAIL, STUDENT_PASS)
    session_id = tutor_client.post("/api/tutor/sessions", json={}).json()["id"]

    response = tutor_client.post(
        f"/api/tutor/sessions/{session_id}/messages",
        json={"content": "Что такое алканы?"},
    )
    assert response.status_code == 503
    assert "OPENAI_API_KEY" not in response.json()["detail"]

    messages = tutor_client.get(f"/api/tutor/sessions/{session_id}").json()["messages"]
    assert messages == []


def test_send_message_without_openai_key_returns_503(
    tmp_path: Path,
    rag_retriever,
    monkeypatch,
) -> None:
    db_file = tmp_path / "tutor_no_key.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        session_maker = async_sessionmaker(engine, expire_on_commit=False)
        async with session_maker() as session:
            student_id = uuid.uuid4()
            session.add(
                User(
                    id=student_id,
                    email="solo@example.com",
                    password_hash=hash_password("solo-pass"),
                    role=UserRole.STUDENT,
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

    monkeypatch.setattr(
        "app.services.rag.theory.Retriever.from_settings",
        lambda settings=None: rag_retriever,
    )

    get_settings.cache_clear()
    app = create_app(settings=Settings(openai_api_key=""))
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as client:
        _login(client, "solo@example.com", "solo-pass")
        session_id = client.post("/api/tutor/sessions", json={}).json()["id"]
        response = client.post(
            f"/api/tutor/sessions/{session_id}/messages",
            json={"content": "Что такое алканы?"},
        )
        assert response.status_code == 503
        assert "OPENAI_API_KEY" in response.json()["detail"]

        # I7: a misconfigured server must not leave an orphan user message.
        detail = client.get(f"/api/tutor/sessions/{session_id}")
        assert detail.status_code == 200
        assert detail.json()["messages"] == []

    asyncio.run(request_engine.dispose())
