from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.candidate import ApplicationConsent, CandidateApplication
from app.services.candidate_contracts import (
    CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
    CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
    CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
    EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED,
    EMAIL_OUTBOX_FAILURE_DELIVERY_PERMANENT,
    EMAIL_OUTBOX_FAILURE_DELIVERY_TEMPORARY,
    EMAIL_OUTBOX_FAILURE_DELIVERY_UNEXPECTED,
)
from app.services.email_delivery import (
    CandidateConsentSnapshot,
    CandidateNotificationSnapshot,
    EmailDeliveryConfigError,
    EmailDeliveryPermanentError,
    EmailDeliveryTemporaryError,
    EmailTransport,
    SmtpDeliveryConfig,
    SmtpEmailTransport,
    render_candidate_notification_email,
    smtp_delivery_config_from_settings,
)
from app.services.email_outbox import (
    EmailOutboxClaim,
    EmailOutboxClaimLostError,
    EmailOutboxPersistenceError,
    EmailOutboxPolicy,
    claim_email_outbox_batch,
    email_outbox_policy_from_settings,
    mark_email_outbox_sent,
    record_email_outbox_failure,
    recover_stale_email_outbox,
)

SessionFactory = Callable[[], Session]

REQUIRED_CONSENT_TYPES = (
    CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
    CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
    CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
)


@dataclass(frozen=True, slots=True)
class EmailOutboxRunResult:
    recovered: int
    claimed: int
    sent: int
    delivery_failures: int


class EmailWorkerError(RuntimeError):
    pass


class EmailWorkerConfigurationError(EmailWorkerError):
    pass


class EmailWorkerPersistenceError(EmailWorkerError):
    pass


class EmailWorkerOperationalError(EmailWorkerError):
    pass


class EmailWorkerDataError(EmailWorkerError):
    pass


def run_email_outbox_once(
    settings: Settings,
    session_factory: SessionFactory,
    *,
    transport: EmailTransport | None = None,
    now: datetime | None = None,
) -> EmailOutboxRunResult:
    current = _ensure_utc(now or datetime.now(UTC))
    config = _validate_delivery_config(settings)
    policy = email_outbox_policy_from_settings(settings)
    delivery_transport = transport or SmtpEmailTransport(config)

    recovered = _run_recovery(session_factory, policy, current)
    claims = _run_claim(session_factory, policy, current)
    sent = 0
    delivery_failures = 0
    for claim in claims:
        try:
            snapshot = _load_candidate_snapshot(session_factory, claim)
        except EmailWorkerPersistenceError:
            raise
        except EmailWorkerDataError:
            _record_terminal_worker_failure(session_factory, claim, current, policy)
            delivery_failures += 1
            continue

        try:
            message = render_candidate_notification_email(snapshot, config)
            delivery_transport.send(message)
        except EmailDeliveryTemporaryError:
            _record_delivery_failure(
                session_factory,
                claim,
                current,
                policy,
                EMAIL_OUTBOX_FAILURE_DELIVERY_TEMPORARY,
                retryable=True,
            )
            delivery_failures += 1
            continue
        except EmailDeliveryPermanentError:
            _record_delivery_failure(
                session_factory,
                claim,
                current,
                policy,
                EMAIL_OUTBOX_FAILURE_DELIVERY_PERMANENT,
                retryable=False,
            )
            delivery_failures += 1
            continue
        except Exception:  # noqa: BLE001
            _record_delivery_failure(
                session_factory,
                claim,
                current,
                policy,
                EMAIL_OUTBOX_FAILURE_DELIVERY_UNEXPECTED,
                retryable=False,
            )
            delivery_failures += 1
            continue

        try:
            _mark_sent(session_factory, claim, current)
            sent += 1
        except EmailOutboxClaimLostError as exc:
            raise EmailWorkerOperationalError("Email outbox claim was lost") from exc
        except EmailOutboxPersistenceError as exc:
            raise EmailWorkerPersistenceError("Email outbox sent transition failed") from exc

    return EmailOutboxRunResult(
        recovered=recovered,
        claimed=len(claims),
        sent=sent,
        delivery_failures=delivery_failures,
    )


