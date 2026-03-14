"""Backend FastAPI app factory.

Bind to 127.0.0.1:8001 only - this app is never exposed via the
Cloudflare tunnel and is only reachable on the local machine.

Entry point: uvicorn tg_central_hub_bot.webapp.backend_app:backend_app
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger as lg

from tg_central_hub_bot.config.sample_app_config import SampleAppConfig
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_sample_app_params
from tg_central_hub_bot.webapp.internal import entries_internal_router
from tg_central_hub_bot.webapp.services.entries_service import EntriesService


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Startup and shutdown for the backend app."""
    config: SampleAppConfig = app.state.config

    service = EntriesService(db_path=config.db_path)
    await service.init_db()
    app.state.entries_service = service
    app.state.bot_api_key = config.bot_api_key.get_secret_value().encode()
    lg.info("Backend app started; DB initialized")

    yield

    lg.info("Backend app shutdown complete")


def create_backend_app(config: SampleAppConfig | None = None) -> FastAPI:
    """Create and configure the backend FastAPI app.

    Args:
        config: Sample app configuration. If None, loads from environment.

    Returns:
        Configured FastAPI application instance.
    """
    if config is None:
        config = get_sample_app_params().to_config()

    app = FastAPI(
        title="Backend Internal API",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        lifespan=_lifespan,
    )
    app.state.config = config
    app.include_router(entries_internal_router)
    lg.info("Backend app created")
    return app


backend_app = create_backend_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "tg_central_hub_bot.webapp.backend_app:backend_app",
        host="127.0.0.1",
        port=8001,
        reload=False,
    )
