import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.config import settings
from bot.services.moderation import mention_html
from bot.telegram.topics import get_thread_id

logger = structlog.get_logger(__name__)

_WELCOME_TEXT = (
    "👋 Welcome to <b>Sagunto Hub</b>, {mention}!\n\n"
    "This is your community space for expats and locals in Sagunto.\n\n"
    "📌 <b>Quick guide:</b>\n"
    "• Use the correct topic for each type of message\n"
    "• Be respectful and constructive\n"
    "• Commands: /help for the full list\n\n"
    "Enjoy! 🌞"
)


async def welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.new_chat_members:
        return
    if settings.telegram_group_id == 0:
        return

    thread_id = get_thread_id("general")

    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        text = _WELCOME_TEXT.format(mention=mention_html(member))
        await context.bot.send_message(
            chat_id=settings.telegram_group_id,
            message_thread_id=thread_id,
            text=text,
            parse_mode="HTML",
        )
        logger.info("member_welcomed", user_id=member.id)
