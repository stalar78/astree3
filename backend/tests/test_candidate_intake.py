from __future__ import annotations

from dataclasses import fields
from datetime import UTC, date

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.models.candidate import CandidateApplication
from app.services.candidate_contracts import (
    EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED,
    EMAIL_OUTBOX_STATUS_PENDING,
)
from app.services.candidate_intake import (
    REQUIRED_CONSENT_TYPES,
    CandidateConsentVersions,
    CandidateIntakeError,
    CandidateIntakePersistenceError,
    CandidateIntakeResult,
    CandidateSubmissionData,
    intake_candidate_application,
)
from app.services.candidate_photos import PreparedCandidatePhoto
from app.services.private_photo_storage import PrivatePhotoStorageError


def test_submission_and_result_contracts_expose_only_expected_fields() -> None:
    assert {field.name for field in fields(CandidateSubmissionData)} == {
        "full_name",
        "date_of_birth",
        "city",
        "phone",
        "email",
        "education",
        "occupation",
        "marital_status",
        "other_organizations",
        "social_links",
        "motivation",
    }
    assert {field.name for field in fields(CandidateIntakeResult)} == {"application_id"}
    assert not hasattr(CandidateSubmissionData(), "religion")
    assert not hasattr(CandidateSubmissionData(), "ip_address")
    assert not hasattr(CandidateSubmissionData(), "fingerprint")


def test_success_persists_application_consents_outbox_and_photo_metadata() -> None:
    submission = CandidateSubmissionData(
        full_name="Test Candidate",
        date_of_birth=date(1990, 5, 17),
        city="Saint Petersburg",
        phone="+7-900-000-00-00",
        email="test@example.com",
        education="Higher education",
        occupation="Engineer",
        marital_status="Single",
        other_organizations="None",
        social_links="https://example.com/profile",
        motivation="Seeking membership",
    )
    photo = PreparedCandidatePhoto(
        storage_key="candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
        media_type="image/jpeg",
        size_bytes=32123,
        width=800,
        height=600,
        normalized_bytes=b"normalized-bytes",
    )
    consent_versions = CandidateConsentVersions(
        " personal-data-v1 ",
        " privacy-policy-v2 ",
        " saint-petersburg-v3 ",
    )
    db = FakeSession()
    storage = FakeStorage()

    result = intake_candidate_application(db, storage, submission, photo, consent_versions)

    application = db.added[0]
    assert result == CandidateIntakeResult(application_id=application.id)
    assert storage.save_calls == [photo]
    assert storage.deleted_keys == []
    assert db.commit_calls == 1
    assert db.rollback_calls == 0
    assert db.operations == ["add", "flush", "commit"]
    assert application.full_name == submission.full_name
    assert application.date_of_birth == submission.date_of_birth
    assert application.photo_storage_key == photo.storage_key
    assert application.photo_media_type == photo.media_type
    assert application.photo_size_bytes == photo.size_bytes
    assert not hasattr(application, "normalized_bytes")

    assert len(application.consents) == 3
    assert {item.consent_type for item in application.consents} == set(REQUIRED_CONSENT_TYPES)
    assert {item.document_version for item in application.consents} == {
        "personal-data-v1",
        "privacy-policy-v2",
        "saint-petersburg-v3",
    }
    assert all(item.accepted_at.tzinfo is UTC for item in application.consents)

    outbox = application.email_outbox_entries[0]
    assert len(application.email_outbox_entries) == 1
    assert outbox.event_type == EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED
    assert outbox.status == EMAIL_OUTBOX_STATUS_PENDING
    assert outbox.attempts == 0
    assert outbox.processing_started_at is None
    assert outbox.next_attempt_at is None
    assert outbox.last_error is None
    assert outbox.sent_at is None


