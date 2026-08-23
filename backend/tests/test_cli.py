from __future__ import annotations

from typing import Any

import pytest

from app import cli
from app.core import config
from app.core.config import Settings
from app.db.session import SessionLocal
from app.services.email_delivery import (
    EmailDeliveryConfigError,
    EmailDeliveryPermanentError,
    EmailDeliveryTemporaryError,
)
from app.services.email_worker import (
    EmailOutboxRunResult,
    EmailWorkerConfigurationError,
    EmailWorkerError,
    EmailWorkerOperationalError,
    EmailWorkerPersistenceError,
)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_process_email_outbox_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    calls: list[tuple[Settings, Any]] = []

    def fake_get_settings() -> Settings:
        return _settings()

    def fake_run(settings: Settings, session_factory, *, transport=None, now=None):
        calls.append((settings, session_factory))
        return EmailOutboxRunResult(recovered=2, claimed=3, sent=4, delivery_failures=1)

    monkeypatch.setattr(cli, "get_settings", fake_get_settings)
    monkeypatch.setattr(cli, "run_email_outbox_once", fake_run)

    exit_code = cli.main(["process-email-outbox"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0][1] is SessionLocal
    assert calls[0][0].database_url == _settings().database_url
    assert captured.err == ""
    assert captured.out.strip() == "Email outbox run completed: recovered=2 claimed=3 sent=4 delivery_failures=1"
    assert "candidate" not in captured.out.lower()
    assert "secret" not in captured.out.lower()


def test_process_email_outbox_invalid_worker_config_is_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    def fail_run(*args, **kwargs):
        raise EmailWorkerConfigurationError("secret")

    monkeypatch.setattr(cli, "run_email_outbox_once", fail_run)

    exit_code = cli.main(["process-email-outbox"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Email outbox configuration is invalid."


def test_process_email_outbox_malformed_settings_are_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/astrea")
    monkeypatch.setenv("EMAIL_OUTBOX_RETRY_BASE_SECONDS", "120")
    monkeypatch.setenv("EMAIL_OUTBOX_RETRY_MAX_SECONDS", "60")

    def fail_run(*args, **kwargs):
        raise AssertionError("worker should not run when settings are invalid")

    monkeypatch.setattr(cli, "run_email_outbox_once", fail_run)

    exit_code = cli.main(["process-email-outbox"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Email outbox configuration is invalid."
    assert "120" not in captured.err
    assert "60" not in captured.err
    assert "traceback" not in captured.err.lower()


@pytest.mark.parametrize(
    "exc_type",
    [EmailWorkerPersistenceError, EmailWorkerOperationalError, EmailWorkerError],
)
def test_process_email_outbox_worker_failures_are_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc_type: type[Exception],
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    def fail_run(*args, **kwargs):
        raise exc_type("provider secret")

    monkeypatch.setattr(cli, "run_email_outbox_once", fail_run)

    exit_code = cli.main(["process-email-outbox"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "Email outbox processing failed."
    assert "provider" not in captured.err.lower()


def test_check_smtp_success(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    created: list[object] = []

    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    class FakeTransport:
        def __init__(self, config):
            created.append(config)

        def check_connection(self):
            return None

    monkeypatch.setattr(cli, "SmtpEmailTransport", FakeTransport)

    exit_code = cli.main(["check-smtp"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.err == ""
    assert captured.out.strip() == "SMTP readiness check succeeded."
    assert created and created[0].host == "smtp.example.test"


def test_check_smtp_invalid_config_is_safe(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    def fail_config(_settings: Settings) -> object:
        raise EmailDeliveryConfigError("secret")

    monkeypatch.setattr(cli, "smtp_delivery_config_from_settings", fail_config)

    exit_code = cli.main(["check-smtp"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == "SMTP readiness configuration is invalid."
    assert "traceback" not in captured.err.lower()


@pytest.mark.parametrize(
    ("exc_type", "expected_message"),
    [
        (EmailDeliveryTemporaryError, "SMTP readiness check failed."),
        (EmailDeliveryPermanentError, "SMTP readiness check failed."),
    ],
)
def test_check_smtp_runtime_failures_are_safe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    exc_type: type[Exception],
    expected_message: str,
) -> None:
    monkeypatch.setattr(cli, "get_settings", lambda: _settings())

    class FailingTransport:
        def __init__(self, config):
            pass

        def check_connection(self):
            raise exc_type("provider secret")

    monkeypatch.setattr(cli, "SmtpEmailTransport", FailingTransport)

    exit_code = cli.main(["check-smtp"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert captured.err.strip() == expected_message
    assert "provider" not in captured.err.lower()
    assert "traceback" not in captured.err.lower()


def _settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/astrea",
        SMTP_HOST="smtp.example.test",
        SMTP_FROM_EMAIL="notifications@example.test",
        APPLICATION_NOTIFICATION_EMAIL="admin@example.test",
        SITE_BASE_URL="https://astrea.example.test/",
    )
