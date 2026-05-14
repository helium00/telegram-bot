import os

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
