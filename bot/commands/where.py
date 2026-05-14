from telegram import Update
from telegram.ext import ContextTypes


async def where_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None or update.effective_message is None:
        return
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id
    thread_display = thread_id if thread_id is not None else "—  (main chat / no topic)"
    await update.effective_message.reply_text(
        f"<b>Chat ID:</b> <code>{chat_id}</code>\n"
        f"<b>Thread ID:</b> <code>{thread_display}</code>",
        parse_mode="HTML",
    )
