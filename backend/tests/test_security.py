"""Security hardening tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from app.repositories.content.base import open_readonly
from tests.content.conftest import _create_tests_db


def test_content_sqlite_connection_is_read_only(tmp_path: Path) -> None:
    db_path = tmp_path / "test_ege.db"
    _create_tests_db(db_path, with_bug=True)

    with open_readonly(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM tests").fetchone()[0] == 3

        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute(
                """
                INSERT INTO tests
                    (filename, type, question, correct_ans, has_issue)
                VALUES ('999.txt', 1, 'Injected question', '1', 0)
                """
            )
