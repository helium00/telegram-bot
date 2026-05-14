import os

# Set env vars BEFORE any bot module is imported.
# os.environ takes precedence over .env file in pydantic-settings,
# so these override any empty values present in a local .env.
os.environ["TELEGRAM_BOT_TOKEN"] = "0:test_token"
os.environ["TELEGRAM_GROUP_ID"] = "-1001234567890"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://user:pass@localhost/testdb"
os.environ["TOPIC_GENERAL_ID"] = "0"
os.environ["TOPIC_SPANISH_ID"] = "0"
os.environ["TOPIC_ENGLISH_ID"] = "0"
os.environ["TOPIC_BUREAUCRACY_ID"] = "0"
os.environ["TOPIC_EVENTS_ID"] = "0"
os.environ["TOPIC_ACTIVITIES_ID"] = "0"
os.environ["TOPIC_ANNOUNCEMENTS_ID"] = "0"
