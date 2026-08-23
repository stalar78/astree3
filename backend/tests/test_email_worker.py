from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.models.candidate import ApplicationConsent, CandidateApplication, EmailOutbox
from app.services.candidate_contracts import (
    CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
    CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
    CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
)
from app.services.email_delivery import (
    EmailDeliveryPermanentError,
    EmailDeliveryTemporaryError,
    EmailTransport,
    render_candidate_notification_email,
)
from app.services.email_outbox import EmailOutboxClaimLostError, EmailOutboxPersistenceError
from app.services.email_worker import (
    EmailOutboxRunResult,
    EmailWorkerConfigurationError,
    EmailWorkerOperationalError,
    EmailWorkerPersistenceError,
    run_email_outbox_once,
)


@dataclass
class FakeTransport(EmailTransport):
    messages: list[EmailMessage]
    fail_first: Exception | None = None

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)
        if self.fail_first is not None:
            error = self.fail_first
            self.fail_first = None
            raise error


@pytest.fixture()
def session_factory(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'worker.db'}")

    @event.listens_for(engine, "connect")
    def register_sqlite_functions(dbapi_connection, _connection_record) -> None:
        dbapi_connection.create_function(
            "btrim",
            1,
            lambda value: value.strip() if value is not None else None,
        )

    Base.metadata.create_all(
        engine,
        tables=[CandidateApplication.__table__, ApplicationConsent.__table__, EmailOutbox.__table__],
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    return factory


def test_worker_success_sends_and_marks_sent(session_factory) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])
    settings = _settings()

    result = run_email_outbox_once(settings, session_factory, transport=transport, now=NOW)

    assert result == EmailOutboxRunResult(recovered=0, claimed=1, sent=1, delivery_failures=0)
    assert len(transport.messages) == 1
    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "sent"
        assert outbox.sent_at is not None


def test_worker_temporary_failure_requeues(session_factory) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[], fail_first=EmailDeliveryTemporaryError("network secret"))

    result = run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert result.delivery_failures == 1
    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "pending"
        assert outbox.last_error == "delivery_temporary_failure"
        assert outbox.next_attempt_at is not None


def test_recovery_persistence_failure_aborts_before_smtp(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])

    def fail_recovery(*args, **kwargs):
        raise EmailOutboxPersistenceError("recovery sql secret")

    monkeypatch.setattr("app.services.email_worker.recover_stale_email_outbox", fail_recovery)

    with pytest.raises(EmailWorkerPersistenceError) as exc_info:
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email outbox recovery failed"
    assert "sql" not in str(exc_info.value).lower()
    assert transport.messages == []


def test_claim_persistence_failure_aborts_before_smtp(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])

    def fail_claim(*args, **kwargs):
        raise EmailOutboxPersistenceError("claim sql secret")

    monkeypatch.setattr("app.services.email_worker.claim_email_outbox_batch", fail_claim)

    with pytest.raises(EmailWorkerPersistenceError) as exc_info:
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email outbox claim failed"
    assert "sql" not in str(exc_info.value).lower()
    assert transport.messages == []


def test_claim_lost_during_claim_is_reported_safely(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])

    def lose_claim(*args, **kwargs):
        raise EmailOutboxClaimLostError("lost row secret")

    monkeypatch.setattr("app.services.email_worker.claim_email_outbox_batch", lose_claim)

    with pytest.raises(EmailWorkerOperationalError) as exc_info:
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email outbox claim was lost"
    assert transport.messages == []


def test_post_send_db_failure_aborts_without_failure_transition(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])

    def fail_mark_sent(*args, **kwargs):
        raise EmailOutboxPersistenceError("synthetic db failure")

    monkeypatch.setattr("app.services.email_worker._mark_sent", fail_mark_sent)

    with pytest.raises(EmailWorkerPersistenceError):
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "processing"
    assert len(transport.messages) == 1


def test_delivery_permanent_failure_marks_terminal_failure(session_factory) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[], fail_first=EmailDeliveryPermanentError("provider secret"))

    result = run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert result.delivery_failures == 1
    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "failed"
        assert outbox.last_error == "delivery_permanent_failure"
        assert outbox.next_attempt_at is None


def test_unexpected_transport_exception_marks_terminal_failure(session_factory) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[], fail_first=RuntimeError("provider secret"))

    result = run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert result.delivery_failures == 1
    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "failed"
        assert outbox.last_error == "delivery_unexpected_failure"
        assert outbox.next_attempt_at is None
    assert len(transport.messages) == 1


