from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from telegram import Bot, ChatPermissions, User
from telegram.error import TelegramError

logger = structlog.get_logger(__name__)

MUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
)

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def is_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except TelegramError:
        return False


def parse_duration(text: str) -> Optional[datetime]:
    """Parse '30m', '2h', '1d' into an absolute UTC datetime."""
    _units = {"m": 60, "h": 3600, "d": 86400}
    if len(text) >= 2 and text[-1] in _units:
        try:
            amount = int(text[:-1])
            return datetime.now(timezone.utc) + timedelta(seconds=amount * _units[text[-1]])
        except ValueError:
            pass
    return None


def mention_html(user: User) -> str:
    name = user.full_name or f"User {user.id}"
    return f'<a href="tg://user?id={user.id}">{name}</a>'
