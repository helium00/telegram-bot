# Dynamic Topic Routing — Design Spec

**Date:** 2026-05-14
**Status:** Approved

## Problem

Topic names and IDs are hardcoded in `config.py` and `topics.py`. Adding or removing a topic requires editing 3+ Python files. The goal is to manage topics entirely from `.env`.

## Solution (Approach A)

Topics are discovered at runtime by scanning `os.environ` for variables matching `TOPIC_*_ID`. No code changes are needed to add or remove a topic.

## Naming Convention

The topic name is derived from the env var by lowercasing the middle segment:

```
TOPIC_WEATHER_ID=5        →  topic name: "weather"
TOPIC_SPANISH_ID=7        →  topic name: "spanish"
TOPIC_SPANISH_LEARNING_ID=9  →  topic name: "spanish_learning"
```

Sources reference topic names as plain lowercase strings. The string must match the middle segment of the `TOPIC_*_ID` env var exactly.

## Changes

### `bot/telegram/topics.py` — full rewrite

- Remove all hardcoded constants (`GENERAL`, `SPANISH`, etc.)
- Remove import of `settings`
- Add `_load_topic_map()`: scans `os.environ`, returns `dict[str, int]`
- `get_thread_id(topic_name)` uses `_load_topic_map()` — returns `int | None`
- Add `all_topics()` helper that returns list of configured topic names

### `bot/config.py`

- Remove all `topic_*_id` fields
- Remove those fields from the `empty_str_to_zero` validator (keep only `telegram_group_id`)

### `bot/sources/base.py`

- Replace abstract `target_topic` with abstract `default_topic: str`
- Add concrete `target_topic` property that returns `default_topic` (simple string, no env override)

### `bot/sources/*.py`

Each source: replace constant import with plain string in `default_topic`.

| Source | default_topic |
|---|---|
| WeatherSource | `"weather"` |
| EventsSource | `"events"` |
| BureaucracySource | `"bureaucracy"` |
| SpanishWordSource | `"spanish"` |
| EnglishWordSource | `"english"` |

### `bot/telegram/router.py`

Remove import of topic constants. Use plain strings directly.

### `.env.example`

Replace fixed topic block with free-form pattern section + comment.

### `tests/conftest.py`

Set `TOPIC_GENERAL_ID=1`, `TOPIC_WEATHER_ID=2`, etc. to populate the dynamic map during tests.

### `tests/unit/test_routing.py`

Remove references to removed constants. Test dynamic discovery directly.

### `README.md`

Add section explaining the `TOPIC_*_ID` pattern, naming convention, and how to add/remove topics with zero code changes.

## What Does NOT Change

- Sources still have `target_topic` as a property (interface unchanged)
- `TelegramClient.send_to_topic()` unchanged
- Scheduler unchanged
- All other tests unchanged

## Adding a Topic (after this change)

```bash
# 1. Create the topic in Telegram, get thread ID via /where
# 2. Add one line to .env:
TOPIC_WEATHER_ID=42
# 3. Restart the bot — done. No code changes.
```

## Removing a Topic

```bash
# Remove or comment out the line in .env:
# TOPIC_ANNOUNCEMENTS_ID=13
# Restart — done.
```
