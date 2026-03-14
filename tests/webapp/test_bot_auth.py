"""Tests for bot_auth.py - verify_bot_api_key FastAPI dependency."""

from collections.abc import AsyncGenerator
from collections.abc import Generator
from contextlib import asynccontextmanager
from pathlib import Path
import tempfile

from fastapi import FastAPI
from fastapi import status
from fastapi.testclient import TestClient
import pytest

from tg_central_hub_bot.webapp.internal.entries_router import router as internal_router
from tg_central_hub_bot.webapp.services.entries_service import EntriesService


def _make_backend_app(api_key: str, db_path: Path) -> FastAPI:
    """Create a minimal backend app with the internal router."""

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncGenerator[None]:
        service = EntriesService(db_path=db_path)
        await service.init_db()
        app.state.entries_service = service
        app.state.bot_api_key = api_key.encode()
        yield

    app = FastAPI(lifespan=_lifespan)
    app.include_router(internal_router)
    return app


@pytest.fixture
def backend_api_key() -> str:
    """Return a test bot API key."""
    return "testkey1234567890abcdef"


@pytest.fixture
def backend_client(backend_api_key: str) -> Generator[TestClient]:
    """Create a TestClient for the backend app backed by a temp DB."""
    with tempfile.TemporaryDirectory() as tmp:
        app = _make_backend_app(backend_api_key, Path(tmp) / "test.db")
        with TestClient(app) as client:
            yield client


def test_valid_key_creates_entry(
    backend_client: TestClient,
    backend_api_key: str,
) -> None:
    """Valid API key allows POST /internal/entries."""
    response = backend_client.post(
        "/internal/entries",
        json={"text": "hello world"},
        headers={"Authorization": f"Bearer {backend_api_key}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["text"] == "hello world"
    assert data["id"] == 1


def test_wrong_key_is_forbidden(backend_client: TestClient) -> None:
    """Wrong API key returns 403 Forbidden."""
    response = backend_client.post(
        "/internal/entries",
        json={"text": "hello"},
        headers={"Authorization": "Bearer wrongkey"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_missing_auth_header_is_rejected(backend_client: TestClient) -> None:
    """Missing Authorization header returns 401 (HTTPBearer requirement)."""
    response = backend_client.post(
        "/internal/entries",
        json={"text": "hello"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_empty_text_is_rejected(
    backend_client: TestClient,
    backend_api_key: str,
) -> None:
    """Empty text body returns 422 Unprocessable Content."""
    response = backend_client.post(
        "/internal/entries",
        json={"text": ""},
        headers={"Authorization": f"Bearer {backend_api_key}"},
    )
    assert response.status_code == 422
