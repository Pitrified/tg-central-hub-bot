"""Internal router: POST /internal/entries (bot to backend only).

This router is mounted only on the backend app (port 8001) which is
bound to 127.0.0.1 and never exposed via the Cloudflare tunnel.
Every request must carry a valid bot API key.
"""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Request

from tg_central_hub_bot.webapp.core.bot_auth import verify_bot_api_key
from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryCreate
from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryRead
from tg_central_hub_bot.webapp.services.entries_service import EntriesService

router = APIRouter(prefix="/internal", tags=["internal"])


def _get_entries_service(request: Request) -> EntriesService:
    return request.app.state.entries_service  # type: ignore[no-any-return]


@router.post(
    "/entries",
    status_code=201,
    dependencies=[Depends(verify_bot_api_key)],
    summary="Create entry (bot auth required)",
    description=(
        "Authenticated bot-to-backend endpoint. "
        "Inserts a new text entry into the SQLite database."
    ),
)
async def create_entry(
    body: EntryCreate,
    service: Annotated[EntriesService, Depends(_get_entries_service)],
) -> EntryRead:
    """Create a new entry.

    Args:
        body: Entry text payload.
        service: EntriesService from app state.

    Returns:
        The created entry record.
    """
    return await service.create_entry(body)
