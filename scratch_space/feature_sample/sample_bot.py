"""Sample bot: /add <text> command.

Sends text to the internal backend (127.0.0.1:8001) via httpx and
confirms the saved entry to the user.

Run with:
    uv run python scratch_space/feature_sample/sample_bot.py
"""

import os

import httpx
from loguru import logger as lg
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from tg_central_hub_bot.params.load_env import load_env
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params

BACKEND_URL = "http://127.0.0.1:8001/internal/entries"


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if update.message is None:
        return
    await update.message.reply_text(
        "Hello! Send /add <text> to save an entry.\n"
        "Visit https://app.pitrified.qzz.io/entries to see all saved entries.",
    )


async def add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /add <text> command.

    Calls the internal backend with the bot API key and reports the result.
    """
    if update.message is None:
        return

    args = context.args or []
    text = " ".join(args).strip()

    if not text:
        await update.message.reply_text("Usage: /add <text>")
        return

    bot_api_key: str = context.bot_data.get("bot_api_key", "")
    if not bot_api_key:
        lg.error("bot_api_key not set in bot_data")
        msg = "Bot configuration error - please contact the admin."
        await update.message.reply_text(msg)
        return

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                BACKEND_URL,
                json={"text": text},
                headers={"Authorization": f"Bearer {bot_api_key}"},
            )
        response.raise_for_status()
        data = response.json()
        await update.message.reply_text(f"Saved entry #{data['id']}: {data['text']}")
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        body = exc.response.text
        lg.error(f"Backend returned error {status}: {body}")
        await update.message.reply_text("Failed to save entry - backend error.")
    except httpx.RequestError as exc:
        lg.error(f"Backend request failed: {exc}")
        await update.message.reply_text("Failed to reach the backend - is it running?")


def main() -> None:
    """Start the bot using polling."""
    load_env()

    bot_api_key = os.getenv("BOT_API_KEY", "")
    if not bot_api_key:
        msg = "BOT_API_KEY is not set - cannot authenticate with the backend"
        raise RuntimeError(msg)

    bot_params = get_bot_params()
    token = bot_params.to_config().token.get_secret_value()

    application = ApplicationBuilder().token(token).build()
    # Store bot_api_key in bot_data so handlers can access it
    application.bot_data["bot_api_key"] = bot_api_key

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add))

    lg.info("Sample bot starting (polling mode)")
    application.run_polling()


if __name__ == "__main__":
    main()
