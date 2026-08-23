from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.candidate import CandidateApplication, EmailOutbox
from app.services.email_outbox import (
    EmailOutboxClaimLostError,
    EmailOutboxPersistenceError,
    EmailOutboxPolicy,
    claim_email_outbox_batch,
    mark_email_outbox_sent,
    record_email_outbox_failure,
    recover_stale_email_outbox,
)

NOW = datetime(2026, 8, 23, 12, 0, tzinfo=UTC)
POLICY = EmailOutboxPolicy(
    batch_size=2,
    max_attempts=3,
    retry_base_seconds=60,
    retry_max_seconds=180,
    processing_timeout_seconds=900,
)


@pytest.fixture()
def session(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'outbox.db'}")
    Base.metadata.create_all(engine, tables=[CandidateApplication.__table__, EmailOutbox.__table__])
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as db:
        yield db


def test_initial_outbox_delivery_fields_are_empty(session: Session) -> None:
    row = _add_outbox(session, created_at=NOW)
    assert row.status == "pending"
    assert row.attempts == 0
    assert row.processing_started_at is None
    assert row.next_attempt_at is None
    assert row.last_error is None
    assert row.sent_at is None


def test_claim_is_due_oldest_first_bounded_and_increments_once(session: Session) -> None:
    first = _add_outbox(session, created_at=NOW - timedelta(minutes=3))
    second = _add_outbox(session, created_at=NOW - timedelta(minutes=2))
    _add_outbox(session, created_at=NOW - timedelta(minutes=1), next_attempt_at=NOW + timedelta(seconds=10))
    processing = _add_outbox(session, created_at=NOW, status="processing", processing_started_at=NOW)
    sent = _add_outbox(session, created_at=NOW, status="sent")
    failed = _add_outbox(session, created_at=NOW, status="failed")
    session.commit()

    claims = claim_email_outbox_batch(session, POLICY, now=NOW)

    assert [claim.outbox_id for claim in claims] == [first.id, second.id]
    assert [claim.attempt_number for claim in claims] == [1, 1]
    assert session.get(EmailOutbox, first.id).status == "processing"
    assert session.get(EmailOutbox, first.id).attempts == 1
    assert session.get(EmailOutbox, first.id).processing_started_at == NOW
    assert session.get(EmailOutbox, first.id).next_attempt_at is None
    assert session.get(EmailOutbox, processing.id).status == "processing"
    assert session.get(EmailOutbox, sent.id).status == "sent"
    assert session.get(EmailOutbox, failed.id).status == "failed"


