"""Application instance for uvicorn.

Entry point: uvicorn tg_central_hub_bot.webapp.app:app
"""

from tg_central_hub_bot.webapp.main import create_app

# Create application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn

    from tg_central_hub_bot.params.tg_central_hub_bot_params import get_webapp_params

    params = get_webapp_params()
    uvicorn.run(
        "tg_central_hub_bot.webapp.app:app",
        host=params.host,
        port=params.port,
        reload=params.debug,
    )
