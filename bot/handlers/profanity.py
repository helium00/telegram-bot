import structlog
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.config import settings
from bot.services.moderation import is_admin, mention_html
from bot.services.profanity_filter import profanity_filter

logger = structlog.get_logger(__name__)


async def profanity_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not settings.profanity_enabled:
        return
    if await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return

    text = update.message.text or ""
    if not await profanity_filter.contains_profanity(text):
        return

    try:
        await update.message.delete()
    except TelegramError:
        logger.warning("profanity_delete_failed", message_id=update.message.message_id)

    mention = mention_html(update.effective_user)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.message.message_thread_id,
        text=f"⚠️ {mention}, attento al linguaggio!",
        parse_mode="HTML",
    )
    logger.info("profanity_deleted", user_id=update.effective_user.id)
