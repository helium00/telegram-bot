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
        """Resolved topic name (equals default_topic)."""
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
