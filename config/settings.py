from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    bot_token: str = ""
    webapp_url: str = "http://127.0.0.1:8080"
    backend_url: str = "http://127.0.0.1:8080"
    news_channel_id: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/bydloland.db"

    rcon_host: str = "127.0.0.1"
    rcon_port: int = 25575
    rcon_password: str = ""

    plugin_api_url: str = "http://127.0.0.1:8765"
    plugin_api_key: str = ""

    internal_api_key: str = ""

    map_url: str = ""

    build_windows_url: str = ""
    build_zip_url: str = ""
    build_version: str = "1.21.10"
    build_windows_size: str = ""
    build_zip_size: str = ""

    server_name: str = "БыдлоЛенд"
    server_version: str = "1.21.10"
    server_max_players: int = 100
    miniapp_title: str = "БыдлоЛенд"

    head_admin_telegram_ids: str = ""

    hosting_panel_url: str = "https://mgr.hosting-minecraft.pro"
    hosting_server_id: str = "09390ef6"
    hosting_api_key: str = ""
    minecraft_server_host: str = ""
    minecraft_server_alias: str = ""

    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8080
    app_env: str = "dev"
    dev_telegram_id: int = 1
    dev_username: str = "bydlo_dev"

    report_limit_count: int = 3
    report_limit_minutes: int = 10
    suggestion_limit_count: int = 5
    suggestion_limit_hours: int = 1
    idea_limit_count: int = 10
    idea_limit_hours: int = 1

    @field_validator("bot_token", "internal_api_key", "plugin_api_key", "rcon_password", mode="before")
    @classmethod
    def strip_secrets(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def head_admin_ids(self) -> List[int]:
        result: List[int] = []
        for part in self.head_admin_telegram_ids.split(","):
            part = part.strip()
            if part.isdigit():
                result.append(int(part))
        return result

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def news_channel(self) -> int | None:
        raw = self.news_channel_id.strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
