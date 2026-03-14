"""Internal API module (bot-to-backend, never tunneled)."""

from tg_central_hub_bot.webapp.internal.entries_router import (
    router as entries_internal_router,
)

__all__ = ["entries_internal_router"]
