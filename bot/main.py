import asyncio

import structlog
from sqlalchemy import text
from telegram.ext import Application, CommandHandler

from bot.commands.help import help_handler
from bot.commands.id import id_handler
from bot.commands.start import start_handler
from bot.commands.where import where_handler
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


async def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    # Run in a thread because Alembic uses sync connections
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.upgrade, cfg, "head")


async def main() -> None:
    configure_logging(log_level=settings.log_level, json_logs=settings.is_production)
    logger.info("starting", env=settings.app_env)

    await run_migrations()
    logger.info("migrations_applied")

    # Verify DB connectivity
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("database_connected")

    application = Application.builder().token(settings.telegram_bot_token).build()

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("id", id_handler))
    application.add_handler(CommandHandler("where", where_handler))

    bot = application.bot
    tg_client = TelegramClient(bot)

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

    logger.info("polling_started")
    await application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
