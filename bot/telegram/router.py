from bot.telegram import topics

# Maps content/source type labels → logical topic names.
# Extend this dict when adding new source types.
CONTENT_TYPE_ROUTING: dict[str, str] = {
    "weather": topics.ACTIVITIES,
    "event": topics.EVENTS,
    "bureaucracy": topics.BUREAUCRACY,
    "spanish_word": topics.SPANISH,
    "english_word": topics.ENGLISH,
    "announcement": topics.ANNOUNCEMENTS,
    "general": topics.GENERAL,
}


def route(content_type: str) -> str:
    """Return the logical topic name for a given content type.

    Falls back to GENERAL if the content_type is unknown.
    """
    return CONTENT_TYPE_ROUTING.get(content_type, topics.GENERAL)
