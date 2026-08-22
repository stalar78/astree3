from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "Astrea API"
    api_v1_prefix: str = "/api/v1"
    app_env: str = Field(default="local", alias="APP_ENV")
    database_url: PostgresDsn = Field(alias="DATABASE_URL")

    @property
    def debug(self) -> bool:
        return self.app_env.lower() in {"local", "development", "dev", "test"}

    @property
    def is_development(self) -> bool:
        return self.debug

    @property
    def sqlalchemy_database_uri(self) -> str:
        return str(self.database_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
