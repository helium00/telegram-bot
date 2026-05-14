# Sagunto Hub Bot

A production-ready Telegram bot for the **Sagunto Hub** community. It automatically routes different types of content (weather, events, bureaucracy tips, language learning) to the correct topic in a Telegram supergroup.

---

## Table of Contents

1. [Architecture](#architecture)
2. [How Telegram Topics Work](#how-telegram-topics-work)
3. [Creating the Bot with BotFather](#creating-the-bot-with-botfather)
4. [Creating a Supergroup with Topics](#creating-a-supergroup-with-topics)
5. [Obtaining Chat ID and Thread IDs](#obtaining-chat-id-and-thread-ids)
6. [Generating Secrets](#generating-secrets)
7. [Running Locally](#running-locally)
8. [Adding a New Source](#adding-a-new-source)
9. [Migrating to an Ubuntu Server](#migrating-to-an-ubuntu-server)
10. [Backup and Restore PostgreSQL](#backup-and-restore-postgresql)
11. [Troubleshooting](#troubleshooting)

---

## Architecture

```
sagunto-hub-bot/
├── bot/
│   ├── main.py              # Entry point: wires app, scheduler, migrations
│   ├── config.py            # Pydantic Settings — all env vars
│   ├── logging_config.py    # structlog setup
│   ├── telegram/
│   │   ├── client.py        # TelegramClient — sends to topics
│   │   ├── router.py        # Content type → topic name mapping
│   │   └── topics.py        # Topic name → message_thread_id mapping
│   ├── database/
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── session.py       # Async engine + session factory
│   │   └── migrations/      # Alembic migrations
│   ├── services/
│   │   ├── duplicate_guard.py  # Deduplication via DB
│   │   ├── formatter.py        # HTML formatting helpers
│   │   └── scheduler.py        # APScheduler job builder
│   ├── sources/
│   │   ├── base.py             # BaseSource interface
│   │   ├── weather_source.py   # Mock weather → Activities
│   │   ├── events_source.py    # Mock events → Events
│   │   ├── bureaucracy_source.py  # Mock reminders → Bureaucracy
│   │   └── language_source.py  # Word of the Day → Spanish/English
│   └── commands/
│       ├── start.py / help.py / id.py / where.py
├── scripts/
│   ├── generate_secrets.sh  # Generates random credentials → .env
│   ├── init_postgres.sql    # DB privilege setup
│   └── backup_postgres.sh   # pg_dump to gzipped file
├── tests/unit/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
└── .env.example
```

**Data flow:**

```
APScheduler → Source.fetch_items() → duplicate_guard → TelegramClient.send_to_topic()
                                                              ↓
                                                   PostgreSQL (posted_items)
```

---

## How Telegram Topics Work

A Telegram **supergroup** with **Topics** enabled acts like a forum: each topic is a thread with its own `message_thread_id`. The bot uses `message_thread_id` when calling `sendMessage` to route content to the correct thread.

To send to the main chat (no topic), omit `message_thread_id` (or set it to `None`).

---

## Creating the Bot with BotFather

1. Open Telegram and start a chat with **@BotFather**.
2. Send `/newbot` and follow the prompts (name + username).
3. Copy the **bot token** — this is your `TELEGRAM_BOT_TOKEN`.
4. Send `/setprivacy` → select your bot → **Disable** (so it can read messages in groups).
5. Optionally send `/setcommands` to register slash commands.

> **Keep your bot token private.** Anyone with the token can control your bot.

---

## Creating a Supergroup with Topics

1. Create a new Telegram group.
2. Open **Group Info → Edit → Topics** and enable it (this converts the group to a supergroup).
3. Create the topics: General, Spanish Learning, English Learning, Bureaucracy, Events, Activities, Announcements.
4. Add your bot as an **administrator** with at least "Post Messages" permission.

---

## Obtaining Chat ID and Thread IDs

1. Add the bot to the supergroup.
2. Send `/id` in the main chat → copy the **Chat ID** (negative number).
3. Open each topic and send `/where` → copy the **Thread ID** for that topic.
4. Fill in your `.env`:

```
TELEGRAM_GROUP_ID=-1001234567890
TOPIC_GENERAL_ID=1
TOPIC_SPANISH_ID=2
TOPIC_ENGLISH_ID=3
TOPIC_BUREAUCRACY_ID=4
TOPIC_EVENTS_ID=5
TOPIC_ACTIVITIES_ID=6
TOPIC_ANNOUNCEMENTS_ID=7
```

---

## Generating Secrets

```bash
make secrets
```

This copies `.env.example` to `.env` and fills in a random `POSTGRES_PASSWORD`. Then edit `.env` and add your Telegram credentials and topic IDs.

---

## Running Locally

**Prerequisites:** Docker, Docker Compose, `make`, Python 3, `python3-venv`.

```bash
# On Ubuntu — install venv support if missing
sudo apt install -y python3-venv

# 1. Create virtualenv and install Python dependencies (required for make test / make lint)
make install

# 2. Generate secrets
make secrets

# 3. Edit .env — add TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID, TOPIC_*_ID

# 4. Build and start
make build
make up

# 5. Tail logs
make logs

# 6. Connect to DB (optional)
make db-shell

# 7. Run tests
make test
```

---

## Adding a New Source

1. Create `bot/sources/my_source.py` implementing `BaseSource`:

```python
from bot.sources.base import BaseSource
from bot.telegram.topics import EVENTS  # choose the right topic

class MySource(BaseSource):
    @property
    def name(self) -> str:
        return "my_source"

    @property
    def target_topic(self) -> str:
        return EVENTS

    async def fetch_items(self):
        # TODO: call real API here
        return [{"id": "item_1", "title": "My item", "body": "Hello"}]

    def format_item(self, item):
        return f"<b>{item['title']}</b>\n\n{item['body']}"
```

2. Register a schedule in `bot/services/scheduler.py` — add an entry to `schedule_map`.
3. Instantiate and add to the `sources` list in `bot/main.py`.
4. Add the cron env var to `.env.example` and `.env`.

---

## Migrating to an Ubuntu Server

```bash
# On the server — install system dependencies
sudo apt update && sudo apt install -y docker.io docker-compose-plugin make git python3-venv

# Clone the repo
git clone <your-repo-url> sagunto-hub-bot
cd sagunto-hub-bot

# Install Python dependencies (needed for make test / make lint)
make install

# Copy your .env (do NOT commit it)
scp local/.env ubuntu@server:/path/sagunto-hub-bot/.env

# Build and start
make build
make up

# Enable auto-start on reboot (Docker daemon already starts automatically)
# To ensure containers restart: docker-compose.yml already sets restart: unless-stopped
```

To run as a systemd service instead:

```ini
# /etc/systemd/system/sagunto-hub-bot.service
[Unit]
Description=Sagunto Hub Bot
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/opt/sagunto-hub-bot
ExecStart=/usr/bin/docker compose up
ExecStop=/usr/bin/docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sagunto-hub-bot
```

---

## Backup and Restore PostgreSQL

**Backup:**
```bash
make backup
# Creates backups/sagunto_hub_bot_YYYYMMDD_HHMMSS.sql.gz
```

**Restore:**
```bash
gunzip -c backups/sagunto_hub_bot_20240101_080000.sql.gz \
  | docker compose exec -T postgres psql \
      -U sagunto_bot_user sagunto_hub_bot
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Bot doesn't post to topics | Check `TELEGRAM_GROUP_ID` is negative and `TOPIC_*_ID` values are correct — use `/where` inside each topic |
| `permission denied` when posting | Ensure the bot is a group admin with "Post Messages" enabled |
| Database connection refused | Check `DATABASE_URL` matches `POSTGRES_USER`/`POSTGRES_PASSWORD`/`POSTGRES_DB` in `.env` |
| Duplicate posts | `posted_items` table may be empty — DB state is source of truth; check `make db-shell` |
| Bot token invalid | Regenerate with BotFather `/revoke` and update `TELEGRAM_BOT_TOKEN` |
| Container won't start | Check `make logs` for the error; ensure `.env` exists and is populated |
