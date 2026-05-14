from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    telegram_group_id: int = 0  # discovered via /id command after first run

    # Topic thread IDs (0 means "not configured / use general chat")
    topic_general_id: int = 0
    topic_spanish_id: int = 0
    topic_english_id: int = 0
    topic_bureaucracy_id: int = 0
    topic_events_id: int = 0
    topic_activities_id: int = 0
    topic_announcements_id: int = 0

    # Database
    database_url: str

    # App
    log_level: str = "INFO"
    app_env: str = "local"

    # Schedules (cron expressions)
    schedule_weather: str = "0 8 * * *"
    schedule_spanish_word: str = "0 9 * * *"
    schedule_english_word: str = "0 9 * * *"
    schedule_events: str = "0 */6 * * *"
    schedule_bureaucracy: str = "0 10 * * 1,4"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()  # type: ignore[call-arg]
