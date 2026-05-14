from telegram import Update
from telegram.ext import ContextTypes

HELP_TEXT = (
    "🤖 <b>Sagunto Hub Bot — Commands</b>\n\n"
    "/start — Welcome message\n"
    "/help — Show this help\n"
    "/id — Show the current chat ID\n"
    "/where — Show the current chat ID and topic thread ID\n\n"
    "<b>Automatic content</b>\n"
    "• Daily weather → Activities\n"
    "• Spanish Word of the Day → Spanish Learning\n"
    "• English Word of the Day → English Learning\n"
    "• Local events → Events\n"
    "• Bureaucracy reminders → Bureaucracy"
)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is None:
        return
    await update.effective_message.reply_text(HELP_TEXT, parse_mode="HTML")
