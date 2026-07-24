"""Repair local SQLite DB after rolled-back Alembic revisions.

When alembic_version points at a revision that no longer exists in the repo,
stamp the DB to the last known pre-groups revision and drop orphan schema
from removed migrations (student groups / homework templates). Then run
``alembic upgrade head`` to apply 019+ cleanly.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_DB = BACKEND / "data" / "app.db"

# Last revision before homework_templates / student_groups (019).
# Stamp here after dropping orphan schema so ``alembic upgrade head`` recreates it.
SAFE_STAMP_REVISION = "018_normalize_user_email_lowercase"


def _current_revision(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
    return row[0] if row else None


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (name,),
    ).fetchone()
    return row is not None


def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in cols)


def _drop_templates_and_groups_schema(conn: sqlite3.Connection) -> None:
    """Remove orphan template/group columns and tables so 019 can recreate them."""
    if _table_exists(conn, "homework_assignments") and (
        _column_exists(conn, "homework_assignments", "source_group_id")
        or _column_exists(conn, "homework_assignments", "template_id")
    ):
        conn.executescript(
            """
            PRAGMA foreign_keys=OFF;
            BEGIN;
            CREATE TABLE homework_assignments__repair (
                id CHAR(32) NOT NULL,
                student_id CHAR(32) NOT NULL,
                teacher_id CHAR(32) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                due_at DATETIME,
                items JSON NOT NULL,
                status VARCHAR(20) NOT NULL,
                created_at DATETIME DEFAULT (CURRENT_TIMESTAMP) NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(teacher_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY(student_id) REFERENCES users (id) ON DELETE CASCADE
            );
            INSERT INTO homework_assignments__repair (
                id, student_id, teacher_id, title, description, due_at, items, status, created_at
            )
            SELECT
                id, student_id, teacher_id, title, description, due_at, items, status, created_at
            FROM homework_assignments;
            DROP TABLE homework_assignments;
            ALTER TABLE homework_assignments__repair RENAME TO homework_assignments;
            COMMIT;
            PRAGMA foreign_keys=ON;
            """
        )

    conn.execute("DROP TABLE IF EXISTS student_group_members")
    conn.execute("DROP TABLE IF EXISTS student_groups")
    conn.execute("DROP TABLE IF EXISTS homework_templates")


def repair(db_path: Path = DEFAULT_DB) -> str:
    if not db_path.is_file():
        raise FileNotFoundError(f"Database not found: {db_path}")

    cfg = Config(str(BACKEND / "alembic.ini"))
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    if head is None:
        raise RuntimeError("No Alembic head revision found")

    known_revisions = {rev.revision for rev in script.walk_revisions()}
    if SAFE_STAMP_REVISION not in known_revisions:
        raise RuntimeError(
            f"Safe stamp revision {SAFE_STAMP_REVISION!r} not found in migrations"
        )

    conn = sqlite3.connect(db_path)
    try:
        current = _current_revision(conn)

        if current == head:
            return current

        if current and current not in known_revisions:
            print(
                f"Unknown alembic revision in DB: {current!r} -> "
                f"stamping {SAFE_STAMP_REVISION!r} (run alembic upgrade head)"
            )
            _drop_templates_and_groups_schema(conn)
            conn.execute("DELETE FROM alembic_version")
            conn.execute(
                "INSERT INTO alembic_version (version_num) VALUES (?)",
                (SAFE_STAMP_REVISION,),
            )
            conn.commit()
            return SAFE_STAMP_REVISION

        if current and current != head:
            print(f"DB revision {current!r} differs from head {head!r}; leaving as-is")
            return current

        conn.execute("DELETE FROM alembic_version")
        conn.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            (head,),
        )
        conn.commit()
        return head
    finally:
        conn.close()


def main() -> int:
    db = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DB
    try:
        head = repair(db)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"alembic_version set to {head}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
