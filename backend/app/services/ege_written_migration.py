"""Offline migration: EGE written tasks (29–34) from source SQLite to test_ege.db (SPEC §1.10, Task 86)."""

from __future__ import annotations

import csv
import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

QUESTION_IMAGE_PREFIX = "рисунок"
ANSWER_IMAGE_PREFIX = "ответ"
TASK_TYPE_MIN = 29
TASK_TYPE_MAX = 34


@dataclass(frozen=True, slots=True)
class SkippedSourceRow:
    id: int
    task_number: int
    source_file: str | None


@dataclass(frozen=True, slots=True)
class MigrationImage:
    filename: str
    data: bytes


@dataclass(frozen=True, slots=True)
class MigrationRecord:
    source_id: int
    filename: str
    type: int
    question: str
    correct_ans: str
    images: tuple[MigrationImage, ...]
    action: Literal["insert", "update"]


@dataclass(slots=True)
class MigrationPlan:
    records: list[MigrationRecord] = field(default_factory=list)
    skipped_null_variant: list[SkippedSourceRow] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    @property
    def insert_count(self) -> int:
        return sum(1 for record in self.records if record.action == "insert")

    @property
    def update_count(self) -> int:
        return sum(1 for record in self.records if record.action == "update")


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_source_db(root: Path | None = None) -> Path:
    base = root or default_repo_root()
    matches = sorted(base.glob("ege*.db"))
    if not matches:
        raise FileNotFoundError(f"No source database matching ege*.db under {base}")
    return matches[0]


def default_target_db(root: Path | None = None) -> Path:
    base = root or default_repo_root()
    return base / "test_ege.db"


def _max_image_index(filenames: list[str], prefix: str) -> int:
    pattern = re.compile(rf"{re.escape(prefix)}(\d+)", re.IGNORECASE)
    max_index = -1
    for name in filenames:
        match = pattern.search(name)
        if match:
            max_index = max(max_index, int(match.group(1)))
    return max_index


def _append_placeholder(text: str | None, placeholder: str) -> str:
    base = (text or "").strip()
    if not base:
        return placeholder
    return f"{base}\n\n{placeholder}"


def _load_existing_tests(conn: sqlite3.Connection) -> dict[tuple[str, int], str]:
    rows = conn.execute(
        "SELECT filename, type, question FROM tests WHERE type BETWEEN ? AND ?",
        (TASK_TYPE_MIN, TASK_TYPE_MAX),
    ).fetchall()
    return {(row[0], int(row[1])): row[2] or "" for row in rows}


def _load_image_filenames(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT filename FROM images").fetchall()
    return [row[0] for row in rows]


def build_migration_plan(
    source_path: Path,
    target_path: Path,
) -> MigrationPlan:
    plan = MigrationPlan()

    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    target = sqlite3.connect(target_path)

    try:
        existing = _load_existing_tests(target)
        image_names = _load_image_filenames(target)
        next_question_idx = _max_image_index(image_names, QUESTION_IMAGE_PREFIX) + 1
        next_answer_idx = _max_image_index(image_names, ANSWER_IMAGE_PREFIX) + 1

        rows = source.execute(
            """
            SELECT id, task_number, question_text, question_image,
                   answer_text, answer_image, source_file, variant_number
            FROM tasks
            WHERE task_number BETWEEN ? AND ?
            ORDER BY variant_number, task_number, id
            """,
            (TASK_TYPE_MIN, TASK_TYPE_MAX),
        ).fetchall()

        for row in rows:
            if row["variant_number"] is None:
                plan.skipped_null_variant.append(
                    SkippedSourceRow(
                        id=int(row["id"]),
                        task_number=int(row["task_number"]),
                        source_file=row["source_file"],
                    )
                )
                continue

            filename = f"{int(row['variant_number']):03d}.txt"
            task_type = int(row["task_number"])
            key = (filename, task_type)

            images: list[MigrationImage] = []
            question = (row["question_text"] or "").strip()
            answer = (row["answer_text"] or "").strip()

            if row["question_image"]:
                placeholder = f"[{QUESTION_IMAGE_PREFIX}{next_question_idx:04d}]"
                image_name = f"{QUESTION_IMAGE_PREFIX}{next_question_idx:04d}.png"
                question = _append_placeholder(question, placeholder)
                images.append(
                    MigrationImage(filename=image_name, data=bytes(row["question_image"]))
                )
                next_question_idx += 1

            if row["answer_image"]:
                placeholder = f"[{ANSWER_IMAGE_PREFIX}{next_answer_idx:04d}]"
                image_name = f"{ANSWER_IMAGE_PREFIX}{next_answer_idx:04d}.png"
                answer = _append_placeholder(answer, placeholder)
                images.append(
                    MigrationImage(filename=image_name, data=bytes(row["answer_image"]))
                )
                next_answer_idx += 1

            action: Literal["insert", "update"] = "insert"
            if key in existing:
                action = "update"
                if existing[key] != question:
                    plan.conflicts.append(
                        f"{filename} type={task_type}: upsert will replace existing question text"
                    )

            plan.records.append(
                MigrationRecord(
                    source_id=int(row["id"]),
                    filename=filename,
                    type=task_type,
                    question=question,
                    correct_ans=answer,
                    images=tuple(images),
                    action=action,
                )
            )
    finally:
        source.close()
        target.close()

    return plan


def _ensure_images_filename_unique(conn: sqlite3.Connection) -> None:
    """Legacy content DBs may lack UNIQUE on images.filename; required for ON CONFLICT."""
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_images_filename ON images(filename)"
    )


