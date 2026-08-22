from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import admin_auth as admin_api
from app.api.admin_auth import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, SESSION_COOKIE_NAME
from app.db.session import get_db
from app.main import create_app
from app.models.admin import AdminSession, AdminUser
from app.services.admin_auth import (
    DUMMY_PASSWORD_HASH,
    hash_admin_csrf_token,
    hash_admin_password,
    hash_admin_token,
)

VALID_PASSWORD = "Correct Horse Battery Staple"
SPACED_PASSWORD = "  Valid Passphrase With Spaces  "


def test_login_success_sets_secure_cookies_and_persists_session() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "  Astrea.Admin  ", "password": VALID_PASSWORD},
        )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "username": "astrea.admin"}
    assert response.headers["cache-control"] == "no-store"
    assert VALID_PASSWORD not in response.text
    assert response.cookies.get(SESSION_COOKIE_NAME) != response.cookies.get(CSRF_COOKIE_NAME)

    session_cookie = response.cookies.get(SESSION_COOKIE_NAME)
    csrf_cookie = response.cookies.get(CSRF_COOKIE_NAME)
    assert session_cookie is not None
    assert csrf_cookie is not None

    session_header = _set_cookie_header(response, SESSION_COOKIE_NAME)
    csrf_header = _set_cookie_header(response, CSRF_COOKIE_NAME)
    assert "httponly" in session_header.lower()
    assert "samesite=strict" in session_header.lower()
    assert "path=/api/v1/admin" in session_header.lower()
    assert "secure" not in session_header.lower()
    assert "httponly" not in csrf_header.lower()
    assert "samesite=strict" in csrf_header.lower()
    assert "path=/" in csrf_header.lower()
    assert "secure" not in csrf_header.lower()

    stored_session = session.sessions[0]
    assert stored_session.token_hash == hash_admin_token(session_cookie)
    assert stored_session.csrf_token_hash == hash_admin_csrf_token(csrf_cookie)
    assert len(stored_session.token_hash) == 64
    assert len(stored_session.csrf_token_hash) == 64
    assert stored_session.expires_at.tzinfo is UTC
    assert stored_session.expires_at > datetime.now(UTC)
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_login_secure_cookie_policy_tracks_environment() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session, _settings(app_env="production")) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )

    session_header = _set_cookie_header(response, SESSION_COOKIE_NAME)
    csrf_header = _set_cookie_header(response, CSRF_COOKIE_NAME)
    assert "secure" in session_header.lower()
    assert "secure" in csrf_header.lower()


def test_login_reuses_no_incoming_session_and_generates_new_tokens() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        first = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
            cookies={SESSION_COOKIE_NAME: "bogus-session-token"},
        )
        second = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )

    first_session_token = first.cookies.get(SESSION_COOKIE_NAME)
    first_csrf_token = first.cookies.get(CSRF_COOKIE_NAME)
    second_session_token = second.cookies.get(SESSION_COOKIE_NAME)
    second_csrf_token = second.cookies.get(CSRF_COOKIE_NAME)

    assert first_session_token != "bogus-session-token"
    assert first_csrf_token is not None
    assert second_session_token is not None
    assert second_csrf_token is not None
    assert first_session_token != second_session_token
    assert first_csrf_token != second_csrf_token
    assert len(session.sessions) == 2
    assert session.sessions[0].token_hash != session.sessions[1].token_hash
    assert session.sessions[0].csrf_token_hash != session.sessions[1].csrf_token_hash


