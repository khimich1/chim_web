"""Fixtures for tutor RAG tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.services.rag.ingestion import ingest_all_documents_from_paths
from app.services.rag.retriever import Retriever


def _create_rag_lectures_db(path: Path) -> None:
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
    conn.executemany(
        """
        INSERT INTO prepared_lectures
            (topic, chunk_idx, chunk_title, lecture, qa_questions, qa_answers)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "Алканы",
                0,
                "Свойства алканов",
                "# Алканы\n\nАлканы малореакционны из-за прочных связей C-C и C-H.",
                json.dumps(["Почему алканы малореакционны?"]),
                json.dumps(["Из-за неполярных связей и отсутствия реакционного центра."]),
            ),
            (
                "Соли",
                0,
                "Введение",
                "# Соли\n\nИонные соединения образуют кристаллическую решётку.",
                None,
                None,
            ),
        ],
    )
    conn.commit()
    conn.close()


def _create_rag_tests_db(path: Path, *, track_label: str) -> None:
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
    conn.execute("CREATE TABLE tests_bug (filename TEXT)")
    conn.executemany(
        """
        INSERT INTO tests
            (filename, type, question, correct_ans, hint, detailed_explanation, has_issue)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                "001.txt",
                15,
                f"{track_label} question",
                "secret-answer",
                f"Подсказка для {track_label}",
                f"Разбор задания {track_label}",
                0,
            ),
            (
                "002.txt",
                1,
                "Bad",
                "9",
                "skip",
                "skip",
                1,
            ),
        ],
    )
    conn.execute("INSERT INTO tests_bug (filename) VALUES ('002.txt')")
    conn.commit()
    conn.close()


@pytest.fixture
def rag_content_dbs(tmp_path: Path) -> dict[str, Path]:
    lectures = tmp_path / "prepared_lectures.db"
    ege = tmp_path / "test_ege.db"
    oge = tmp_path / "test_oge.db"
    _create_rag_lectures_db(lectures)
    _create_rag_tests_db(ege, track_label="EGE")
    _create_rag_tests_db(oge, track_label="OGE")
    return {"lectures": lectures, "ege": ege, "oge": oge}


@pytest.fixture
def rag_retriever(rag_content_dbs: dict[str, Path]) -> Retriever:
    documents = ingest_all_documents_from_paths(
        lectures_db_path=rag_content_dbs["lectures"],
    )
    return Retriever(documents)
