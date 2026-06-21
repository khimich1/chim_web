"""Smoke test for E2E seed CLI (Task 99)."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import sqlite3
from sqlalchemy.ext.asyncio import create_async_engine

from app.cli import seed_e2e as seed_e2e_module
from app.core.config import get_settings
from app.db.base import Base


def _create_minimal_ege_db(path: Path) -> None:
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
    conn.execute(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("001.txt", 1, "Q1", "1", 0),
    )
    conn.commit()
    conn.close()


def test_seed_e2e_cli_creates_homework(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_file = tmp_path / "cli_seed.db"
    db_url = f"sqlite+aiosqlite:///{db_file.as_posix()}"
    ege_db = tmp_path / "test_ege.db"
    _create_minimal_ege_db(ege_db)

    async def _setup() -> None:
        engine = create_async_engine(db_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_setup())

    monkeypatch.setenv("DATABASE_URL", db_url)
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-seed-e2e-cli")
    monkeypatch.setenv("CONTENT_EGE_DB_PATH", str(ege_db))
    get_settings.cache_clear()

    payload = asyncio.run(seed_e2e_module.seed_e2e())

    assert payload["studentEmail"] == seed_e2e_module.STUDENT_EMAIL
    assert payload["correctAnswer"] == "1"
    assert payload["homeworkId"]
