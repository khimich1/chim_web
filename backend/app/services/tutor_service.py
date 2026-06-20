"""Tutor chat orchestration: PostgreSQL history + LangGraph agent."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ExamTrack,
    StudentProfile,
    TestSession,
    TestSessionStatus,
    TutorMessageRole,
    TutorSession,
    User,
    UserRole,
)
from app.core.config import Settings, get_settings
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.tutor_repo import TutorRepository
from app.schemas.tutor import (
    TutorHealthResponse,
    TutorMessageCreate,
    TutorMessageRead,
    TutorMessageResponse,
    TutorSessionCreate,
    TutorSessionDetail,
    TutorSessionSummary,
    TutorSourceCitation,
)
from app.services.tutor.context import TutorRunContext
from app.services.tutor.graph import build_graph
from app.services.tutor.solve_gating import resolve_incorrect_step_gate
from app.services.tutor.student_tools import StudentTutorToolsService
from app.services.tutor.teacher_tools import TeacherTutorToolsService

logger = logging.getLogger(__name__)


class TutorService:
    def __init__(
        self,
        db: AsyncSession,
        *,
        llm: Any | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._db = db
        self._repo = TutorRepository(db)
        self._llm = llm
        self._settings = settings or get_settings()

    async def create_session(
        self,
        user: User,
        payload: TutorSessionCreate,
    ) -> TutorSessionSummary:
        page_context = (
            payload.page_context.model_dump(mode="json", exclude_none=True)
            if payload.page_context
            else None
        )
        session = await self._repo.create_session(
            user_id=user.id,
            role_context=user.role,
            page_context=page_context,
        )
        await self._db.commit()
        return self._to_summary(session, message_count=0)

    async def list_sessions(self, user: User) -> list[TutorSessionSummary]:
        sessions = await self._repo.list_sessions_for_user(user.id)
        return [
            self._to_summary(session, message_count=len(session.messages))
            for session in sessions
        ]

    async def list_student_sessions(
        self,
        teacher: User,
        student_id: uuid.UUID,
    ) -> list[TutorSessionSummary]:
        student = await StudentRepository(self._db).get_student_for_teacher(
            student_id,
            teacher.id,
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student not found or not yours",
            )
        sessions = await self._repo.list_sessions_for_student(student_id)
        return [
            self._to_summary(session, message_count=len(session.messages))
            for session in sessions
        ]

    async def get_session(self, user: User, session_id: uuid.UUID) -> TutorSessionDetail:
        session = await self._load_session(session_id)
        self._ensure_session_access(user, session)
        return self._to_detail(session)

    async def send_message(
        self,
        user: User,
        session_id: uuid.UUID,
        payload: TutorMessageCreate,
    ) -> TutorMessageResponse:
        session = await self._load_session(session_id)
        self._ensure_session_access(user, session)

        # I3/I7: verify the LLM is available BEFORE persisting anything, so a
        # misconfigured server never leaves an orphan user message in the DB.
        if self._llm is None and not self._settings.openai_api_key.strip():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=(
                    "OPENAI_API_KEY не задан. Добавьте ключ в backend/.env "
                    "и перезапустите сервер."
                ),
            )

        # B1: replay prior transcript from PostgreSQL (source of truth) into the
        # agent. Load it before adding the new turn.
        history = await self._repo.list_messages(session.id)

        # I2 (phase 1): persist the user message and commit, so we do NOT hold a
        # write transaction open for the duration of the (slow) agent call.
        user_message = await self._repo.add_message(
            session_id=session.id,
            role=TutorMessageRole.USER,
            content=payload.content,
        )
        user_message_id = user_message.id
        await self._db.commit()

        loop = asyncio.get_running_loop()
        invoke_timeout = self._settings.tutor_invoke_timeout

        def run_async(coro):  # type: ignore[no-untyped-def]
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=invoke_timeout)

        student_service = (
            StudentTutorToolsService(self._db, user=user)
            if user.role == UserRole.STUDENT
            else None
        )
        teacher_service = (
            TeacherTutorToolsService(self._db, user=user)
            if user.role == UserRole.TEACHER
            else None
        )
        ctx = await self._build_run_context(
            user,
            session.page_context,
            run_async=run_async,
            student_tools_service=student_service,
            teacher_tools_service=teacher_service,
        )
        graph = build_graph(ctx, llm=self._llm, settings=self._settings)
        invoke_input = {
            "messages": [
                *self._history_to_lc_messages(history),
                HumanMessage(content=payload.content),
            ]
        }
        timeout = self._settings.tutor_invoke_timeout

        try:
            # I4: bound the blocking LangGraph call so a hung LLM cannot pin a
            # worker thread indefinitely.
            result = await asyncio.wait_for(
                asyncio.to_thread(graph.invoke, invoke_input),
                timeout=timeout,
            )
        except asyncio.TimeoutError as exc:
            # I5: distinct detail per failure mode; roll back the user turn so the
            # transcript has no orphan question (matches frontend optimistic undo).
            await self._discard_message(user_message_id)
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Агент-советчик не ответил вовремя. Попробуйте ещё раз.",
            ) from exc
        except Exception as exc:  # noqa: BLE001 — surface agent errors to client
            logger.exception("Tutor agent invoke failed for session %s", session.id)
            await self._discard_message(user_message_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Ошибка агента-советчика. Повторите запрос позже.",
            ) from exc

        assistant_text = self._extract_assistant_text(result["messages"])
        sources = self._extract_sources(
            result["messages"],
            theory_hits=result.get("theory_hits"),
        )

        # I2 (phase 2) + S3: persist the assistant turn in a fresh transaction;
        # serialize sources with mode="json" for parity with page_context.
        assistant_message = await self._repo.add_message(
            session_id=session.id,
            role=TutorMessageRole.ASSISTANT,
            content=assistant_text,
            sources=[
                source.model_dump(mode="json", exclude_none=True)
                for source in sources
            ],
        )
        session.updated_at = assistant_message.created_at
        await self._db.commit()

        return TutorMessageResponse(
            message_id=assistant_message.id,
            content=assistant_text,
            sources=sources,
        )

    async def _discard_message(self, message_id: uuid.UUID) -> None:
        """Remove a just-persisted message after an agent failure and commit."""
        await self._repo.delete_message(message_id)
        await self._db.commit()

    @staticmethod
    def _history_to_lc_messages(
        history: list,
    ) -> list[HumanMessage | AIMessage]:
        """Convert stored transcript into LangChain messages for replay.

        Only user/assistant text is replayed; assistant messages are stored as
        plain text (no tool_calls), so reconstructed AIMessages carry no orphan
        tool calls that would break the LLM API.
        """
        replayed: list[HumanMessage | AIMessage] = []
        for message in history:
            if message.role == TutorMessageRole.USER:
                replayed.append(HumanMessage(content=message.content))
            elif message.role == TutorMessageRole.ASSISTANT:
                replayed.append(AIMessage(content=message.content))
        return replayed

    @staticmethod
    def get_health(settings: Settings | None = None) -> TutorHealthResponse:
        app_settings = settings or get_settings()
        return TutorHealthResponse(
            rag_index_exists=app_settings.rag_index_path.is_file(),
            openai_configured=bool(app_settings.openai_api_key.strip()),
        )

    async def _load_session(self, session_id: uuid.UUID) -> TutorSession:
        session = await self._repo.get_session(session_id)
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tutor session not found",
            )
        return session

    def _ensure_session_access(self, user: User, session: TutorSession) -> None:
        if session.user_id == user.id:
            return
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    async def _build_run_context(
        self,
        user: User,
        page_context: dict[str, Any] | None,
        *,
        run_async=None,
        student_tools_service: StudentTutorToolsService | None = None,
        teacher_tools_service: TeacherTutorToolsService | None = None,
    ) -> TutorRunContext:
        track: ExamTrack = ExamTrack.EGE
        active_test_session_id: uuid.UUID | None = None
        allowed_solve_test_id: int | None = None
        solve_student_answer: str | None = None

        if user.role == UserRole.STUDENT:
            profile = await self._db.scalar(
                select(StudentProfile).where(StudentProfile.user_id == user.id)
            )
            if profile is not None:
                track = profile.track

            active_test_session_id = await self._get_active_test_session_id(user.id)
            if page_context and page_context.get("test_session_id"):
                try:
                    page_ts = uuid.UUID(str(page_context["test_session_id"]))
                    if await self._is_active_session_for_user(page_ts, user.id):
                        active_test_session_id = page_ts
                except ValueError:
                    pass

            gate = await resolve_incorrect_step_gate(
                self._db,
                student_id=user.id,
                page_context=page_context,
            )
            if gate is not None:
                active_test_session_id = gate.test_session_id
                allowed_solve_test_id = gate.test_id
                solve_student_answer = gate.student_answer

        return TutorRunContext(
            track=track.value,
            user_id=str(user.id),
            role=user.role.value,  # type: ignore[arg-type]
            active_test_session_id=active_test_session_id,
            allowed_solve_test_id=allowed_solve_test_id,
            solve_student_answer=solve_student_answer,
            run_async=run_async,
            student_tools_service=student_tools_service,
            teacher_tools_service=teacher_tools_service,
        )

    async def _get_active_test_session_id(self, student_id: uuid.UUID) -> uuid.UUID | None:
        stmt = (
            select(TestSession.id)
            .where(
                TestSession.student_id == student_id,
                TestSession.status == TestSessionStatus.IN_PROGRESS,
            )
            .order_by(TestSession.created_at.desc())
            .limit(1)
        )
        return await self._db.scalar(stmt)

    async def _is_active_session_for_user(
        self,
        session_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> bool:
        stmt = select(TestSession.id).where(
            TestSession.id == session_id,
            TestSession.student_id == student_id,
            TestSession.status == TestSessionStatus.IN_PROGRESS,
        )
        return await self._db.scalar(stmt) is not None

    @staticmethod
    def _extract_assistant_text(messages: list) -> str:
        for message in reversed(messages):
            if isinstance(message, AIMessage):
                content = message.content
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    parts = [
                        block.get("text", "")
                        for block in content
                        if isinstance(block, dict) and block.get("type") == "text"
                    ]
                    text = "\n".join(part for part in parts if part).strip()
                    if text:
                        return text
        return "Не удалось сформировать ответ."

    @staticmethod
    def _extract_sources(
        messages: list,
        *,
        theory_hits: list[dict[str, Any]] | None = None,
    ) -> list[TutorSourceCitation]:
        citations: list[TutorSourceCitation] = []
        seen: set[tuple[str | None, str | None, int | None]] = set()

        for hit in theory_hits or []:
            if not isinstance(hit, dict):
                continue
            key = (
                hit.get("topic"),
                hit.get("chunk_title"),
                hit.get("chunk_idx"),
            )
            if key in seen:
                continue
            seen.add(key)
            citations.append(
                TutorSourceCitation(
                    source=hit.get("source") or "lecture",
                    topic=hit.get("topic"),
                    chunk_idx=hit.get("chunk_idx"),
                    chunk_title=hit.get("chunk_title"),
                )
            )

        for message in messages:
            if not isinstance(message, ToolMessage) or message.name != "retrieve_theory":
                continue
            if not isinstance(message.content, str):
                continue
            try:
                hits = json.loads(message.content)
            except json.JSONDecodeError:
                continue
            if not isinstance(hits, list):
                continue
            for hit in hits:
                if not isinstance(hit, dict):
                    continue
                key = (
                    hit.get("topic"),
                    hit.get("chunk_title"),
                    hit.get("chunk_idx"),
                )
                if key in seen:
                    continue
                seen.add(key)
                citations.append(
                    TutorSourceCitation(
                        source=hit.get("source") or "lecture",
                        topic=hit.get("topic"),
                        chunk_idx=hit.get("chunk_idx"),
                        chunk_title=hit.get("chunk_title"),
                    )
                )
        return citations

    @staticmethod
    def _to_summary(session: TutorSession, *, message_count: int) -> TutorSessionSummary:
        return TutorSessionSummary(
            id=session.id,
            role_context=session.role_context.value,
            page_context=session.page_context,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
        )

    @staticmethod
    def _to_detail(session: TutorSession) -> TutorSessionDetail:
        return TutorSessionDetail(
            id=session.id,
            role_context=session.role_context.value,
            page_context=session.page_context,
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=[
                TutorMessageRead(
                    id=message.id,
                    role=message.role.value,
                    content=message.content,
                    sources=(
                        [
                            TutorSourceCitation.model_validate(source)
                            for source in message.sources
                        ]
                        if message.sources
                        else None
                    ),
                    created_at=message.created_at,
                )
                for message in session.messages
            ],
        )
