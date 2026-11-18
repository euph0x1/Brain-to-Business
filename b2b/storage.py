"""SQLite storage for past ideas."""
import sqlite3
from contextlib import closing
from datetime import datetime

from . import config
from .schemas import Brief


def _connect() -> sqlite3.Connection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS ideas (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               created_at TEXT NOT NULL,
               title TEXT NOT NULL,
               overall REAL NOT NULL,
               data TEXT NOT NULL)"""
    )
    return conn


def save(brief: Brief) -> int:
    with closing(_connect()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO ideas (created_at, title, overall, data) VALUES (?, ?, ?, ?)",
            (
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                brief.clarified.one_liner,
                brief.overall,
                brief.model_dump_json(),
            ),
        )
        return cur.lastrowid


def list_ideas() -> list[dict]:
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT id, created_at, title, overall FROM ideas ORDER BY id DESC"
        ).fetchall()
    return [{"id": r[0], "created_at": r[1], "title": r[2], "overall": r[3]} for r in rows]


def load(idea_id: int) -> Brief | None:
    with closing(_connect()) as conn:
        row = conn.execute("SELECT data FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    return Brief.model_validate_json(row[0]) if row else None


def delete(idea_id: int) -> None:
    with closing(_connect()) as conn, conn:
        conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))
