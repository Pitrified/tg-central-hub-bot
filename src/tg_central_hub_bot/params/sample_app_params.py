"""Sample app runtime parameters."""

import os
from pathlib import Path

from loguru import logger as lg
from pydantic import SecretStr

from tg_central_hub_bot.config.sample_app_config import SampleAppConfig
from tg_central_hub_bot.params.env_type import EnvType


class MissingBotApiKeyError(Exception):
    """Raised when the BOT_API_KEY environment variable is not set."""


class SampleAppParams:
    """Loads sample app parameters from environment variables."""

    def __init__(self, env_type: EnvType) -> None:
        """Load sample app parameters from environment variables."""
        lg.info("Loading SampleAppParams")
        self.env_type = env_type
        key = os.getenv("BOT_API_KEY")
        if not key:
            msg = "BOT_API_KEY environment variable is not set"
            raise MissingBotApiKeyError(msg)
        self._bot_api_key = SecretStr(key)
        raw_db = os.getenv("SAMPLE_DB_PATH", "data/sample.db")
        self.db_path = Path(raw_db)

    def to_config(self) -> SampleAppConfig:
        """Return SampleAppConfig populated from loaded parameters."""
        return SampleAppConfig(db_path=self.db_path, bot_api_key=self._bot_api_key)

    def __str__(self) -> str:
        """Return masked string representation."""
        s = "SampleAppParams:"
        s += f"\n  db_path: {self.db_path}"
        s += "\n  bot_api_key: ******"
        return s

    def __repr__(self) -> str:
        """Return repr delegating to __str__."""
        return str(self)
