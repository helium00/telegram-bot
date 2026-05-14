# Sagunto Hub Bot

A production-ready Telegram bot for the **Sagunto Hub** community. It automatically routes content (weather, events, bureaucracy tips, language learning) to the correct topic in a Telegram supergroup, moderates the group, and welcomes new members.

---

## Table of Contents

1. [What the Bot Does](#what-the-bot-does)
2. [Architecture](#architecture)
3. [How Telegram Topics Work](#how-telegram-topics-work)
4. [Step 1 — Create the Bot with BotFather](#step-1--create-the-bot-with-botfather)
5. [Step 2 — Create a Supergroup with Topics](#step-2--create-a-supergroup-with-topics)
6. [Step 3 — Clone and Configure](#step-3--clone-and-configure)
7. [Step 4 — Start the Bot](#step-4--start-the-bot)
8. [Step 5 — Discover Group ID and Topic IDs](#step-5--discover-group-id-and-topic-ids)
9. [Step 6 — Complete Configuration and Restart](#step-6--complete-configuration-and-restart)
10. [Bot Commands](#bot-commands)
11. [Automated Content](#automated-content)
12. [Managing Topics](#managing-topics)
13. [Moderation](#moderation)
14. [Running Tests](#running-tests)
15. [Adding a New Source](#adding-a-new-source)
16. [Migrating to an Ubuntu Server](#migrating-to-an-ubuntu-server)
17. [Backup and Restore PostgreSQL](#backup-and-restore-postgresql)
18. [Troubleshooting](#troubleshooting)

---

## What the Bot Does

The Sagunto Hub Bot has three roles:

**1. Content router (automated)**
Runs on a schedule via APScheduler. Fetches content from configured sources and posts it to the right Telegram topic. Deduplication ensures each item is posted only once, even if the scheduler fires multiple times.

**2. Group moderator**
Admin-only commands to ban, kick, mute, warn, and delete messages. Warnings are tracked in PostgreSQL. A user is automatically banned after reaching the configured warning threshold.

**3. Welcome bot**
When a new member joins the group, the bot sends a welcome message to the General topic automatically.

---

## Architecture

```
sagunto-hub-bot/
├── bot/
│   ├── main.py                    # Entry point: wires app, scheduler, migrations
│   ├── config.py                  # Pydantic Settings — all env vars
│   ├── logging_config.py          # structlog setup (JSON in prod, console in local)
│   ├── telegram/
│   │   ├── client.py              # TelegramClient — sends messages to topics
│   │   ├── router.py              # Content type → topic name mapping
│   │   └── topics.py              # Scans TOPIC_*_ID env vars → thread ID map
│   ├── database/
│   │   ├── models.py              # SQLAlchemy models: PostedItem, SourceRun, User, Warning
│   │   ├── session.py             # Async engine + session factory
│   │   └── migrations/            # Alembic migrations (run automatically on startup)
│   ├── services/
│   │   ├── duplicate_guard.py     # Deduplication via DB (content hash + external ID)
│   │   ├── formatter.py           # HTML formatting helpers
│   │   ├── moderation.py          # Shared helpers: is_admin, mention_html, parse_duration
│   │   └── scheduler.py           # APScheduler job builder
│   ├── sources/
│   │   ├── base.py                # Abstract BaseSource interface
│   │   ├── weather_source.py      # Daily weather summary → weather topic
│   │   ├── events_source.py       # Local events → events topic
│   │   ├── bureaucracy_source.py  # Bureaucracy reminders → bureaucracy topic
│   │   └── language_source.py     # Word of the Day → spanish / english topics
│   ├── commands/
│   │   ├── start.py               # /start
│   │   ├── help.py                # /help
│   │   ├── id.py                  # /id
│   │   ├── where.py               # /where
│   │   ├── ban.py                 # /ban
│   │   ├── kick.py                # /kick
│   │   ├── mute.py                # /mute and /unmute
│   │   ├── warn.py                # /warn (DB-backed, auto-ban)
│   │   └── delete_msg.py          # /del
│   └── handlers/
│       └── welcome.py             # Greets new members in General topic
├── scripts/
│   ├── generate_secrets.sh        # Generates random credentials → .env
│   ├── init_postgres.sql          # DB privilege setup
│   └── backup_postgres.sh         # pg_dump to gzipped file
├── tests/unit/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── Makefile
└── .env.example
```

**Data flow — scheduled content:**

```
APScheduler → Source.fetch_items() → duplicate_guard → TelegramClient.send_to_topic()
                                                              ↓
                                                   PostgreSQL (posted_items)
```

**Data flow — moderation:**

```
User sends /warn (reply) → is_admin check → Warning saved to DB → count checked
                                                                        ↓
                                                          reply with count / auto-ban
```

---

## How Telegram Topics Work

A Telegram **supergroup** with **Topics** enabled works like a forum: each topic is a thread with its own `message_thread_id`. The bot uses this ID when calling `sendMessage` to route content to the right thread.

If a topic ID is not configured (empty or 0), the bot falls back to posting in the main chat instead of crashing.

---

## Step 1 — Create the Bot with BotFather

1. Open Telegram and start a chat with **@BotFather**.
2. Send `/newbot` and follow the prompts (name + username ending in `bot`).
3. BotFather will reply with your **bot token** — copy it immediately.
4. Send `/setprivacy` → select your bot → choose **Disable** so it can read group messages.
5. Optionally send `/setcommands` and paste the full command list:

```
start - Welcome message
help - Show all available commands
id - Show the current chat ID
where - Show chat ID and topic thread ID
ban - Ban a user (reply to their message)
kick - Kick a user (reply to their message)
mute - Mute a user (reply to their message)
unmute - Unmute a user (reply to their message)
warn - Warn a user (reply to their message)
del - Delete a message (reply to it)
```

> **Keep your bot token private.** Anyone with the token can control your bot. Never commit it to git.

---

## Step 2 — Create a Supergroup with Topics

1. Create a new Telegram group.
2. Open **Group Info → Edit → Topics** and enable it.
   - This converts the group to a **supergroup** automatically.
3. Create the following topics one by one:
   - General
   - Weather (or Activities)
   - Events
   - Bureaucracy
   - Spanish Learning
   - English Learning
   - Announcements (optional)
4. Add your bot to the group.
5. Promote the bot to **administrator** and enable:
   - ✅ Post Messages
   - ✅ Ban Users *(required for `/ban`, `/kick`, `/warn` auto-ban)*
   - ✅ Restrict Members *(required for `/mute` and `/unmute`)*
   - ✅ Delete Messages *(required for `/del`)*
   - ✅ Manage Topics *(optional but recommended)*

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

Now open `.env` and fill in **only** the bot token — everything else can be discovered after the bot starts:

```env
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Leave all `TOPIC_*_ID` and `TELEGRAM_GROUP_ID` fields empty for now.

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
The bot replies:
```
Chat ID: -1001234567890
```
Copy this number — it is your `TELEGRAM_GROUP_ID`.

**Get each Topic ID:**

Open each topic one by one and send:
```
/where
```
The bot replies:
```
Chat ID: -1001234567890
Thread ID: 5
```
The **Thread ID** is the `message_thread_id` for that topic.

Repeat `/where` in every topic and note each value:

| Topic | Example Thread ID |
|---|---|
| General | 1 |
| Weather / Activities | 3 |
| Events | 5 |
| Bureaucracy | 7 |
| Spanish Learning | 9 |
| English Learning | 11 |
| Announcements | 13 |

---

## Step 6 — Complete Configuration and Restart

Edit `.env` and fill in all IDs you collected:

```env
TELEGRAM_BOT_TOKEN=123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_GROUP_ID=-1001234567890

TOPIC_GENERAL_ID=1
TOPIC_WEATHER_ID=3
TOPIC_EVENTS_ID=5
TOPIC_BUREAUCRACY_ID=7
TOPIC_SPANISH_ID=9
TOPIC_ENGLISH_ID=11
TOPIC_ANNOUNCEMENTS_ID=13

MAX_WARNINGS=3
```

Restart the bot:

```bash
make down
make up
make logs
```

The bot is now fully configured.

---

## Bot Commands

### Utility commands (anyone can use)

| Command | Where to use | What it returns |
|---|---|---|
| `/start` | Any chat | Welcome message |
| `/help` | Any chat | Full list of available commands |
| `/id` | Group main chat | The numeric chat ID of the current chat |
| `/where` | Inside a topic | The chat ID and the thread ID of the current topic |

**Usage examples:**

- Send `/id` in the main group to get your `TELEGRAM_GROUP_ID`.
- Open a topic (e.g. Events) and send `/where` to get that topic's thread ID.
- `/where` in the main chat returns `Thread ID: —` (you are not in a topic).

---

### Moderation commands (group admins only)

All moderation commands must be used by **replying to a message** sent by the target user. If the caller is not a group admin, the command is silently ignored — no error is shown.

| Command | Syntax | Effect |
|---|---|---|
| `/ban` | Reply + optional reason | Permanently bans the user from the group |
| `/kick` | Reply + optional reason | Removes the user; they can rejoin via invite link |
| `/mute` | Reply + optional `[duration]` + optional reason | Prevents the user from sending any message |
| `/unmute` | Reply to any message by the user | Restores full send permissions |
| `/warn` | Reply + optional reason | Issues a warning; auto-bans when threshold is reached |
| `/del` | Reply to the message to delete | Deletes that message and the `/del` command itself |

**Duration format for `/mute`:**

| Input | Meaning |
|---|---|
| *(none)* | Indefinite mute |
| `30m` | 30 minutes |
| `2h` | 2 hours |
| `1d` | 1 day |

**Examples:**

```
# Reply to a spam message and type:
/ban spamming product links

# Mute for 2 hours:
/mute 2h flooding the chat

# Mute indefinitely:
/mute no reason given

# Warn (3rd warning auto-bans):
/warn repeatedly ignoring rules

# Delete a message (reply to it):
/del
```

**Warning system:**

- Each `/warn` stores a record in PostgreSQL with the target user ID, the admin who warned, and the reason.
- After each warning the bot replies: `⚠️ User warned (2/3).`
- When the warning count reaches `MAX_WARNINGS` (default 3), the bot automatically bans the user and replies: `🚫 User has been banned after 3 warnings.`
- The threshold is configurable in `.env`:
  ```env
  MAX_WARNINGS=3
  ```

---

## Automated Content

The bot runs five scheduled jobs. Each job fetches content from a source, checks for duplicates, and posts to the matching topic.

| Source | Default topic | Default schedule | Env var |
|---|---|---|---|
| WeatherSource | `weather` | Daily at 08:00 | `SCHEDULE_WEATHER` |
| EventsSource | `events` | Every 6 hours | `SCHEDULE_EVENTS` |
| BureaucracySource | `bureaucracy` | Mon + Thu at 10:00 | `SCHEDULE_BUREAUCRACY` |
| SpanishWordSource | `spanish` | Daily at 09:00 | `SCHEDULE_SPANISH_WORD` |
| EnglishWordSource | `english` | Daily at 09:00 | `SCHEDULE_ENGLISH_WORD` |

**Schedule format:** standard cron expression (`minute hour day month weekday`).

Override any schedule in `.env`:

```env
SCHEDULE_WEATHER=0 8 * * *
SCHEDULE_EVENTS=0 */6 * * *
SCHEDULE_BUREAUCRACY=0 10 * * 1,4
SCHEDULE_SPANISH_WORD=0 9 * * *
SCHEDULE_ENGLISH_WORD=0 9 * * *
```

> **Note:** The current sources use mock data. Replace `fetch_items()` in each source file with a real API call when ready. See [Adding a New Source](#adding-a-new-source) for the interface.

**Deduplication:** each posted item is recorded in the `posted_items` table by `external_id` and `content_hash`. If the same content would be posted again, it is skipped silently.

---

## Managing Topics

Topics are fully driven by `.env`. No code changes are needed to add or remove a topic.

### Naming convention

The topic name used by sources is the middle segment of `TOPIC_*_ID`, **lowercased**:

| Env var | Topic name |
|---|---|
| `TOPIC_WEATHER_ID` | `weather` |
| `TOPIC_SPANISH_ID` | `spanish` |
| `TOPIC_SPANISH_LEARNING_ID` | `spanish_learning` |

### Adding a topic

1. Create the topic in your Telegram supergroup.
2. Send `/where` inside it — copy the **Thread ID**.
3. Add one line to `.env`:
   ```env
   TOPIC_NEWS_ID=42
   ```
4. Restart:
   ```bash
   make down && make up
   ```

### Removing a topic

Comment out the line in `.env`:

```env
# TOPIC_ANNOUNCEMENTS_ID=13
```

Restart. The topic is ignored; existing `posted_items` records in the DB are kept.

### Fallback behaviour

If a source's `default_topic` has no matching `TOPIC_*_ID` in `.env`, the message is sent to the **main group chat** instead of a topic. No crash, no error.

---

## Moderation

### Grant admin permissions

Before moderation commands work, the bot must be a group administrator with these permissions:

1. Open **Group Info → Administrators → Add Admin** → select the bot.
2. Enable:
   - ✅ **Ban Users** — `/ban`, `/kick`, `/warn` auto-ban
   - ✅ **Restrict Members** — `/mute`, `/unmute`
   - ✅ **Delete Messages** — `/del`
3. Save.

### Welcome message

When any non-bot member joins the group, the bot automatically sends a welcome message to the **General** topic:

```
👋 Welcome to Sagunto Hub, @username!

This is your community space for expats and locals in Sagunto.

📌 Quick guide:
• Use the correct topic for each type of message
• Be respectful and constructive
• Commands: /help for the full list

Enjoy! 🌞
```

**Requirement:** `TOPIC_GENERAL_ID` must be set and `TELEGRAM_GROUP_ID` must be non-zero.

### Warning threshold

Configurable in `.env`:

```env
MAX_WARNINGS=3
```

Restart after changing:

```bash
make down && make up
```

Warning records are stored in the `warnings` PostgreSQL table indefinitely. Banning a user does not reset their warning count.

---

## Running Tests

```bash
# First time only — create virtualenv and install dependencies
make install

# Run tests
make test
```

> **Note:** The virtualenv is created in `~/.venvs/sagunto-hub-bot/` (outside the project folder) to avoid symlink issues on VirtualBox shared filesystems.

The test suite covers topic routing, duplicate detection, all sources, and moderation service helpers (36 tests total).

---

## Adding a New Source

1. Create `bot/sources/my_source.py` implementing `BaseSource`:

```python
from bot.sources.base import BaseSource

class MySource(BaseSource):
    @property
    def name(self) -> str:
        return "my_source"

    @property
    def default_topic(self) -> str:
        # Must match the TOPIC_*_ID key in .env (lowercased middle segment).
        # e.g. "weather" → reads TOPIC_WEATHER_ID
        return "my_topic"

    async def fetch_items(self):
        # TODO: call real API here
        return [{"id": "item_1", "title": "My item", "body": "Hello"}]

    def format_item(self, item):
        return f"<b>{item['title']}</b>\n\n{item['body']}"
```

2. Add `TOPIC_MY_TOPIC_ID=<thread_id>` to `.env`.
3. Register a schedule in `bot/services/scheduler.py` → `schedule_map`.
4. Instantiate and add to the `sources` list in `bot/main.py`.
5. Add the cron env var to `.env.example` and `.env`.

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
| `Protocol error: lib64` | Makefile already handles this — venv is in `~/.venvs/` outside shared folders |
| `externally-managed-environment` | Use `make install` — it creates a virtualenv automatically |
| Bot container keeps restarting | Run `make logs` and check the error; most likely `.env` is misconfigured |
| `password authentication failed` | `DATABASE_URL` password must match `POSTGRES_PASSWORD` in `.env`; if the volume exists with an old password: `make down && docker volume rm telegram-bot_postgres_data && make up` |
| `Input should be a valid integer` | Leave `TOPIC_*_ID` fields completely empty or set to `0`, never a word or placeholder |
| Bot doesn't respond to commands | Check the bot is admin in the group with "Post Messages" enabled |
| Bot doesn't post to topics | Fill in `TOPIC_*_ID` via `/where`, update `.env`, restart with `make down && make up` |
| `/where` returns `Thread ID: —` | You are in the main chat, not inside a topic — open a specific topic first |
| Bot token invalid | Regenerate with BotFather `/revoke` and update `TELEGRAM_BOT_TOKEN` in `.env` |
| `/ban`, `/mute`, `/warn` do nothing | Bot is not an admin, or the calling user is not an admin — check group admin settings |
| `/del` doesn't delete | Bot needs "Delete Messages" admin permission |
| Warning count not incrementing | Bot is running but the DB migration may not have applied — check logs for `migrations_applied`; if missing, restart with `make down && make up` |
| Welcome message not sent | `TELEGRAM_GROUP_ID` or `TOPIC_GENERAL_ID` is 0 or empty — set both in `.env` and restart |
