from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.exc import SQLAlchemyError

from app.api.admin_auth import CSRF_COOKIE_NAME, CSRF_HEADER_NAME
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models.admin import AdminSession, AdminUser
from app.models.candidate import ApplicationConsent, CandidateApplication
from app.services.candidate_contracts import (
    CANDIDATE_STATUS_ARCHIVED,
    CANDIDATE_STATUS_CLOSED,
    CANDIDATE_STATUS_CONTACTED,
    CANDIDATE_STATUS_IN_REVIEW,
    CANDIDATE_STATUS_NEW,
)
from app.services.candidate_photos import (
    NORMALIZED_MEDIA_TYPE,
    CandidatePhotoLimits,
    prepare_candidate_photo,
)
from app.services.private_photo_storage import PrivatePhotoStorage
from tests.test_admin_http_auth import VALID_PASSWORD, FakeAdminAuthSession, _admin_user


def test_create_app_registers_admin_candidate_routes() -> None:
    app = create_app(_settings())

    with TestClient(app):
        paths = set(app.openapi()["paths"])

    assert "/api/v1/admin/candidates" in paths
    assert "/api/v1/admin/candidates/{application_id}" in paths
    assert "/api/v1/admin/candidates/{application_id}/photo" in paths
    assert "/api/v1/admin/candidates/{application_id}/status" in paths
    assert "/api/v1/admin/candidates/register" not in paths
    assert not any(path.startswith("/api/v1/candidate-applications") for path in paths)


@pytest.mark.parametrize(
    "path, method",
    [
        ("/api/v1/admin/candidates", "get"),
        ("/api/v1/admin/candidates/1", "get"),
        ("/api/v1/admin/candidates/1/photo", "get"),
        ("/api/v1/admin/candidates/1/status", "patch"),
    ],
)
def test_admin_candidate_routes_require_auth(path: str, method: str) -> None:
    session = FakeAdminCandidateSession(users=[_admin_user()])

    with _client(session) as client:
        if method == "patch":
            response = client.request("PATCH", path, json={"status": CANDIDATE_STATUS_NEW})
        else:
            response = client.request("GET", path)

    assert response.status_code == 401


def test_admin_candidate_list_returns_summary_and_filters_status() -> None:
    session = FakeAdminCandidateSession(
        users=[_admin_user()],
        candidates=[
            _candidate(
                id=1,
                status=CANDIDATE_STATUS_NEW,
                created_at=datetime(2026, 8, 1, tzinfo=UTC),
                updated_at=datetime(2026, 8, 1, tzinfo=UTC),
            ),
            _candidate(
                id=2,
                status=CANDIDATE_STATUS_CONTACTED,
                created_at=datetime(2026, 8, 3, tzinfo=UTC),
                updated_at=datetime(2026, 8, 3, tzinfo=UTC),
            ),
            _candidate(
                id=3,
                status=CANDIDATE_STATUS_IN_REVIEW,
                created_at=datetime(2026, 8, 2, tzinfo=UTC),
                updated_at=datetime(2026, 8, 2, tzinfo=UTC),
                photo_storage_key="candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
            ),
        ],
    )

    with _client(session) as client:
        _login(client)
        response = client.get("/api/v1/admin/candidates?limit=1&offset=0&status=in_review")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.json() == {
        "items": [
            {
                "id": 3,
                "full_name": "Ada Lovelace",
                "city": "Saint Petersburg",
                "email": "ada@example.com",
                "phone": "+7 999 123-45-67",
                "status": CANDIDATE_STATUS_IN_REVIEW,
                "has_photo": True,
                "created_at": "2026-08-02T00:00:00Z",
                "updated_at": "2026-08-02T00:00:00Z",
            }
        ],
        "limit": 1,
        "offset": 0,
    }
    assert "education" not in response.text
    assert "photo_storage_key" not in response.text
    assert "last_error" not in response.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_admin_candidate_list_validation_and_db_failure_are_generic() -> None:
    session = FakeAdminCandidateSession(users=[_admin_user()])

    with _client(session) as client:
        _login(client)
        invalid = client.get("/api/v1/admin/candidates?status=invalid")
        session.candidate_execute_error = SQLAlchemyError("lookup")
        failure = client.get("/api/v1/admin/candidates")

    assert invalid.status_code == 422
    assert invalid.json() == {"detail": "Invalid candidate status"}
    assert failure.status_code == 503
    assert failure.json() == {"detail": "Candidate administration temporarily unavailable"}
    assert "lookup" not in failure.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 1


