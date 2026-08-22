from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.candidate import ApplicationConsent, CandidateApplication, EmailOutbox
from app.services.candidate_contracts import (
    CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
    CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
    CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
    EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED,
    EMAIL_OUTBOX_STATUS_PENDING,
)
from app.services.candidate_photos import PreparedCandidatePhoto
from app.services.private_photo_storage import PrivatePhotoStorage, PrivatePhotoStorageError

REQUIRED_CONSENT_TYPES = (
    CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
    CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
    CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
)


class CandidateIntakeError(ValueError):
    pass


class CandidateIntakePersistenceError(CandidateIntakeError):
    pass


@dataclass(frozen=True, slots=True)
class CandidateSubmissionData:
    full_name: str | None = None
    date_of_birth: date | None = None
    city: str | None = None
    phone: str | None = None
    email: str | None = None
    education: str | None = None
    occupation: str | None = None
    marital_status: str | None = None
    other_organizations: str | None = None
    social_links: str | None = None
    motivation: str | None = None


@dataclass(frozen=True, slots=True)
class CandidateConsentVersions:
    personal_data_processing: str
    privacy_policy_acknowledgement: str
    saint_petersburg_acknowledgement: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "personal_data_processing",
            _normalize_document_version(self.personal_data_processing),
        )
        object.__setattr__(
            self,
            "privacy_policy_acknowledgement",
            _normalize_document_version(self.privacy_policy_acknowledgement),
        )
        object.__setattr__(
            self,
            "saint_petersburg_acknowledgement",
            _normalize_document_version(self.saint_petersburg_acknowledgement),
        )


@dataclass(frozen=True, slots=True)
class CandidateIntakeResult:
    application_id: int


def intake_candidate_application(
    db: Session,
    storage: PrivatePhotoStorage,
    submission: CandidateSubmissionData,
    prepared_photo: PreparedCandidatePhoto,
    consent_versions: CandidateConsentVersions,
) -> CandidateIntakeResult:
    try:
        storage_key = storage.save(prepared_photo)
    except PrivatePhotoStorageError as exc:
        raise CandidateIntakeError("Candidate intake photo storage failed") from exc

    application_id: int | None = None
    rollback_error: Exception | None = None
    try:
        application = CandidateApplication(
            full_name=submission.full_name,
            date_of_birth=submission.date_of_birth,
            city=submission.city,
            phone=submission.phone,
            email=submission.email,
            education=submission.education,
            occupation=submission.occupation,
            marital_status=submission.marital_status,
            other_organizations=submission.other_organizations,
            social_links=submission.social_links,
            motivation=submission.motivation,
            photo_storage_key=storage_key,
            photo_media_type=prepared_photo.media_type,
            photo_size_bytes=prepared_photo.size_bytes,
        )
        accepted_at = datetime.now(UTC)
        application.consents.extend(_build_application_consents(consent_versions, accepted_at))
        application.email_outbox_entries.append(_build_email_outbox())

        db.add(application)
        db.flush()
        application_id = application.id
        db.commit()
        return CandidateIntakeResult(application_id=application_id)
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except SQLAlchemyError as rollback_exc:  # pragma: no cover - defensive fallback
            rollback_error = rollback_exc

        try:
            storage.delete(storage_key)
        except PrivatePhotoStorageError as cleanup_exc:
            raise CandidateIntakePersistenceError(
                "Candidate intake failed and stored photo cleanup failed"
            ) from cleanup_exc

        if rollback_error is not None:
            raise CandidateIntakePersistenceError(
                "Candidate intake failed and transaction rollback failed"
            ) from rollback_error

        raise CandidateIntakePersistenceError("Candidate intake failed") from exc


def _build_application_consents(
    consent_versions: CandidateConsentVersions,
    accepted_at: datetime,
) -> tuple[ApplicationConsent, ...]:
    return (
        ApplicationConsent(
            consent_type=CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
            accepted_at=accepted_at,
            document_version=consent_versions.personal_data_processing,
        ),
        ApplicationConsent(
            consent_type=CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
            accepted_at=accepted_at,
            document_version=consent_versions.privacy_policy_acknowledgement,
        ),
        ApplicationConsent(
            consent_type=CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
            accepted_at=accepted_at,
            document_version=consent_versions.saint_petersburg_acknowledgement,
        ),
    )


def _build_email_outbox() -> EmailOutbox:
    return EmailOutbox(
        event_type=EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED,
        status=EMAIL_OUTBOX_STATUS_PENDING,
        attempts=0,
    )


def _normalize_document_version(version: str) -> str:
    if not isinstance(version, str):
        raise CandidateIntakeError("Candidate consent versions are invalid")

    normalized = version.strip()
    if not normalized:
        raise CandidateIntakeError("Candidate consent versions are invalid")
    return normalized


__all__ = [
    "REQUIRED_CONSENT_TYPES",
    "CandidateConsentVersions",
    "CandidateIntakeError",
    "CandidateIntakePersistenceError",
    "CandidateIntakeResult",
    "CandidateSubmissionData",
    "intake_candidate_application",
]
