"""Fixtures: minimal content SQLite databases for repository tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


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
    # Insert out of alphabetical order to verify ORDER BY MIN(rowid)
    conn.executemany(
        """
        INSERT INTO prepared_lectures
            (topic, chunk_idx, chunk_title, lecture, tts_audio)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("Соли", 0, "Введение", "# Соли", None),
            ("Соли", 1, "Свойства", "# Свойства солей", b"audio"),
            ("Алканы", 0, "Алканы intro", "# Алканы", None),
        ],
    )
    conn.commit()
    conn.close()


def _create_tests_db(path: Path, *, with_bug: bool) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tests (
            filename TEXT,
            type INTEGER,
            question TEXT,
            options TEXT,
            correct_ans TEXT,
            hint TEXT,
            detailed_explanation TEXT,
            has_issue INTEGER DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE tests_bug (
            filename TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE images (
            filename TEXT PRIMARY KEY,
            data BLOB NOT NULL
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO tests
            (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("001.txt", 1, "Q1", "1", 0),
            ("001.txt", 2, "Q2 with [рисунок0001]", "2", 0),
            ("002.txt", 1, "Bad Q", "9", 1),
        ],
    )
    conn.execute(
        "INSERT INTO images (filename, data) VALUES (?, ?)",
        ("рисунок0001.png", b"png-bytes"),
    )
    if with_bug:
        conn.execute("INSERT INTO tests_bug (filename) VALUES ('002.txt')")
    conn.commit()
    conn.close()


@pytest.fixture
def lectures_db(tmp_path: Path) -> Path:
    path = tmp_path / "prepared_lectures.db"
    _create_lectures_db(path)
    return path


@pytest.fixture
def ege_tests_db(tmp_path: Path) -> Path:
    path = tmp_path / "test_ege.db"
    _create_tests_db(path, with_bug=True)
    return path


@pytest.fixture
def oge_tests_db(tmp_path: Path) -> Path:
    path = tmp_path / "test_oge.db"
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
    conn.executemany(
        """
        INSERT INTO tests (filename, type, question, correct_ans, has_issue)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            ("001.txt", 1, "OGE Q1", "1", 0),
            ("019.txt", 1, "OGE Q19", "4", 0),
        ],
    )
    conn.commit()
    conn.close()
    return path
