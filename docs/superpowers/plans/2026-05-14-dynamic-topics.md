# Dynamic Topic Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Topics are discovered at runtime from `TOPIC_*_ID` env vars — add or remove a topic by editing only `.env`, zero code changes required.

**Architecture:** `topics.py` scans `os.environ` for the `TOPIC_*_ID` pattern and builds a `dict[str, int]` at call time. `config.py` loses all `topic_*_id` fields. Sources declare `default_topic: str` (a plain lowercase string) which must match the middle segment of the corresponding env var.

**Tech Stack:** Python 3.12, pydantic-settings, python-telegram-bot 21, pytest, pytest-asyncio

---

### Task 1: Rewrite `topics.py` — dynamic env scanning

**Files:**
- Modify: `bot/telegram/topics.py`
- Modify: `tests/unit/test_routing.py`
- Modify: `tests/conftest.py`

- [ ] **Step 1: Update conftest.py to set dynamic topic env vars**

Replace the existing `TOPIC_*` entries in `tests/conftest.py` with:

```python
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
```

- [ ] **Step 2: Rewrite `tests/unit/test_routing.py` for the new API**

Replace the entire file content:

```python
import os
import pytest

from bot.telegram import router
from bot.telegram.topics import all_topics, get_thread_id


def test_get_thread_id_returns_correct_id_for_configured_topic():
    # TOPIC_WEATHER_ID=2 is set in conftest.py
    assert get_thread_id("weather") == 2


def test_get_thread_id_returns_none_for_unconfigured_topic():
    assert get_thread_id("nonexistent_topic") is None


def test_get_thread_id_returns_none_for_zero_value(monkeypatch):
    monkeypatch.setenv("TOPIC_ZERO_ID", "0")
    assert get_thread_id("zero") is None


def test_all_topics_includes_configured_topics():
    topics = all_topics()
    assert "weather" in topics
    assert "events" in topics
    assert "spanish" in topics


def test_all_topics_excludes_zero_values(monkeypatch):
    monkeypatch.setenv("TOPIC_EMPTY_ID", "0")
    assert "empty" not in all_topics()


def test_topic_name_derived_from_env_var_key():
    # TOPIC_SPANISH_ID → topic name "spanish"
    assert get_thread_id("spanish") == 5


def test_unknown_content_type_falls_back_to_general():
    assert router.route("nonexistent_type") == "general"


def test_known_content_types_map_to_expected_topics():
    assert router.route("weather") == "weather"
    assert router.route("event") == "events"
    assert router.route("bureaucracy") == "bureaucracy"
    assert router.route("spanish_word") == "spanish"
    assert router.route("english_word") == "english"
    assert router.route("general") == "general"
```

- [ ] **Step 3: Run tests — expect failures**

```bash
make test
```

Expected: failures in `test_routing.py` (constants no longer exist, `all_topics` not defined).

- [ ] **Step 4: Rewrite `bot/telegram/topics.py`**

Replace the entire file:

```python
import os
import re

_PATTERN = re.compile(r'^TOPIC_(.+)_ID$')


def _load_topic_map() -> dict[str, int]:
    result: dict[str, int] = {}
    for key, value in os.environ.items():
        m = _PATTERN.match(key)
        if m and value.strip():
            try:
                thread_id = int(value.strip())
                if thread_id != 0:
                    result[m.group(1).lower()] = thread_id
            except ValueError:
                pass
    return result


def get_thread_id(topic_name: str) -> int | None:
    """Return the Telegram message_thread_id for a topic name, or None if not configured."""
    return _load_topic_map().get(topic_name)


def all_topics() -> list[str]:
    """Return all configured topic names."""
    return list(_load_topic_map().keys())
```

- [ ] **Step 5: Run tests — expect routing tests to pass**

```bash
make test
```

Expected: all `test_routing.py` tests pass. `test_sources.py` may fail (sources still import old constants) — that's fine, fixed in Task 2.

- [ ] **Step 6: Commit**

```bash
git add bot/telegram/topics.py tests/unit/test_routing.py tests/conftest.py
git commit -m "refactor: dynamic topic discovery from TOPIC_*_ID env vars"
```

---

### Task 2: Update `bot/telegram/router.py` — remove constant imports

**Files:**
- Modify: `bot/telegram/router.py`

- [ ] **Step 1: Replace constant references with plain strings**

Replace the entire file:

