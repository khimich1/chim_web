"""Base helpers for read-only content SQLite access."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class ContentDbError(Exception):
    """Raised when a content database is missing or invalid."""


def open_readonly(db_path: Path) -> sqlite3.Connection:
    """Open SQLite in read-only URI mode (SELECT only by convention)."""
    if not db_path.is_file():
        raise ContentDbError(f"Content database not found: {db_path}")

    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn
