"""Tutorial bot sample — PTB v22 style.

Based on https://gitlab.com/Athamaxy/telegram-bot-tutorial/-/blob/main/TutorialBot.py
Ported from TutorialBotOld.py (PTB v13) with the following changes:
  - Fully async handlers using async/await
  - ApplicationBuilder pattern (PTB v20+)
  - Global screaming state replaced with context.bot_data
  - ParseMode imported from telegram.constants
  - Token loaded via get_bot_params() instead of a hardcoded string
  - load_env() called to populate env vars from ~/cred/
  - loguru used instead of stdlib logging
"""

from loguru import logger as lg
from telegram import InlineKeyboardButton
from telegram import InlineKeyboardMarkup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder
from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters

from tg_central_hub_bot.params.load_env import load_env
from tg_central_hub_bot.params.tg_central_hub_bot_params import get_bot_params

# ---------------------------------------------------------------------------
# Menu text and button labels
# ---------------------------------------------------------------------------

FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."

NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

FIRST_MENU_MARKUP = InlineKeyboardMarkup(
    [[InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)]]
)
SECOND_MENU_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
        [
            InlineKeyboardButton(
                TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api"
            )
        ],
    ]
)

# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("Hi! I am a tutorial bot.")


async def help_command(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text("Help!")


async def scream(_update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /scream command - enable screaming mode."""
    context.bot_data["screaming"] = True


async def whisper(_update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /whisper command - disable screaming mode."""
    context.bot_data["screaming"] = False


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /menu command - send the first inline-keyboard menu."""
    await context.bot.send_message(
        update.message.from_user.id,
        FIRST_MENU,
        parse_mode=ParseMode.HTML,
        reply_markup=FIRST_MENU_MARKUP,
    )


async def button_tap(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button presses - navigate between menus."""
    query = update.callback_query
    data = query.data
    text = ""
    markup = None

    if data == NEXT_BUTTON:
        text = SECOND_MENU
        markup = SECOND_MENU_MARKUP
    elif data == BACK_BUTTON:
        text = FIRST_MENU
        markup = FIRST_MENU_MARKUP

    await query.answer()
    await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user's message; uppercase it when screaming mode is active."""
    if context.bot_data.get("screaming") and update.message.text:
        await context.bot.send_message(
            update.message.chat_id,
            update.message.text.upper(),
            entities=update.message.entities,
        )
    else:
        await update.message.copy(update.message.chat_id)


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
    app.add_handler(CommandHandler("scream", scream))
    app.add_handler(CommandHandler("whisper", whisper))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CallbackQueryHandler(button_tap))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    lg.info("Polling …")
    app.run_polling()


if __name__ == "__main__":
    main()
