import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from bot.services.profanity_filter import ProfanityFilter


# --- contains_profanity ---

@pytest.mark.asyncio
async def test_contains_profanity_exact_match():
    ProfanityFilter._cache = {"mierda", "fuck", "cazzo"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("qué mierda!") is True


@pytest.mark.asyncio
async def test_contains_profanity_case_insensitive():
    ProfanityFilter._cache = {"mierda", "fuck", "cazzo"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("FUCK this") is True


@pytest.mark.asyncio
async def test_contains_profanity_no_match():
    ProfanityFilter._cache = {"mierda", "fuck", "cazzo"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("hello world") is False


@pytest.mark.asyncio
async def test_contains_profanity_no_substring_match():
    ProfanityFilter._cache = {"ass"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("assassin") is False


@pytest.mark.asyncio
async def test_contains_profanity_accented_chars():
    ProfanityFilter._cache = {"coño"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("menudo coño!") is True


@pytest.mark.asyncio
async def test_contains_profanity_empty_string():
    ProfanityFilter._cache = {"mierda"}
    pf = ProfanityFilter()
    assert await pf.contains_profanity("") is False


# --- cache loading ---

@pytest.mark.asyncio
async def test_load_populates_cache_from_db():
    mock_row = MagicMock()
    mock_row.__getitem__ = lambda self, idx: "mierda"
    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]

    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        result = await pf._load()
        assert "mierda" in result
        assert ProfanityFilter._cache is not None


@pytest.mark.asyncio
async def test_load_uses_cache_on_second_call():
    ProfanityFilter._cache = {"cached_word"}
    pf = ProfanityFilter()
    with patch("bot.services.profanity_filter.AsyncSessionLocal") as mock_session_cls:
        result = await pf._load()
        mock_session_cls.assert_not_called()
        assert result == {"cached_word"}


# --- add_word ---

@pytest.mark.asyncio
async def test_add_word_invalidates_cache():
    ProfanityFilter._cache = {"existing"}
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        result = await pf.add_word("newword", added_by=123)
        assert result is True
        assert ProfanityFilter._cache is None


@pytest.mark.asyncio
async def test_add_word_returns_false_on_duplicate():
    from sqlalchemy.exc import IntegrityError
    mock_session = AsyncMock()
    mock_session.commit.side_effect = IntegrityError("", {}, Exception())
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        result = await pf.add_word("mierda", added_by=123)
        assert result is False


# --- remove_word ---

@pytest.mark.asyncio
async def test_remove_word_returns_true_when_found():
    ProfanityFilter._cache = {"mierda"}
    mock_entry = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_entry
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        result = await pf.remove_word("mierda")
        assert result is True
        assert ProfanityFilter._cache is None


@pytest.mark.asyncio
async def test_remove_word_returns_false_when_not_found():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        result = await pf.remove_word("notexist")
        assert result is False


# --- list_words ---

@pytest.mark.asyncio
async def test_list_words_returns_sorted_list():
    mock_result = MagicMock()
    mock_result.all.return_value = [("mierda",), ("cazzo",), ("fuck",)]
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        words = await pf.list_words()
        assert words == ["mierda", "cazzo", "fuck"]


@pytest.mark.asyncio
async def test_list_words_empty():
    mock_result = MagicMock()
    mock_result.all.return_value = []
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)

    with patch("bot.services.profanity_filter.AsyncSessionLocal", return_value=mock_session):
        pf = ProfanityFilter()
        words = await pf.list_words()
        assert words == []