```python
# Maps content/source type labels → logical topic names.
# Topic names must match the middle segment of TOPIC_*_ID env vars (lowercase).
CONTENT_TYPE_ROUTING: dict[str, str] = {
    "weather": "weather",
    "event": "events",
    "bureaucracy": "bureaucracy",
    "spanish_word": "spanish",
    "english_word": "english",
    "announcement": "announcements",
    "general": "general",
}


def route(content_type: str) -> str:
    """Return the logical topic name for a given content type.

    Falls back to 'general' if the content_type is unknown.
    """
    return CONTENT_TYPE_ROUTING.get(content_type, "general")
```

- [ ] **Step 2: Run tests**

```bash
make test
```

Expected: routing tests still pass.

- [ ] **Step 3: Commit**

```bash
git add bot/telegram/router.py
git commit -m "refactor: remove hardcoded topic constants from router"
```

---

### Task 3: Update `bot/sources/base.py` and all sources

**Files:**
- Modify: `bot/sources/base.py`
- Modify: `bot/sources/weather_source.py`
- Modify: `bot/sources/events_source.py`
- Modify: `bot/sources/bureaucracy_source.py`
- Modify: `bot/sources/language_source.py`

- [ ] **Step 1: Update `bot/sources/base.py`**

Replace the entire file:

```python
from abc import ABC, abstractmethod
from typing import Any


class BaseSource(ABC):
    """All content sources must implement this interface."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique machine-readable identifier for this source."""

    @property
    @abstractmethod
    def default_topic(self) -> str:
        """Logical topic name where items from this source are posted.

        Must match the middle segment of the corresponding TOPIC_*_ID env var.
        Example: 'weather' matches TOPIC_WEATHER_ID.
        """

    @property
    def target_topic(self) -> str:
        """Resolved topic name (equals default_topic — override point for subclasses)."""
        return self.default_topic

    @abstractmethod
    async def fetch_items(self) -> list[dict[str, Any]]:
        """Fetch items from the underlying data source.

        Each item must include at least:
          - 'id': str  — unique identifier within this source
          - 'title': str  — short title used for deduplication and display

        Returns an empty list when there is nothing to post.
        """

    @abstractmethod
    def format_item(self, item: dict[str, Any]) -> str:
        """Convert a raw item dict into a Telegram HTML message string."""
```

- [ ] **Step 2: Update `bot/sources/weather_source.py`**

Replace only the import line and the `target_topic` property:

```python
import random
from datetime import date
from typing import Any

from bot.sources.base import BaseSource

# TODO: Replace mock data with AEMET OpenData API
# Endpoint: https://opendata.aemet.es/opendata/api/prediccion/especifica/municipio/diaria/{municipio_id}
# Municipality code for Sagunto: 46220
# Requires API key: https://opendata.aemet.es/centrodedescargas/altaUsuario


_CONDITIONS = ["Sunny", "Partly cloudy", "Cloudy", "Light rain", "Clear"]
_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


class WeatherSource(BaseSource):
    @property
    def name(self) -> str:
        return "weather"

    @property
    def default_topic(self) -> str:
        return "weather"

    async def fetch_items(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        return [
            {
                "id": f"weather_{today}",
                "title": f"Weather Sagunto {today}",
                "date": today,
                "condition": random.choice(_CONDITIONS),
                "temp_max": random.randint(18, 35),
                "temp_min": random.randint(10, 20),
                "wind_speed": random.randint(5, 40),
                "wind_dir": random.choice(_DIRECTIONS),
                "humidity": random.randint(30, 90),
            }
        ]

    def format_item(self, item: dict[str, Any]) -> str:
        return (
            f"☀️ <b>Weather in Sagunto — {item['date']}</b>\n\n"
            f"🌡 Temperature: {item['temp_min']}°C – {item['temp_max']}°C\n"
            f"🌤 Conditions: {item['condition']}\n"
            f"💨 Wind: {item['wind_speed']} km/h {item['wind_dir']}\n"
            f"💧 Humidity: {item['humidity']}%\n\n"
            f"<i>Data: mock (AEMET integration pending)</i>"
        )
```

- [ ] **Step 3: Update `bot/sources/events_source.py`**

Replace `target_topic` property and remove the `EVENTS` import:

