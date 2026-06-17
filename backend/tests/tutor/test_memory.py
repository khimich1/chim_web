"""Tests for tutor session persistence in PostgreSQL."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import TutorMessageRole, User, UserRole
from app.repositories.app.tutor_repo import TutorRepository


@pytest.mark.asyncio
async def test_tutor_repo_persists_messages(tmp_path: Path) -> None:
    db_url = f"sqlite+aiosqlite:///{(tmp_path / 'tutor_memory.db').as_posix()}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    user_id = uuid.uuid4()

    async with session_maker() as db:
        db.add(
            User(
                id=user_id,
                email="mem@test.com",
                password_hash="hash",
                role=UserRole.STUDENT,
            )
        )
        await db.flush()

        repo = TutorRepository(db)
        tutor_session = await repo.create_session(
            user_id=user_id,
            role_context=UserRole.STUDENT,
            page_context={"topic": "Алканы"},
        )
        await repo.add_message(
            session_id=tutor_session.id,
            role=TutorMessageRole.USER,
            content="Вопрос",
        )
        await repo.add_message(
            session_id=tutor_session.id,
            role=TutorMessageRole.ASSISTANT,
            content="Ответ",
            sources=[{"topic": "Алканы", "chunk_title": "Свойства"}],
        )
        await db.commit()

    async with session_maker() as db:
        loaded = await TutorRepository(db).get_session(tutor_session.id)
        assert loaded is not None
        assert len(loaded.messages) == 2
        assert loaded.messages[0].content == "Вопрос"
        assert loaded.messages[1].sources[0]["topic"] == "Алканы"

    await engine.dispose()
