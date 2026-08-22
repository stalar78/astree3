from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.api.candidate_applications import CandidateRateLimiter
from app.core.config import Settings
from app.db.session import get_db
from app.main import create_app
from app.models.candidate import CandidateApplication


def test_feature_gate_defaults_to_disabled() -> None:
    assert _settings().candidate_intake_enabled is False


def test_disabled_app_omits_candidate_post_route_and_openapi() -> None:
    app = create_app(_settings())

    assert "/api/v1/candidate-applications" not in _paths(app)
    assert "/api/v1/candidate-applications" not in app.openapi()["paths"]


def test_enabled_settings_require_all_legal_versions() -> None:
    with pytest.raises(TypeError):
        _settings(candidate_intake_enabled=True)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "candidate_personal_data_consent_version": " ",
            "candidate_privacy_policy_version": "v2",
            "candidate_saint_petersburg_acknowledgement_version": "v3",
        },
        {
            "candidate_personal_data_consent_version": "v1",
            "candidate_privacy_policy_version": "\t",
            "candidate_saint_petersburg_acknowledgement_version": "v3",
        },
        {
            "candidate_personal_data_consent_version": "v1",
            "candidate_privacy_policy_version": "v2",
            "candidate_saint_petersburg_acknowledgement_version": "v" * 81,
        },
    ],
)
def test_enabled_settings_reject_blank_or_too_long_versions(kwargs: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        _settings(candidate_intake_enabled=True, **kwargs)


def test_enabled_settings_accept_valid_versions() -> None:
    settings = _settings(
        candidate_intake_enabled=True,
        candidate_personal_data_consent_version=" pd-v1 ",
        candidate_privacy_policy_version=" pp-v2 ",
        candidate_saint_petersburg_acknowledgement_version=" sp-v3 ",
    )

    assert settings.candidate_consent_versions.personal_data_processing == "pd-v1"
    assert settings.candidate_consent_versions.privacy_policy_acknowledgement == "pp-v2"
    assert settings.candidate_consent_versions.saint_petersburg_acknowledgement == "sp-v3"


def test_successful_multipart_submission_reaches_internal_intake_and_private_storage(
    tmp_path: Path,
) -> None:
    settings = _enabled_settings(tmp_path)
    app = create_app(settings)
    session = RecordingSession()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    response = client.post(
        "/api/v1/candidate-applications",
        data={
            "full_name": "  Test Candidate  ",
            "date_of_birth": "1990-05-17",
            "city": "  Saint Petersburg ",
            "phone": " +7 (900) 111-22-33 ",
            "email": " test@example.com ",
            "education": "  Higher education ",
            "occupation": " Engineer ",
            "marital_status": " Single ",
            "motivation": "  I want to join. ",
            "personal_data_processing": "true",
            "privacy_policy_acknowledgement": "true",
            "saint_petersburg_acknowledgement": "true",
            "candidate_personal_data_consent_version": "client-controlled",
            "candidate_privacy_policy_version": "client-controlled",
            "candidate_saint_petersburg_acknowledgement_version": "client-controlled",
            "website": "",
            "other_organizations": "  ",
            "social_links": "  ",
        },
        files={"photo": ("evil.exe", _image_bytes("PNG"), "application/octet-stream")},
    )

    assert response.status_code == 201
    assert response.json() == {"accepted": True}
    assert len(session.added) == 1
    application = session.added[0]
    assert application.full_name == "Test Candidate"
    assert application.city == "Saint Petersburg"
    assert application.phone == "+7 (900) 111-22-33"
    assert application.email == "test@example.com"
    assert application.photo_storage_key.startswith("candidate-photos/")
    assert application.photo_storage_key.endswith(".jpg")
    assert len(application.consents) == 3
    assert all(consent.accepted_at.tzinfo is not None for consent in application.consents)
    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    stored_photo = settings.private_media_root / application.photo_storage_key
    assert stored_photo.exists()
    with Image.open(stored_photo) as image:
        assert image.format == "JPEG"
        assert image.mode == "RGB"


@pytest.mark.parametrize(
    "field, payload",
    [
        ("full_name", ""),
        ("city", " "),
        ("education", " "),
        ("occupation", " "),
        ("marital_status", " "),
        ("motivation", " "),
    ],
)
def test_blank_required_fields_rejected(field: str, payload: str, tmp_path: Path) -> None:
    response = _post_candidate(tmp_path, {field: payload})
    assert response.status_code in {400, 422}


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    response = _post_candidate(tmp_path, {}, remove_fields={"city"})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "missing_field",
    [
        "personal_data_processing",
        "privacy_policy_acknowledgement",
        "saint_petersburg_acknowledgement",
    ],
)
def test_missing_each_consent_rejected(missing_field: str, tmp_path: Path) -> None:
    response = _post_candidate(tmp_path, {}, remove_fields={missing_field})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "consent_field",
    [
        "personal_data_processing",
        "privacy_policy_acknowledgement",
        "saint_petersburg_acknowledgement",
    ],
)
def test_false_each_consent_rejected(consent_field: str, tmp_path: Path) -> None:
    response = _post_candidate(tmp_path, {consent_field: "false"})

    assert response.status_code == 400


