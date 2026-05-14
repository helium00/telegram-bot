import random
from datetime import date
from typing import Any

from bot.sources.base import BaseSource
from bot.telegram.topics import ACTIVITIES

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
    def target_topic(self) -> str:
        return ACTIVITIES

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
