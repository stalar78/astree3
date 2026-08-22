from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint

from app.db.base import Base
from app.models.candidate import ApplicationConsent, CandidateApplication, EmailOutbox
from app.services.candidate_contracts import (
    CANDIDATE_STATUS_ARCHIVED,
    CANDIDATE_STATUS_CLOSED,
    CANDIDATE_STATUS_CONTACTED,
    CANDIDATE_STATUS_IN_REVIEW,
    CANDIDATE_STATUS_NEW,
    CANDIDATE_STATUSES,
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
    "admin_users",
    "admin_sessions",
}


def test_metadata_contains_stage_4_3a_tables() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_candidate_application_expected_fields_and_exclusions() -> None:
    table = CandidateApplication.__table__
    columns = set(table.columns.keys())

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
        "status",
        "created_at",
        "updated_at",
    }.issubset(columns)
    assert "religion" not in columns
    assert "original_filename" not in columns
    assert "public_photo_url" not in columns
    assert "photo_blob" not in columns
    assert "photo_binary" not in columns
    assert "ip_address" not in columns
    assert "ck_candidate_applications_photo_size_non_negative" in _constraint_names(
        table,
        CheckConstraint,
    )
    assert "ck_candidate_applications_status" in _constraint_names(table, CheckConstraint)
    assert table.c.status.default.arg == CANDIDATE_STATUS_NEW
    assert table.c.status.server_default.arg == CANDIDATE_STATUS_NEW
    assert table.c.status.nullable is False
    assert table.c.status.index is True
    assert set(CANDIDATE_STATUSES) == {
        CANDIDATE_STATUS_NEW,
        CANDIDATE_STATUS_IN_REVIEW,
        CANDIDATE_STATUS_CONTACTED,
        CANDIDATE_STATUS_CLOSED,
        CANDIDATE_STATUS_ARCHIVED,
    }


def test_consent_constraints_and_constant() -> None:
    table = ApplicationConsent.__table__

    assert _has_fk_to(table, "candidate_applications.id")
    assert _fk_ondelete_values(table, "candidate_applications.id") == {"CASCADE"}
    assert _constraint_names(table, UniqueConstraint) == {"uq_application_consents_type"}
    assert "ck_application_consents_type" in _constraint_names(table, CheckConstraint)
    assert "ck_application_consents_document_version" in _constraint_names(table, CheckConstraint)
    document_version_constraint = _constraint_by_name(
        table,
        "ck_application_consents_document_version",
    )
    assert "btrim(document_version)" in str(document_version_constraint.sqltext)
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
    assert _fk_ondelete_values(table, "candidate_applications.id") == {"CASCADE"}
    assert "ck_email_outbox_event_type" in _constraint_names(table, CheckConstraint)
    assert "ck_email_outbox_status" in _constraint_names(table, CheckConstraint)
    assert "ck_email_outbox_attempts_non_negative" in _constraint_names(table, CheckConstraint)
    assert table.c.last_error.type.length == 2000
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
    assert _migration_constraint_names(created_tables["candidate_applications"]) == {
        "ck_candidate_applications_photo_size_non_negative"
    }
    assert _migration_constraint_names(created_tables["application_consents"]) == {
        "ck_application_consents_type",
        "ck_application_consents_document_version",
        "uq_application_consents_type",
    }
    assert _migration_constraint_names(created_tables["email_outbox"]) == {
        "ck_email_outbox_event_type",
        "ck_email_outbox_status",
        "ck_email_outbox_attempts_non_negative",
    }
    assert _migration_fk_ondelete_values(created_tables["application_consents"]) == {"CASCADE"}
    assert _migration_fk_ondelete_values(created_tables["email_outbox"]) == {"CASCADE"}
    assert _migration_column(created_tables["email_outbox"], "last_error").type.length == 2000
    document_version_constraint = _migration_constraint_by_name(
        created_tables["application_consents"],
        "ck_application_consents_document_version",
    )
    assert "btrim(document_version)" in str(document_version_constraint.sqltext)


