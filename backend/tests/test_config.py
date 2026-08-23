import pytest
from pydantic import ValidationError

from app.core import config
from app.core.config import Settings
from app.services.email_outbox import email_outbox_policy_from_settings


def test_settings_require_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings()


def test_settings_normalizes_plain_postgresql_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/astrea")

    settings = Settings()

    assert settings.sqlalchemy_database_uri.startswith("postgresql+psycopg://")


def test_settings_preserves_explicit_psycopg_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/astrea")

    settings = Settings()

    assert settings.app_env == "test"
    assert settings.sqlalchemy_database_uri.startswith("postgresql+psycopg://")


def test_settings_expose_admin_auth_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/astrea")

    settings = Settings()

    assert settings.admin_session_ttl_seconds == 28_800
    assert settings.admin_login_rate_limit_requests == 10
    assert settings.admin_login_rate_limit_window_seconds == 900


def test_settings_expose_email_outbox_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/astrea")

    settings = Settings()

    assert settings.email_outbox_batch_size == 10
    assert settings.email_outbox_max_attempts == 5
    assert settings.email_outbox_retry_base_seconds == 60
    assert settings.email_outbox_retry_max_seconds == 3600
    assert settings.email_outbox_processing_timeout_seconds == 900
    assert email_outbox_policy_from_settings(settings).batch_size == 10


def test_settings_reject_invalid_email_outbox_backoff(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/astrea")
    monkeypatch.setenv("EMAIL_OUTBOX_RETRY_BASE_SECONDS", "120")
    monkeypatch.setenv("EMAIL_OUTBOX_RETRY_MAX_SECONDS", "60")

    with pytest.raises(ValidationError):
        Settings()


def test_settings_rejects_non_postgresql_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "mysql://user:pass@localhost:3306/astrea")

    with pytest.raises(ValidationError):
        Settings()


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()
