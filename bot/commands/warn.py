import structlog
from sqlalchemy import func, select
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.database.models import Warning
from bot.database.session import AsyncSessionLocal
from bot.services.moderation import is_admin, mention_html

logger = structlog.get_logger(__name__)


async def warn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("Reply to a message to warn that user.")
        return

    target = update.message.reply_to_message.from_user
    reason = " ".join(context.args) if context.args else "No reason given"

    async with AsyncSessionLocal() as session:
        warning = Warning(
            user_id=target.id,
            warned_by=update.effective_user.id,
            reason=reason,
        )
        session.add(warning)
        await session.commit()

        count_result = await session.execute(
            select(func.count()).where(Warning.user_id == target.id)
        )
        warn_count = count_result.scalar_one()

    logger.info("user_warned", target_id=target.id, by=update.effective_user.id, count=warn_count)

    if warn_count >= settings.max_warnings:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await update.message.reply_text(
            f"🚫 {mention_html(target)} has been <b>banned</b> after {warn_count} warnings.\n<b>Last reason:</b> {reason}",
            parse_mode="HTML",
        )
        logger.info("user_auto_banned", target_id=target.id, warn_count=warn_count)
    else:
        await update.message.reply_text(
            f"⚠️ {mention_html(target)} warned ({warn_count}/{settings.max_warnings}).\n<b>Reason:</b> {reason}",
            parse_mode="HTML",
        )
