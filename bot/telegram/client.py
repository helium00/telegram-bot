import structlog
from telegram import Bot
from telegram.constants import ParseMode

from bot.config import settings
from bot.telegram.topics import get_thread_id

logger = structlog.get_logger(__name__)


class TelegramClient:
    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._group_id = settings.telegram_group_id

    async def send_to_topic(
        self,
        topic_name: str,
        text: str,
        parse_mode: str = ParseMode.HTML,
    ) -> None:
        thread_id = get_thread_id(topic_name)
        await self._bot.send_message(
            chat_id=self._group_id,
            message_thread_id=thread_id,
            text=text,
            parse_mode=parse_mode,
        )
        logger.info("message_sent", topic=topic_name, thread_id=thread_id, chars=len(text))
