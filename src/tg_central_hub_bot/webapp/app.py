"""Application instance for uvicorn.

Entry point: uvicorn tg_central_hub_bot.webapp.app:app
"""

from tg_central_hub_bot.params.tg_central_hub_bot_params import (
    get_tg_central_hub_bot_params,
)
from tg_central_hub_bot.webapp.main import create_app

_p = get_tg_central_hub_bot_params()
_sample = _p.sample_app.to_config() if _p.sample_app is not None else None

app = create_app(sample_app_config=_sample)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "tg_central_hub_bot.webapp.app:app",
        host=_p.webapp.host,
        port=_p.webapp.port,
        reload=_p.webapp.debug,
    )