```python
import random
from datetime import date, timedelta
from typing import Any

from bot.sources.base import BaseSource

# TODO: Replace mock data with real event APIs such as:
# - Eventbrite API: https://www.eventbrite.com/platform/api
# - Ajuntament de Sagunt open data portal
# - Local RSS feeds


_EVENT_TEMPLATES = [
    ("Summer Concert at Teatre Romà", "Teatre Romà"),
    ("Local Market — Mercat Artesà", "Plaça Major"),
    ("Photography Exhibition", "Centre Cultural"),
    ("Flamenco Night", "Casa de la Cultura"),
    ("Triathlon Sagunto", "Port de Sagunt"),
    ("Book Fair — Fira del Llibre", "Plaça de l'Exèdra"),
]


class EventsSource(BaseSource):
    @property
    def name(self) -> str:
        return "events"

    @property
    def default_topic(self) -> str:
        return "events"

    async def fetch_items(self) -> list[dict[str, Any]]:
        today = date.today()
        events = []
        for i, (title, venue) in enumerate(random.sample(_EVENT_TEMPLATES, k=2)):
            event_date = today + timedelta(days=random.randint(1, 14))
            events.append(
                {
                    "id": f"event_{today.isoformat()}_{i}",
                    "title": title,
                    "venue": venue,
                    "event_date": event_date.isoformat(),
                }
            )
        return events

    def format_item(self, item: dict[str, Any]) -> str:
        return (
            f"📅 <b>{item['title']}</b>\n\n"
            f"📍 {item['venue']}\n"
            f"🗓 {item['event_date']}\n\n"
            f"<i>Data: mock (real API integration pending)</i>"
        )
```

- [ ] **Step 4: Update `bot/sources/bureaucracy_source.py`**

Replace `target_topic` property and remove the `BUREAUCRACY` import:

```python
import random
from datetime import date
from typing import Any

from bot.sources.base import BaseSource

# TODO: Replace mock data with real sources such as:
# - BOE (Boletín Oficial del Estado) RSS: https://www.boe.es/rss/
# - Generalitat Valenciana open data: https://dadesobertes.gva.es
# - Ajuntament de Sagunt official announcements


_REMINDERS = [
    {
        "id": "empadronamiento",
        "title": "Empadronamiento reminder",
        "body": (
            "📋 <b>Bureaucracy Reminder: Empadronamiento</b>\n\n"
            "If you have recently moved to Sagunto, remember to register your "
            "residence (<i>empadronarse</i>) at the Ajuntament.\n\n"
            "📍 Plaça Major, 1 — Mon/Wed/Fri 9:00–14:00\n"
            "📞 962 65 58 58\n\n"
            "<i>Data: mock (official API integration pending)</i>"
        ),
    },
    {
        "id": "nie_nie",
        "title": "NIE renewal reminder",
        "body": (
            "🪪 <b>Bureaucracy Reminder: NIE / TIE Renewal</b>\n\n"
            "Check the expiry date on your NIE/TIE. Renewal appointments can be "
            "booked online through the Sede Electrónica de Extranjería.\n\n"
            "🔗 sede.administracionespublicas.gob.es\n\n"
            "<i>Data: mock (official API integration pending)</i>"
        ),
    },
    {
        "id": "ibi_tax",
        "title": "IBI property tax reminder",
        "body": (
            "🏠 <b>Bureaucracy Reminder: IBI Property Tax</b>\n\n"
            "The voluntary IBI payment period typically runs Sept–Nov in Sagunto. "
            "Pay early to avoid surcharges.\n\n"
            "📍 Oficina de Recaptació — C/ Doctor Simarro\n\n"
            "<i>Data: mock (official calendar integration pending)</i>"
        ),
    },
]


class BureaucracySource(BaseSource):
    @property
    def name(self) -> str:
        return "bureaucracy"

    @property
    def default_topic(self) -> str:
        return "bureaucracy"

    async def fetch_items(self) -> list[dict[str, Any]]:
        reminder = random.choice(_REMINDERS)
        today = date.today().isoformat()
        return [
            {
                "id": f"{reminder['id']}_{today}",
                "title": reminder["title"],
                "body": reminder["body"],
            }
        ]

    def format_item(self, item: dict[str, Any]) -> str:
        return item["body"]
```

- [ ] **Step 5: Update `bot/sources/language_source.py`**

Replace `target_topic` properties and remove topic constant imports:

