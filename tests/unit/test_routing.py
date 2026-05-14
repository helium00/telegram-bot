import os
import pytest

from bot.telegram import router
from bot.telegram.topics import all_topics, get_thread_id


def test_get_thread_id_returns_correct_id_for_configured_topic():
    assert get_thread_id("weather") == 2


def test_get_thread_id_returns_none_for_unconfigured_topic():
    assert get_thread_id("nonexistent_topic") is None


def test_get_thread_id_returns_none_for_zero_value(monkeypatch):
    monkeypatch.setenv("TOPIC_ZERO_ID", "0")
    assert get_thread_id("zero") is None


def test_all_topics_includes_configured_topics():
    topics = all_topics()
    assert "weather" in topics
    assert "events" in topics
    assert "spanish" in topics


def test_all_topics_excludes_zero_values(monkeypatch):
    monkeypatch.setenv("TOPIC_EMPTY_ID", "0")
    assert "empty" not in all_topics()


def test_topic_name_derived_from_env_var_key():
    assert get_thread_id("spanish") == 5


def test_unknown_content_type_falls_back_to_general():
    assert router.route("nonexistent_type") == "general"


def test_known_content_types_map_to_expected_topics():
    assert router.route("weather") == "weather"
    assert router.route("event") == "events"
    assert router.route("bureaucracy") == "bureaucracy"
    assert router.route("spanish_word") == "spanish"
    assert router.route("english_word") == "english"
    assert router.route("general") == "general"
