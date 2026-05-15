import asyncio

import structlog
from sqlalchemy import text
from telegram import Bot
from telegram.ext import Application, CommandHandler

from bot.commands.help import help_handler
from bot.commands.id import id_handler
from bot.commands.start import start_handler
from bot.commands.where import where_handler
from telegram.ext import MessageHandler, filters

from bot.commands.ban import ban_handler
from bot.commands.kick import kick_handler
from bot.commands.mute import mute_handler, unmute_handler
from bot.commands.warn import warn_handler
from bot.commands.delete_msg import delete_handler
from bot.commands.trigger import trigger_handler
from bot.handlers.profanity import profanity_handler
from bot.commands.badwords import addword_handler, removeword_handler, listwords_handler
from bot.handlers.welcome import welcome_handler
from bot.config import settings
from bot.database.session import engine
from bot.logging_config import configure_logging
from bot.services.scheduler import build_scheduler
from bot.sources.bureaucracy_source import BureaucracySource
from bot.sources.events_source import EventsSource
from bot.sources.language_source import EnglishWordSource, SpanishWordSource
from bot.sources.weather_source import WeatherSource
from bot.telegram.client import TelegramClient

logger = structlog.get_logger(__name__)


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")


async def post_init(application: Application) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("database_connected")

    tg_client = TelegramClient(application.bot)
    sources = [
        WeatherSource(),
        EventsSource(),
        BureaucracySource(),
        SpanishWordSource(),
        EnglishWordSource(),
    ]
    scheduler = build_scheduler(sources, tg_client)
    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))


def main() -> None:
    configure_logging(log_level=settings.log_level, json_logs=settings.is_production)
    logger.info("starting", env=settings.app_env)

    run_migrations()
    logger.info("migrations_applied")

    application = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("where", where_handler))
    application.add_handler(CommandHandler("ban", ban_handler))
    application.add_handler(CommandHandler("kick", kick_handler))
    application.add_handler(CommandHandler("mute", mute_handler))
    application.add_handler(CommandHandler("unmute", unmute_handler))
    application.add_handler(CommandHandler("warn", warn_handler))
    application.add_handler(CommandHandler("del", delete_handler))
    application.add_handler(CommandHandler("trigger", trigger_handler))
    application.add_handler(CommandHandler("addword", addword_handler))
    application.add_handler(CommandHandler("removeword", removeword_handler))
    application.add_handler(CommandHandler("listwords", listwords_handler))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, profanity_handler)
    )
    application.add_handler(
        MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_handler)
    )

    # Migrations close the event loop internally (asyncio.run in env.py).
    # PTB needs a running loop — create a fresh one before run_polling.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    logger.info("polling_started")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