```python
import random
from datetime import date
from typing import Any

from bot.sources.base import BaseSource

# TODO: Replace mock data with real dictionary/language APIs such as:
# - WordsAPI (wordsapi.com) for English
# - DRAE API (dle.rae.es) for Spanish
# - Merriam-Webster Dictionary API


_SPANISH_WORDS = [
    ("acoger", "to welcome / to shelter", "La comunidad acoge a los recién llegados."),
    ("madrugada", "early morning / dawn", "Llegó a casa de madrugada."),
    ("arraigo", "rootedness / ties to a place", "Tiene mucho arraigo en el pueblo."),
    ("cotidiano", "everyday / daily", "Es parte de la vida cotidiana."),
    ("sosiego", "peace / calm", "Encontró sosiego en la naturaleza."),
]

_ENGLISH_WORDS = [
    ("perseverance", "n. continued effort despite difficulty", "Perseverance is key to success."),
    ("eloquent", "adj. fluent and persuasive in speech", "She gave an eloquent speech."),
    ("mundane", "adj. ordinary, not exciting", "Even mundane tasks have value."),
    ("ephemeral", "adj. lasting a very short time", "Fame can be ephemeral."),
    ("serendipity", "n. happy accident or pleasant surprise", "Finding the café was pure serendipity."),
]


class SpanishWordSource(BaseSource):
    @property
    def name(self) -> str:
        return "spanish_word"

    @property
    def default_topic(self) -> str:
        return "spanish"

    async def fetch_items(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        word, definition, example = random.choice(_SPANISH_WORDS)
        return [
            {
                "id": f"es_{today}",
                "title": f"Spanish word: {word}",
                "word": word,
                "definition": definition,
                "example": example,
            }
        ]

    def format_item(self, item: dict[str, Any]) -> str:
        return (
            f"🇪🇸 <b>Spanish Word of the Day</b>\n\n"
            f"<b>{item['word']}</b>\n"
            f"📖 {item['definition']}\n\n"
            f"💬 <i>{item['example']}</i>\n\n"
            f"<i>Data: mock (DRAE API integration pending)</i>"
        )


class EnglishWordSource(BaseSource):
    @property
    def name(self) -> str:
        return "english_word"

    @property
    def default_topic(self) -> str:
        return "english"

    async def fetch_items(self) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        word, definition, example = random.choice(_ENGLISH_WORDS)
        return [
            {
                "id": f"en_{today}",
                "title": f"English word: {word}",
                "word": word,
                "definition": definition,
                "example": example,
            }
        ]

    def format_item(self, item: dict[str, Any]) -> str:
        return (
            f"🇬🇧 <b>English Word of the Day</b>\n\n"
            f"<b>{item['word']}</b>\n"
            f"📖 {item['definition']}\n\n"
            f"💬 <i>{item['example']}</i>\n\n"
            f"<i>Data: mock (WordsAPI integration pending)</i>"
        )
```

- [ ] **Step 6: Update `tests/unit/test_sources.py` — fix topic assertions**

Replace topic constant references with plain strings:

```python
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
```

- [ ] **Step 7: Run all tests**

```bash
make test
```

Expected: 22 passed.

- [ ] **Step 8: Commit**

```bash
git add bot/sources/ tests/unit/test_sources.py
git commit -m "refactor: sources use default_topic string, remove topics constant imports"
```

---

### Task 4: Clean up `bot/config.py`

**Files:**
- Modify: `bot/config.py`

- [ ] **Step 1: Remove all `topic_*_id` fields and their validator entries**

Replace the entire file:

```python
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    telegram_group_id: int = 0  # discovered via /id command after first run

    # Database
    database_url: str

    # App
    log_level: str = "INFO"
    app_env: str = "local"

    # Schedules (cron expressions)
    schedule_weather: str = "0 8 * * *"
    schedule_spanish_word: str = "0 9 * * *"
    schedule_english_word: str = "0 9 * * *"
    schedule_events: str = "0 */6 * * *"
    schedule_bureaucracy: str = "0 10 * * 1,4"

    @field_validator("telegram_group_id", mode="before")
    @classmethod
    def empty_str_to_zero(cls, v: object) -> object:
        if v == "":
            return 0
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()  # type: ignore[call-arg]
```

- [ ] **Step 2: Run all tests**

```bash
make test
```

Expected: 22 passed.

- [ ] **Step 3: Commit**

```bash
git add bot/config.py
git commit -m "refactor: remove hardcoded topic_*_id fields from config"
```

---

### Task 5: Update `.env.example`

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Replace the fixed topic block with a free-form pattern section**

Replace the entire file:

