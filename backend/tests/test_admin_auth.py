from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.models.admin import AdminSession, AdminUser
from app.services.admin_auth import (
    admin_password_needs_rehash,
    generate_admin_csrf_token,
    generate_admin_session_token,
    hash_admin_csrf_token,
    hash_admin_password,
    hash_admin_token,
    normalize_admin_username,
    validate_admin_password,
    verify_admin_password,
)
from app.services.admin_bootstrap import AdminBootstrapError, bootstrap_initial_admin


def test_admin_username_is_normalized_and_validated() -> None:
    assert normalize_admin_username("  Astrea.Admin_01  ") == "astrea.admin_01"

    with pytest.raises(ValueError):
        normalize_admin_username("ab")

    with pytest.raises(ValueError):
        normalize_admin_username("-admin")

    with pytest.raises(ValueError):
        normalize_admin_username("админ")


def test_admin_password_hashing_and_verification() -> None:
    password = "correct horse battery staple"

    hashed = hash_admin_password(password)

    assert hashed.startswith("$argon2id$")
    assert verify_admin_password(hashed, password)
    assert not verify_admin_password(hashed, "incorrect horse battery staple")
    assert not admin_password_needs_rehash(hashed)


def test_admin_password_validation_rejects_short_or_control_char_passwords() -> None:
    with pytest.raises(ValueError):
        validate_admin_password("short")

    with pytest.raises(ValueError):
        validate_admin_password("a" * 11)

    with pytest.raises(ValueError):
        validate_admin_password("a" * 11 + "\x00")


def test_admin_token_hashes_are_opaque_sha256_digests() -> None:
    session_token = generate_admin_session_token()
    csrf_token = generate_admin_csrf_token()

    assert len(hash_admin_token(session_token)) == 64
    assert len(hash_admin_csrf_token(csrf_token)) == 64
    assert session_token != csrf_token


