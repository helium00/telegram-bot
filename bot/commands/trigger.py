import structlog
from telegram import Update
from telegram.ext import ContextTypes

from bot.services.moderation import is_admin, mention_html
from bot.services.scheduler import _run_source
from bot.sources.bureaucracy_source import BureaucracySource
from bot.sources.base import BaseSource
from bot.sources.events_source import EventsSource
from bot.sources.language_source import EnglishWordSource, SpanishWordSource
from bot.sources.weather_source import WeatherSource
from bot.telegram.client import TelegramClient

logger = structlog.get_logger(__name__)

_SOURCES: dict[str, type[BaseSource]] = {
    "weather": WeatherSource,
    "events": EventsSource,
    "bureaucracy": BureaucracySource,
    "spanish": SpanishWordSource,
    "english": EnglishWordSource,
}


async def trigger_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user or not update.effective_chat:
        return
    if not await is_admin(context.bot, update.effective_chat.id, update.effective_user.id):
        return

    if not context.args:
        names = ", ".join(f"<code>{n}</code>" for n in _SOURCES)
        await update.message.reply_text(
            f"Usage: /trigger &lt;source&gt;\n\nAvailable sources: {names}",
            parse_mode="HTML",
        )
        return

    name = context.args[0].lower()
    source_cls = _SOURCES.get(name)
    if source_cls is None:
        names = ", ".join(f"<code>{n}</code>" for n in _SOURCES)
        await update.message.reply_text(
            f"Unknown source <code>{name}</code>.\n\nAvailable: {names}",
            parse_mode="HTML",
        )
        return

    msg = await update.message.reply_text(f"⏳ Running <code>{name}</code>...", parse_mode="HTML")
    try:
        client = TelegramClient(context.bot)
        await _run_source(source_cls(), client)
        await msg.edit_text(f"✅ <code>{name}</code> completed.", parse_mode="HTML")
        logger.info("manual_trigger", source=name, by=update.effective_user.id)
    except Exception as exc:
        await msg.edit_text(
            f"❌ <code>{name}</code> failed: {exc}",
            parse_mode="HTML",
        )
        logger.error("manual_trigger_failed", source=name, error=str(exc))