def test_snapshot_db_failure_keeps_claim_processing_and_skips_smtp(session_factory) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[])
    snapshot_factory = _SnapshotFailureFactory(session_factory)

    with pytest.raises(EmailWorkerPersistenceError) as exc_info:
        run_email_outbox_once(_settings(), snapshot_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email worker snapshot load failed"
    assert transport.messages == []
    with session_factory() as db:
        outbox = db.get(EmailOutbox, 1)
        assert outbox.status == "processing"


def test_failure_transition_persistence_failure_aborts_without_second_send(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[], fail_first=EmailDeliveryTemporaryError("network secret"))

    def fail_transition(*args, **kwargs):
        raise EmailOutboxPersistenceError("transition sql secret")

    monkeypatch.setattr("app.services.email_worker.record_email_outbox_failure", fail_transition)

    with pytest.raises(EmailWorkerPersistenceError) as exc_info:
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email outbox failure transition failed"
    assert len(transport.messages) == 1


def test_claim_lost_during_failure_transition_is_operational(
    session_factory,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_candidate(session_factory)
    transport = FakeTransport(messages=[], fail_first=EmailDeliveryTemporaryError("network secret"))

    def lose_transition(*args, **kwargs):
        raise EmailOutboxClaimLostError("lost row secret")

    monkeypatch.setattr("app.services.email_worker.record_email_outbox_failure", lose_transition)

    with pytest.raises(EmailWorkerOperationalError) as exc_info:
        run_email_outbox_once(_settings(), session_factory, transport=transport, now=NOW)

    assert str(exc_info.value) == "Email outbox claim was lost"
    assert len(transport.messages) == 1


def test_invalid_config_fails_before_claim(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    settings = _settings(SMTP_HOST=None)

    with pytest.raises(EmailWorkerConfigurationError):
        run_email_outbox_once(settings, session_factory, transport=FakeTransport(messages=[]), now=NOW)


def test_worker_closes_snapshot_session_before_render_and_send(session_factory, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_candidate(session_factory)
    tracker = _SessionTracker(session_factory)
    render_open_counts: list[int] = []
    send_open_counts: list[int] = []

    def capture_render(snapshot, config):
        render_open_counts.append(tracker.open_sessions)
        return render_candidate_notification_email(snapshot, config)

    class CheckingTransport:
        def send(self, message: EmailMessage) -> None:
            send_open_counts.append(tracker.open_sessions)

    monkeypatch.setattr("app.services.email_worker.render_candidate_notification_email", capture_render)

    run_email_outbox_once(_settings(), tracker.factory, transport=CheckingTransport(), now=NOW)

    assert render_open_counts == [0]
    assert send_open_counts == [0]


class _SessionTracker:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.open_sessions = 0

    def factory(self):
        session = self._session_factory()
        return _TrackingSession(session, self)


class _TrackingSession:
    def __init__(self, session, tracker: _SessionTracker):
        self._session = session
        self._tracker = tracker

    def __enter__(self):
        self._tracker.open_sessions += 1
        return self._session.__enter__()

    def __exit__(self, exc_type, exc, tb):
        try:
            return self._session.__exit__(exc_type, exc, tb)
        finally:
            self._tracker.open_sessions -= 1


class _SnapshotFailureFactory:
    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.calls == 3:
            return _FailingSnapshotSession()
        return self._session_factory()


class _FailingSnapshotSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, statement):
        raise SQLAlchemyError("snapshot sql secret")


NOW = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)


def _settings(**overrides) -> Settings:
    values = {
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/astrea",
        "SMTP_HOST": "smtp.example.test",
        "SMTP_FROM_EMAIL": "notifications@example.test",
        "APPLICATION_NOTIFICATION_EMAIL": "admin@example.test",
        "SITE_BASE_URL": "https://astrea.example.test",
    }
    values.update(overrides)
    return Settings(**values)


def _seed_candidate(session_factory) -> None:
    with session_factory() as db:
        candidate = CandidateApplication(
            full_name="Candidate Name",
            city="Saint Petersburg",
            email="candidate@example.test",
            created_at=NOW - timedelta(hours=1),
        )
        db.add(candidate)
        db.flush()
        db.add(
            EmailOutbox(
                application_id=candidate.id,
                status="pending",
                attempts=0,
            )
        )
        for consent_type in (
            CONSENT_TYPE_PERSONAL_DATA_PROCESSING,
            CONSENT_TYPE_PRIVACY_POLICY_ACKNOWLEDGEMENT,
            CONSENT_TYPE_SAINT_PETERSBURG_ACKNOWLEDGEMENT,
        ):
            candidate.consents.append(
                ApplicationConsent(
                    consent_type=consent_type,
                    accepted_at=NOW - timedelta(hours=1),
                    document_version="v1",
                )
            )
        db.commit()
