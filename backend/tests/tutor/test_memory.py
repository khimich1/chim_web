"""Tests for tutor profile persistence in PostgreSQL (Task 47 A7)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models import TutorMessageRole, User, UserRole
from app.repositories.app.tutor_repo import TutorRepository
from app.services.tutor.context import TutorRunContext
from app.services.tutor.profile_service import TutorProfileService


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


@pytest.mark.asyncio
async def test_tutor_profile_read_write_in_postgres(tmp_path: Path) -> None:
    db_url = f"sqlite+aiosqlite:///{(tmp_path / 'tutor_profile.db').as_posix()}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    user_id = uuid.uuid4()

    async with session_maker() as db:
        db.add(
            User(
                id=user_id,
                email="profile@test.com",
                password_hash="hash",
                role=UserRole.STUDENT,
            )
        )
        await db.flush()
        service = TutorProfileService(db, user_id=user_id)
        assert await service.load() == {}
        await service.update_key("grade", "11 класс")
        await db.commit()

    async with session_maker() as db:
        service = TutorProfileService(db, user_id=user_id)
        profile = await service.load()
        assert profile["grade"] == "11 класс"
        await service.update_key("name", "Роман")
        await db.commit()

    async with session_maker() as db:
        profile = await TutorProfileService(db, user_id=user_id).load()
        assert profile == {"grade": "11 класс", "name": "Роман"}

    await engine.dispose()


@pytest.mark.asyncio
async def test_load_profile_via_memory_bridge(tmp_path: Path) -> None:
    from app.services.tutor.memory import load_profile

    db_url = f"sqlite+aiosqlite:///{(tmp_path / 'load_profile.db').as_posix()}"
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    user_id = uuid.uuid4()

    async with session_maker() as db:
        db.add(
            User(
                id=user_id,
                email="load@test.com",
                password_hash="hash",
                role=UserRole.STUDENT,
            )
        )
        await db.flush()
        service = TutorProfileService(db, user_id=user_id)
        await service.update_key("grade", "11 класс")
        await db.commit()

    async with session_maker() as db:
        service = TutorProfileService(db, user_id=user_id)
        loop = asyncio.get_running_loop()

        def run_async(coro):  # type: ignore[no-untyped-def]
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=5)

        ctx = TutorRunContext(
            track="ege",
            user_id=str(user_id),
            run_async=run_async,
            profile_service=service,
        )
        from app.services.tutor.context import set_tutor_context

        set_tutor_context(ctx)
        profile = await asyncio.to_thread(load_profile, str(user_id))
        assert profile["grade"] == "11 класс"

    await engine.dispose()
