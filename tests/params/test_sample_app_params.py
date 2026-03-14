"""Tests for SampleAppParams."""

from pathlib import Path

import pytest

from tg_central_hub_bot.config.sample_app_config import SampleAppConfig
from tg_central_hub_bot.params.env_type import EnvLocationType
from tg_central_hub_bot.params.env_type import EnvStageType
from tg_central_hub_bot.params.env_type import EnvType
from tg_central_hub_bot.params.sample_app_params import MissingBotApiKeyError
from tg_central_hub_bot.params.sample_app_params import SampleAppParams


def _dev_env() -> EnvType:
    return EnvType(stage=EnvStageType.DEV, location=EnvLocationType.LOCAL)


def test_sample_app_params_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """SampleAppParams loads BOT_API_KEY and SAMPLE_DB_PATH from environment."""
    monkeypatch.setenv("BOT_API_KEY", "apikey123")
    monkeypatch.setenv("SAMPLE_DB_PATH", "data/test.db")
    params = SampleAppParams(env_type=_dev_env())
    assert params.db_path == Path("data/test.db")


def test_sample_app_params_default_db_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """SampleAppParams uses data/sample.db as default db path."""
    monkeypatch.setenv("BOT_API_KEY", "apikey123")
    monkeypatch.delenv("SAMPLE_DB_PATH", raising=False)
    params = SampleAppParams(env_type=_dev_env())
    assert params.db_path == Path("data/sample.db")


def test_sample_app_params_missing_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """SampleAppParams raises MissingBotApiKeyError when BOT_API_KEY is absent."""
    monkeypatch.delenv("BOT_API_KEY", raising=False)
    with pytest.raises(MissingBotApiKeyError, match="BOT_API_KEY"):
        SampleAppParams(env_type=_dev_env())


def test_sample_app_params_to_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """to_config() returns a SampleAppConfig instance."""
    monkeypatch.setenv("BOT_API_KEY", "mykey")
    params = SampleAppParams(env_type=_dev_env())
    cfg = params.to_config()
    assert isinstance(cfg, SampleAppConfig)
    assert cfg.bot_api_key.get_secret_value() == "mykey"


def test_sample_app_params_str_masks_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """bot_api_key is masked in __str__."""
    monkeypatch.setenv("BOT_API_KEY", "secretkey9876")
    params = SampleAppParams(env_type=_dev_env())
    assert "secretkey9876" not in str(params)
    assert "******" in str(params)
