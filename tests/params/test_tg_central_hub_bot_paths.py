"""Test the tg_central_hub_bot paths."""

from tg_central_hub_bot.params.tg_central_hub_bot_params import get_tg_central_hub_bot_paths


def test_tg_central_hub_bot_paths() -> None:
    """Test the tg_central_hub_bot paths."""
    tg_central_hub_bot_paths = get_tg_central_hub_bot_paths()
    assert tg_central_hub_bot_paths.src_fol.name == "tg_central_hub_bot"
    assert tg_central_hub_bot_paths.root_fol.name == "tg-central-hub-bot"
    assert tg_central_hub_bot_paths.data_fol.name == "data"
