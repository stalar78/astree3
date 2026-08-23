import smtplib
from datetime import UTC, datetime
from email.message import EmailMessage

import pytest

from app.core.config import Settings
from app.services.email_delivery import (
    CandidateConsentSnapshot,
    CandidateNotificationSnapshot,
    EmailDeliveryConfigError,
    EmailDeliveryPermanentError,
    EmailDeliveryTemporaryError,
    SmtpEmailTransport,
    render_candidate_notification_email,
    smtp_delivery_config_from_settings,
)


def _settings(**overrides) -> Settings:
    values = {
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/astrea",
        "APP_ENV": "test",
        "SMTP_HOST": "smtp.example.test",
        "SMTP_FROM_EMAIL": "notifications@example.test",
        "APPLICATION_NOTIFICATION_EMAIL": "admin@example.test",
        "SITE_BASE_URL": "https://astrea.example.test/",
    }
    values.update(overrides)
    return Settings(**values)


def _snapshot() -> CandidateNotificationSnapshot:
    return CandidateNotificationSnapshot(
        application_id=42,
        created_at=datetime(2026, 8, 23, 7, 15, tzinfo=UTC),
        full_name="<script>alert('x')</script>",
        date_of_birth=None,
        city="Saint Petersburg",
        phone="+7 900 000 00 00",
        email="candidate@example.test",
        education="Education\nSecond line",
        occupation="Engineer",
        marital_status="Single",
        other_organizations="None",
        social_links="https://example.test/profile\n<script>bad</script>",
        motivation="Please review",
        has_photo=True,
        consents=(
            CandidateConsentSnapshot("personal_data_processing", datetime.now(UTC), "v1"),
            CandidateConsentSnapshot("privacy_policy_acknowledgement", datetime.now(UTC), "v1"),
            CandidateConsentSnapshot("saint_petersburg_acknowledgement", datetime.now(UTC), "v1"),
        ),
    )


def test_delivery_config_is_optional_for_normal_settings_and_validates_worker_config() -> None:
    settings = Settings(DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/astrea")
    assert settings.smtp_host is None
    assert settings.application_notification_email == "info@mason-astrea.ru"

    config = smtp_delivery_config_from_settings(_settings())
    assert config.site_base_url == "https://astrea.example.test"
    assert smtp_delivery_config_from_settings(_settings(SITE_BASE_URL="http://localhost:8080")).site_base_url == "http://localhost:8080"

    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(SMTP_SECURITY="imap"))
    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(SMTP_USERNAME="user"))
    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(SMTP_PASSWORD="secret"))
    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(SITE_BASE_URL="http://example.test"))
    for value in (
        "https://user:pass@astrea.example.test",
        "https://astrea.example.test?token=1",
        "https://astrea.example.test#frag",
    ):
        with pytest.raises(EmailDeliveryConfigError):
            smtp_delivery_config_from_settings(_settings(SITE_BASE_URL=value))
    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(SMTP_FROM_EMAIL="bad\r\nBcc:evil@example.test"))
    with pytest.raises(EmailDeliveryConfigError):
        smtp_delivery_config_from_settings(_settings(APPLICATION_NOTIFICATION_EMAIL="bad\r\nBcc:evil@example.test"))


def test_renderer_has_plain_and_html_parts_and_escapes_candidate_content() -> None:
    message = render_candidate_notification_email(_snapshot(), smtp_delivery_config_from_settings(_settings()))
    assert isinstance(message, EmailMessage)
    assert "candidate@example.test" not in message["To"]
    assert "<script>" not in message["Subject"]
    assert "42" in message["Subject"]
    body = message.get_body(preferencelist=("html",)).get_content()
    plain = message.get_body(preferencelist=("plain",)).get_content()
    assert "&lt;script&gt;alert" in body
    assert "<script>bad</script>" not in body
    assert "Education" in plain
    assert "23.08.2026 10:15 MSK" in plain
    assert "https://astrea.example.test/admin/candidates/42" in plain
    assert "photo_storage" not in body
    assert "private" not in body


