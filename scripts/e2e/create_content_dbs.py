"""Create minimal read-only content SQLite files for Playwright E2E (Task 99).

Writes to ``e2e-fixtures/`` at monorepo root. Reuses the same shape as pytest content fixtures.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FIXTURES_DIR = _REPO_ROOT / "e2e-fixtures"


def _create_lectures_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE prepared_lectures (
            topic TEXT NOT NULL,
            chunk_idx INTEGER NOT NULL,
            chunk_title TEXT,
            orig_text TEXT,
            lecture TEXT,
            tts_text TEXT,
            tts_audio BLOB,
            tts_audio_format TEXT,
            duration_ms INTEGER,
            qa_questions TEXT,
            qa_answers TEXT,
            PRIMARY KEY (topic, chunk_idx)
        )
        """
    )
    conn.execute(
        """
        INSERT INTO prepared_lectures (topic, chunk_idx, chunk_title, lecture, tts_audio)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("Алканы", 0, "Введение", "# Алканы", None),
    )
    conn.commit()
    conn.close()


def _create_ege_db(path: Path) -> None:
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
            ("001.txt", 1, "E2E: выберите ответ", "1", 0),
            ("001.txt", 2, "E2E: второй шаг", "2", 0),
        ],
    )
    conn.commit()
    conn.close()


def _create_oge_db(path: Path) -> None:
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
    conn.commit()
    conn.close()


def main() -> int:
    _FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    _create_lectures_db(_FIXTURES_DIR / "prepared_lectures.db")
    _create_ege_db(_FIXTURES_DIR / "test_ege.db")
    _create_oge_db(_FIXTURES_DIR / "test_oge.db")
    print(f"Created E2E content DBs in {_FIXTURES_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