def test_login_unknown_username_uses_dummy_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeAdminAuthSession(users=[])
    called_hashes: list[str] = []
    original = admin_api.verify_admin_password

    def tracking_verify(password_hash: str, password: str) -> bool:
        called_hashes.append(password_hash)
        return original(password_hash, password)

    monkeypatch.setattr(admin_api, "verify_admin_password", tracking_verify)

    with _client(session) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "missing.admin", "password": VALID_PASSWORD},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid admin credentials"}
    assert called_hashes == [DUMMY_PASSWORD_HASH]
    assert session.scalar_calls == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "not*valid", "password": VALID_PASSWORD},
        {"username": "astrea.admin", "password": "bad\x00value"},
        {"username": "astrea.admin", "password": "a" * 257},
    ],
)
def test_login_invalid_credentials_are_generic_and_non_echoing(payload: dict[str, str]) -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        response = client.post("/api/v1/admin/auth/login", json=payload)

    assert response.status_code in {401, 422}
    assert payload["username"] not in response.text
    assert payload["password"][:20] not in response.text
    if response.status_code == 401:
        assert response.json() == {"detail": "Invalid admin credentials"}
    else:
        assert response.json() == {"detail": "Invalid admin authentication request"}


def test_login_extra_fields_are_rejected_generically() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={
                "username": "astrea.admin",
                "password": VALID_PASSWORD,
                "extra": "SHOULD_NOT_LEAK",
            },
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin authentication request"}
    assert "SHOULD_NOT_LEAK" not in response.text


def test_login_validation_errors_are_generic() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": "x" * 257},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin authentication request"}
    assert "x" * 30 not in response.text


def test_login_rate_limit_blocks_after_configured_attempts_and_ignores_forwarded_for() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session, _settings(admin_login_rate_limit_requests=1)) as client:
        first = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": "wrong password"},
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        second = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": "wrong password"},
            headers={"X-Forwarded-For": "5.6.7.8"},
        )

    assert first.status_code == 401
    assert second.status_code == 429
    assert session.scalar_calls == 1
    assert "Retry-After" in second.headers


def test_login_lookup_and_persistence_failures_are_generic_503() -> None:
    cases = [
        FakeAdminAuthSession(users=[_admin_user()], scalar_error=SQLAlchemyError("lookup")),
        FakeAdminAuthSession(users=[_admin_user()], flush_error=SQLAlchemyError("flush")),
        FakeAdminAuthSession(users=[_admin_user()], commit_error=SQLAlchemyError("commit")),
    ]

    for case in cases:
        with _client(case) as client:
            response = client.post(
                "/api/v1/admin/auth/login",
                json={"username": "astrea.admin", "password": VALID_PASSWORD},
            )

    assert response.status_code == 503
    assert response.json() == {"detail": "Admin authentication temporarily unavailable"}
    assert "lookup" not in response.text
    assert "flush" not in response.text
    assert "commit" not in response.text
    assert not response.cookies.get(SESSION_COOKIE_NAME)
    assert not response.cookies.get(CSRF_COOKIE_NAME)
    assert case.rollback_calls == 1


def test_me_returns_authenticated_admin_without_extending_session() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        previous_expiry = session.sessions[0].expires_at
        me = client.get("/api/v1/admin/auth/me")

    assert me.status_code == 200
    assert me.json() == {"authenticated": True, "username": "astrea.admin"}
    assert me.headers["cache-control"] == "no-store"
    assert session.sessions[0].expires_at == previous_expiry
    assert session.commit_calls == 1
    assert login.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "cookie_value, expect_db_lookup",
    [
        (None, False),
        ("bad", False),
        ("x" * 129, False),
        ("unknown-admin-session-token-1234567890", True),
    ],
)
def test_me_handles_missing_unknown_and_malformed_sessions(
    cookie_value: str | None,
    expect_db_lookup: bool,
) -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])
    session.sessions.append(
        _session_for_user(session.users[0], "known-session-token-1234567890", "known-csrf-token-1234567890")
    )

    with _client(session) as client:
        cookies = {SESSION_COOKIE_NAME: cookie_value} if cookie_value is not None else {}
        response = client.get("/api/v1/admin/auth/me", cookies=cookies)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid admin session"}
    assert "unknown-admin" not in response.text
    assert session.execute_calls == (1 if expect_db_lookup else 0)