```bash
# ── Telegram ──────────────────────────────────────────────────────────────────
# IMPORTANT: Keep your bot token private. Never commit this file with real values.
TELEGRAM_BOT_TOKEN=

# Supergroup ID (negative number, e.g. -1001234567890)
# Discover it by sending /id in the group after starting the bot.
TELEGRAM_GROUP_ID=

# ── Topics ────────────────────────────────────────────────────────────────────
# Add one line per topic. Format: TOPIC_<NAME>_ID=<thread_id>
# The NAME (lowercase) must match the target_topic of the source that posts there.
# Discover thread IDs by sending /where inside each topic.
#
# Examples:
TOPIC_GENERAL_ID=
TOPIC_WEATHER_ID=
TOPIC_SPANISH_ID=
TOPIC_ENGLISH_ID=
TOPIC_BUREAUCRACY_ID=
TOPIC_EVENTS_ID=
TOPIC_ACTIVITIES_ID=
#
# To remove a topic: delete or comment out its line. No code changes needed.
# To add a topic:   add a new TOPIC_<NAME>_ID= line. No code changes needed.

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://sagunto_bot_user:CHANGE_ME@postgres:5432/sagunto_hub_bot
POSTGRES_DB=sagunto_hub_bot
POSTGRES_USER=sagunto_bot_user
POSTGRES_PASSWORD=CHANGE_ME

# ── App ────────────────────────────────────────────────────────────────────────
LOG_LEVEL=INFO
APP_ENV=local

# ── Schedules (cron expressions) ──────────────────────────────────────────────
SCHEDULE_WEATHER=0 8 * * *
SCHEDULE_SPANISH_WORD=0 9 * * *
SCHEDULE_ENGLISH_WORD=0 9 * * *
SCHEDULE_EVENTS=0 */6 * * *
SCHEDULE_BUREAUCRACY=0 10 * * 1,4
```

- [ ] **Step 2: Run all tests**

```bash
make test
```

Expected: 22 passed.

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: update .env.example with free-form TOPIC_*_ID pattern"
```

---

### Task 6: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add "Managing Topics" section after "Step 6"**

Add this new section between "Step 6 — Complete Configuration and Restart" and "Running Tests":

````markdown
## Managing Topics

Topics are fully driven by `.env`. No code changes are ever needed to add or remove one.

### Naming convention

The topic name is the middle segment of `TOPIC_*_ID`, **lowercased**:

| Env var | Topic name used by sources |
|---|---|
| `TOPIC_WEATHER_ID` | `weather` |
| `TOPIC_SPANISH_ID` | `spanish` |
| `TOPIC_SPANISH_LEARNING_ID` | `spanish_learning` |

### Adding a topic

1. Create the topic in your Telegram supergroup.
2. Send `/where` inside the new topic — copy the **Thread ID**.
3. Add one line to `.env`:
   ```
   TOPIC_WEATHER_ID=42
   ```
4. Restart the bot:
   ```bash
   make down && make up
   ```

No code changes needed.

### Removing a topic

Delete or comment out the line in `.env`:

```
# TOPIC_ANNOUNCEMENTS_ID=13
```

Restart the bot. The topic is ignored — existing posted_items records are kept in the DB.

### Built-in sources and their default topics

| Source | Default topic name | Env var to configure |
|---|---|---|
| WeatherSource | `weather` | `TOPIC_WEATHER_ID` |
| EventsSource | `events` | `TOPIC_EVENTS_ID` |
| BureaucracySource | `bureaucracy` | `TOPIC_BUREAUCRACY_ID` |
| SpanishWordSource | `spanish` | `TOPIC_SPANISH_ID` |
| EnglishWordSource | `english` | `TOPIC_ENGLISH_ID` |

If a source's `default_topic` has no matching `TOPIC_*_ID` in `.env`, the bot sends the message to the **main group chat** instead of a topic (silent fallback, no crash).
````

- [ ] **Step 2: Update the "Adding a New Source" section**

Replace the existing section content to reference `default_topic` instead of `target_topic` constant:

````markdown
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
        # e.g. default_topic = "weather" → reads TOPIC_WEATHER_ID
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
````

- [ ] **Step 3: Run all tests**

```bash
make test
```

Expected: 22 passed.

- [ ] **Step 4: Commit and push**

```bash
git add README.md
git commit -m "docs: add Managing Topics section with TOPIC_*_ID pattern guide"
git push
```
