import pytest

from bot.sources.weather_source import WeatherSource
from bot.sources.events_source import EventsSource
from bot.sources.bureaucracy_source import BureaucracySource
from bot.sources.language_source import SpanishWordSource, EnglishWordSource


@pytest.mark.asyncio
async def test_weather_source_returns_one_item():
    source = WeatherSource()
    items = await source.fetch_items()
    assert len(items) == 1
    assert items[0]["id"].startswith("weather_")


@pytest.mark.asyncio
async def test_weather_source_format_contains_expected_text():
    source = WeatherSource()
    items = await source.fetch_items()
    text = source.format_item(items[0])
    assert "Sagunto" in text
    assert "Temperature" in text


def test_weather_source_targets_weather_topic():
    assert WeatherSource().target_topic == "weather"


@pytest.mark.asyncio
async def test_events_source_returns_two_items():
    source = EventsSource()
    items = await source.fetch_items()
    assert len(items) == 2


@pytest.mark.asyncio
async def test_events_source_format_contains_date():
    source = EventsSource()
    items = await source.fetch_items()
    text = source.format_item(items[0])
    assert "🗓" in text


def test_events_source_targets_events_topic():
    assert EventsSource().target_topic == "events"


@pytest.mark.asyncio
async def test_bureaucracy_source_returns_one_item():
    source = BureaucracySource()
    items = await source.fetch_items()
    assert len(items) == 1


def test_bureaucracy_source_targets_bureaucracy_topic():
    assert BureaucracySource().target_topic == "bureaucracy"


@pytest.mark.asyncio
async def test_spanish_word_source_returns_item_with_word():
    source = SpanishWordSource()
    items = await source.fetch_items()
    assert len(items) == 1
    assert "word" in items[0]
    assert items[0]["id"].startswith("es_")


@pytest.mark.asyncio
async def test_english_word_source_returns_item_with_word():
    source = EnglishWordSource()
    items = await source.fetch_items()
    assert len(items) == 1
    assert "word" in items[0]
    assert items[0]["id"].startswith("en_")


def test_spanish_word_source_targets_spanish_topic():
    assert SpanishWordSource().target_topic == "spanish"


def test_english_word_source_targets_english_topic():
    assert EnglishWordSource().target_topic == "english"