def test_me_rejects_expired_and_inactive_sessions() -> None:
    expired_user = _admin_user()
    inactive_user = _admin_user(username="inactive.admin", is_active=False)
    expired_session = _session_for_user(
        expired_user,
        "expired-session-token-1234567890",
        "expired-csrf-token-1234567890",
        expires_at=datetime.now(UTC) - timedelta(minutes=1),
    )
    inactive_session = _session_for_user(
        inactive_user,
        "inactive-session-token-1234567890",
        "inactive-csrf-token-1234567890",
    )

    session = FakeAdminAuthSession(users=[expired_user, inactive_user], sessions=[expired_session, inactive_session])

    with _client(session) as client:
        expired = client.get("/api/v1/admin/auth/me", cookies={SESSION_COOKIE_NAME: expired_session.token_hash_raw})
        inactive = client.get("/api/v1/admin/auth/me", cookies={SESSION_COOKIE_NAME: inactive_session.token_hash_raw})

    assert expired.status_code == 401
    assert inactive.status_code == 401
    assert session.commit_calls == 0


def test_me_lookup_failure_returns_generic_503() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()], execute_error=SQLAlchemyError("lookup"))

    with _client(session) as client:
        response = client.get(
            "/api/v1/admin/auth/me",
            cookies={SESSION_COOKIE_NAME: "known-session-token-1234567890abcd"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": "Admin authentication temporarily unavailable"}
    assert "lookup" not in response.text
    assert session.rollback_calls == 1


def test_logout_success_requires_csrf_and_clears_both_cookies() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        csrf_cookie = login.cookies.get(CSRF_COOKIE_NAME)
        response = client.post(
            "/api/v1/admin/auth/logout",
            headers={CSRF_HEADER_NAME: csrf_cookie},
        )

    assert response.status_code == 204
    assert response.headers["cache-control"] == "no-store"
    clear_headers = _set_cookie_headers(response)
    assert any(header.lower().startswith(f"{SESSION_COOKIE_NAME.lower()}=") for header in clear_headers)
    assert any(header.lower().startswith(f"{CSRF_COOKIE_NAME.lower()}=") for header in clear_headers)
    assert any("max-age=0" in header.lower() for header in clear_headers)
    assert any("path=/api/v1/admin" in header.lower() for header in clear_headers)
    assert any("path=/" in header.lower() for header in clear_headers)
    assert session.delete_calls == 1
    assert session.commit_calls == 2
    assert len(session.sessions) == 0


@pytest.mark.parametrize(
    "headers, cookies, mutated_hash",
    [
        ({}, None, None),
        ({CSRF_HEADER_NAME: "wrong"}, None, None),
        ({}, {CSRF_COOKIE_NAME: "wrong"}, None),
        ({CSRF_HEADER_NAME: "wrong"}, {CSRF_COOKIE_NAME: "wrong"}, None),
        ({CSRF_HEADER_NAME: "x" * 129}, {CSRF_COOKIE_NAME: "x" * 129}, None),
    ],
)
def test_logout_csrf_failures_do_not_delete_or_commit(
    headers: dict[str, str],
    cookies: dict[str, str] | None,
    mutated_hash: str | None,
) -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        csrf_cookie = login.cookies.get(CSRF_COOKIE_NAME)
        session.sessions[0].csrf_token_hash = mutated_hash or session.sessions[0].csrf_token_hash
        request_cookies = {
            SESSION_COOKIE_NAME: login.cookies.get(SESSION_COOKIE_NAME),
            CSRF_COOKIE_NAME: csrf_cookie,
        }
        if cookies is not None:
            request_cookies.update(cookies)
        response = client.post("/api/v1/admin/auth/logout", headers=headers, cookies=request_cookies)

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid admin CSRF token"}
    assert session.delete_calls == 0
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_logout_missing_csrf_cookie_is_rejected() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        client.cookies.clear()
        client.cookies.set(SESSION_COOKIE_NAME, login.cookies.get(SESSION_COOKIE_NAME), path="/api/v1/admin")
        response = client.post(
            "/api/v1/admin/auth/logout",
            headers={CSRF_HEADER_NAME: login.cookies.get(CSRF_COOKIE_NAME)},
        )

    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid admin CSRF token"}
    assert session.delete_calls == 0
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_logout_hash_mismatch_between_cookie_and_session_is_rejected() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        session.sessions[0].csrf_token_hash = hash_admin_csrf_token("different-token-1234567890")
        response = client.post(
            "/api/v1/admin/auth/logout",
            headers={CSRF_HEADER_NAME: login.cookies.get(CSRF_COOKIE_NAME)},
        )

    assert response.status_code == 403
    assert session.delete_calls == 0
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_logout_lookup_and_delete_failures_are_generic_503() -> None:
    cases = [
        ("lookup", "execute_error", SQLAlchemyError("lookup"), "Admin authentication temporarily unavailable"),
        ("delete", "delete_error", SQLAlchemyError("delete"), "Admin logout temporarily unavailable"),
        ("commit", "commit_error", SQLAlchemyError("commit"), "Admin logout temporarily unavailable"),
    ]

    for _, error_attr, error, expected_detail in cases:
        session = FakeAdminAuthSession(users=[_admin_user()])
        with _client(session) as client:
            login = client.post(
                "/api/v1/admin/auth/login",
                json={"username": "astrea.admin", "password": VALID_PASSWORD},
            )
            csrf_header = _set_cookie_header(login, CSRF_COOKIE_NAME)
            csrf_token = csrf_header.split(";", 1)[0].split("=", 1)[1].strip('"')
            setattr(session, error_attr, error)
            response = client.post(
                "/api/v1/admin/auth/logout",
                headers={CSRF_HEADER_NAME: csrf_token},
            )

        assert response.status_code == 503
        assert response.json() == {"detail": expected_detail}
        assert "lookup" not in response.text
        assert "delete" not in response.text
        assert "commit" not in response.text
        assert session.rollback_calls == 1


def test_logout_does_not_succeed_without_matching_current_session() -> None:
    session = FakeAdminAuthSession(users=[_admin_user()])

    with _client(session) as client:
        login = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": VALID_PASSWORD},
        )
        response = client.post(
            "/api/v1/admin/auth/logout",
            headers={CSRF_HEADER_NAME: login.cookies.get(CSRF_COOKIE_NAME)},
            cookies={SESSION_COOKIE_NAME: "unknown-session-token-1234567890"},
        )

    assert response.status_code == 401
    assert session.delete_calls == 0
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_login_password_with_spaces_remains_exactly_as_submitted() -> None:
    session = FakeAdminAuthSession(users=[_admin_user(password=SPACED_PASSWORD)])

    with _client(session) as client:
        response = client.post(
            "/api/v1/admin/auth/login",
            json={"username": "astrea.admin", "password": SPACED_PASSWORD},
        )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True, "username": "astrea.admin"}
    assert response.cookies.get(SESSION_COOKIE_NAME) is not None