def test_admin_candidate_detail_returns_expected_fields() -> None:
    application = _candidate(
        id=10,
        status=CANDIDATE_STATUS_CONTACTED,
        created_at=datetime(2026, 8, 4, tzinfo=UTC),
        updated_at=datetime(2026, 8, 5, tzinfo=UTC),
        consents=_consents(),
        photo_storage_key="candidate-photos/00000000-0000-4000-8000-000000000000.jpg",
    )
    session = FakeAdminCandidateSession(users=[_admin_user()], candidates=[application])

    with _client(session) as client:
        _login(client)
        response = client.get("/api/v1/admin/candidates/10")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 10
    assert body["status"] == CANDIDATE_STATUS_CONTACTED
    assert body["has_photo"] is True
    assert body["consents"] == [
        {
            "consent_type": "personal_data_processing",
            "accepted_at": "2026-08-04T00:00:00Z",
            "document_version": "v1",
        },
        {
            "consent_type": "privacy_policy_acknowledgement",
            "accepted_at": "2026-08-04T00:00:00Z",
            "document_version": "v2",
        },
        {
            "consent_type": "saint_petersburg_acknowledgement",
            "accepted_at": "2026-08-04T00:00:00Z",
            "document_version": "v3",
        },
    ]
    assert "photo_storage_key" not in response.text
    assert "last_error" not in response.text
    assert "religion" not in response.text
    assert "ip_address" not in response.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_admin_candidate_detail_missing_and_db_failure_are_generic() -> None:
    session = FakeAdminCandidateSession(users=[_admin_user()])

    with _client(session) as client:
        _login(client)
        missing = client.get("/api/v1/admin/candidates/404")
        session.candidate_execute_error = SQLAlchemyError("lookup")
        failure = client.get("/api/v1/admin/candidates/10")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "Candidate application not found"}
    assert failure.status_code == 503
    assert failure.json() == {"detail": "Candidate administration temporarily unavailable"}
    assert "lookup" not in failure.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 1


def test_admin_candidate_photo_returns_private_jpeg_and_checks_integrity(tmp_path: Path) -> None:
    prepared = prepare_candidate_photo(_jpeg_bytes(), _photo_limits())
    storage = PrivatePhotoStorage(tmp_path)
    storage_key = storage.save(prepared)

    session = FakeAdminCandidateSession(
        users=[_admin_user()],
        candidates=[
            _candidate(
                id=20,
                status=CANDIDATE_STATUS_NEW,
                created_at=datetime(2026, 8, 6, tzinfo=UTC),
                updated_at=datetime(2026, 8, 6, tzinfo=UTC),
                photo_storage_key=storage_key,
                photo_media_type=NORMALIZED_MEDIA_TYPE,
                photo_size_bytes=len(prepared.normalized_bytes),
            ),
        ],
    )

    settings = _settings(private_media_root=tmp_path)
    with _client(session, settings) as client:
        _login(client)
        response = client.get("/api/v1/admin/candidates/20/photo")

    assert response.status_code == 200
    assert response.headers["content-type"] == NORMALIZED_MEDIA_TYPE
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.content == prepared.normalized_bytes
    assert storage_key not in response.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


