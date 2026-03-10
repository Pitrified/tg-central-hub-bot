"""Tests for BotParams."""

import pytest

from tg_central_hub_bot.config.bot_config import BotConfig
from tg_central_hub_bot.params.bot_params import BotParams
from tg_central_hub_bot.params.bot_params import MissingBotTokenError
from tg_central_hub_bot.params.env_type import EnvLocationType
from tg_central_hub_bot.params.env_type import EnvStageType
from tg_central_hub_bot.params.env_type import EnvType


def _make_env_type() -> EnvType:
    """Return a minimal dev/local EnvType for tests."""
    return EnvType(stage=EnvStageType.DEV, location=EnvLocationType.LOCAL)


def test_bot_params_loads_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """BotParams loads token from environment."""
    monkeypatch.setenv("BOT_TOKEN", "test-token-123")
    params = BotParams(env_type=_make_env_type())
    config = params.to_config()
    assert config.token.get_secret_value() == "test-token-123"


def test_bot_params_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """BotParams raises MissingBotTokenError if BOT_TOKEN is missing."""
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    with pytest.raises(MissingBotTokenError, match="BOT_TOKEN"):
        BotParams(env_type=_make_env_type())


def test_bot_params_str_fully_masked(monkeypatch: pytest.MonkeyPatch) -> None:
    """Token is fully masked in string representation of BotParams."""
    monkeypatch.setenv("BOT_TOKEN", "123456:ABCDEFxyz")
    params = BotParams(env_type=_make_env_type())
    s = str(params)
    assert "123456" not in s
    assert "ABCDEFxyz" not in s
    assert "******" in s


def test_to_config_returns_bot_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """to_config() returns a BotConfig instance."""
    monkeypatch.setenv("BOT_TOKEN", "real-token-abc")
    params = BotParams(env_type=_make_env_type())
    config = params.to_config()
    assert isinstance(config, BotConfig)


def test_to_config_token_masked_in_str(monkeypatch: pytest.MonkeyPatch) -> None:
    """SecretStr masks the token in str() of BotConfig."""
    monkeypatch.setenv("BOT_TOKEN", "real-token-abc")
    params = BotParams(env_type=_make_env_type())
    config = params.to_config()
    assert "real-token-abc" not in str(config.token)
    assert config.token.get_secret_value() == "real-token-abc"


def test_to_config_parse_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    """to_config() forwards parse_mode correctly."""
    monkeypatch.setenv("BOT_TOKEN", "some-token")
    params = BotParams(env_type=_make_env_type())
    assert params.to_config().parse_mode == "HTML"
