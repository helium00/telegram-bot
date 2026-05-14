import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import is_admin

logger = structlog.get_logger(__name__)


async def delete_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("Reply to a message to delete it.")
        return

    await update.message.reply_to_message.delete()
    await update.message.delete()
    logger.info("message_deleted", by=update.effective_user.id)