def _validate_delivery_config(settings: Settings) -> SmtpDeliveryConfig:
    try:
        return smtp_delivery_config_from_settings(settings)
    except EmailDeliveryConfigError as exc:
        raise EmailWorkerConfigurationError("Email worker configuration is invalid") from exc


def _run_recovery(session_factory: SessionFactory, policy: EmailOutboxPolicy, now: datetime) -> int:
    with session_factory() as db:
        return recover_stale_email_outbox(db, policy, now=now)


def _run_claim(session_factory: SessionFactory, policy: EmailOutboxPolicy, now: datetime) -> list[EmailOutboxClaim]:
    with session_factory() as db:
        return claim_email_outbox_batch(db, policy, now=now)


def _load_candidate_snapshot(
    session_factory: SessionFactory,
    claim: EmailOutboxClaim,
) -> CandidateNotificationSnapshot:
    if claim.event_type != EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED:
        raise EmailWorkerDataError("Unsupported outbox event")
    try:
        with session_factory() as db:
            candidate = db.execute(
                select(CandidateApplication).where(CandidateApplication.id == claim.application_id)
            ).scalar_one_or_none()
            consents = db.execute(
                select(ApplicationConsent).where(
                    ApplicationConsent.application_id == claim.application_id,
                    ApplicationConsent.consent_type.in_(REQUIRED_CONSENT_TYPES),
                ).order_by(ApplicationConsent.consent_type)
            ).scalars().all()
    except SQLAlchemyError as exc:
        raise EmailWorkerPersistenceError("Email worker snapshot load failed") from exc
    if candidate is None:
        raise EmailWorkerDataError("Candidate application is missing")
    consent_map = {consent.consent_type: consent for consent in consents}
    if not all(consent_type in consent_map for consent_type in REQUIRED_CONSENT_TYPES):
        raise EmailWorkerDataError("Candidate application consents are incomplete")
    return CandidateNotificationSnapshot(
        application_id=candidate.id,
        created_at=candidate.created_at,
        full_name=candidate.full_name,
        date_of_birth=candidate.date_of_birth,
        city=candidate.city,
        phone=candidate.phone,
        email=candidate.email,
        education=candidate.education,
        occupation=candidate.occupation,
        marital_status=candidate.marital_status,
        other_organizations=candidate.other_organizations,
        social_links=candidate.social_links,
        motivation=candidate.motivation,
        has_photo=bool(candidate.photo_storage_key),
        consents=tuple(_snapshot_consent(consent_map[key]) for key in REQUIRED_CONSENT_TYPES),
    )


def _snapshot_consent(consent: ApplicationConsent) -> CandidateConsentSnapshot:
    return CandidateConsentSnapshot(
        consent_type=consent.consent_type,
        accepted_at=consent.accepted_at,
        document_version=consent.document_version,
    )


def _mark_sent(session_factory: SessionFactory, claim: EmailOutboxClaim, now: datetime) -> None:
    with session_factory() as db:
        mark_email_outbox_sent(db, claim, now=now)


def _record_delivery_failure(
    session_factory: SessionFactory,
    claim: EmailOutboxClaim,
    now: datetime,
    policy: EmailOutboxPolicy,
    failure_code: str,
    *,
    retryable: bool,
) -> None:
    try:
        with session_factory() as db:
            record_email_outbox_failure(
                db,
                claim,
                failure_code,  # type: ignore[arg-type]
                retryable=retryable,
                policy=policy,
                now=now,
            )
    except EmailOutboxClaimLostError as exc:
        raise EmailWorkerOperationalError("Email outbox claim was lost") from exc
    except EmailOutboxPersistenceError as exc:
        raise EmailWorkerPersistenceError("Email outbox failure transition failed") from exc


def _record_terminal_worker_failure(
    session_factory: SessionFactory,
    claim: EmailOutboxClaim,
    now: datetime,
    policy: EmailOutboxPolicy,
) -> None:
    _record_delivery_failure(
        session_factory,
        claim,
        now,
        policy,
        EMAIL_OUTBOX_FAILURE_DELIVERY_UNEXPECTED,
        retryable=False,
    )


def _ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
