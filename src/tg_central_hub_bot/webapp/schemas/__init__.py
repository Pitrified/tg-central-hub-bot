"""Webapp schemas module."""

from tg_central_hub_bot.webapp.schemas.auth_schemas import GoogleUserInfo
from tg_central_hub_bot.webapp.schemas.auth_schemas import LoginResponse
from tg_central_hub_bot.webapp.schemas.auth_schemas import SessionData
from tg_central_hub_bot.webapp.schemas.auth_schemas import UserResponse
from tg_central_hub_bot.webapp.schemas.common_schemas import ErrorResponse
from tg_central_hub_bot.webapp.schemas.common_schemas import HealthResponse

__all__ = [
    "ErrorResponse",
    "GoogleUserInfo",
    "HealthResponse",
    "LoginResponse",
    "SessionData",
    "UserResponse",
]
