"""Webapp routers module."""

from tg_central_hub_bot.webapp.routers.auth_router import router as auth_router
from tg_central_hub_bot.webapp.routers.health_router import router as health_router
from tg_central_hub_bot.webapp.routers.pages_router import router as pages_router

__all__ = [
    "auth_router",
    "health_router",
    "pages_router",
]
