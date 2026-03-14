"""API v1 entries router - read-only list endpoint for the HTMX frontend.

Requires Google OAuth authentication (same as the rest of the frontend).
The entries data is written exclusively through the internal backend router.
"""

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status

from tg_central_hub_bot.webapp.core.dependencies import get_current_user
from tg_central_hub_bot.webapp.schemas.auth_schemas import SessionData
from tg_central_hub_bot.webapp.schemas.entry_schemas import EntryRead
from tg_central_hub_bot.webapp.services.entries_service import EntriesService

router = APIRouter(prefix="/entries", tags=["entries"])


def _get_entries_service(request: Request) -> EntriesService:
    service = getattr(request.app.state, "entries_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Entries service not configured",
        )
    return service  # type: ignore[return-value]


@router.get(
    "/",
    summary="List entries",
    description="Returns all entries, newest first. Requires authentication.",
)
async def list_entries(
    _user: Annotated[SessionData, Depends(get_current_user)],
    service: Annotated[EntriesService, Depends(_get_entries_service)],
) -> list[EntryRead]:
    """Return all entries from the database.

    Args:
        _user: Authenticated user session (dependency enforces auth).
        service: EntriesService from app state.

    Returns:
        List of entries, newest first.
    """
    return await service.list_entries()
