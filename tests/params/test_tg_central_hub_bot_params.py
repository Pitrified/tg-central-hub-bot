"""Test the TgCentralHubBotParams class."""

from tg_central_hub_bot.params.tg_central_hub_bot_params import TgCentralHubBotParams
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_tg_central_hub_bot_params
from tg_central_hub_bot.params.tg_central_hub_bot_paths import TgCentralHubBotPaths
from tg_central_hub_bot.params.sample_params import SampleParams


def test_tg_central_hub_bot_params_singleton() -> None:
    """Test that TgCentralHubBotParams is a singleton."""
    params1 = TgCentralHubBotParams()
    params2 = TgCentralHubBotParams()
    assert params1 is params2
    assert get_tg_central_hub_bot_params() is params1


def test_tg_central_hub_bot_params_init() -> None:
    """Test initialization of TgCentralHubBotParams."""
    params = TgCentralHubBotParams()
    assert isinstance(params.paths, TgCentralHubBotPaths)
    assert isinstance(params.sample, SampleParams)


def test_tg_central_hub_bot_params_str() -> None:
    """Test string representation."""
    params = TgCentralHubBotParams()
    s = str(params)
    assert "TgCentralHubBotParams:" in s
    assert "TgCentralHubBotPaths:" in s
    assert "SampleParams:" in s
