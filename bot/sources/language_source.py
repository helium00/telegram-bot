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
