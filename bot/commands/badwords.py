import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import is_admin
from bot.services.profanity_filter import profanity_filter

logger = structlog.get_logger(__name__)


async def addword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /addword <word>")
        return

    word = context.args[0].lower()
    added = await profanity_filter.add_word(word, update.effective_user.id)
    if added:
        await update.message.reply_text(f"✅ Word '{word}' added to the filter.")
        logger.info("badword_added", word=word, by=update.effective_user.id)
    else:
        await update.message.reply_text(f"⚠️ Word '{word}' is already in the filter.")


async def removeword_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text("Usage: /removeword <word>")
        return

    word = context.args[0].lower()
    removed = await profanity_filter.remove_word(word)
    if removed:
        await update.message.reply_text(f"✅ Word '{word}' removed from the filter.")
        logger.info("badword_removed", word=word, by=update.effective_user.id)
    else:
        await update.message.reply_text(f"⚠️ Word '{word}' not found in the filter.")


async def listwords_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return

    words = await profanity_filter.list_words()
    if not words:
        await update.message.reply_text("The profanity filter is empty.")
        return

    word_list = "\n".join(f"• {w}" for w in words)
    await update.message.reply_text(
        f"🚫 <b>Filtered words ({len(words)}):</b>\n{word_list}",
        parse_mode="HTML",
    )
