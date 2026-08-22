from functools import lru_cache
from pathlib import Path

from pydantic import Field, PositiveInt, PostgresDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.services.candidate_intake import CandidateConsentVersions


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
    admin_initial_username: str | None = Field(default=None, alias="ADMIN_INITIAL_USERNAME")
    admin_initial_password: SecretStr | None = Field(
        default=None,
        alias="ADMIN_INITIAL_PASSWORD",
    )
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
    candidate_intake_enabled: bool = Field(default=False, alias="CANDIDATE_INTAKE_ENABLED")
    candidate_personal_data_consent_version: str | None = Field(
        default=None,
        alias="CANDIDATE_PERSONAL_DATA_CONSENT_VERSION",
    )
    candidate_privacy_policy_version: str | None = Field(
        default=None,
        alias="CANDIDATE_PRIVACY_POLICY_VERSION",
    )
    candidate_saint_petersburg_acknowledgement_version: str | None = Field(
        default=None,
        alias="CANDIDATE_SAINT_PETERSBURG_ACKNOWLEDGEMENT_VERSION",
    )
    candidate_rate_limit_requests: PositiveInt = Field(
        default=5,
        alias="CANDIDATE_RATE_LIMIT_REQUESTS",
    )
    candidate_rate_limit_window_seconds: PositiveInt = Field(
        default=900,
        alias="CANDIDATE_RATE_LIMIT_WINDOW_SECONDS",
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

    @property
    def candidate_consent_versions(self) -> CandidateConsentVersions:
        return CandidateConsentVersions(
            personal_data_processing=self.candidate_personal_data_consent_version or "",
            privacy_policy_acknowledgement=self.candidate_privacy_policy_version or "",
            saint_petersburg_acknowledgement=(
                self.candidate_saint_petersburg_acknowledgement_version or ""
            ),
        )

    @model_validator(mode="after")
    def _validate_candidate_intake_settings(self) -> "Settings":
        if not self.candidate_intake_enabled:
            return self

        self.candidate_personal_data_consent_version = _normalize_enabled_version(
            self.candidate_personal_data_consent_version,
            "CANDIDATE_PERSONAL_DATA_CONSENT_VERSION",
        )
        self.candidate_privacy_policy_version = _normalize_enabled_version(
            self.candidate_privacy_policy_version,
            "CANDIDATE_PRIVACY_POLICY_VERSION",
        )
        self.candidate_saint_petersburg_acknowledgement_version = _normalize_enabled_version(
            self.candidate_saint_petersburg_acknowledgement_version,
            "CANDIDATE_SAINT_PETERSBURG_ACKNOWLEDGEMENT_VERSION",
        )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _normalize_enabled_version(value: str | None, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be configured when candidate intake is enabled")

    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be configured when candidate intake is enabled")
    if len(normalized) > 80:
        raise ValueError(f"{field_name} must not exceed 80 characters")
    return normalized