def _client(session: FakeAdminAuthSession, settings: Any | None = None) -> TestClient:
    app = create_app(settings or _settings())
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app)


def _settings(
    *,
    app_env: str = "test",
    admin_login_rate_limit_requests: int = 10,
    admin_login_rate_limit_window_seconds: int = 900,
    admin_session_ttl_seconds: int = 28_800,
) -> Any:
    from app.core.config import Settings

    return Settings(
        DATABASE_URL="postgresql://user:pass@localhost:5432/astrea",
        APP_ENV=app_env,
        ADMIN_LOGIN_RATE_LIMIT_REQUESTS=admin_login_rate_limit_requests,
        ADMIN_LOGIN_RATE_LIMIT_WINDOW_SECONDS=admin_login_rate_limit_window_seconds,
        ADMIN_SESSION_TTL_SECONDS=admin_session_ttl_seconds,
    )


def _admin_user(
    *,
    username: str = "astrea.admin",
    password: str = VALID_PASSWORD,
    is_active: bool = True,
) -> AdminUser:
    user = AdminUser(username=username, password_hash=hash_admin_password(password), is_active=is_active)
    user.id = 1
    return user


def _session_for_user(
    user: AdminUser,
    raw_session_token: str,
    raw_csrf_token: str,
    *,
    expires_at: datetime | None = None,
) -> AdminSession:
    session = AdminSession(
        admin_user_id=user.id,
        token_hash=hash_admin_token(raw_session_token),
        csrf_token_hash=hash_admin_csrf_token(raw_csrf_token),
        expires_at=expires_at or (datetime.now(UTC) + timedelta(hours=1)),
    )
    session.id = 1
    session.admin_user = user
    session.token_hash_raw = raw_session_token
    return session


