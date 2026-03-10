"""TgCentralHubBot project params.

Parameters are actual value of the config.

The class is a singleton, so it can be accessed from anywhere in the code.

There is a parameter regarding the environment type (stage and location), which
is used to load different paths and other parameters based on the environment.
"""

from loguru import logger as lg

from tg_central_hub_bot.metaclasses.singleton import Singleton
from tg_central_hub_bot.params.bot_params import BotParams
from tg_central_hub_bot.params.env_type import EnvType
from tg_central_hub_bot.params.sample_params import SampleParams
from tg_central_hub_bot.params.tg_central_hub_bot_paths import TgCentralHubBotPaths
from tg_central_hub_bot.params.webapp import WebappParams


class TgCentralHubBotParams(metaclass=Singleton):
    """TgCentralHubBot project parameters."""

    def __init__(self) -> None:
        """Load the TgCentralHubBot params."""
        lg.info("Loading TgCentralHubBot params")
        self.set_env_type()

    def set_env_type(self, env_type: EnvType | None = None) -> None:
        """Set the environment type.

        Args:
            env_type (EnvType | None): The environment type.
                If None, it will be set from the environment variables.
                Defaults to None.
        """
        if env_type is not None:
            self.env_type = env_type
        else:
            self.env_type = EnvType.from_env_var()
        self.load_config()

    def load_config(self) -> None:
        """Load the tg_central_hub_bot configuration."""
        self.paths = TgCentralHubBotPaths(env_type=self.env_type)
        self.sample = SampleParams()
        self.webapp = WebappParams(
            stage=self.env_type.stage,
            location=self.env_type.location,
        )
        self.bot = BotParams(env_type=self.env_type)

    def __str__(self) -> str:
        """Return the string representation of the object."""
        s = "TgCentralHubBotParams:"
        s += f"\n{self.paths}"
        s += f"\n{self.sample}"
        s += f"\n{self.webapp}"
        s += f"\n{self.bot}"
        return s

    def __repr__(self) -> str:
        """Return the string representation of the object."""
        return str(self)


def get_tg_central_hub_bot_params() -> TgCentralHubBotParams:
    """Get the tg_central_hub_bot params."""
    return TgCentralHubBotParams()


def get_tg_central_hub_bot_paths() -> TgCentralHubBotPaths:
    """Get the tg_central_hub_bot paths."""
    return get_tg_central_hub_bot_params().paths


def get_webapp_params() -> WebappParams:
    """Get the webapp params."""
    return get_tg_central_hub_bot_params().webapp


def get_bot_params() -> BotParams:
    """Get the bot params."""
    return get_tg_central_hub_bot_params().bot