def apply_migration_plan(target_path: Path, plan: MigrationPlan) -> None:
    conn = sqlite3.connect(target_path)
    try:
        _ensure_images_filename_unique(conn)
        conn.execute("BEGIN")
        for record in plan.records:
            if record.action == "update":
                conn.execute(
                    """
                    UPDATE tests
                    SET question = ?, correct_ans = ?, options = NULL,
                        hint = NULL, detailed_explanation = NULL,
                        has_issue = 0
                    WHERE filename = ? AND type = ?
                    """,
                    (record.question, record.correct_ans, record.filename, record.type),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO tests
                        (filename, type, question, options, correct_ans,
                         hint, detailed_explanation, has_issue)
                    VALUES (?, ?, ?, NULL, ?, NULL, NULL, 0)
                    """,
                    (record.filename, record.type, record.question, record.correct_ans),
                )

            for image in record.images:
                conn.execute(
                    """
                    INSERT INTO images (filename, mime_type, size_bytes, data)
                    VALUES (?, 'image/png', ?, ?)
                    ON CONFLICT(filename) DO UPDATE SET
                        mime_type = excluded.mime_type,
                        size_bytes = excluded.size_bytes,
                        data = excluded.data
                    """,
                    (image.filename, len(image.data), image.data),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def export_skipped_rows(
    rows: list[SkippedSourceRow],
    output_path: Path,
    *,
    fmt: Literal["json", "csv"] = "json",
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {
            "id": row.id,
            "task_number": row.task_number,
            "source_file": row.source_file,
        }
        for row in rows
    ]
    if fmt == "json":
        output_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "task_number", "source_file"])
        writer.writeheader()
        writer.writerows(payload)


class PlanSummary(TypedDict):
    records: int
    inserts: int
    updates: int
    skipped_null_variant: int
    conflicts: list[str]
    variants: list[str]
    types: list[int]
    images: int


def summarize_plan(plan: MigrationPlan) -> PlanSummary:
    variants = sorted({record.filename for record in plan.records})
    types = sorted({record.type for record in plan.records})
    return {
        "records": len(plan.records),
        "inserts": plan.insert_count,
        "updates": plan.update_count,
        "skipped_null_variant": len(plan.skipped_null_variant),
        "conflicts": plan.conflicts,
        "variants": variants,
        "types": types,
        "images": sum(len(record.images) for record in plan.records),
    }


def format_report(plan: MigrationPlan) -> str:
    summary = summarize_plan(plan)
    lines = [
        "EGE written tasks migration plan",
        f"  records: {summary['records']} (insert={summary['inserts']}, update={summary['updates']})",
        f"  skipped (variant_number IS NULL): {summary['skipped_null_variant']}",
        f"  images to write: {summary['images']}",
        f"  variants: {', '.join(summary['variants']) or '(none)'}",
        f"  types: {summary['types']}",
    ]
    if summary["conflicts"]:
        lines.append("  upsert notes:")
        for note in summary["conflicts"]:
            lines.append(f"    - {note}")
    if plan.skipped_null_variant:
        lines.append("  skipped rows (first 5):")
        for row in plan.skipped_null_variant[:5]:
            lines.append(
                f"    id={row.id} task={row.task_number} source={row.source_file!r}"
            )
    return "\n".join(lines)
