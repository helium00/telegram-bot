import hashlib

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import PostedItem

logger = structlog.get_logger(__name__)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


async def is_duplicate(
    session: AsyncSession,
    source_name: str,
    external_id: str,
    content_hash: str,
) -> bool:
    result = await session.execute(
        select(PostedItem.id).where(
            (PostedItem.source_name == source_name) & (PostedItem.external_id == external_id)
            | (PostedItem.content_hash == content_hash)
        )
    )
    found = result.scalar_one_or_none() is not None
    if found:
        logger.debug("duplicate_skipped", source=source_name, external_id=external_id)
    return found


async def mark_posted(
    session: AsyncSession,
    source_name: str,
    external_id: str,
    content_hash: str,
    topic_name: str,
    title: str | None = None,
) -> None:
    item = PostedItem(
        source_name=source_name,
        external_id=external_id,
        title=title,
        content_hash=content_hash,
        topic_name=topic_name,
    )
    session.add(item)
    await session.commit()
    logger.debug("marked_posted", source=source_name, external_id=external_id)
