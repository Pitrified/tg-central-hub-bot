"""SQLite CRUD service for sample app entries.

Uses asyncio.to_thread to avoid blocking the event loop.
All SQL statements use parameterised queries (no string interpolation).
"""

import asyncio
from datetime import UTC
from datetime import datetime
from pathlib import Path
import sqlite3

from loguru import logger as lg

from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryCreate
from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryRead


def _create_table(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                text        TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            )
            """,
        )
        conn.commit()


def _insert_entry(db_path: Path, text: str) -> EntryRead:
    created_at = datetime.now(UTC)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO entries (text, created_at) VALUES (?, ?)",
            (text, created_at.isoformat()),
        )
        conn.commit()
        row_id: int = cursor.lastrowid  # type: ignore[assignment]
    return EntryRead(id=row_id, text=text, created_at=created_at)


def _list_entries(db_path: Path) -> list[EntryRead]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, text, created_at FROM entries ORDER BY id DESC",
        ).fetchall()
    return [
        EntryRead(id=row[0], text=row[1], created_at=datetime.fromisoformat(row[2]))
        for row in rows
    ]


class EntriesService:
    """Async wrapper around stdlib sqlite3 for entries CRUD."""

    def __init__(self, db_path: Path) -> None:
        """Initialise the service with the given database file path."""
        self.db_path = db_path

    async def init_db(self) -> None:
        """Create the entries table if it does not exist."""
        await asyncio.to_thread(_create_table, self.db_path)
        lg.info(f"Entries DB ready at {self.db_path}")

    async def create_entry(self, entry: EntryCreate) -> EntryRead:
        """Insert a new entry and return the created record."""
        return await asyncio.to_thread(_insert_entry, self.db_path, entry.text)

    async def list_entries(self) -> list[EntryRead]:
        """Return all entries, newest first."""
        return await asyncio.to_thread(_list_entries, self.db_path)
