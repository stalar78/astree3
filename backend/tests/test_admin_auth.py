from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from sqlalchemy import CheckConstraint, ForeignKeyConstraint
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.main import create_app
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


def test_admin_password_safety_contracts() -> None:
    password = "Correct Horse Battery Staple"
    spaced_password = "  Valid Passphrase With Spaces  "

    hashed = hash_admin_password(password)
    spaced_hash = hash_admin_password(spaced_password)

    assert hashed.startswith("$argon2id$")
    assert password not in hashed
    assert verify_admin_password(hashed, password)
    assert verify_admin_password(hashed, "wrong password") is False
    assert verify_admin_password("$argon2id$v=19$m=broken", password) is False
    assert verify_admin_password(hashed, None) is False  # type: ignore[arg-type]
    assert validate_admin_password(spaced_password) == spaced_password
    assert verify_admin_password(spaced_hash, spaced_password)
    assert verify_admin_password(spaced_hash, spaced_password.strip()) is False
    assert validate_admin_password(password) == password
    assert verify_admin_password(hashed, password.lower()) is False
    with pytest.raises(ValueError):
        validate_admin_password("short")
    with pytest.raises(ValueError):
        validate_admin_password("a" * 257)
    with pytest.raises(ValueError):
        validate_admin_password("bad\x00value")
    assert not admin_password_needs_rehash(hashed)


def test_admin_token_contracts() -> None:
    session_token_one = generate_admin_session_token()
    session_token_two = generate_admin_session_token()
    csrf_token_one = generate_admin_csrf_token()
    csrf_token_two = generate_admin_csrf_token()

    session_digest = hash_admin_token(session_token_one)
    csrf_digest = hash_admin_csrf_token(csrf_token_one)

    assert session_token_one != session_token_two
    assert csrf_token_one != csrf_token_two
    assert session_token_one != csrf_token_one
    assert len(session_digest) == 64
    assert len(csrf_digest) == 64
    assert session_digest != session_token_one
    assert csrf_digest != csrf_token_one
    assert _missing_admin_session_fields().isdisjoint(AdminSession.__table__.columns.keys())


