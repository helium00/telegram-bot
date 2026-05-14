import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import (
    FULL_PERMISSIONS,
    MUTE_PERMISSIONS,
    is_admin,
    mention_html,
    parse_duration,
)

logger = structlog.get_logger(__name__)


async def mute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("Reply to a message to mute that user.")
        return

    target = update.message.reply_to_message.from_user
    until_date = None
    args = list(context.args or [])

    if args:
        until_date = parse_duration(args[0])
        if until_date:
            args.pop(0)

    reason = " ".join(args) if args else "No reason given"
    duration_note = (
        f" until {until_date.strftime('%Y-%m-%d %H:%M UTC')}" if until_date else " indefinitely"
    )

    await context.bot.restrict_chat_member(
        update.effective_chat.id, target.id, MUTE_PERMISSIONS, until_date=until_date
    )
    await update.message.reply_text(
        f"🔇 {mention_html(target)} has been muted{duration_note}.\n<b>Reason:</b> {reason}",
        parse_mode="HTML",
    )
    logger.info("user_muted", target_id=target.id, by=update.effective_user.id, until=str(until_date))


async def unmute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not update.message.reply_to_message or not update.message.reply_to_message.from_user:
        await update.message.reply_text("Reply to a message to unmute that user.")
        return

    target = update.message.reply_to_message.from_user
    await context.bot.restrict_chat_member(update.effective_chat.id, target.id, FULL_PERMISSIONS)
    await update.message.reply_text(
        f"🔊 {mention_html(target)} has been unmuted.",
        parse_mode="HTML",
    )
    logger.info("user_unmuted", target_id=target.id, by=update.effective_user.id)
