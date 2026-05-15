import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_update(args: list[str] | None = None, is_admin_val: bool = True):
    message = MagicMock()
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.message = message
    update.effective_user = MagicMock()
    update.effective_user.id = 99
    update.effective_chat = MagicMock()
    update.effective_chat.id = -1001234567890

    context = MagicMock()
    context.bot = AsyncMock()
    context.bot.get_chat_member = AsyncMock(
        return_value=MagicMock(status="administrator" if is_admin_val else "member")
    )
    context.args = args or []

    return update, context


# --- /addword ---

@pytest.mark.asyncio
async def test_addword_adds_new_word():
    from bot.commands.badwords import addword_handler
    update, context = _make_update(args=["testword"])

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.add_word = AsyncMock(return_value=True)
        await addword_handler(update, context)
        mock_pf.add_word.assert_awaited_once_with("testword", 99)
        update.message.reply_text.assert_awaited_once()
        assert "added" in update.message.reply_text.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_addword_reports_duplicate():
    from bot.commands.badwords import addword_handler
    update, context = _make_update(args=["mierda"])

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.add_word = AsyncMock(return_value=False)
        await addword_handler(update, context)
        update.message.reply_text.assert_awaited_once()
        assert "already" in update.message.reply_text.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_addword_requires_argument():
    from bot.commands.badwords import addword_handler
    update, context = _make_update(args=[])

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.add_word = AsyncMock()
        await addword_handler(update, context)
        mock_pf.add_word.assert_not_awaited()
        update.message.reply_text.assert_awaited_once()
        assert "usage" in update.message.reply_text.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_addword_ignored_for_non_admin():
    from bot.commands.badwords import addword_handler
    update, context = _make_update(args=["word"], is_admin_val=False)

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.add_word = AsyncMock()
        await addword_handler(update, context)
        mock_pf.add_word.assert_not_awaited()
        update.message.reply_text.assert_not_awaited()


# --- /removeword ---

@pytest.mark.asyncio
async def test_removeword_removes_existing():
    from bot.commands.badwords import removeword_handler
    update, context = _make_update(args=["mierda"])

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.remove_word = AsyncMock(return_value=True)
        await removeword_handler(update, context)
        mock_pf.remove_word.assert_awaited_once_with("mierda")
        assert "removed" in update.message.reply_text.call_args.args[0].lower()


@pytest.mark.asyncio
async def test_removeword_reports_not_found():
    from bot.commands.badwords import removeword_handler
    update, context = _make_update(args=["ghost"])

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.remove_word = AsyncMock(return_value=False)
        await removeword_handler(update, context)
        assert "not found" in update.message.reply_text.call_args.args[0].lower()


# --- /listwords ---

@pytest.mark.asyncio
async def test_listwords_shows_words():
    from bot.commands.badwords import listwords_handler
    update, context = _make_update()

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.list_words = AsyncMock(return_value=["cazzo", "fuck", "mierda"])
        await listwords_handler(update, context)
        reply_text = update.message.reply_text.call_args.args[0]
        assert "cazzo" in reply_text
        assert "3" in reply_text


@pytest.mark.asyncio
async def test_listwords_empty_filter():
    from bot.commands.badwords import listwords_handler
    update, context = _make_update()

    with patch("bot.commands.badwords.profanity_filter") as mock_pf:
        mock_pf.list_words = AsyncMock(return_value=[])
        await listwords_handler(update, context)
        reply_text = update.message.reply_text.call_args.args[0]
        assert "empty" in reply_text.lower()
