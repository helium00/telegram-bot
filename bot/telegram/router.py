# Maps content/source type labels → logical topic names.
# Extend this dict when adding new source types.
CONTENT_TYPE_ROUTING: dict[str, str] = {
    "weather": "weather",
    "event": "events",
    "bureaucracy": "bureaucracy",
    "spanish_word": "spanish",
    "english_word": "english",
    "announcement": "announcements",
    "general": "general",
}

_FALLBACK = "general"


def route(content_type: str) -> str:
    """Return the logical topic name for a given content type.

    Falls back to 'general' if the content_type is unknown.
    """
    return CONTENT_TYPE_ROUTING.get(content_type, _FALLBACK)
