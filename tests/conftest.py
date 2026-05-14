import os

import pytest

# Provide minimal env vars so config.py can be imported without a real .env
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "0:test_token")
os.environ.setdefault("TELEGRAM_GROUP_ID", "-1001234567890")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/testdb")