@pytest.mark.parametrize(
    "candidate_kwargs, delete_file, expected_status, expected_detail",
    [
        (
            {"photo_storage_key": None, "photo_media_type": None, "photo_size_bytes": None},
            False,
            404,
            "Candidate application not found",
        ),
        (
            {"photo_media_type": "image/png", "photo_size_bytes": 1},
            False,
            503,
            "Candidate photo temporarily unavailable",
        ),
        (
            {"photo_media_type": NORMALIZED_MEDIA_TYPE, "photo_size_bytes": 9999},
            False,
            503,
            "Candidate photo temporarily unavailable",
        ),
        (
            {"photo_media_type": NORMALIZED_MEDIA_TYPE, "photo_size_bytes": None},
            True,
            503,
            "Candidate photo temporarily unavailable",
        ),
    ],
)
def test_admin_candidate_photo_missing_and_invalid_cases_are_generic(
    tmp_path: Path,
    candidate_kwargs: dict[str, Any],
    delete_file: bool,
    expected_status: int,
    expected_detail: str,
) -> None:
    prepared = prepare_candidate_photo(_jpeg_bytes(), _photo_limits())
    storage = PrivatePhotoStorage(tmp_path)
    storage_key = storage.save(prepared)
    if delete_file:
        storage.delete(storage_key)

    candidate = _candidate(
        id=30,
        status=CANDIDATE_STATUS_ARCHIVED,
        created_at=datetime(2026, 8, 7, tzinfo=UTC),
        updated_at=datetime(2026, 8, 7, tzinfo=UTC),
        photo_storage_key=storage_key,
        photo_media_type=NORMALIZED_MEDIA_TYPE,
        photo_size_bytes=len(prepared.normalized_bytes),
    )
    for key, value in candidate_kwargs.items():
        setattr(candidate, key, value)

    session = FakeAdminCandidateSession(users=[_admin_user()], candidates=[candidate])
    settings = _settings(private_media_root=tmp_path)

    with _client(session, settings) as client:
        _login(client)
        response = client.get("/api/v1/admin/candidates/30/photo")

    assert response.status_code == expected_status
    assert "candidate-photos" not in response.text
    assert "lookup" not in response.text
    assert response.json() == {"detail": expected_detail}
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_admin_candidate_photo_db_failure_is_generic(tmp_path: Path) -> None:
    session = FakeAdminCandidateSession(users=[_admin_user()])

    with _client(session, _settings(private_media_root=tmp_path)) as client:
        _login(client)
        session.candidate_execute_error = SQLAlchemyError("lookup")
        response = client.get("/api/v1/admin/candidates/20/photo")

    assert response.status_code == 503
    assert response.json() == {"detail": "Candidate administration temporarily unavailable"}
    assert "lookup" not in response.text
    assert session.commit_calls == 1
    assert session.rollback_calls == 1


@pytest.mark.parametrize(
    "status_value",
    [
        CANDIDATE_STATUS_NEW,
        CANDIDATE_STATUS_IN_REVIEW,
        CANDIDATE_STATUS_CONTACTED,
        CANDIDATE_STATUS_CLOSED,
        CANDIDATE_STATUS_ARCHIVED,
    ],
)
def test_admin_candidate_status_patch_updates_and_persists(status_value: str) -> None:
    candidate = _candidate(
        id=40,
        status=CANDIDATE_STATUS_NEW,
        created_at=datetime(2026, 8, 8, tzinfo=UTC),
        updated_at=datetime(2026, 8, 8, tzinfo=UTC),
    )
    session = FakeAdminCandidateSession(users=[_admin_user()], candidates=[candidate])

    with _client(session) as client:
        _login(client)
        response = client.patch(
            "/api/v1/admin/candidates/40/status",
            headers={CSRF_HEADER_NAME: client.cookies.get(CSRF_COOKIE_NAME)},
            json={"status": status_value},
        )

    assert response.status_code == 200
    assert response.json() == {"id": 40, "status": status_value}
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["pragma"] == "no-cache"
    assert candidate.status == status_value
    assert session.commit_calls == 2
    assert session.rollback_calls == 0


