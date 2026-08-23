from __future__ import annotations

import html
import smtplib
import ssl
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
from typing import Protocol
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pydantic import SecretStr

from app.core.config import Settings

MOSCOW = ZoneInfo("Europe/Moscow")
SMTP_SECURITY_STARTTLS = "starttls"
SMTP_SECURITY_SSL = "ssl"
SMTP_SECURITY_MODES = {SMTP_SECURITY_STARTTLS, SMTP_SECURITY_SSL}


@dataclass(frozen=True, slots=True)
class SmtpDeliveryConfig:
    host: str
    port: int
    username: str | None
    password: SecretStr | None
    from_email: str
    notification_email: str
    security: str
    timeout_seconds: int
    site_base_url: str


@dataclass(frozen=True, slots=True)
class CandidateConsentSnapshot:
    consent_type: str
    accepted_at: datetime
    document_version: str


@dataclass(frozen=True, slots=True)
class CandidateNotificationSnapshot:
    application_id: int
    created_at: datetime
    full_name: str | None
    date_of_birth: date | None
    city: str | None
    phone: str | None
    email: str | None
    education: str | None
    occupation: str | None
    marital_status: str | None
    other_organizations: str | None
    social_links: str | None
    motivation: str | None
    has_photo: bool
    consents: tuple[CandidateConsentSnapshot, ...]


class EmailTransport(Protocol):
    def send(self, message: EmailMessage) -> None:
        ...


class EmailDeliveryConfigError(ValueError):
    pass


class EmailDeliveryTemporaryError(RuntimeError):
    pass


class EmailDeliveryPermanentError(RuntimeError):
    pass


def smtp_delivery_config_from_settings(settings: Settings) -> SmtpDeliveryConfig:
    host = _required_text(settings.smtp_host, "SMTP_HOST")
    from_email = _validate_mailbox(_required_text(settings.smtp_from_email, "SMTP_FROM_EMAIL"), "SMTP_FROM_EMAIL")
    notification_email = _validate_mailbox(
        _required_text(settings.application_notification_email, "APPLICATION_NOTIFICATION_EMAIL"),
        "APPLICATION_NOTIFICATION_EMAIL",
    )
    security = settings.smtp_security.strip().lower()
    if security not in SMTP_SECURITY_MODES:
        raise EmailDeliveryConfigError("Email delivery configuration is invalid")
    username = _optional_text(settings.smtp_username)
    password = settings.smtp_password
    if (username is None) != (password is None):
        raise EmailDeliveryConfigError("Email delivery configuration is invalid")
    site_base_url = _normalize_site_base_url(settings.site_base_url, debug=settings.debug)
    return SmtpDeliveryConfig(
        host=host,
        port=settings.smtp_port,
        username=username,
        password=password,
        from_email=from_email,
        notification_email=notification_email,
        security=security,
        timeout_seconds=settings.smtp_timeout_seconds,
        site_base_url=site_base_url,
    )


def render_candidate_notification_email(
    snapshot: CandidateNotificationSnapshot,
    config: SmtpDeliveryConfig,
) -> EmailMessage:
    subject = f"Новая заявка в ДЛ «Астрея» №3 — №{snapshot.application_id}"
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr(("ДЛ Астрея №3", config.from_email))
    message["To"] = config.notification_email
    message.set_content(_render_text(snapshot, config), subtype="plain", charset="utf-8")
    message.add_alternative(_render_html(snapshot, config), subtype="html", charset="utf-8")
    return message


