import pytest
from pydantic import ValidationError

from app.core import config
from app.core.config import Settings


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
