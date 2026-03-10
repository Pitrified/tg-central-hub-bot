"""Sample config for the tg_central_hub_bot project."""

from pydantic import Field

from tg_central_hub_bot.data_models.basemodel_kwargs import BaseModelKwargs


class NestedModel(BaseModelKwargs):
    """Nested model for sample config."""

    some_str: str


class SampleConfig(BaseModelKwargs):
    """Sample config model."""

    some_int: int
    nested_model: NestedModel
    kwargs: dict = Field(default_factory=dict)
