"""Tests for EntriesService."""

import asyncio
from pathlib import Path
import tempfile

from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryCreate
from tg_central_hub_bot.webapp.services.entries_service import EntriesService


def test_create_and_list() -> None:
    """Created entries are returned by list_entries."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EntriesService(db_path=Path(tmp) / "test.db")
            await service.init_db()
            entry = await service.create_entry(EntryCreate(text="hello"))
            assert entry.id == 1
            assert entry.text == "hello"
            entries = await service.list_entries()
            assert len(entries) == 1
            assert entries[0].text == "hello"

    asyncio.run(_run())


def test_multiple_entries_newest_first() -> None:
    """list_entries returns entries newest first."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EntriesService(db_path=Path(tmp) / "test.db")
            await service.init_db()
            await service.create_entry(EntryCreate(text="first"))
            await service.create_entry(EntryCreate(text="second"))
            entries = await service.list_entries()
            assert entries[0].text == "second"
            assert entries[1].text == "first"

    asyncio.run(_run())


def test_list_empty_db() -> None:
    """list_entries returns empty list when DB is empty."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as tmp:
            service = EntriesService(db_path=Path(tmp) / "test.db")
            await service.init_db()
            entries = await service.list_entries()
            assert entries == []

    asyncio.run(_run())
