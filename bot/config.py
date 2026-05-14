from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    telegram_bot_token: str
    telegram_group_id: int = 0  # discovered via /id command after first run

    # Database
    database_url: str

    # App
    log_level: str = "INFO"
    app_env: str = "local"
    max_warnings: int = 3

    # Schedules (cron expressions)
    schedule_weather: str = "0 8 * * *"
    schedule_spanish_word: str = "0 9 * * *"
    schedule_english_word: str = "0 9 * * *"
    schedule_events: str = "0 */6 * * *"
    schedule_bureaucracy: str = "0 10 * * 1,4"

    @field_validator("telegram_group_id", mode="before")
    @classmethod
    def empty_str_to_zero(cls, v: object) -> object:
        if v == "":
            return 0
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()  # type: ignore[call-arg]
