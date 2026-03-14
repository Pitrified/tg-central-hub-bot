"""Bot API key authentication dependency for internal endpoints.

The expected key (bytes) is stored in request.app.state.bot_api_key during
application lifespan. Comparison uses hmac.compare_digest to prevent
timing-based side-channel attacks.
"""

import hmac
from typing import Annotated

from fastapi import HTTPException
from fastapi import Request
from fastapi import Security
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

_bearer = HTTPBearer()


def verify_bot_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(_bearer)],
    request: Request,
) -> None:
    """Verify the bot API key using constant-time comparison.

    Args:
        credentials: Bearer token extracted from the Authorization header.
        request: Incoming request (used to read expected key from app state).

    Raises:
        HTTPException: 403 if the key is missing or does not match.
    """
    expected: bytes = request.app.state.bot_api_key
    provided: bytes = credentials.credentials.encode()
    if not hmac.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
