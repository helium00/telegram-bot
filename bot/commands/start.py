from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message is None:
        return
    await update.effective_message.reply_text(
        "👋 <b>Welcome to Sagunto Hub Bot!</b>\n\n"
        "I automatically publish useful content into the right community topics.\n\n"
        "Use /help to see available commands.",
        parse_mode="HTML",
    )
