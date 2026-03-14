"""Sample app configuration model."""

from pathlib import Path

from pydantic import SecretStr

from tg_central_hub_bot.data_models.basemodel_kwargs import BaseModelKwargs


class SampleAppConfig(BaseModelKwargs):
    """Sample app configuration: SQLite path and bot-to-backend API key."""

    db_path: Path
    bot_api_key: SecretStr
