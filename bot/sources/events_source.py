import random
from datetime import date, timedelta
from typing import Any

from bot.sources.base import BaseSource
from bot.telegram.topics import EVENTS

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
    def target_topic(self) -> str:
        return EVENTS

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