def test_validation_and_safety_rejections(tmp_path: Path) -> None:
    base = _base_submission()

    assert _post_candidate(tmp_path, base | {"email": "bad"}).status_code == 400
    assert _post_candidate(tmp_path, base | {"phone": "abc"}).status_code == 400
    assert _post_candidate(tmp_path, base | {"website": "evil"}).status_code == 400
    assert _post_candidate(tmp_path, base, files={"photo": ("a.txt", b"", "text/plain")}).status_code == 400
    assert _post_candidate(tmp_path, base, files={"photo": ("a.txt", b"not-image", "text/plain")}).status_code == 400
    assert _post_candidate(
        tmp_path,
        base,
        files={"photo": ("a.txt", _oversized_png(), "image/png")},
        settings_overrides={"candidate_photo_max_bytes": 10},
    ).status_code == 400
    assert _post_candidate(tmp_path, base, files={"photo": ("a.txt", _animated_webp_bytes(), "image/webp")}).status_code == 400
    assert _post_candidate(tmp_path, base, files={"photo": ("a.txt", _image_bytes("GIF"), "image/gif")}).status_code == 400


def test_rate_limiter_allows_then_blocks_and_prunes() -> None:
    current = [0.0]
    limiter = CandidateRateLimiter(2, 10, monotonic=lambda: current[0])

    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("127.0.0.1") is False

    current[0] = 11.0
    assert limiter.allow("127.0.0.1") is True
    assert limiter.allow("10.0.0.1") is True


def test_rate_limiter_ignores_forwarded_for_header_and_does_not_persist_identity(
    tmp_path: Path,
) -> None:
    settings = _enabled_settings(tmp_path)
    app = create_app(settings)
    session = RecordingSession()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    data = _base_submission()
    files = {"photo": ("photo.png", _image_bytes("PNG"), "image/png")}

    assert (
        client.post(
            "/api/v1/candidate-applications",
            data=data,
            files=files,
            headers={"X-Forwarded-For": "1.1.1.1"},
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/candidate-applications",
            data=data,
            files=files,
            headers={"X-Forwarded-For": "8.8.8.8"},
        ).status_code
        == 429
    )
    assert session.added and session.commit_calls == 1