def test_claim_statement_compiles_with_postgresql_skip_locked() -> None:
    from app.services.email_outbox import build_postgresql_claim_statement

    statement = build_postgresql_claim_statement(POLICY, NOW)
    sql = str(statement.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE SKIP LOCKED" in sql


def test_success_transition_clears_processing_state(session: Session) -> None:
    row = _add_outbox(session, created_at=NOW)
    session.commit()
    claim = claim_email_outbox_batch(session, POLICY, now=NOW)[0]

    mark_email_outbox_sent(session, claim, now=NOW + timedelta(seconds=3))

    refreshed = session.get(EmailOutbox, row.id)
    assert refreshed.status == "sent"
    assert refreshed.sent_at == NOW + timedelta(seconds=3)
    assert refreshed.processing_started_at is None
    assert refreshed.next_attempt_at is None
    assert refreshed.last_error is None
    assert refreshed.attempts == 1


def test_retry_backoff_is_deterministic_and_capped(session: Session) -> None:
    row = _add_outbox(session, created_at=NOW)
    session.commit()
    claim = claim_email_outbox_batch(session, POLICY, now=NOW)[0]
    record_email_outbox_failure(session, claim, "delivery_temporary_failure", retryable=True, policy=POLICY, now=NOW)
    assert session.get(EmailOutbox, row.id).next_attempt_at == NOW + timedelta(seconds=60)

    claim_two = claim_email_outbox_batch(session, POLICY, now=NOW + timedelta(seconds=60))[0]
    record_email_outbox_failure(session, claim_two, "delivery_temporary_failure", retryable=True, policy=POLICY, now=NOW + timedelta(seconds=60))
    assert session.get(EmailOutbox, row.id).next_attempt_at == NOW + timedelta(seconds=180)


def test_permanent_and_exhausted_failures_are_terminal(session: Session) -> None:
    permanent = _add_outbox(session, created_at=NOW)
    exhausted = _add_outbox(session, created_at=NOW + timedelta(seconds=1), attempts=2)
    session.commit()
    permanent_claim, exhausted_claim = claim_email_outbox_batch(session, POLICY, now=NOW)

    record_email_outbox_failure(session, permanent_claim, "delivery_permanent_failure", retryable=False, policy=POLICY, now=NOW)
    record_email_outbox_failure(session, exhausted_claim, "delivery_temporary_failure", retryable=True, policy=POLICY, now=NOW)

    assert session.get(EmailOutbox, permanent.id).status == "failed"
    assert session.get(EmailOutbox, exhausted.id).status == "failed"
    assert session.get(EmailOutbox, permanent.id).next_attempt_at is None
    assert session.get(EmailOutbox, exhausted.id).next_attempt_at is None


def test_failure_codes_are_closed_and_machine_safe(session: Session) -> None:
    _add_outbox(session, created_at=NOW)
    session.commit()
    claim = claim_email_outbox_batch(session, POLICY, now=NOW)[0]

    with pytest.raises(ValueError):
        record_email_outbox_failure(session, claim, "smtp password leaked", retryable=False, policy=POLICY, now=NOW)  # type: ignore[arg-type]


def test_stale_recovery_is_bounded_and_preserves_fresh_rows(session: Session) -> None:
    stale = _add_outbox(session, created_at=NOW, status="processing", attempts=1, processing_started_at=NOW - timedelta(hours=1))
    _add_outbox(session, created_at=NOW + timedelta(seconds=1), status="processing", attempts=1, processing_started_at=NOW - timedelta(minutes=1))
    session.commit()

    recovered = recover_stale_email_outbox(session, POLICY, now=NOW)

    assert recovered == 1
    stale_row = session.get(EmailOutbox, stale.id)
    assert stale_row.status == "pending"
    assert stale_row.last_error == "processing_timeout"
    assert stale_row.next_attempt_at == NOW + timedelta(seconds=60)


def test_stale_claim_cannot_mutate_newer_generation(session: Session) -> None:
    row = _add_outbox(session, created_at=NOW)
    session.commit()
    old_claim = claim_email_outbox_batch(session, POLICY, now=NOW)[0]
    recover_stale_email_outbox(session, POLICY, now=NOW + timedelta(hours=1))
    new_claim = claim_email_outbox_batch(session, POLICY, now=NOW + timedelta(hours=1, minutes=1))[0]

    assert new_claim.attempt_number == 2
    with pytest.raises(EmailOutboxClaimLostError):
        mark_email_outbox_sent(session, old_claim, now=NOW)
    with pytest.raises(EmailOutboxClaimLostError):
        record_email_outbox_failure(session, old_claim, "delivery_temporary_failure", retryable=True, policy=POLICY, now=NOW)
    assert session.get(EmailOutbox, row.id).attempts == 2
    assert session.get(EmailOutbox, row.id).status == "processing"


def test_postgresql_db_failure_is_generic(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_commit() -> None:
        raise SQLAlchemyError("DATABASE_URL secret")

    monkeypatch.setattr(session, "commit", fail_commit)
    with pytest.raises(EmailOutboxPersistenceError) as exc_info:
        claim_email_outbox_batch(session, POLICY, now=NOW)
    assert str(exc_info.value) == "Email outbox claim failed"
    assert "DATABASE_URL" not in str(exc_info.value)


def test_migration_0005_is_additive_and_down_revision_is_0004(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration()
    added: list[tuple[str, object]] = []
    constraints: list[tuple[str, str, str]] = []
    indexes: list[tuple[str, str, tuple[str, ...]]] = []

    monkeypatch.setattr(migration.op, "add_column", lambda table, column: added.append((table, column)))
    monkeypatch.setattr(migration.op, "execute", lambda *_: None)
    monkeypatch.setattr(migration.op, "create_check_constraint", lambda name, table, condition: constraints.append((name, table, condition)))
    monkeypatch.setattr(migration.op, "create_index", lambda name, table, columns, unique=False: indexes.append((name, table, tuple(columns))))
    monkeypatch.setattr(migration.op, "drop_index", lambda *_: None)
    monkeypatch.setattr(migration.op, "drop_constraint", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(migration.op, "drop_column", lambda *_: None)

    migration.upgrade()

    assert migration.down_revision == "20260822_0004"
    assert [column.name for table, column in added if table == "email_outbox"] == ["processing_started_at", "next_attempt_at"]
    assert constraints[0][0] == "ck_email_outbox_processing_started_state"
    assert indexes == [("ix_email_outbox_status_next_attempt_id", "email_outbox", ("status", "next_attempt_at", "id"))]


def _add_outbox(session: Session, **kwargs) -> EmailOutbox:
    application = CandidateApplication()
    session.add(application)
    session.flush()
    row = EmailOutbox(application_id=application.id, **kwargs)
    session.add(row)
    session.flush()
    return row


def _load_migration() -> ModuleType:
    path = Path("alembic/versions/20260823_0005_email_outbox_delivery_state.py")
    spec = spec_from_file_location("email_outbox_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load email outbox migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
