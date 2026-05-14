import pytest

from bot.telegram import router, topics


def test_known_content_types_map_to_expected_topics():
    assert router.route("weather") == topics.ACTIVITIES
    assert router.route("event") == topics.EVENTS
    assert router.route("bureaucracy") == topics.BUREAUCRACY
    assert router.route("spanish_word") == topics.SPANISH
    assert router.route("english_word") == topics.ENGLISH
    assert router.route("announcement") == topics.ANNOUNCEMENTS
    assert router.route("general") == topics.GENERAL


def test_unknown_content_type_falls_back_to_general():
    assert router.route("nonexistent_type") == topics.GENERAL


def test_get_thread_id_returns_none_for_unconfigured_topic():
    # All topic IDs default to 0 in test env — should return None
    result = topics.get_thread_id(topics.GENERAL)
    assert result is None


def test_get_thread_id_returns_none_for_unknown_topic():
    result = topics.get_thread_id("unknown_topic")
    assert result is None
