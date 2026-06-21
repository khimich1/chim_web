"""Tests for EGE written tasks migration (Task 86)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from app.services.ege_written_migration import (
    apply_migration_plan,
    build_migration_plan,
    export_skipped_rows,
    summarize_plan,
)


def _create_source_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_number INTEGER,
            question_text TEXT,
            question_image BLOB,
            answer_text TEXT,
            answer_image BLOB,
            source_file TEXT,
            page_number INTEGER,
            variant_number INTEGER,
            created_at TEXT
        )
        """
    )
    conn.executemany(
        """
        INSERT INTO tasks
            (task_number, question_text, question_image, answer_text, answer_image,
             source_file, variant_number)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (29, "Written Q1", None, "Answer 1", None, "v1.pdf", 1),
            (
                30,
                "Written Q2 with image",
                b"q-img",
                "Answer 2",
                b"a-img",
                "v1.pdf",
                1,
            ),
            (31, "Skipped null variant", None, "Answer", None, "draft.pdf", None),
            (32, "Variant 2 task", None, "Ans", None, "v2.pdf", 2),
        ],
    )
    conn.commit()
    conn.close()


def _create_target_db(
    path: Path,
    *,
    with_existing: bool = False,
    filename_unique: bool = True,
) -> None:
    conn = sqlite3.connect(path)
    filename_col = "filename TEXT UNIQUE NOT NULL" if filename_unique else "filename TEXT NOT NULL"
    conn.executescript(
        f"""
        CREATE TABLE tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            type INTEGER,
            question TEXT,
            options TEXT,
            correct_ans TEXT,
            explanation TEXT,
            hint TEXT,
            detailed_explanation TEXT,
            has_issue INTEGER DEFAULT 0,
            issue_reason TEXT DEFAULT '',
            issue_reported_at TEXT DEFAULT ''
        );
        CREATE TABLE images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {filename_col},
            mime_type TEXT,
            size_bytes INTEGER,
            data BLOB NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.execute(
        """
        INSERT INTO tests (filename, type, question, correct_ans)
        VALUES ('001.txt', 1, 'Old exact', '1')
        """
    )
    conn.execute(
        """
        INSERT INTO images (filename, mime_type, size_bytes, data)
        VALUES ('рисунок0001.png', 'image/png', 3, ?)
        """,
        (b"old",),
    )
    if with_existing:
        conn.execute(
            """
            INSERT INTO tests (filename, type, question, correct_ans)
            VALUES ('001.txt', 29, 'Old written', 'old answer')
            """
        )
    conn.commit()
    conn.close()


@pytest.fixture
def migration_dbs(tmp_path: Path) -> tuple[Path, Path]:
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _create_source_db(source)
    _create_target_db(target)
    return source, target


def test_build_migration_plan_skips_null_variants(migration_dbs: tuple[Path, Path]) -> None:
    source, target = migration_dbs
    plan = build_migration_plan(source, target)
    summary = summarize_plan(plan)

    assert summary["records"] == 3
    assert summary["skipped_null_variant"] == 1
    assert summary["inserts"] == 3
    assert summary["updates"] == 0
    assert summary["types"] == [29, 30, 32]
    assert summary["images"] == 2


def test_apply_migration_inserts_tests_and_images(migration_dbs: tuple[Path, Path]) -> None:
    source, target = migration_dbs
    plan = build_migration_plan(source, target)
    apply_migration_plan(target, plan)

    conn = sqlite3.connect(target)
    count = conn.execute("SELECT COUNT(*) FROM tests WHERE type >= 29").fetchone()[0]
    assert count == 3

    row = conn.execute(
        "SELECT question, correct_ans FROM tests WHERE filename='001.txt' AND type=30"
    ).fetchone()
    assert row is not None
    assert "[рисунок0002]" in row[0]
    assert "[ответ0000]" in row[1]

    images = conn.execute(
        "SELECT filename FROM images WHERE filename LIKE 'ответ%' OR filename LIKE 'рисунок0002%'"
    ).fetchall()
    assert len(images) == 2
    conn.close()


def test_apply_migration_creates_filename_index_on_legacy_db(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _create_source_db(source)
    _create_target_db(target, filename_unique=False)

    plan = build_migration_plan(source, target)
    apply_migration_plan(target, plan)

    conn = sqlite3.connect(target)
    index = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_images_filename'"
    ).fetchone()
    assert index is not None
    assert conn.execute("SELECT COUNT(*) FROM images").fetchone()[0] >= 3
    conn.close()


def test_apply_migration_upserts_existing_row(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    _create_source_db(source)
    _create_target_db(target, with_existing=True)
    plan = build_migration_plan(source, target)

    assert plan.update_count == 1
    assert plan.insert_count == 2

    apply_migration_plan(target, plan)
    conn = sqlite3.connect(target)
    row = conn.execute(
        "SELECT question FROM tests WHERE filename='001.txt' AND type=29"
    ).fetchone()
    assert row is not None
    assert row[0] == "Written Q1"
    conn.close()


def test_export_skipped_rows_json(migration_dbs: tuple[Path, Path], tmp_path: Path) -> None:
    source, target = migration_dbs
    plan = build_migration_plan(source, target)
    out = tmp_path / "skipped.json"
    export_skipped_rows(plan.skipped_null_variant, out)

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["task_number"] == 31
    assert payload[0]["source_file"] == "draft.pdf"
