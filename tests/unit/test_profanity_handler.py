import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.profanity import profanity_handler


def _make_update(text: str = "hello", is_bot: bool = False, thread_id: int = 5):
    user = MagicMock()
    user.id = 42
    user.full_name = "Test User"
    user.is_bot = is_bot

    message = MagicMock()
    message.text = text
    message.message_id = 100
    message.message_thread_id = thread_id
    message.delete = AsyncMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.message = message
    update.effective_user = user
    update.effective_chat = MagicMock()
    update.effective_chat.id = -1001234567890

    return update


def _make_context(is_admin: bool = False):
    bot = AsyncMock()
    bot.send_message = AsyncMock()
    context = MagicMock()
    context.bot = bot
    context.bot.get_chat_member = AsyncMock(
        return_value=MagicMock(status="administrator" if is_admin else "member")
    )
    return context


@pytest.mark.asyncio
async def test_profanity_handler_deletes_and_replies():
    update = _make_update(text="esto es una mierda!")
    context = _make_context(is_admin=False)

    with patch("bot.handlers.profanity.profanity_filter") as mock_pf, \
         patch("bot.handlers.profanity.settings") as mock_settings:
        mock_settings.profanity_enabled = True
        mock_pf.contains_profanity = AsyncMock(return_value=True)

        await profanity_handler(update, context)

        update.message.delete.assert_awaited_once()
        context.bot.send_message.assert_awaited_once()
        call_kwargs = context.bot.send_message.call_args.kwargs
        assert "attento al linguaggio" in call_kwargs["text"]
        assert call_kwargs["message_thread_id"] == 5


@pytest.mark.asyncio
async def test_profanity_handler_skips_clean_message():
    update = _make_update(text="good morning!")
    context = _make_context(is_admin=False)

    with patch("bot.handlers.profanity.profanity_filter") as mock_pf, \
         patch("bot.handlers.profanity.settings") as mock_settings:
        mock_settings.profanity_enabled = True
        mock_pf.contains_profanity = AsyncMock(return_value=False)

        await profanity_handler(update, context)

        update.message.delete.assert_not_awaited()
        context.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_profanity_handler_skips_admin():
    update = _make_update(text="mierda!")
    context = _make_context(is_admin=True)

    with patch("bot.handlers.profanity.profanity_filter") as mock_pf, \
         patch("bot.handlers.profanity.settings") as mock_settings:
        mock_settings.profanity_enabled = True
        mock_pf.contains_profanity = AsyncMock(return_value=True)

        await profanity_handler(update, context)

        update.message.delete.assert_not_awaited()
        mock_pf.contains_profanity.assert_not_awaited()


@pytest.mark.asyncio
async def test_profanity_handler_skips_when_disabled():
    update = _make_update(text="mierda!")
    context = _make_context(is_admin=False)

    with patch("bot.handlers.profanity.profanity_filter") as mock_pf, \
         patch("bot.handlers.profanity.settings") as mock_settings:
        mock_settings.profanity_enabled = False
        mock_pf.contains_profanity = AsyncMock(return_value=True)

        await profanity_handler(update, context)

        update.message.delete.assert_not_awaited()
        mock_pf.contains_profanity.assert_not_awaited()


@pytest.mark.asyncio
async def test_profanity_handler_survives_delete_error():
    from telegram.error import TelegramError
    update = _make_update(text="fuck this")
    context = _make_context(is_admin=False)
    update.message.delete.side_effect = TelegramError("already deleted")

    with patch("bot.handlers.profanity.profanity_filter") as mock_pf, \
         patch("bot.handlers.profanity.settings") as mock_settings:
        mock_settings.profanity_enabled = True
        mock_pf.contains_profanity = AsyncMock(return_value=True)

        await profanity_handler(update, context)

        context.bot.send_message.assert_awaited_once()
