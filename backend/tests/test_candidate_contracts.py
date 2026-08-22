from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.base import Base
from app.models.candidate import ApplicationConsent, CandidateApplication, EmailOutbox
from app.services.candidate_contracts import (
    CONSENT_TYPES,
    EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED,
    EMAIL_OUTBOX_STATUS_PENDING,
    EMAIL_OUTBOX_STATUSES,
    SAINT_PETERSBURG_ACKNOWLEDGEMENT_TEXT,
)

EXPECTED_TABLES = {
    "pages",
    "news_posts",
    "videos",
    "candidate_applications",
    "application_consents",
    "email_outbox",
}


def test_metadata_contains_stage_4_3a_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_candidate_application_expected_fields_and_exclusions() -> None:
    columns = set(CandidateApplication.__table__.columns.keys())

    assert {
        "id",
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
        "photo_storage_key",
        "photo_media_type",
        "photo_size_bytes",
        "created_at",
        "updated_at",
    }.issubset(columns)
    assert "religion" not in columns
    assert "original_filename" not in columns
    assert "public_photo_url" not in columns
    assert "photo_blob" not in columns
    assert "photo_binary" not in columns
    assert "ip_address" not in columns


def test_consent_constraints_and_constant() -> None:
    table = ApplicationConsent.__table__

    assert _has_fk_to(table, "candidate_applications.id")
    assert _constraint_names(table, UniqueConstraint) == {"uq_application_consents_type"}
    assert "ck_application_consents_type" in _constraint_names(table, CheckConstraint)
    assert "ck_application_consents_document_version" in _constraint_names(table, CheckConstraint)
    assert table.c.document_version.nullable is False
    assert set(CONSENT_TYPES) == {
        "personal_data_processing",
        "privacy_policy_acknowledgement",
        "saint_petersburg_acknowledgement",
    }
    assert (
        SAINT_PETERSBURG_ACKNOWLEDGEMENT_TEXT
        == "Я понимаю, что подаю заявку на вступление в ложу, работающую в Санкт-Петербурге"
    )


def test_email_outbox_constraints_defaults_and_exclusions() -> None:
    table = EmailOutbox.__table__
    columns = set(table.columns.keys())

    assert _has_fk_to(table, "candidate_applications.id")
    assert "ck_email_outbox_event_type" in _constraint_names(table, CheckConstraint)
    assert "ck_email_outbox_status" in _constraint_names(table, CheckConstraint)
    assert "ck_email_outbox_attempts_non_negative" in _constraint_names(table, CheckConstraint)
    assert EmailOutbox().status is None
    assert table.c.status.default.arg == EMAIL_OUTBOX_STATUS_PENDING
    assert table.c.attempts.default.arg == 0
    assert table.c.event_type.default.arg == EMAIL_OUTBOX_EVENT_CANDIDATE_APPLICATION_RECEIVED
    assert set(EMAIL_OUTBOX_STATUSES) == {"pending", "processing", "sent", "failed"}
    assert "smtp_password" not in columns
    assert "payload" not in columns
    assert "candidate_payload" not in columns
    assert "photo_blob" not in columns


def test_candidate_migration_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration_module()
    created_tables: dict[str, tuple[Any, ...]] = {}
    dropped_tables: list[str] = []

    def capture_create_table(name: str, *columns_and_constraints: Any, **_: Any) -> None:
        created_tables[name] = columns_and_constraints

    def capture_drop_table(name: str) -> None:
        dropped_tables.append(name)

    monkeypatch.setattr(migration.op, "create_table", capture_create_table)
    monkeypatch.setattr(migration.op, "drop_table", capture_drop_table)
    monkeypatch.setattr(migration.op, "create_index", _noop)
    monkeypatch.setattr(migration.op, "drop_index", _noop)
    monkeypatch.setattr(migration.op, "f", lambda name: name)

    migration.upgrade()
    migration.downgrade()

    assert migration.down_revision == "20260822_0001"
    assert set(created_tables) == {
        "candidate_applications",
        "application_consents",
        "email_outbox",
    }
    assert dropped_tables == ["email_outbox", "application_consents", "candidate_applications"]
    assert "religion" not in _all_column_names(created_tables)
    assert "photo_blob" not in _all_column_names(created_tables)
    assert "original_filename" not in _all_column_names(created_tables)
    assert "public_photo_url" not in _all_column_names(created_tables)


def _constraint_names(table: Any, constraint_type: type[Any]) -> set[str | None]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, constraint_type)
    }


def _has_fk_to(table: Any, target: str) -> bool:
    return any(
        element.target_fullname == target
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
    )


def _load_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0002_candidate_intake.py")
    spec = spec_from_file_location("candidate_intake_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate intake migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _all_column_names(created_tables: dict[str, tuple[Any, ...]]) -> set[str]:
    return {
        item.name
        for columns_and_constraints in created_tables.values()
        for item in columns_and_constraints
        if hasattr(item, "name")
    }


def _noop(*_: Any, **__: Any) -> None:
    return None
