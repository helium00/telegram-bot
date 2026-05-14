from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from telegram import User

from bot.services.moderation import is_admin, mention_html, parse_duration


def test_mention_html_uses_full_name():
    user = Mock(spec=User)
    user.full_name = "Ivan Zara"
    user.id = 12345
    assert mention_html(user) == '<a href="tg://user?id=12345">Ivan Zara</a>'


def test_mention_html_fallback_when_no_name():
    user = Mock(spec=User)
    user.full_name = None
    user.id = 99
    assert mention_html(user) == '<a href="tg://user?id=99">User 99</a>'


def test_parse_duration_hours():
    result = parse_duration("2h")
    assert result is not None
    diff = (result - datetime.now(timezone.utc)).total_seconds()
    assert 7190 < diff < 7210


def test_parse_duration_minutes():
    result = parse_duration("30m")
    assert result is not None
    diff = (result - datetime.now(timezone.utc)).total_seconds()
    assert 1790 < diff < 1810


def test_parse_duration_days():
    result = parse_duration("1d")
    assert result is not None
    diff = (result - datetime.now(timezone.utc)).total_seconds()
    assert 86390 < diff < 86410


def test_parse_duration_invalid_returns_none():
    assert parse_duration("forever") is None
    assert parse_duration("abc") is None
    assert parse_duration("") is None


@pytest.mark.asyncio
async def test_is_admin_true_for_administrator():
    bot = AsyncMock()
    member = Mock()
    member.status = "administrator"
    bot.get_chat_member.return_value = member
    assert await is_admin(bot, -1001234567890, 999) is True


@pytest.mark.asyncio
async def test_is_admin_true_for_creator():
    bot = AsyncMock()
    member = Mock()
    member.status = "creator"
    bot.get_chat_member.return_value = member
    assert await is_admin(bot, -1001234567890, 1) is True


@pytest.mark.asyncio
async def test_is_admin_false_for_member():
    bot = AsyncMock()
    member = Mock()
    member.status = "member"
    bot.get_chat_member.return_value = member
    assert await is_admin(bot, -1001234567890, 42) is False
