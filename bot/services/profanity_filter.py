import re
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.database.models import CustomBadWord
from bot.database.session import AsyncSessionLocal

logger = structlog.get_logger(__name__)

_TOKENIZE = re.compile(r"[a-záéíóúüñàèìòùç\w]+")


class ProfanityFilter:
    _cache: Optional[set[str]] = None

    async def _load(self) -> set[str]:
        if ProfanityFilter._cache is None:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(CustomBadWord.word))
                ProfanityFilter._cache = {row[0].lower() for row in result.all()}
        return ProfanityFilter._cache

    async def contains_profanity(self, text: str) -> bool:
        wordset = await self._load()
        tokens = _TOKENIZE.findall(text.lower())
        return any(token in wordset for token in tokens)

    async def add_word(self, word: str, added_by: int) -> bool:
        try:
            async with AsyncSessionLocal() as session:
                session.add(CustomBadWord(word=word.lower(), added_by=added_by))
                await session.commit()
            ProfanityFilter._cache = None
            return True
        except IntegrityError:
            return False

    async def remove_word(self, word: str) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CustomBadWord).where(CustomBadWord.word == word.lower())
            )
            entry = result.scalar_one_or_none()
            if entry is None:
                return False
            await session.delete(entry)
            await session.commit()
        ProfanityFilter._cache = None
        return True

    async def list_words(self) -> list[str]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CustomBadWord.word).order_by(CustomBadWord.word)
            )
            return [row[0] for row in result.all()]


profanity_filter = ProfanityFilter()