class SmtpEmailTransport:
    def __init__(self, config: SmtpDeliveryConfig) -> None:
        self.config = config

    def send(self, message: EmailMessage) -> None:
        self._run_secure_session(lambda smtp: smtp.send_message(message))

    def check_connection(self) -> None:
        self._run_secure_session(lambda _smtp: None)

    def _run_secure_session(self, action: Callable[[object], None]) -> None:
        try:
            context = ssl.create_default_context()
            if self.config.security == SMTP_SECURITY_SSL:
                with smtplib.SMTP_SSL(
                    self.config.host,
                    self.config.port,
                    timeout=self.config.timeout_seconds,
                    context=context,
                ) as smtp:
                    self._login(smtp)
                    action(smtp)
            else:
                with smtplib.SMTP(self.config.host, self.config.port, timeout=self.config.timeout_seconds) as smtp:
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                    self._login(smtp)
                    action(smtp)
        except (EmailDeliveryTemporaryError, EmailDeliveryPermanentError):
            raise
        except smtplib.SMTPAuthenticationError as exc:
            raise EmailDeliveryPermanentError("Email delivery failed permanently") from exc
        except smtplib.SMTPNotSupportedError as exc:
            raise EmailDeliveryPermanentError("Email delivery failed permanently") from exc
        except smtplib.SMTPRecipientsRefused as exc:
            raise _recipient_refusal_error(exc.recipients) from exc
        except smtplib.SMTPSenderRefused as exc:
            raise _smtp_code_error(exc.smtp_code) from exc
        except smtplib.SMTPDataError as exc:
            raise _smtp_code_error(exc.smtp_code) from exc
        except smtplib.SMTPResponseException as exc:
            raise _smtp_code_error(exc.smtp_code) from exc
        except (TimeoutError, OSError, smtplib.SMTPServerDisconnected) as exc:
            raise EmailDeliveryTemporaryError("Email delivery failed temporarily") from exc

    def _login(self, smtp) -> None:
        if self.config.username and self.config.password:
            smtp.login(self.config.username, self.config.password.get_secret_value())


def _render_text(snapshot: CandidateNotificationSnapshot, config: SmtpDeliveryConfig) -> str:
    admin_link = _admin_link(snapshot, config)
    lines = [
        "Новая заявка в ДЛ «Астрея» №3",
        "",
        f"Внутренний номер: {snapshot.application_id}",
        f"Получено: {_format_moscow(snapshot.created_at)}",
        "",
        "Основные данные",
        f"ФИО: {_value(snapshot.full_name)}",
        f"Дата рождения: {_date_value(snapshot.date_of_birth)}",
        f"Город: {_value(snapshot.city)}",
        "",
        "Контакты",
        f"Телефон: {_value(snapshot.phone)}",
        f"Email: {_value(snapshot.email)}",
        f"Социальные ссылки: {_value(snapshot.social_links)}",
        "",
        "Образование и деятельность",
        f"Образование: {_value(snapshot.education)}",
        f"Деятельность: {_value(snapshot.occupation)}",
        "",
        "Семья",
        f"Семейное положение: {_value(snapshot.marital_status)}",
        "",
        "Дополнительная информация",
        f"Организации: {_value(snapshot.other_organizations)}",
        f"Мотивация: {_value(snapshot.motivation)}",
        "",
        "Подтверждения",
        *_consent_lines(snapshot),
        "",
        "Фотография",
        "Фотография загружена" if snapshot.has_photo else "Фотография не загружена",
        admin_link,
    ]
    return "\n".join(lines)


