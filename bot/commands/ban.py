import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import is_admin, mention_html

logger = structlog.get_logger(__name__)


async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("Reply to a message to ban that user.")
        return

    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "No reason given"

    await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    await update.message.reply_text(
        f"🔨 {mention_html(target)} has been banned.\n<b>Reason:</b> {reason}",
        parse_mode="HTML",
    )
    logger.info("user_banned", target_id=target.id, by=update.effective_user.id, reason=reason)
