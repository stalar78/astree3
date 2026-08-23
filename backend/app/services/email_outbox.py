from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from sqlalchemy import and_, asc, or_, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.config import Settings
from app.models.candidate import EmailOutbox
from app.services.candidate_contracts import (
    EMAIL_OUTBOX_FAILURE_CODES,
    EMAIL_OUTBOX_FAILURE_PROCESSING_TIMEOUT,
    EMAIL_OUTBOX_STATUS_FAILED,
    EMAIL_OUTBOX_STATUS_PENDING,
    EMAIL_OUTBOX_STATUS_PROCESSING,
    EMAIL_OUTBOX_STATUS_SENT,
)

EmailOutboxFailureCode = Literal[
    "delivery_temporary_failure",
    "delivery_permanent_failure",
    "delivery_unexpected_failure",
    "processing_timeout",
]


@dataclass(frozen=True, slots=True)
class EmailOutboxPolicy:
    batch_size: int
    max_attempts: int
    retry_base_seconds: int
    retry_max_seconds: int
    processing_timeout_seconds: int

    def __post_init__(self) -> None:
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be positive")
        if self.retry_base_seconds <= 0:
            raise ValueError("retry_base_seconds must be positive")
        if self.retry_max_seconds < self.retry_base_seconds:
            raise ValueError("retry_max_seconds must be >= retry_base_seconds")
        if self.processing_timeout_seconds <= 0:
            raise ValueError("processing_timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class EmailOutboxClaim:
    outbox_id: int
    application_id: int
    event_type: str
    attempt_number: int


class EmailOutboxPersistenceError(RuntimeError):
    pass


class EmailOutboxClaimLostError(RuntimeError):
    pass


class EmailOutboxPolicyError(ValueError):
    pass


def claim_email_outbox_batch(
    db: Session,
    policy: EmailOutboxPolicy,
    *,
    now: datetime | None = None,
) -> list[EmailOutboxClaim]:
    current = _ensure_utc(now or datetime.now(UTC))
    try:
        statement = _build_claim_statement(policy, current)
        rows = db.execute(statement).scalars().all()
        claims: list[EmailOutboxClaim] = []
        for row in rows:
            row.status = EMAIL_OUTBOX_STATUS_PROCESSING
            row.attempts += 1
            row.processing_started_at = current
            row.next_attempt_at = None
            claims.append(
                EmailOutboxClaim(
                    outbox_id=row.id,
                    application_id=row.application_id,
                    event_type=row.event_type,
                    attempt_number=row.attempts,
                )
            )
        db.flush()
        db.commit()
        return claims
    except SQLAlchemyError as exc:
        _safe_rollback(db)
        raise EmailOutboxPersistenceError("Email outbox claim failed") from exc


def email_outbox_policy_from_settings(settings: Settings) -> EmailOutboxPolicy:
    return EmailOutboxPolicy(
        batch_size=settings.email_outbox_batch_size,
        max_attempts=settings.email_outbox_max_attempts,
        retry_base_seconds=settings.email_outbox_retry_base_seconds,
        retry_max_seconds=settings.email_outbox_retry_max_seconds,
        processing_timeout_seconds=settings.email_outbox_processing_timeout_seconds,
    )


def mark_email_outbox_sent(
    db: Session,
    claim: EmailOutboxClaim,
    *,
    now: datetime | None = None,
) -> None:
    current = _ensure_utc(now or datetime.now(UTC))
    try:
        result = db.execute(
            _guarded_update(claim.outbox_id, claim.attempt_number).values(
                status=EMAIL_OUTBOX_STATUS_SENT,
                sent_at=current,
                processing_started_at=None,
                next_attempt_at=None,
                last_error=None,
            ),
        )
        if result.rowcount != 1:
            raise EmailOutboxClaimLostError("Email outbox claim was lost")
        db.commit()
    except EmailOutboxClaimLostError:
        _safe_rollback(db)
        raise
    except SQLAlchemyError as exc:
        _safe_rollback(db)
        raise EmailOutboxPersistenceError("Email outbox update failed") from exc


def record_email_outbox_failure(
    db: Session,
    claim: EmailOutboxClaim,
    failure_code: EmailOutboxFailureCode,
    *,
    retryable: bool,
    policy: EmailOutboxPolicy,
    now: datetime | None = None,
) -> None:
    if failure_code not in EMAIL_OUTBOX_FAILURE_CODES:
        raise EmailOutboxPolicyError("Invalid email outbox failure code")
    current = _ensure_utc(now or datetime.now(UTC))
    next_attempt = None
    status = EMAIL_OUTBOX_STATUS_FAILED
    if retryable and claim.attempt_number < policy.max_attempts:
        status = EMAIL_OUTBOX_STATUS_PENDING
        next_attempt = current + timedelta(seconds=_backoff_seconds(claim.attempt_number, policy))
    try:
        result = db.execute(
            _guarded_update(claim.outbox_id, claim.attempt_number).values(
                status=status,
                processing_started_at=None,
                next_attempt_at=next_attempt,
                last_error=failure_code,
                sent_at=None,
            ),
        )
        if result.rowcount != 1:
            raise EmailOutboxClaimLostError("Email outbox claim was lost")
        db.commit()
    except EmailOutboxClaimLostError:
        _safe_rollback(db)
        raise
    except SQLAlchemyError as exc:
        _safe_rollback(db)
        raise EmailOutboxPersistenceError("Email outbox update failed") from exc


def recover_stale_email_outbox(
    db: Session,
    policy: EmailOutboxPolicy,
    *,
    now: datetime | None = None,
) -> int:
    current = _ensure_utc(now or datetime.now(UTC))
    cutoff = current - timedelta(seconds=policy.processing_timeout_seconds)
    try:
        rows = (
            db.execute(
                select(EmailOutbox)
                .where(
                    EmailOutbox.status == EMAIL_OUTBOX_STATUS_PROCESSING,
                    EmailOutbox.processing_started_at.is_not(None),
                    EmailOutbox.processing_started_at <= cutoff,
                )
                .order_by(asc(EmailOutbox.processing_started_at), asc(EmailOutbox.id))
                .limit(policy.batch_size)
                .with_for_update(skip_locked=True)
            )
            .scalars()
            .all()
        )
        for row in rows:
            failure_code: EmailOutboxFailureCode = EMAIL_OUTBOX_FAILURE_PROCESSING_TIMEOUT
            if row.attempts < policy.max_attempts:
                row.status = EMAIL_OUTBOX_STATUS_PENDING
                row.next_attempt_at = current + timedelta(seconds=_backoff_seconds(row.attempts, policy))
            else:
                row.status = EMAIL_OUTBOX_STATUS_FAILED
                row.next_attempt_at = None
            row.processing_started_at = None
            row.last_error = failure_code
            row.sent_at = None
        db.flush()
        db.commit()
        return len(rows)
    except SQLAlchemyError as exc:
        _safe_rollback(db)
        raise EmailOutboxPersistenceError("Email outbox recovery failed") from exc


def build_postgresql_claim_statement(policy: EmailOutboxPolicy, now: datetime) -> Select[tuple[EmailOutbox]]:
    return _build_claim_statement(policy, _ensure_utc(now))


def _guarded_update(outbox_id: int, attempt_number: int):
    return update(EmailOutbox).where(
        and_(
            EmailOutbox.id == outbox_id,
            EmailOutbox.status == EMAIL_OUTBOX_STATUS_PROCESSING,
            EmailOutbox.attempts == attempt_number,
        )
    )


def _backoff_seconds(attempt_number: int, policy: EmailOutboxPolicy) -> int:
    exponent = max(0, attempt_number - 1)
    if exponent > 30:
        return policy.retry_max_seconds
    delay = policy.retry_base_seconds * (2**exponent)
    return min(delay, policy.retry_max_seconds)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise EmailOutboxPolicyError("Datetime must be timezone-aware")
    return value.astimezone(UTC)


def _safe_rollback(db: Session) -> None:
    try:
        db.rollback()
    except SQLAlchemyError:
        pass


def _build_claim_statement(policy: EmailOutboxPolicy, now: datetime) -> Select[tuple[EmailOutbox]]:
    return (
        select(EmailOutbox)
        .where(
            EmailOutbox.status == EMAIL_OUTBOX_STATUS_PENDING,
            or_(EmailOutbox.next_attempt_at.is_(None), EmailOutbox.next_attempt_at <= now),
        )
        .order_by(asc(EmailOutbox.created_at), asc(EmailOutbox.id))
        .limit(policy.batch_size)
        .with_for_update(skip_locked=True)
    )
