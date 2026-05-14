from bot.config import settings

# Logical topic names used throughout the codebase
GENERAL = "general"
SPANISH = "spanish"
ENGLISH = "english"
BUREAUCRACY = "bureaucracy"
EVENTS = "events"
ACTIVITIES = "activities"
ANNOUNCEMENTS = "announcements"

ALL_TOPICS = [GENERAL, SPANISH, ENGLISH, BUREAUCRACY, EVENTS, ACTIVITIES, ANNOUNCEMENTS]


def get_thread_id(topic_name: str) -> int | None:
    """Return the Telegram message_thread_id for a logical topic name.

    Returns None when the topic ID is not configured (value == 0),
    which causes the message to be sent to the main chat instead.
    """
    mapping: dict[str, int] = {
        GENERAL: settings.topic_general_id,
        SPANISH: settings.topic_spanish_id,
        ENGLISH: settings.topic_english_id,
        BUREAUCRACY: settings.topic_bureaucracy_id,
        EVENTS: settings.topic_events_id,
        ACTIVITIES: settings.topic_activities_id,
        ANNOUNCEMENTS: settings.topic_announcements_id,
    }
    thread_id = mapping.get(topic_name, 0)
    return thread_id if thread_id != 0 else None
