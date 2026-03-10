"""Telegram bot runtime parameters."""

import os

from pydantic import SecretStr

from tg_central_hub_bot.config.bot_config import BotConfig
from tg_central_hub_bot.params.env_type import EnvType


class MissingBotTokenError(Exception):
    """Raised when the BOT_TOKEN environment variable is not set."""


class BotParams:
    """Telegram bot runtime parameters."""

    def __init__(self, env_type: EnvType) -> None:
        """Load bot params from environment variables.

        Args:
            env_type: The environment type.

        Raises:
            MissingBotTokenError: If BOT_TOKEN is not set.
        """
        self.env_type = env_type
        token = os.getenv("BOT_TOKEN")
        if not token:
            msg = "BOT_TOKEN environment variable is not set"
            raise MissingBotTokenError(msg)
        self._token: SecretStr = SecretStr(token)
        self.parse_mode: str = "HTML"

    def to_config(self) -> BotConfig:
        """Convert to BotConfig with SecretStr token.

        Returns:
            BotConfig: The bot configuration.
        """
        return BotConfig(token=self._token, parse_mode=self.parse_mode)

    def __str__(self) -> str:
        """Return the string representation (token is always masked)."""
        return f"BotParams: token=******, parse_mode={self.parse_mode}"

    def __repr__(self) -> str:
        """Return the string representation of the object."""
        return str(self)