def _set_cookie_header(response: Any, cookie_name: str) -> str:
    for header in _set_cookie_headers(response):
        if header.lower().startswith(f"{cookie_name.lower()}="):
            return header
    raise AssertionError(f"Missing Set-Cookie header for {cookie_name}")


def _set_cookie_headers(response: Any) -> list[str]:
    headers = response.headers
    if hasattr(headers, "get_list"):
        return headers.get_list("set-cookie")
    if hasattr(headers, "getlist"):
        return headers.getlist("set-cookie")
    value = headers.get("set-cookie")
    return [value] if value else []


@dataclass
class FakeExecuteResult:
    row: tuple[AdminSession, AdminUser] | None

    def first(self) -> tuple[AdminSession, AdminUser] | None:
        return self.row


class FakeAdminAuthSession:
    def __init__(
        self,
        *,
        users: list[AdminUser] | None = None,
        sessions: list[AdminSession] | None = None,
        scalar_error: Exception | None = None,
        execute_error: Exception | None = None,
        flush_error: Exception | None = None,
        commit_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        self.users = users or []
        self.sessions = sessions or []
        self.scalar_error = scalar_error
        self.execute_error = execute_error
        self.flush_error = flush_error
        self.commit_error = commit_error
        self.delete_error = delete_error
        self.pending_sessions: list[AdminSession] = []
        self.scalar_calls = 0
        self.execute_calls = 0
        self.add_calls = 0
        self.flush_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0
        self.delete_calls = 0
        self._next_session_id = 1

    def scalar(self, statement: Any) -> AdminUser | None:
        self.scalar_calls += 1
        if self.scalar_error is not None:
            raise self.scalar_error
        username = _where_value(statement, "username")
        return next((user for user in self.users if user.username == username), None)

    def execute(self, statement: Any) -> FakeExecuteResult:
        self.execute_calls += 1
        if self.execute_error is not None:
            raise self.execute_error
        token_hash = _where_value(statement, "token_hash")
        if token_hash is None:
            return FakeExecuteResult(None)
        session = next((item for item in self.sessions if item.token_hash == token_hash), None)
        if session is None:
            return FakeExecuteResult(None)
        admin_user = session.admin_user or next(
            (user for user in self.users if user.id == session.admin_user_id),
            None,
        )
        if admin_user is None:
            return FakeExecuteResult(None)
        session.admin_user = admin_user
        return FakeExecuteResult((session, admin_user))

    def add(self, obj: Any) -> None:
        self.add_calls += 1
        if isinstance(obj, AdminSession):
            obj.admin_user = next((user for user in self.users if user.id == obj.admin_user_id), None)
            self.pending_sessions.append(obj)

    def flush(self) -> None:
        self.flush_calls += 1
        if self.flush_error is not None:
            raise self.flush_error
        for session in self.pending_sessions:
            session.id = self._next_session_id
            self._next_session_id += 1

    def commit(self) -> None:
        self.commit_calls += 1
        if self.commit_error is not None:
            raise self.commit_error
        self.sessions.extend(self.pending_sessions)
        self.pending_sessions.clear()

    def rollback(self) -> None:
        self.rollback_calls += 1
        self.pending_sessions.clear()

    def delete(self, obj: Any) -> None:
        self.delete_calls += 1
        if self.delete_error is not None:
            raise self.delete_error
        if isinstance(obj, AdminSession):
            if obj in self.sessions:
                self.sessions.remove(obj)
            if obj in self.pending_sessions:
                self.pending_sessions.remove(obj)


def _where_value(statement: Any, key: str) -> Any:
    params = statement.compile().params
    for param_key, value in params.items():
        if param_key.startswith(f"{key}_"):
            return value
    return None
