from telegram import Update
from telegram.ext import ContextTypes


async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.effective_message is None:
        return
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(
        f"<b>Chat ID:</b> <code>{chat_id}</code>",
        parse_mode="HTML",
    )