def test_admin_model_constraints_and_relationships() -> None:
    user = AdminUser(username="  Astrea.Admin  ", password_hash="x" * 10)
    session = AdminSession(
        admin_user=user,
        token_hash="0" * 64,
        csrf_token_hash="1" * 64,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    assert user.username == "astrea.admin"
    assert AdminUser.__table__.c.is_active.default is not None
    assert AdminUser.__table__.c.is_active.default.arg is True
    assert session.admin_user is user
    assert _constraint_names(AdminUser.__table__, CheckConstraint) == {
        "ck_admin_users_username_length",
        "ck_admin_users_password_hash_nonblank",
    }
    assert _constraint_names(AdminSession.__table__, CheckConstraint) == {
        "ck_admin_sessions_token_hash_length",
        "ck_admin_sessions_csrf_token_hash_length",
    }
    assert _fk_ondelete_values(AdminSession.__table__, "admin_users.id") == {"CASCADE"}
    assert AdminUser.__table__.c.username.unique is True
    assert AdminUser.__table__.c.username.index is True
    assert AdminSession.__table__.c.admin_user_id.index is True
    assert AdminSession.__table__.c.token_hash.unique is True
    assert AdminSession.__table__.c.token_hash.index is True
    assert AdminSession.__table__.c.expires_at.index is True


def test_admin_migration_creates_only_admin_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    migration = _load_migration_module()
    created_tables: dict[str, tuple[Any, ...]] = {}
    created_indexes: list[tuple[str, str, tuple[str, ...], bool]] = []
    dropped_tables: list[str] = []
    dropped_indexes: list[tuple[str, str | None]] = []

    def capture_create_table(name: str, *columns_and_constraints: Any, **_: Any) -> None:
        created_tables[name] = columns_and_constraints

    def capture_create_index(
        name: str,
        table_name: str,
        columns: list[str],
        unique: bool = False,
        **_: Any,
    ) -> None:
        created_indexes.append((name, table_name, tuple(columns), unique))

    def capture_drop_table(name: str) -> None:
        dropped_tables.append(name)

    def capture_drop_index(name: str, table_name: str | None = None, **_: Any) -> None:
        dropped_indexes.append((name, table_name))

    monkeypatch.setattr(migration.op, "create_table", capture_create_table)
    monkeypatch.setattr(migration.op, "create_index", capture_create_index)
    monkeypatch.setattr(migration.op, "drop_table", capture_drop_table)
    monkeypatch.setattr(migration.op, "drop_index", capture_drop_index)
    monkeypatch.setattr(migration.op, "f", lambda name: name)

    migration.upgrade()
    migration.downgrade()

    assert migration.down_revision == "20260822_0002"
    assert set(created_tables) == {"admin_users", "admin_sessions"}
    assert created_indexes == [
        ("ix_admin_users_username", "admin_users", ("username",), True),
        ("ix_admin_sessions_admin_user_id", "admin_sessions", ("admin_user_id",), False),
        ("ix_admin_sessions_token_hash", "admin_sessions", ("token_hash",), True),
        ("ix_admin_sessions_expires_at", "admin_sessions", ("expires_at",), False),
    ]
    assert dropped_tables == ["admin_sessions", "admin_users"]
    assert dropped_indexes == [
        ("ix_admin_sessions_expires_at", "admin_sessions"),
        ("ix_admin_sessions_token_hash", "admin_sessions"),
        ("ix_admin_sessions_admin_user_id", "admin_sessions"),
        ("ix_admin_users_username", "admin_users"),
    ]
    assert _migration_constraint_names(created_tables["admin_users"]) == {
        "ck_admin_users_username_length",
        "ck_admin_users_password_hash_nonblank",
    }
    assert _migration_constraint_names(created_tables["admin_sessions"]) == {
        "ck_admin_sessions_token_hash_length",
        "ck_admin_sessions_csrf_token_hash_length",
    }
    assert _migration_fk_ondelete_values(created_tables["admin_sessions"]) == {"CASCADE"}
    assert _migration_column(created_tables["admin_users"], "username").type.length == 80
    assert _migration_column(created_tables["admin_sessions"], "token_hash").type.length == 64
    assert _migration_column(created_tables["admin_sessions"], "csrf_token_hash").type.length == 64
    assert _migration_column(created_tables["admin_sessions"], "expires_at").nullable is False


def test_initial_admin_bootstrap_creates_user_once() -> None:
    session = _make_session()
    settings = Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/astrea",
        ADMIN_INITIAL_USERNAME="  Astrea.Admin  ",
        ADMIN_INITIAL_PASSWORD="correct horse battery staple",
    )

    first = bootstrap_initial_admin(session, settings)
    second = bootstrap_initial_admin(session, settings)

    user = session.scalar(select(AdminUser).where(AdminUser.username == "astrea.admin"))

    assert first.created is True
    assert second.created is False
    assert first.username == "astrea.admin"
    assert first.admin_user_id == second.admin_user_id
    assert user is not None
    assert verify_admin_password(user.password_hash, "correct horse battery staple")


def test_initial_admin_bootstrap_requires_credentials() -> None:
    session = _make_session()
    settings = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/astrea")

    with pytest.raises(AdminBootstrapError):
        bootstrap_initial_admin(session, settings)


def _constraint_names(table: Any, constraint_type: type[Any]) -> set[str | None]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, constraint_type)
    }


def _fk_ondelete_values(table: Any, target: str) -> set[str | None]:
    return {
        element.ondelete
        for constraint in table.constraints
        if isinstance(constraint, ForeignKeyConstraint)
        for element in constraint.elements
        if element.target_fullname == target
    }


def _migration_constraint_names(columns_and_constraints: tuple[Any, ...]) -> set[str | None]:
    return {
        item.name
        for item in columns_and_constraints
        if isinstance(item, CheckConstraint)
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


def _load_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0003_admin_auth.py")
    spec = spec_from_file_location("admin_auth_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load admin auth migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine, tables=[AdminUser.__table__, AdminSession.__table__])
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    return SessionLocal()
