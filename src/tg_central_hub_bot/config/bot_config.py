"""Bot configuration model."""

from pydantic import SecretStr

from tg_central_hub_bot.data_models.basemodel_kwargs import BaseModelKwargs


class BotConfig(BaseModelKwargs):
    """Telegram bot configuration model."""

    token: SecretStr
    parse_mode: str = "HTML"
