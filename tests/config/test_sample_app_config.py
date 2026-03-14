"""Tests for SampleAppConfig."""

from pathlib import Path

from pydantic import SecretStr

from tg_central_hub_bot.config.sample_app_config import SampleAppConfig


def test_sample_app_config_init() -> None:
    """SampleAppConfig stores db_path and bot_api_key."""
    cfg = SampleAppConfig(
        db_path=Path("data/sample.db"),
        bot_api_key=SecretStr("testapikey"),
    )
    assert cfg.db_path == Path("data/sample.db")
    assert cfg.bot_api_key.get_secret_value() == "testapikey"


def test_sample_app_config_key_masked() -> None:
    """SecretStr masks the bot_api_key in string representation."""
    cfg = SampleAppConfig(
        db_path=Path("data/sample.db"),
        bot_api_key=SecretStr("supersecret"),
    )
    assert "supersecret" not in str(cfg)
