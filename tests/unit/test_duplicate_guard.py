import pytest
from unittest.mock import AsyncMock, MagicMock

from bot.services.duplicate_guard import compute_hash, is_duplicate, mark_posted


def test_compute_hash_is_deterministic():
    h1 = compute_hash("hello")
    h2 = compute_hash("hello")
    assert h1 == h2


def test_compute_hash_differs_for_different_content():
    assert compute_hash("hello") != compute_hash("world")


def test_compute_hash_returns_64_char_hex():
    h = compute_hash("some content")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


@pytest.mark.asyncio
async def test_is_duplicate_returns_true_when_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = 1
    session.execute.return_value = mock_result

    result = await is_duplicate(session, "weather", "weather_2024-01-01", "abc123")
    assert result is True


@pytest.mark.asyncio
async def test_is_duplicate_returns_false_when_not_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    result = await is_duplicate(session, "weather", "weather_2024-01-01", "abc123")
    assert result is False


@pytest.mark.asyncio
async def test_mark_posted_adds_item_and_commits():
    session = AsyncMock()

    await mark_posted(
        session,
        source_name="weather",
        external_id="weather_2024-01-01",
        content_hash="abc123",
        topic_name="activities",
        title="Weather today",
    )

    session.add.assert_called_once()
    session.commit.assert_called_once()
