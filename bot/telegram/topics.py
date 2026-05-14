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
