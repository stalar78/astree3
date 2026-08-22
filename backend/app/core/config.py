from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt, PostgresDsn
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
    private_media_root: Path = Field(default=Path("var/private"), alias="PRIVATE_MEDIA_ROOT")
    candidate_photo_max_bytes: PositiveInt = Field(
        default=10 * 1024 * 1024,
        alias="CANDIDATE_PHOTO_MAX_BYTES",
    )
    candidate_photo_max_pixels: PositiveInt = Field(
        default=20_000_000,
        alias="CANDIDATE_PHOTO_MAX_PIXELS",
    )
    candidate_photo_max_edge: PositiveInt = Field(default=6000, alias="CANDIDATE_PHOTO_MAX_EDGE")
    candidate_photo_output_max_edge: PositiveInt = Field(
        default=2048,
        alias="CANDIDATE_PHOTO_OUTPUT_MAX_EDGE",
    )

    @property
    def debug(self) -> bool:
        return self.app_env.lower() in {"local", "development", "dev", "test"}

    @property
    def is_development(self) -> bool:
        return self.debug

    @property
    def sqlalchemy_database_uri(self) -> str:
        database_url = str(self.database_url)
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