def test_smtp_transport_starttls_uses_verified_context_and_login(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    context = object()

    class FakeSmtp:
        def __init__(self, host, port, timeout):
            calls.append(("init", (host, port, timeout)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            calls.append(("ehlo", None))

        def starttls(self, context):
            calls.append(("starttls", context))

        def login(self, username, password):
            calls.append(("login", (username, password)))

        def send_message(self, message):
            calls.append(("send", message))

    monkeypatch.setattr("smtplib.SMTP", FakeSmtp)
    monkeypatch.setattr("ssl.create_default_context", lambda: context)
    config = smtp_delivery_config_from_settings(_settings(SMTP_USERNAME="user", SMTP_PASSWORD="secret"))
    SmtpEmailTransport(config).send(EmailMessage())
    assert calls[0] == ("init", ("smtp.example.test", 587, 15))
    assert calls[1][0] == "ehlo"
    assert calls[2] == ("starttls", context)
    assert calls[3] == ("ehlo", None)
    assert calls[4] == ("login", ("user", "secret"))
    assert calls[5][0] == "send"


def test_smtp_transport_ssl_mode_uses_ssl_context_and_skips_starttls(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, object]] = []
    context = object()

    class FakeSmtpSsl:
        def __init__(self, host, port, timeout, context=None):
            calls.append(("init", (host, port, timeout, context)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def login(self, username, password):
            calls.append(("login", (username, password)))

        def send_message(self, message):
            calls.append(("send", message))

    monkeypatch.setattr("smtplib.SMTP_SSL", FakeSmtpSsl)
    monkeypatch.setattr("ssl.create_default_context", lambda: context)
    config = smtp_delivery_config_from_settings(_settings(SMTP_SECURITY="ssl", SMTP_USERNAME="user", SMTP_PASSWORD="secret"))
    SmtpEmailTransport(config).send(EmailMessage())
    assert calls[0] == ("init", ("smtp.example.test", 587, 15, context))
    assert calls[1] == ("login", ("user", "secret"))
    assert calls[2][0] == "send"


@pytest.mark.parametrize(
    ("overrides", "login_expected"),
    [
        ({"SMTP_USERNAME": "user", "SMTP_PASSWORD": "secret"}, True),
        ({}, False),
    ],
)
def test_smtp_transport_login_occurs_only_with_complete_credentials(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, str],
    login_expected: bool,
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeSmtp:
        def __init__(self, host, port, timeout):
            calls.append(("init", (host, port, timeout)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            pass

        def login(self, username, password):
            calls.append(("login", (username, password)))

        def send_message(self, message):
            calls.append(("send", message))

    monkeypatch.setattr("smtplib.SMTP", FakeSmtp)
    config = smtp_delivery_config_from_settings(_settings(**overrides))
    SmtpEmailTransport(config).send(EmailMessage())
    assert any(call[0] == "login" for call in calls) is login_expected


@pytest.mark.parametrize(
    ("exc_factory", "expected_type", "expected_message"),
    [
        (lambda: smtplib.SMTPResponseException(421, "provider secret"), EmailDeliveryTemporaryError, "Email delivery failed temporarily"),
        (lambda: smtplib.SMTPResponseException(550, "provider secret"), EmailDeliveryPermanentError, "Email delivery failed permanently"),
        (lambda: TimeoutError("provider secret"), EmailDeliveryTemporaryError, "Email delivery failed temporarily"),
        (lambda: OSError("provider secret"), EmailDeliveryTemporaryError, "Email delivery failed temporarily"),
    ],
)
def test_smtp_transport_classifies_common_failures(
    monkeypatch: pytest.MonkeyPatch,
    exc_factory,
    expected_type,
    expected_message,
) -> None:
    class FailingSmtp:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            raise exc_factory()

    monkeypatch.setattr("smtplib.SMTP", FailingSmtp)
    config = smtp_delivery_config_from_settings(_settings())
    with pytest.raises(expected_type) as exc_info:
        SmtpEmailTransport(config).send(EmailMessage())
    assert str(exc_info.value) == expected_message
    assert "provider" not in str(exc_info.value)


def test_smtp_transport_authentication_error_is_permanent(monkeypatch: pytest.MonkeyPatch) -> None:
    class FailingSmtp:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            pass

        def login(self, username, password):
            raise smtplib.SMTPAuthenticationError(535, "provider secret")

        def send_message(self, message):
            pass

    monkeypatch.setattr("smtplib.SMTP", FailingSmtp)
    config = smtp_delivery_config_from_settings(_settings(SMTP_USERNAME="user", SMTP_PASSWORD="secret"))
    with pytest.raises(EmailDeliveryPermanentError) as exc_info:
        SmtpEmailTransport(config).send(EmailMessage())
    assert str(exc_info.value) == "Email delivery failed permanently"
    assert "provider" not in str(exc_info.value)


def test_smtp_failures_are_classified_without_provider_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class TemporarySmtp:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            raise TimeoutError("provider secret text")

    monkeypatch.setattr("smtplib.SMTP", TemporarySmtp)
    config = smtp_delivery_config_from_settings(_settings())
    with pytest.raises(EmailDeliveryTemporaryError) as exc_info:
        SmtpEmailTransport(config).send(EmailMessage())
    assert str(exc_info.value) == "Email delivery failed temporarily"
    assert "provider" not in str(exc_info.value)


def test_smtp_transport_check_connection_starttls_uses_verified_context_and_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    context = object()

    class FakeSmtp:
        def __init__(self, host, port, timeout):
            calls.append(("init", (host, port, timeout)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            calls.append(("ehlo", None))

        def starttls(self, context):
            calls.append(("starttls", context))

        def login(self, username, password):
            calls.append(("login", (username, password)))

        def send_message(self, message):
            calls.append(("send", message))

    monkeypatch.setattr("smtplib.SMTP", FakeSmtp)
    monkeypatch.setattr("ssl.create_default_context", lambda: context)
    config = smtp_delivery_config_from_settings(_settings(SMTP_USERNAME="user", SMTP_PASSWORD="secret"))

    SmtpEmailTransport(config).check_connection()

    assert calls == [
        ("init", ("smtp.example.test", 587, 15)),
        ("ehlo", None),
        ("starttls", context),
        ("ehlo", None),
        ("login", ("user", "secret")),
    ]
    assert not any(call[0] == "send" for call in calls)


def test_smtp_transport_check_connection_ssl_uses_ssl_context_and_skips_starttls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    context = object()

    class FakeSmtpSsl:
        def __init__(self, host, port, timeout, context=None):
            calls.append(("init", (host, port, timeout, context)))

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def login(self, username, password):
            calls.append(("login", (username, password)))

        def send_message(self, message):
            calls.append(("send", message))

    monkeypatch.setattr("smtplib.SMTP_SSL", FakeSmtpSsl)
    monkeypatch.setattr("ssl.create_default_context", lambda: context)
    config = smtp_delivery_config_from_settings(_settings(SMTP_SECURITY="ssl", SMTP_USERNAME="user", SMTP_PASSWORD="secret"))

    SmtpEmailTransport(config).check_connection()

    assert calls == [
        ("init", ("smtp.example.test", 587, 15, context)),
        ("login", ("user", "secret")),
    ]
    assert not any(call[0] == "send" for call in calls)


@pytest.mark.parametrize(
    ("failure_stage", "exc_factory", "expected_type", "expected_message", "configure_credentials"),
    [
        ("starttls", lambda: TimeoutError("provider secret"), EmailDeliveryTemporaryError, "Email delivery failed temporarily", False),
        (
            "login",
            lambda: smtplib.SMTPAuthenticationError(535, "provider secret"),
            EmailDeliveryPermanentError,
            "Email delivery failed permanently",
            True,
        ),
        (
            "starttls",
            lambda: smtplib.SMTPNotSupportedError("provider secret"),
            EmailDeliveryPermanentError,
            "Email delivery failed permanently",
            False,
        ),
        (
            "starttls",
            lambda: smtplib.SMTPResponseException(421, "provider secret"),
            EmailDeliveryTemporaryError,
            "Email delivery failed temporarily",
            False,
        ),
    ],
)
def test_smtp_transport_check_connection_classifies_failures(
    monkeypatch: pytest.MonkeyPatch,
    failure_stage,
    exc_factory,
    expected_type,
    expected_message,
    configure_credentials,
) -> None:
    class FailingSmtp:
        def __init__(self, *_args, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def ehlo(self):
            pass

        def starttls(self, context):
            if failure_stage == "starttls":
                raise exc_factory()

        def login(self, username, password):
            if failure_stage == "login":
                raise exc_factory()

        def send_message(self, message):
            raise AssertionError("send_message must not be called")

    monkeypatch.setattr("smtplib.SMTP", FailingSmtp)
    overrides = {"SMTP_USERNAME": "user", "SMTP_PASSWORD": "secret"} if configure_credentials else {}
    config = smtp_delivery_config_from_settings(_settings(**overrides))

    with pytest.raises(expected_type) as exc_info:
        SmtpEmailTransport(config).check_connection()

    assert str(exc_info.value) == expected_message
    assert "provider" not in str(exc_info.value)
