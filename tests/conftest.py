import os
import pytest

# Set env vars BEFORE any bot module is imported.
os.environ["TELEGRAM_BOT_TOKEN"] = "0:test_token"
os.environ["TELEGRAM_GROUP_ID"] = "-1001234567890"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
# Dynamic topic env vars — used by topics.py scanner
os.environ["TOPIC_GENERAL_ID"] = "1"
os.environ["TOPIC_WEATHER_ID"] = "2"
os.environ["TOPIC_EVENTS_ID"] = "3"
os.environ["TOPIC_BUREAUCRACY_ID"] = "4"
os.environ["TOPIC_SPANISH_ID"] = "5"
os.environ["TOPIC_ENGLISH_ID"] = "6"


@pytest.fixture(autouse=True)
def reset_topics_cache():
    import bot.telegram.topics as _topics_mod
    _topics_mod._cache = None
    yield
    _topics_mod._cache = None


@pytest.fixture(autouse=True)
def reset_profanity_cache():
    import bot.services.profanity_filter as _pf_mod
    _pf_mod.ProfanityFilter._cache = None
    yield
    _pf_mod.ProfanityFilter._cache = None
