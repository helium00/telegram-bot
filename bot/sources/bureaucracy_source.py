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