@pytest.mark.parametrize("status_value", ["invalid", "accepted", "", "NEW"])
def test_admin_candidate_status_patch_rejects_invalid_status(status_value: str) -> None:
    candidate = _candidate(
        id=41,
        status=CANDIDATE_STATUS_NEW,
        created_at=datetime(2026, 8, 8, tzinfo=UTC),
        updated_at=datetime(2026, 8, 8, tzinfo=UTC),
    )
    session = FakeAdminCandidateSession(users=[_admin_user()], candidates=[candidate])

    with _client(session) as client:
        _login(client)
        csrf = client.cookies.get(CSRF_COOKIE_NAME)
        response = client.patch(
            "/api/v1/admin/candidates/41/status",
            headers={CSRF_HEADER_NAME: csrf},
            json={"status": status_value},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid candidate status"}
    assert candidate.status == CANDIDATE_STATUS_NEW
    assert session.commit_calls == 1
    assert session.rollback_calls == 0


def test_admin_candidate_status_patch_requires_csrf_and_rolls_back_on_failure() -> None:
    candidate = _candidate(
        id=42,
        status=CANDIDATE_STATUS_CONTACTED,
        created_at=datetime(2026, 8, 8, tzinfo=UTC),
        updated_at=datetime(2026, 8, 8, tzinfo=UTC),
    )
    session = FakeAdminCandidateSession(users=[_admin_user()], candidates=[candidate])

    with _client(session) as client:
        _login(client)
        no_csrf = client.patch("/api/v1/admin/candidates/42/status", json={"status": CANDIDATE_STATUS_CLOSED})
        bad_csrf = client.patch(
            "/api/v1/admin/candidates/42/status",
            headers={CSRF_HEADER_NAME: "bad"},
            json={"status": CANDIDATE_STATUS_CLOSED},
        )
        csrf = client.cookies.get(CSRF_COOKIE_NAME)
        assert csrf is not None
        session.commit_error = SQLAlchemyError("commit")
        commit_failure = client.patch(
            "/api/v1/admin/candidates/42/status",
            headers={CSRF_HEADER_NAME: csrf},
            json={"status": CANDIDATE_STATUS_CLOSED},
        )

    assert no_csrf.status_code == 403
    assert bad_csrf.status_code == 403
    assert commit_failure.status_code == 503
    assert commit_failure.json() == {"detail": "Candidate administration temporarily unavailable"}
    assert candidate.status == CANDIDATE_STATUS_CONTACTED
    assert session.commit_calls == 2
    assert session.rollback_calls == 1


def _client(session: FakeAdminCandidateSession, settings: Any | None = None) -> TestClient:
    app = create_app(settings or _settings())
    app.dependency_overrides[get_db] = lambda: session
    return TestClient(app)


def _settings(*, private_media_root: Path = Path("var/private"), app_env: str = "test") -> Settings:
    return Settings(
        DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/astrea",
        APP_ENV=app_env,
        PRIVATE_MEDIA_ROOT=private_media_root,
    )


def _login(client: TestClient) -> None:
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "astrea.admin", "password": VALID_PASSWORD},
    )
    assert response.status_code == 200


def _candidate(
    *,
    id: int,
    status: str,
    created_at: datetime,
    updated_at: datetime,
    consents: list[ApplicationConsent] | None = None,
    photo_storage_key: str | None = None,
    photo_media_type: str | None = NORMALIZED_MEDIA_TYPE,
    photo_size_bytes: int | None = None,
) -> CandidateApplication:
    application = CandidateApplication(
        full_name="Ada Lovelace",
        date_of_birth=date(1815, 12, 10),
        city="Saint Petersburg",
        phone="+7 999 123-45-67",
        email="ada@example.com",
        education="Higher",
        occupation="Analyst",
        marital_status="single",
        other_organizations="",
        social_links="",
        motivation="Motivated",
        photo_storage_key=photo_storage_key,
        photo_media_type=photo_media_type,
        photo_size_bytes=photo_size_bytes,
        status=status,
    )
    application.id = id
    application.created_at = created_at
    application.updated_at = updated_at
    application.consents = consents or []
    return application


def _consents() -> list[ApplicationConsent]:
    accepted_at = datetime(2026, 8, 4, tzinfo=UTC)
    consent_one = ApplicationConsent(
        consent_type="personal_data_processing",
        accepted_at=accepted_at,
        document_version="v1",
    )
    consent_one.id = 1
    consent_two = ApplicationConsent(
        consent_type="privacy_policy_acknowledgement",
        accepted_at=accepted_at,
        document_version="v2",
    )
    consent_two.id = 2
    consent_three = ApplicationConsent(
        consent_type="saint_petersburg_acknowledgement",
        accepted_at=accepted_at,
        document_version="v3",
    )
    consent_three.id = 3
    return [consent_one, consent_two, consent_three]