def _render_html(snapshot: CandidateNotificationSnapshot, config: SmtpDeliveryConfig) -> str:
    admin_link = html.escape(_admin_link(snapshot, config), quote=True)
    rows = [
        ("Внутренний номер", str(snapshot.application_id)),
        ("Получено", _format_moscow(snapshot.created_at)),
        ("ФИО", _value(snapshot.full_name)),
        ("Дата рождения", _date_value(snapshot.date_of_birth)),
        ("Город", _value(snapshot.city)),
        ("Телефон", _value(snapshot.phone)),
        ("Email", _value(snapshot.email)),
        ("Социальные ссылки", _value(snapshot.social_links)),
        ("Образование", _value(snapshot.education)),
        ("Деятельность", _value(snapshot.occupation)),
        ("Семейное положение", _value(snapshot.marital_status)),
        ("Организации", _value(snapshot.other_organizations)),
        ("Мотивация", _value(snapshot.motivation)),
        ("Фотография", "Фотография загружена" if snapshot.has_photo else "Фотография не загружена"),
    ]
    body_rows = "\n".join(
        f"<tr><th>{html.escape(label)}</th><td>{_html_multiline(value)}</td></tr>"
        for label, value in rows
    )
    consents = "".join(f"<li>{html.escape(line)}</li>" for line in _consent_lines(snapshot))
    return f"""<!doctype html>
<html><body style="margin:0;background:#f4f0e8;color:#1f1f1f;font-family:Arial,sans-serif">
<div style="background:#111;color:#fff;padding:24px;border-bottom:4px solid #d52420">
<h1 style="margin:0;font-size:22px">Новая заявка в ДЛ «Астрея» №3</h1>
</div>
<div style="padding:24px">
<table style="border-collapse:collapse;width:100%;background:#fff">{body_rows}</table>
<h2 style="color:#d52420">Подтверждения</h2>
<ul>{consents}</ul>
<p><a href="{admin_link}" style="display:inline-block;background:#d52420;color:#fff;padding:12px 18px;text-decoration:none">Открыть заявку и фотографию</a></p>
</div></body></html>"""


def _consent_lines(snapshot: CandidateNotificationSnapshot) -> list[str]:
    accepted = {consent.consent_type for consent in snapshot.consents}
    labels = {
        "personal_data_processing": "Согласие на обработку персональных данных записано",
        "privacy_policy_acknowledgement": "Ознакомление с политикой конфиденциальности записано",
        "saint_petersburg_acknowledgement": "Подтверждение Санкт-Петербурга записано",
    }
    return [label if key in accepted else f"{label}: нет" for key, label in labels.items()]


def _admin_link(snapshot: CandidateNotificationSnapshot, config: SmtpDeliveryConfig) -> str:
    return f"{config.site_base_url}/admin/candidates/{snapshot.application_id}"


def _format_moscow(value: datetime) -> str:
    source = value if value.tzinfo else value.replace(tzinfo=UTC)
    return source.astimezone(MOSCOW).strftime("%d.%m.%Y %H:%M MSK")


def _value(value: str | None) -> str:
    return value if value else "—"


def _date_value(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else "—"


def _html_multiline(value: str) -> str:
    return html.escape(value).replace("\n", "<br>")


def _required_text(value: str | None, field_name: str) -> str:
    normalized = _optional_text(value)
    if normalized is None:
        raise EmailDeliveryConfigError(f"{field_name} is required for email delivery")
    return normalized


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_mailbox(value: str, field_name: str) -> str:
    if "\r" in value or "\n" in value:
        raise EmailDeliveryConfigError(f"{field_name} is invalid")
    name, address = parseaddr(value)
    if name or address != value or "@" not in address or address.startswith("@") or address.endswith("@"):
        raise EmailDeliveryConfigError(f"{field_name} is invalid")
    return value


def _normalize_site_base_url(value: str | None, *, debug: bool) -> str:
    raw = _required_text(value, "SITE_BASE_URL").rstrip("/")
    parsed = urlparse(raw)
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise EmailDeliveryConfigError("SITE_BASE_URL is invalid")
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise EmailDeliveryConfigError("SITE_BASE_URL is invalid")
    if parsed.scheme == "http" and (not debug or parsed.hostname not in {"localhost", "127.0.0.1"}):
        raise EmailDeliveryConfigError("SITE_BASE_URL is invalid")
    return raw


def _smtp_code_error(code: int):
    if 400 <= int(code) <= 499:
        return EmailDeliveryTemporaryError("Email delivery failed temporarily")
    return EmailDeliveryPermanentError("Email delivery failed permanently")


def _recipient_refusal_error(recipients: dict) -> Exception:
    codes = [value[0] for value in recipients.values() if value]
    if codes and all(400 <= int(code) <= 499 for code in codes):
        return EmailDeliveryTemporaryError("Email delivery failed temporarily")
    return EmailDeliveryPermanentError("Email delivery failed permanently")