def test_admin_model_constraints_and_relationships() -> None:
    user = AdminUser(username="  Astrea.Admin  ", password_hash="x" * 10, is_active=True)
    session = AdminSession(
        admin_user=user,
        token_hash="0" * 64,
        csrf_token_hash="1" * 64,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    assert user.username == "astrea.admin"
    assert user.is_active is True
    assert session.admin_user is user
    assert AdminUser.__table__.c.is_active.default is not None
    assert AdminUser.__table__.c.is_active.default.arg is True
    assert _constraint_names(AdminUser.__table__) == {
        "ck_admin_users_username_length",
        "ck_admin_users_password_hash_nonblank",
    }
    assert _constraint_names(AdminSession.__table__) == {
        "ck_admin_sessions_token_hash_length",
        "ck_admin_sessions_csrf_token_hash_length",
    }
    assert _fk_ondelete_values(AdminSession.__table__, "admin_users.id") == {"CASCADE"}
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


@pytest.mark.parametrize(
    ("session_kwargs", "error_message"),
    [
        ({"lookup_error": SQLAlchemyError("lookup SELECT password_hash FROM admin_users")}, "lookup"),
        ({"flush_error": SQLAlchemyError("flush INSERT password_hash leaked")}, "flush"),
        ({"commit_error": SQLAlchemyError("commit DATABASE_URL leaked")}, "commit"),
    ],
)
def test_initial_admin_bootstrap_wraps_sqlalchemy_failures(
    session_kwargs: dict[str, Exception],
    error_message: str,
) -> None:
    session = FakeBootstrapSession(**session_kwargs)
    settings = _bootstrap_settings()

    with pytest.raises(AdminBootstrapError) as exc_info:
        bootstrap_initial_admin(session, settings)

    assert str(exc_info.value) == "Admin bootstrap failed"
    assert error_message not in str(exc_info.value).lower()
    assert session.rollback_calls == 1

    if error_message == "lookup":
        assert session.execute_calls == 1
        assert session.add_calls == 0
        assert session.flush_calls == 0
        assert session.commit_calls == 0
    elif error_message == "flush":
        assert session.execute_calls == 1
        assert session.add_calls == 1
        assert session.flush_calls == 1
        assert session.commit_calls == 0
    else:
        assert session.execute_calls == 1
        assert session.add_calls == 1
        assert session.flush_calls == 1
        assert session.commit_calls == 1


def test_first_initial_admin_bootstrap_creates_one_user_and_commits_once() -> None:
    session = FakeBootstrapSession()
    result = bootstrap_initial_admin(session, _bootstrap_settings())

    admin_user = session.added_users[0]

    assert result.created is True
    assert result.admin_user_id == 1
    assert result.username == "astrea.admin"
    assert len(session.added_users) == 1
    assert admin_user.username == "astrea.admin"
    assert admin_user.is_active is True
    assert admin_user.password_hash.startswith("$argon2id$")
    assert "Correct Horse Battery Staple" not in admin_user.password_hash
    assert session.execute_calls == 1
    assert session.add_calls == 1
    assert session.flush_calls == 1
    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    assert session.refresh_calls == 0


def test_existing_admin_blocks_second_bootstrap_without_changing_credentials() -> None:
    existing_admin = FakeAdminRow(
        id=7,
        username="existing.admin",
        password_hash="existing-password-hash",
    )
    session = FakeBootstrapSession(existing_admin=existing_admin)
    result = bootstrap_initial_admin(
        session,
        Settings(
            DATABASE_URL="postgresql://user:pass@localhost:5432/astrea",
            ADMIN_INITIAL_USERNAME="different.admin",
            ADMIN_INITIAL_PASSWORD="Correct Horse Battery Staple",
        ),
    )

    assert result.created is False
    assert result.admin_user_id == 7
    assert result.username == "existing.admin"
    assert existing_admin.password_hash == "existing-password-hash"
    assert session.execute_calls == 1
    assert session.add_calls == 0
    assert session.flush_calls == 0
    assert session.commit_calls == 0
    assert session.rollback_calls == 0
    assert session.refresh_calls == 0


def test_bootstrap_does_not_refresh_or_query_after_commit() -> None:
    session = FakeBootstrapSession()

    bootstrap_initial_admin(session, _bootstrap_settings())

    assert session.execute_calls == 1
    assert session.commit_calls == 1
    assert session.refresh_calls == 0


def test_create_app_does_not_bootstrap_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_bootstrap(*_: Any, **__: Any) -> None:
        nonlocal called
        called = True
        raise AssertionError("bootstrap should not run during app creation")

    import app.services.admin_bootstrap as admin_bootstrap_module

    monkeypatch.setattr(admin_bootstrap_module, "bootstrap_initial_admin", fail_bootstrap)

    create_app(Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/astrea"))

    assert called is False


def _bootstrap_settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/astrea",
        ADMIN_INITIAL_USERNAME="  Astrea.Admin  ",
        ADMIN_INITIAL_PASSWORD="Correct Horse Battery Staple",
    )


def _constraint_names(table: Any) -> set[str | None]:
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
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


def _missing_admin_session_fields() -> set[str]:
    return {"session_token", "csrf_token", "ip_address", "user_agent", "fingerprint"}


def _load_migration_module() -> ModuleType:
    path = Path("alembic/versions/20260822_0003_admin_auth.py")
    spec = spec_from_file_location("admin_auth_migration", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load admin auth migration")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass
class FakeAdminRow:
    id: int
    username: str
    password_hash: str


@dataclass
class FakeExecuteResult:
    row: FakeAdminRow | None

    def first(self) -> FakeAdminRow | None:
        return self.row


class FakeBootstrapSession:
    def __init__(
        self,
        *,
        existing_admin: FakeAdminRow | None = None,
        lookup_error: Exception | None = None,
        flush_error: Exception | None = None,
        commit_error: Exception | None = None,
    ) -> None:
        self.existing_admin = existing_admin
        self.lookup_error = lookup_error
        self.flush_error = flush_error
        self.commit_error = commit_error
        self.added_users: list[AdminUser] = []
        self.execute_calls = 0
        self.add_calls = 0
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self.refresh_calls = 0
        self._next_id = 1

    def execute(self, statement: Any) -> FakeExecuteResult:
        self.execute_calls += 1
        if self.lookup_error is not None:
            raise self.lookup_error
        return FakeExecuteResult(self.existing_admin)

    def add(self, obj: AdminUser) -> None:
        self.add_calls += 1
        self.added_users.append(obj)

    def flush(self) -> None:
        self.flush_calls += 1
        if self.flush_error is not None:
            raise self.flush_error

        admin_user = self.added_users[0]
        admin_user.id = self._next_id
        self._next_id += 1

    def commit(self) -> None:
        self.commit_calls += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.rollback_calls += 1

    def refresh(self, _: AdminUser) -> None:
        self.refresh_calls += 1