def _jpeg_bytes() -> bytes:
    image = Image.new("RGB", (80, 60), (20, 60, 120))
    output = BytesIO()
    image.save(output, format="JPEG")
    return output.getvalue()


def _photo_limits() -> CandidatePhotoLimits:
    return CandidatePhotoLimits(
        max_bytes=10 * 1024 * 1024,
        max_pixels=20_000_000,
        max_edge=6000,
        output_max_edge=2048,
    )


@dataclass
class _CandidateResult:
    items: list[Any]
    scalar_value: Any | None = None

    def first(self) -> Any | None:
        if self.scalar_value is not None:
            return self.scalar_value
        return self.items[0] if self.items else None

    def scalar_one_or_none(self) -> Any | None:
        if self.scalar_value is not None:
            return self.scalar_value
        return self.items[0] if len(self.items) == 1 else None

    def scalars(self) -> _CandidateScalars:
        return _CandidateScalars(self.items)


@dataclass
class _CandidateScalars:
    items: list[Any]

    def all(self) -> list[Any]:
        return self.items


class FakeAdminCandidateSession(FakeAdminAuthSession):
    def __init__(
        self,
        *,
        users: list[AdminUser] | None = None,
        sessions: list[AdminSession] | None = None,
        candidates: list[CandidateApplication] | None = None,
        scalar_error: Exception | None = None,
        candidate_execute_error: Exception | None = None,
        flush_error: Exception | None = None,
        commit_error: Exception | None = None,
        delete_error: Exception | None = None,
    ) -> None:
        super().__init__(
            users=users,
            sessions=sessions,
            scalar_error=scalar_error,
            execute_error=None,
            flush_error=flush_error,
            commit_error=commit_error,
            delete_error=delete_error,
        )
        self.candidates = candidates or []
        self.candidate_execute_error = candidate_execute_error
        self._candidate_status_snapshots: dict[int, str] = {}

    def execute(self, statement: Any) -> Any:
        entity = _statement_entity(statement)
        if entity is CandidateApplication:
            self.execute_calls += 1
            if self.candidate_execute_error is not None:
                raise self.candidate_execute_error
            candidate_id = _where_value(statement, "id")
            status_value = _where_value(statement, "status")
            if candidate_id is not None:
                candidate = next((item for item in self.candidates if item.id == candidate_id), None)
                if candidate is None:
                    return _CandidateResult([])
                self._snapshot_candidate(candidate)
                return _CandidateResult([candidate], candidate)
            items = [item for item in self.candidates if status_value is None or item.status == status_value]
            items.sort(
                key=lambda item: (
                    item.created_at or datetime.min.replace(tzinfo=UTC),
                    item.id,
                ),
                reverse=True,
            )
            limit = _limit_offset_value(statement, "_limit_clause", len(items))
            offset = _limit_offset_value(statement, "_offset_clause", 0)
            sliced = items[offset : offset + limit]
            for item in sliced:
                self._snapshot_candidate(item)
            return _CandidateResult(sliced)
        return super().execute(statement)

    def commit(self) -> None:
        super().commit()
        self._candidate_status_snapshots.clear()

    def rollback(self) -> None:
        super().rollback()
        for candidate_id, original_status in self._candidate_status_snapshots.items():
            candidate = next((item for item in self.candidates if item.id == candidate_id), None)
            if candidate is not None:
                candidate.status = original_status
        self._candidate_status_snapshots.clear()

    def _snapshot_candidate(self, candidate: CandidateApplication) -> None:
        self._candidate_status_snapshots.setdefault(candidate.id, candidate.status)


def _statement_entity(statement: Any) -> Any:
    descriptions = getattr(statement, "column_descriptions", [])
    if not descriptions:
        return None
    return descriptions[0].get("entity")


def _where_value(statement: Any, key: str) -> Any:
    params = statement.compile().params
    for param_key, value in params.items():
        if param_key.startswith(f"{key}_"):
            return value
    return None


def _limit_offset_value(statement: Any, attr: str, default: int) -> int:
    clause = getattr(statement, attr)
    if clause is None:
        return default
    return int(clause.value)