def test_storage_failure_prevents_database_work() -> None:
    db = FakeSession()
    storage = FakeStorage(save_error=PrivatePhotoStorageError("synthetic storage failure"))

    with pytest.raises(CandidateIntakeError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert str(exc_info.value) == "Candidate intake photo storage failed"
    assert db.added == []
    assert db.commit_calls == 0
    assert db.rollback_calls == 0


def test_flush_failure_rolls_back_and_deletes_photo() -> None:
    db = FakeSession(flush_error=SQLAlchemyError("synthetic flush failure"))
    storage = FakeStorage()

    with pytest.raises(CandidateIntakePersistenceError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate", email="test@example.com"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert "Test Candidate" not in str(exc_info.value)
    assert "test@example.com" not in str(exc_info.value)
    assert db.commit_calls == 0
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]
    assert db.operations == ["add", "flush", "rollback"]


def test_commit_failure_rolls_back_and_deletes_photo() -> None:
    db = FakeSession(commit_error=SQLAlchemyError("synthetic commit failure"))
    storage = FakeStorage()

    with pytest.raises(CandidateIntakePersistenceError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert "Test Candidate" not in str(exc_info.value)
    assert db.commit_calls == 1
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]
    assert db.operations == ["add", "flush", "commit", "rollback"]


def test_cleanup_failure_is_reported_generically() -> None:
    db = FakeSession(flush_error=SQLAlchemyError("synthetic flush failure"))
    storage = FakeStorage(delete_error=PrivatePhotoStorageError("delete failed /private/path"))

    with pytest.raises(CandidateIntakePersistenceError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate", email="test@example.com"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert "Test Candidate" not in str(exc_info.value)
    assert "test@example.com" not in str(exc_info.value)
    assert "private/path" not in str(exc_info.value)
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]


def test_non_sqlalchemy_pre_commit_failure_rolls_back_and_reraises_original() -> None:
    db = FakeSession(flush_error=ValueError("synthetic programmer failure"))
    storage = FakeStorage()

    with pytest.raises(ValueError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate", email="test@example.com"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert str(exc_info.value) == "synthetic programmer failure"
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]
    assert db.commit_calls == 0
    assert db.operations == ["add", "flush", "rollback"]


def test_rollback_failure_still_attempts_cleanup_and_returns_generic_error() -> None:
    db = FakeSession(
        flush_error=ValueError("synthetic programmer failure"),
        rollback_error=RuntimeError("synthetic rollback failure"),
    )
    storage = FakeStorage()

    with pytest.raises(CandidateIntakePersistenceError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate", email="test@example.com"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert str(exc_info.value) == "Candidate intake failed and transaction rollback failed"
    assert "Test Candidate" not in str(exc_info.value)
    assert "test@example.com" not in str(exc_info.value)
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]
    assert db.commit_calls == 0
    assert db.operations == ["add", "flush", "rollback"]


def test_non_sqlalchemy_failure_with_cleanup_failure_returns_generic_cleanup_error() -> None:
    db = FakeSession(flush_error=ValueError("synthetic programmer failure"))
    storage = FakeStorage(delete_error=RuntimeError("delete failed /private/path"))

    with pytest.raises(CandidateIntakePersistenceError) as exc_info:
        intake_candidate_application(
            db,
            storage,
            CandidateSubmissionData(full_name="Test Candidate", email="test@example.com"),
            _photo(),
            CandidateConsentVersions("v1", "v2", "v3"),
        )

    assert "Test Candidate" not in str(exc_info.value)
    assert "test@example.com" not in str(exc_info.value)
    assert "/private/path" not in str(exc_info.value)
    assert "candidate-photos" not in str(exc_info.value)
    assert db.rollback_calls == 1
    assert storage.deleted_keys == ["candidate-photos/00000000-0000-4000-8000-000000000000.jpg"]


@pytest.mark.parametrize(
    "versions",
    [
        {"personal_data_processing": " ", "privacy_policy_acknowledgement": "v2", "saint_petersburg_acknowledgement": "v3"},
        {"personal_data_processing": "v1", "privacy_policy_acknowledgement": "\t", "saint_petersburg_acknowledgement": "v3"},
        {"personal_data_processing": "v1", "privacy_policy_acknowledgement": "v2", "saint_petersburg_acknowledgement": "\n"},
    ],
)
def test_blank_document_versions_are_rejected(versions: dict[str, str]) -> None:
    with pytest.raises(CandidateIntakeError):
        CandidateConsentVersions(**versions)


def test_consent_versions_are_trimmed() -> None:
    versions = CandidateConsentVersions("  v1  ", "\tv2", "v3 \n")

    assert versions.personal_data_processing == "v1"
    assert versions.privacy_policy_acknowledgement == "v2"
    assert versions.saint_petersburg_acknowledgement == "v3"


class FakeSession:
    def __init__(
        self,
        *,
        flush_error: Exception | None = None,
        commit_error: Exception | None = None,
        rollback_error: Exception | None = None,
    ) -> None:
        self.flush_error = flush_error
        self.commit_error = commit_error
        self.rollback_error = rollback_error
        self.added: list[CandidateApplication] = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self.operations: list[str] = []
        self._next_id = 1

    def add(self, obj: CandidateApplication) -> None:
        self.operations.append("add")
        self.added.append(obj)

    def flush(self) -> None:
        self.operations.append("flush")
        if self.flush_error is not None:
            raise self.flush_error

        application = self.added[0]
        application.id = self._next_id
        self._next_id += 1

        for consent in application.consents:
            consent.id = self._next_id
            consent.application_id = application.id
            self._next_id += 1

        for outbox in application.email_outbox_entries:
            outbox.id = self._next_id
            outbox.application_id = application.id
            self._next_id += 1

    def commit(self) -> None:
        self.operations.append("commit")
        self.commit_calls += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.operations.append("rollback")
        self.rollback_calls += 1
        if self.rollback_error is not None:
            raise self.rollback_error


class FakeStorage:
    def __init__(
        self,
        *,
        save_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        self.save_error = save_error
        self.delete_error = delete_error
        self.save_calls: list[PreparedCandidatePhoto] = []
        self.deleted_keys: list[str] = []

    def save(self, photo: PreparedCandidatePhoto) -> str:
        self.save_calls.append(photo)
        if self.save_error is not None:
            raise self.save_error
        return photo.storage_key

    def delete(self, storage_key: str) -> None:
        self.deleted_keys.append(storage_key)
        if self.delete_error is not None:
            raise self.delete_error


def _photo() -> PreparedCandidatePhoto:
    return PreparedCandidatePhoto(
        storage_key="candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
        media_type="image/jpeg",
        size_bytes=12345,
        width=800,
        height=600,
        normalized_bytes=b"normalized-bytes",
    )
