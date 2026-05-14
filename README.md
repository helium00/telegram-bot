# Sagunto Hub Bot

A production-ready Telegram bot for the **Sagunto Hub** community. It automatically routes different types of content (weather, events, bureaucracy tips, language learning) to the correct topic in a Telegram supergroup.

---

## Table of Contents

1. [Architecture](#architecture)
2. [How Telegram Topics Work](#how-telegram-topics-work)
3. [Step 1 — Create the Bot with BotFather](#step-1--create-the-bot-with-botfather)
4. [Step 2 — Create a Supergroup with Topics](#step-2--create-a-supergroup-with-topics)
5. [Step 3 — Clone and Configure](#step-3--clone-and-configure)
6. [Step 4 — Start the Bot](#step-4--start-the-bot)
7. [Step 5 — Discover Group ID and Topic IDs](#step-5--discover-group-id-and-topic-ids)
8. [Step 6 — Complete Configuration and Restart](#step-6--complete-configuration-and-restart)
9. [Running Tests](#running-tests)
10. [Adding a New Source](#adding-a-new-source)
11. [Migrating to an Ubuntu Server](#migrating-to-an-ubuntu-server)
12. [Backup and Restore PostgreSQL](#backup-and-restore-postgresql)
13. [Troubleshooting](#troubleshooting)

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

If a topic ID is not configured (set to 0 or left empty), the bot sends to the main chat instead of crashing.

---

## Step 1 — Create the Bot with BotFather

1. Open Telegram and start a chat with **@BotFather**.
2. Send `/newbot` and follow the prompts (choose a name and a username ending in `bot`).
3. BotFather will reply with your **bot token** — copy it immediately.
4. Send `/setprivacy` → select your bot → choose **Disable** so it can read messages in groups.
5. Optionally send `/setcommands` and paste:
   ```
   start - Welcome message
   help - Show available commands
   id - Show current chat ID
   where - Show chat ID and topic thread ID
   ```

> **Keep your bot token private.** Anyone with the token can control your bot. Never commit it to git.

---

## Step 2 — Create a Supergroup with Topics

1. Create a new Telegram group (any name).
2. Open **Group Info → Edit → Topics** and enable it.
   - This converts the group to a **supergroup** automatically.
3. Create the following topics one by one:
   - General
   - Spanish Learning
   - English Learning
   - Bureaucracy
   - Events
   - Activities
   - Announcements
4. Add your bot to the group.
5. Promote the bot to **administrator** and enable at least:
   - ✅ Post Messages
   - ✅ Manage Topics (optional but recommended)

---

## Step 3 — Clone and Configure

**Prerequisites:** Docker, Docker Compose, `make`, `python3-venv`, `git`.

```bash
# Ubuntu — install prerequisites
sudo apt update && sudo apt install -y docker.io docker-compose-plugin make git python3-venv

# Clone the repo
git clone https://github.com/helium00/telegram-bot.git sagunto-hub-bot
cd sagunto-hub-bot

# Generate .env with a random database password
make secrets
```

Now open `.env` and fill in **only** the bot token — everything else can be discovered later:

```env
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Leave all `TOPIC_*_ID` and `TELEGRAM_GROUP_ID` fields as empty or 0 for now.

---

## Step 4 — Start the Bot

```bash
make build
make up
make logs
```

You should see output like:

```
bot-1  | migrations_applied
bot-1  | database_connected
bot-1  | scheduler_started
bot-1  | polling_started
```

If you see errors, check the [Troubleshooting](#troubleshooting) section.

---

## Step 5 — Discover Group ID and Topic IDs

The bot must be running (Step 4) and added to the group (Step 2) before doing this.

**Get the Group ID:**

Go to the main group chat (not inside any topic) and send:
```
/id
```
The bot replies with something like:
```
Chat ID: -1001234567890
```
Copy this number — it is your `TELEGRAM_GROUP_ID`.

**Get each Topic ID:**

Open each topic one by one and send:
```
/where
```
The bot replies with:
```
Chat ID: -1001234567890
Thread ID: 5
```
The **Thread ID** is the `message_thread_id` for that topic.

Repeat `/where` inside every topic and note each value:

| Topic | Thread ID |
|---|---|
| General | e.g. 1 |
| Spanish Learning | e.g. 3 |
| English Learning | e.g. 5 |
| Bureaucracy | e.g. 7 |
| Events | e.g. 9 |
| Activities | e.g. 11 |
| Announcements | e.g. 13 |

---

## Step 6 — Complete Configuration and Restart

Edit `.env` and fill in all the IDs you collected:

```env
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_GROUP_ID=-1001234567890

TOPIC_GENERAL_ID=1
TOPIC_SPANISH_ID=3
TOPIC_ENGLISH_ID=5
TOPIC_BUREAUCRACY_ID=7
TOPIC_EVENTS_ID=9
TOPIC_ACTIVITIES_ID=11
TOPIC_ANNOUNCEMENTS_ID=13
```

Restart the bot to apply the new configuration:

```bash
make down
make up
make logs
```

The bot is now fully configured and will automatically post content to the correct topics according to the configured schedules.

---

## Running Tests

```bash
# First time only — create virtualenv and install dependencies
make install

# Run tests
make test
```

> **Note:** The virtualenv is created in `~/.venvs/sagunto-hub-bot/` (outside the project folder) to avoid symlink issues on VirtualBox shared filesystems.

---

## Adding a New Source

1. Create `bot/sources/my_source.py` implementing `BaseSource`:

```python
from bot.sources.base import BaseSource
from bot.telegram.topics import EVENTS

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

2. Add a schedule entry in `bot/services/scheduler.py` → `schedule_map`.
3. Add the source to the `sources` list in `bot/main.py`.
4. Add the cron env var to `.env.example` and `.env`.

---

## Migrating to an Ubuntu Server

```bash
# Install prerequisites
sudo apt update && sudo apt install -y docker.io docker-compose-plugin make git python3-venv

# Add your user to the docker group (avoids sudo on every docker command)
sudo usermod -aG docker $USER
newgrp docker

# Clone the repo
git clone https://github.com/helium00/telegram-bot.git sagunto-hub-bot
cd sagunto-hub-bot

# Copy your configured .env from your local machine (never commit it)
# Run this from your LOCAL machine:
# scp .env user@server:/path/to/sagunto-hub-bot/.env

# Build and start
make build
make up
make logs
```

To ensure the bot restarts automatically on server reboot (already configured via `restart: unless-stopped` in docker-compose.yml), make sure the Docker daemon starts on boot:

```bash
sudo systemctl enable docker
```

Optionally, run as a systemd service:

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
| `No module named pip` | Run `sudo apt install -y python3-venv` then `make install` |
| `Protocol error: lib64` | Makefile already handles this — venv is created in `~/.venvs/` outside shared folders |
| `externally-managed-environment` | Use `make install` — it creates a virtualenv automatically |
| Bot container keeps restarting | Run `make logs` and check the error; most likely `.env` is misconfigured |
| `password authentication failed` | `DATABASE_URL` password must match `POSTGRES_PASSWORD` in `.env`; if volume exists with old password run `make down && docker volume rm telegram-bot_postgres_data && make up` |
| `Input should be a valid integer` | Leave `TOPIC_*_ID` fields completely empty or set to `0`, not to a word or placeholder |
| Bot doesn't respond to commands | Check bot is admin in the group with "Post Messages" enabled |
| Bot doesn't post to topics | Fill in `TOPIC_*_ID` via `/where` command, update `.env`, restart with `make down && make up` |
| `/where` returns `Thread ID: —` | You are in the main chat, not inside a topic — open a specific topic first |
| Bot token invalid | Regenerate with BotFather `/revoke` and update `TELEGRAM_BOT_TOKEN` in `.env` |