def test_candidate_admin_status_migration_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_admin_status_migration_module()
    added_columns: list[tuple[str, Any]] = []
    created_constraints: list[tuple[str, str, str]] = []
    created_indexes: list[tuple[str, str, tuple[str, ...], bool]] = []
    dropped_indexes: list[tuple[str, str | None]] = []
    dropped_constraints: list[tuple[str, str, str | None]] = []
    dropped_columns: list[tuple[str, str]] = []

    def capture_add_column(table_name: str, column: Any, **_: Any) -> None:
        added_columns.append((table_name, column))

    def capture_create_constraint(name: str, table_name: str, condition: str, **_: Any) -> None:
        created_constraints.append((name, table_name, condition))

    def capture_create_index(
        name: str,
        table_name: str,
        columns: list[str],
        unique: bool = False,
        **_: Any,
    ) -> None:
        created_indexes.append((name, table_name, tuple(columns), unique))

    def capture_drop_index(name: str, table_name: str | None = None, **_: Any) -> None:
        dropped_indexes.append((name, table_name))

    def capture_drop_constraint(name: str, table_name: str, type_: str | None = None, **_: Any) -> None:
        dropped_constraints.append((name, table_name, type_))

    def capture_drop_column(table_name: str, column_name: str, **_: Any) -> None:
        dropped_columns.append((table_name, column_name))

    monkeypatch.setattr(migration.op, "add_column", capture_add_column)
    monkeypatch.setattr(migration.op, "create_check_constraint", capture_create_constraint)
    monkeypatch.setattr(migration.op, "create_index", capture_create_index)
    monkeypatch.setattr(migration.op, "drop_index", capture_drop_index)
    monkeypatch.setattr(migration.op, "drop_constraint", capture_drop_constraint)
    monkeypatch.setattr(migration.op, "drop_column", capture_drop_column)

    migration.upgrade()
    migration.downgrade()

    assert migration.revision == "20260822_0004"
    assert migration.down_revision == "20260822_0003"
    assert len(added_columns) == 1
    table_name, column = added_columns[0]
    assert table_name == "candidate_applications"
    assert column.name == "status"
    assert column.type.length == 32
    assert column.nullable is False
    assert column.server_default.arg == "new"
    assert created_constraints == [
        (
            "ck_candidate_applications_status",
            "candidate_applications",
            "status IN ('new', 'in_review', 'contacted', 'closed', 'archived')",
        ),
    ]
    assert created_indexes == [("ix_candidate_applications_status", "candidate_applications", ("status",), False)]
    assert dropped_indexes == [("ix_candidate_applications_status", "candidate_applications")]
    assert dropped_constraints == [("ck_candidate_applications_status", "candidate_applications", "check")]
    assert dropped_columns == [("candidate_applications", "status")]


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


def _fk_ondelete_values(table: Any, target: str) -> set[str | None]:
    return {
        element.ondelete
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
        if element.target_fullname == target
    }


def _constraint_by_name(table: Any, name: str) -> CheckConstraint:
    for constraint in table.constraints:
        if isinstance(constraint, CheckConstraint) and constraint.name == name:
            return constraint
    raise AssertionError(f"Missing constraint {name}")


def _load_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0002_candidate_intake.py")
    spec = spec_from_file_location("candidate_intake_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate intake migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_admin_status_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0004_candidate_admin_status.py")
    spec = spec_from_file_location("candidate_admin_status_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate admin status migration")
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


def _migration_constraint_names(columns_and_constraints: tuple[Any, ...]) -> set[str | None]:
    return {
        item.name
        for item in columns_and_constraints
        if isinstance(item, CheckConstraint | UniqueConstraint)
    }


def _migration_fk_ondelete_values(columns_and_constraints: tuple[Any, ...]) -> set[str | None]:
    return {
        element.ondelete
        for item in columns_and_constraints
        if isinstance(item, ForeignKeyConstraint)
        for element in item.elements
    }


def _migration_column(columns_and_constraints: tuple[Any, ...], name: str) -> Any:
    for item in columns_and_constraints:
        if getattr(item, "name", None) == name:
            return item
    raise AssertionError(f"Missing column {name}")


def _migration_constraint_by_name(
    columns_and_constraints: tuple[Any, ...],
    name: str,
) -> CheckConstraint:
    for item in columns_and_constraints:
        if isinstance(item, CheckConstraint) and item.name == name:
            return item
    raise AssertionError(f"Missing constraint {name}")


def _noop(*_: Any, **__: Any) -> None:
    return None