def test_route_failure_mapping_is_generic(tmp_path: Path) -> None:
    settings = _enabled_settings(tmp_path)
    app = create_app(settings)
    session = RecordingSession(commit_error=True)
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)

    response = client.post(
        "/api/v1/candidate-applications",
        data=_base_submission(),
        files={"photo": ("photo.png", _image_bytes("PNG"), "image/png")},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Candidate application temporarily unavailable"}
    assert "application_id" not in response.text


def test_no_public_candidate_get_or_photo_routes(tmp_path: Path) -> None:
    app = create_app(_enabled_settings(tmp_path))
    paths = _paths(app)

    assert "/api/v1/candidate-applications/{id}" not in paths
    assert not any(path.endswith("/photo") for path in paths)
    assert not any("StaticFiles" in repr(route) for route in app.routes)


def _post_candidate(
    tmp_path: Path,
    data_overrides: dict[str, str],
    *,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    remove_fields: set[str] | None = None,
    settings_overrides: dict[str, object] | None = None,
) -> Any:
    settings = _enabled_settings(tmp_path, **(settings_overrides or {}))
    app = create_app(settings)
    session = RecordingSession()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    data = _base_submission() | data_overrides
    for field in remove_fields or set():
        data.pop(field, None)
    upload_files = files or {"photo": ("photo.png", _image_bytes("PNG"), "image/png")}
    return client.post("/api/v1/candidate-applications", data=data, files=upload_files)


def _base_submission() -> dict[str, str]:
    return {
        "full_name": "Test Candidate",
        "date_of_birth": "1990-05-17",
        "city": "Saint Petersburg",
        "phone": "+7 (900) 111-22-33",
        "email": "test@example.com",
        "education": "Higher education",
        "occupation": "Engineer",
        "marital_status": "Single",
        "motivation": "Join",
        "personal_data_processing": "true",
        "privacy_policy_acknowledgement": "true",
        "saint_petersburg_acknowledgement": "true",
        "website": "",
    }


def _enabled_settings(tmp_path: Path, **overrides: object) -> Settings:
    return _settings(
        private_media_root=tmp_path / "private",
        candidate_intake_enabled=True,
        candidate_personal_data_consent_version="pd-v1",
        candidate_privacy_policy_version="pp-v2",
        candidate_saint_petersburg_acknowledgement_version="sp-v3",
        candidate_rate_limit_requests=1,
        candidate_rate_limit_window_seconds=900,
        **overrides,
    )


def _settings(**kwargs: object) -> Settings:
    mapping = {
        "APP_ENV": "test",
        "DATABASE_URL": "postgresql://user:pass@localhost:5432/astrea",
        "PRIVATE_MEDIA_ROOT": Path("var/private"),
        "CANDIDATE_PHOTO_MAX_BYTES": 10 * 1024 * 1024,
        "CANDIDATE_PHOTO_MAX_PIXELS": 20_000_000,
        "CANDIDATE_PHOTO_MAX_EDGE": 6000,
        "CANDIDATE_PHOTO_OUTPUT_MAX_EDGE": 2048,
        "CANDIDATE_INTAKE_ENABLED": False,
        "CANDIDATE_PERSONAL_DATA_CONSENT_VERSION": None,
        "CANDIDATE_PRIVACY_POLICY_VERSION": None,
        "CANDIDATE_SAINT_PETERSBURG_ACKNOWLEDGEMENT_VERSION": None,
        "CANDIDATE_RATE_LIMIT_REQUESTS": 5,
        "CANDIDATE_RATE_LIMIT_WINDOW_SECONDS": 900,
    }
    alias_map = {
        "project_name": "project_name",
        "api_v1_prefix": "api_v1_prefix",
        "app_env": "APP_ENV",
        "database_url": "DATABASE_URL",
        "private_media_root": "PRIVATE_MEDIA_ROOT",
        "candidate_photo_max_bytes": "CANDIDATE_PHOTO_MAX_BYTES",
        "candidate_photo_max_pixels": "CANDIDATE_PHOTO_MAX_PIXELS",
        "candidate_photo_max_edge": "CANDIDATE_PHOTO_MAX_EDGE",
        "candidate_photo_output_max_edge": "CANDIDATE_PHOTO_OUTPUT_MAX_EDGE",
        "candidate_intake_enabled": "CANDIDATE_INTAKE_ENABLED",
        "candidate_personal_data_consent_version": "CANDIDATE_PERSONAL_DATA_CONSENT_VERSION",
        "candidate_privacy_policy_version": "CANDIDATE_PRIVACY_POLICY_VERSION",
        "candidate_saint_petersburg_acknowledgement_version": "CANDIDATE_SAINT_PETERSBURG_ACKNOWLEDGEMENT_VERSION",
        "candidate_rate_limit_requests": "CANDIDATE_RATE_LIMIT_REQUESTS",
        "candidate_rate_limit_window_seconds": "CANDIDATE_RATE_LIMIT_WINDOW_SECONDS",
    }
    for key, value in kwargs.items():
        mapping[alias_map.get(key, key)] = value
    return Settings(**mapping)


def _paths(app: Any) -> set[str]:
    return {route.path for route in app.routes if hasattr(route, "path")}


def _image_bytes(image_format: str) -> bytes:
    image = Image.new("RGB", (32, 32), (100, 120, 140))
    output = BytesIO()
    image.save(output, format=image_format)
    return output.getvalue()


def _oversized_png() -> bytes:
    return _image_bytes("PNG") * 200000


def _animated_webp_bytes() -> bytes:
    first = Image.new("RGB", (16, 16), (255, 0, 0))
    second = Image.new("RGB", (16, 16), (0, 255, 0))
    output = BytesIO()
    first.save(output, format="WEBP", save_all=True, append_images=[second], duration=100, loop=0)
    return output.getvalue()


class RecordingSession:
    def __init__(self, *, commit_error: bool = False) -> None:
        self.added: list[CandidateApplication] = []
        self.commit_calls = 0
        self.rollback_calls = 0
        self._next_id = 1
        self.commit_error = commit_error

    def add(self, obj: CandidateApplication) -> None:
        self.added.append(obj)

    def flush(self) -> None:
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
        self.commit_calls += 1
        if self.commit_error:
            raise SQLAlchemyError("synthetic commit failure")

    def rollback(self) -> None:
        self.rollback_calls += 1
