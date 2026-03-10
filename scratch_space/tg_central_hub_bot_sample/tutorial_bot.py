"""Tutorial bot sample — PTB v20 style.

Based on https://gitlab.com/Athamaxy/telegram-bot-tutorial/-/blob/main/TutorialBot.py
Handler logic is preserved verbatim; only main() has been updated to:
  - call load_env() to populate env vars from ~/cred/
  - load the token via get_bot_params() instead of a hardcoded string
  - use loguru instead of stdlib logging
"""

from loguru import logger as lg
from telegram import Update
from telegram.ext import ApplicationBuilder
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters

from tg_central_hub_bot.params.load_env import load_env
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params

# ---------------------------------------------------------------------------
# Handlers (preserved verbatim from the tutorial)
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("Hi! I am a tutorial bot.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user's message back."""
    await update.message.reply_text(update.message.text)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Start the bot."""
    load_env()
    bot_params = get_bot_params()
    lg.info(f"Starting bot: {bot_params}")

    app = (
        ApplicationBuilder()
        .token(bot_params.to_config().token.get_secret_value())
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    lg.info("Polling …")
    app.run_polling()


if __name__ == "__main__":
    main()
