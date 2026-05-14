from datetime import datetime, timezone
from typing import Any

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database.models import SourceRun
from bot.database.session import AsyncSessionLocal
from bot.services.duplicate_guard import compute_hash, is_duplicate, mark_posted
from bot.sources.base import BaseSource
from bot.telegram.client import TelegramClient

logger = structlog.get_logger(__name__)


async def _run_source(source: BaseSource, client: TelegramClient) -> None:
    async with AsyncSessionLocal() as session:
        run = SourceRun(
            source_name=source.name,
            status="ok",
            started_at=datetime.now(timezone.utc),
        )
        session.add(run)

        try:
            items = await source.fetch_items()
            for item in items:
                text = source.format_item(item)
                content_hash = compute_hash(text)
                external_id = item.get("id", content_hash)

                if await is_duplicate(session, source.name, str(external_id), content_hash):
                    continue

                await client.send_to_topic(source.target_topic, text)
                await mark_posted(
                    session,
                    source_name=source.name,
                    external_id=str(external_id),
                    content_hash=content_hash,
                    topic_name=source.target_topic,
                    title=item.get("title"),
                )

        except Exception as exc:
            run.status = "error"
            run.error_message = str(exc)
            logger.error("source_run_failed", source=source.name, error=str(exc))
        finally:
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()


def build_scheduler(sources: list[BaseSource], client: TelegramClient) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    schedule_map: dict[str, str] = {
        "weather": settings.schedule_weather,
        "spanish_word": settings.schedule_spanish_word,
        "english_word": settings.schedule_english_word,
        "events": settings.schedule_events,
        "bureaucracy": settings.schedule_bureaucracy,
    }

    for source in sources:
        cron_expr = schedule_map.get(source.name)
        if not cron_expr:
            logger.warning("no_schedule_for_source", source=source.name)
            continue

        parts = cron_expr.split()
        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
        scheduler.add_job(
            _run_source,
            trigger=trigger,
            args=[source, client],
            id=f"source_{source.name}",
            replace_existing=True,
        )
        logger.info("job_scheduled", source=source.name, cron=cron_expr)

    return scheduler
