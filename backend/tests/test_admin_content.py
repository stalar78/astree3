from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.api.admin_auth import (
    CSRF_COOKIE_NAME,
    CSRF_HEADER_NAME,
    AuthenticatedAdmin,
    get_authenticated_admin,
    require_admin_csrf,
)
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.news import NewsPost
from app.models.page import Page
from app.models.video import Video


def test_create_app_registers_admin_content_routes() -> None:
    app = create_app(_settings())

    with TestClient(app):
        paths = set(app.openapi()["paths"])

    assert "/api/v1/admin/content/news" in paths
    assert "/api/v1/admin/content/news/{news_id}" in paths
    assert "/api/v1/admin/content/videos" in paths
    assert "/api/v1/admin/content/videos/{video_id}" in paths
    assert "/api/v1/admin/content/pages" in paths
    assert "/api/v1/admin/content/pages/{key}" in paths
    assert "post" not in app.openapi()["paths"]["/api/v1/admin/content/pages"]
    assert "delete" not in app.openapi()["paths"]["/api/v1/admin/content/pages/{key}"]


@pytest.mark.parametrize(
    "path, method",
    [
        ("/api/v1/admin/content/news", "GET"),
        ("/api/v1/admin/content/news", "POST"),
        ("/api/v1/admin/content/news/1", "GET"),
        ("/api/v1/admin/content/news/1", "PATCH"),
        ("/api/v1/admin/content/news/1", "DELETE"),
        ("/api/v1/admin/content/videos", "GET"),
        ("/api/v1/admin/content/pages", "GET"),
        ("/api/v1/admin/content/pages/about", "PATCH"),
    ],
)
def test_admin_content_routes_require_auth(path: str, method: str, tmp_path: Path) -> None:
    client, _ = _client(tmp_path)

    response = client.request(method, path, json=_payload_for(path))

    assert response.status_code == 401


def test_admin_content_writes_require_csrf(tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)

    no_csrf = client.post("/api/v1/admin/content/news", json=_news_payload())
    bad_csrf = client.post(
        "/api/v1/admin/content/news",
        headers={CSRF_HEADER_NAME: "bad"},
        json=_news_payload(slug="second"),
    )

    assert no_csrf.status_code == 403
    assert bad_csrf.status_code == 403
    assert no_csrf.headers["cache-control"] == "private, no-store"


def test_news_crud_public_interop_and_publication_semantics(tmp_path: Path) -> None:
    client, session_factory = _client(tmp_path, authenticated=True)
    csrf = _csrf(client)

    draft = client.post(
        "/api/v1/admin/content/news",
        headers={CSRF_HEADER_NAME: csrf},
        json=_news_payload(slug="draft", is_published=False),
    )
    live = client.post(
        "/api/v1/admin/content/news",
        headers={CSRF_HEADER_NAME: csrf},
        json=_news_payload(slug="live", title="Live", is_published=True),
    )

    assert draft.status_code == 201
    assert draft.json()["published_at"] is None
    assert live.status_code == 201
    first_published_at = live.json()["published_at"]
    assert first_published_at is not None
    assert client.get("/api/v1/news/draft").status_code == 404
    assert client.get("/api/v1/news/live").status_code == 200

    listing = client.get("/api/v1/admin/content/news?published=false")
    assert listing.status_code == 200
    assert [item["slug"] for item in listing.json()["items"]] == ["draft"]
    assert "body" not in listing.text
    assert listing.headers["cache-control"] == "private, no-store"

    detail = client.get(f"/api/v1/admin/content/news/{live.json()['id']}")
    assert detail.status_code == 200
    assert detail.json()["body"] == "Body"

    unpublished = client.patch(
        f"/api/v1/admin/content/news/{live.json()['id']}",
        headers={CSRF_HEADER_NAME: csrf},
        json={"is_published": False},
    )
    assert unpublished.status_code == 200
    assert _parse_timestamp(unpublished.json()["published_at"]) == _parse_timestamp(first_published_at)
    assert client.get("/api/v1/news/live").status_code == 404

    republished = client.patch(
        f"/api/v1/admin/content/news/{live.json()['id']}",
        headers={CSRF_HEADER_NAME: csrf},
        json={"is_published": True, "title": "Republished"},
    )
    assert republished.status_code == 200
    assert _parse_timestamp(republished.json()["published_at"]) == _parse_timestamp(first_published_at)

    deleted = client.delete(f"/api/v1/admin/content/news/{draft.json()['id']}", headers={CSRF_HEADER_NAME: csrf})
    assert deleted.status_code == 204
    assert deleted.headers["cache-control"] == "private, no-store"

    with session_factory() as session:
        assert session.query(NewsPost).filter_by(slug="draft").one_or_none() is None


def test_duplicate_news_slug_returns_409(tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)
    csrf = _csrf(client)
    assert client.post("/api/v1/admin/content/news", headers={CSRF_HEADER_NAME: csrf}, json=_news_payload()).status_code == 201

    response = client.post("/api/v1/admin/content/news", headers={CSRF_HEADER_NAME: csrf}, json=_news_payload())

    assert response.status_code == 409
    assert response.json() == {"detail": "News slug already exists"}


@pytest.mark.parametrize("image_url", ["https://example.com/image.jpg", "/media/news/image.webp", None])
def test_news_image_url_accepts_safe_values(image_url: str | None, tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)
    payload = _news_payload(image_url=image_url)

    response = client.post("/api/v1/admin/content/news", headers={CSRF_HEADER_NAME: _csrf(client)}, json=payload)

    assert response.status_code == 201
    assert response.json()["image_url"] == image_url


@pytest.mark.parametrize(
    "image_url",
    [
        "javascript:alert(1)",
        "data:image/png;base64,AA",
        "file:///tmp/a.png",
        "ftp://example.com/a.png",
        "//example.com/a.png",
        "https://user:pass@example.com/a.png",
        "https://example.com\\evil",
    ],
)
def test_news_image_url_rejects_unsafe_values(image_url: str, tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)

    response = client.post(
        "/api/v1/admin/content/news",
        headers={CSRF_HEADER_NAME: _csrf(client)},
        json=_news_payload(image_url=image_url),
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid admin content request"}


def test_video_crud_strict_rutube_and_public_interop(tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)
    csrf = _csrf(client)
    video_url = "https://rutube.ru/video/0123456789abcdef0123456789abcdef/"

    created = client.post(
        "/api/v1/admin/content/videos",
        headers={CSRF_HEADER_NAME: csrf},
        json={
            "title": "Video",
            "description": "Description",
            "source_url": video_url,
            "is_published": False,
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["provider"] == "rutube"
    assert body["embed_url"] == "https://rutube.ru/play/embed/0123456789abcdef0123456789abcdef/"
    assert body["published_at"] is None
    assert client.get(f"/api/v1/videos/{body['id']}").status_code == 404

    published = client.patch(
        f"/api/v1/admin/content/videos/{body['id']}",
        headers={CSRF_HEADER_NAME: csrf},
        json={"is_published": True},
    )
    assert published.status_code == 200
    assert published.json()["published_at"] is not None
    assert client.get(f"/api/v1/videos/{body['id']}").status_code == 200

    listing = client.get("/api/v1/admin/content/videos?published=true")
    assert listing.status_code == 200
    assert [item["id"] for item in listing.json()["items"]] == [body["id"]]

    invalid = client.post(
        "/api/v1/admin/content/videos",
        headers={CSRF_HEADER_NAME: csrf},
        json={"title": "Bad", "description": "No", "source_url": "https://youtube.com/watch?v=x"},
    )
    forbidden = client.post(
        "/api/v1/admin/content/videos",
        headers={CSRF_HEADER_NAME: csrf},
        json={
            "title": "Bad",
            "description": "No",
            "source_url": video_url,
            "provider": "rutube",
        },
    )
    assert invalid.status_code == 422
    assert forbidden.status_code == 422

    deleted = client.delete(f"/api/v1/admin/content/videos/{body['id']}", headers={CSRF_HEADER_NAME: csrf})
    assert deleted.status_code == 204


def test_page_admin_update_existing_only_and_public_interop(tmp_path: Path) -> None:
    client, _ = _client(
        tmp_path,
        pages=[
            _page("zeta", is_published=True, updated_at=datetime(2026, 8, 1, tzinfo=UTC)),
            _page("about", is_published=False, updated_at=datetime(2026, 8, 22, tzinfo=UTC)),
        ],
        authenticated=True,
    )
    csrf = _csrf(client)

    assert client.get("/api/v1/pages/about").status_code == 404
    listing = client.get("/api/v1/admin/content/pages")
    assert listing.status_code == 200
    assert [item["key"] for item in listing.json()["items"]] == ["about", "zeta"]
    assert all("content" not in item for item in listing.json()["items"])
    assert "limit" not in listing.json()
    assert "offset" not in listing.json()
    assert "limit" not in {param["name"] for param in client.get("/openapi.json").json()["paths"]["/api/v1/admin/content/pages"]["get"].get("parameters", [])}
    assert "offset" not in {param["name"] for param in client.get("/openapi.json").json()["paths"]["/api/v1/admin/content/pages"]["get"].get("parameters", [])}

    updated = client.patch(
        "/api/v1/admin/content/pages/about",
        headers={CSRF_HEADER_NAME: csrf},
        json={"title": "About", "content": "Published content", "is_published": True},
    )
    assert updated.status_code == 200
    assert updated.json()["key"] == "about"
    assert client.get("/api/v1/pages/about").status_code == 200
    assert client.post("/api/v1/admin/content/pages", headers={CSRF_HEADER_NAME: csrf}, json={}).status_code == 405
    assert client.delete("/api/v1/admin/content/pages/about", headers={CSRF_HEADER_NAME: csrf}).status_code == 405
    assert client.patch(
        "/api/v1/admin/content/pages/missing",
        headers={CSRF_HEADER_NAME: csrf},
        json={"title": "Missing"},
    ).status_code == 404

    key_in_payload = client.patch(
        "/api/v1/admin/content/pages/about",
        headers={CSRF_HEADER_NAME: csrf},
        json={"key": "renamed"},
    )
    assert key_in_payload.status_code == 422


@pytest.mark.parametrize(
    "method, path, payload",
    [
        (
            "POST",
            "/api/v1/admin/content/news",
            {
                "slug": "csrf-news",
                "title": "Title",
                "excerpt": "Excerpt",
                "body": "Body",
            },
        ),
        ("PATCH", "/api/v1/admin/content/news/1", {"title": "Changed"}),
        ("DELETE", "/api/v1/admin/content/news/1", None),
        (
            "POST",
            "/api/v1/admin/content/videos",
            {
                "title": "Video",
                "description": "Description",
                "source_url": "https://rutube.ru/video/0123456789abcdef0123456789abcdef/",
            },
        ),
        ("PATCH", "/api/v1/admin/content/videos/1", {"title": "Changed"}),
        ("DELETE", "/api/v1/admin/content/videos/1", None),
        ("PATCH", "/api/v1/admin/content/pages/about", {"title": "Changed"}),
    ],
)
def test_all_admin_write_families_require_csrf(
    method: str,
    path: str,
    payload: dict[str, Any] | None,
    tmp_path: Path,
) -> None:
    client, _ = _client(tmp_path, pages=[_page("about")], authenticated=True)

    response = client.request(method, path, json=payload)

    assert response.status_code == 403


def test_post_commit_mutations_do_not_execute_sql_after_commit(tmp_path: Path) -> None:
    client, _ = _client(tmp_path, authenticated=True)
    csrf = _csrf(client)
    FailingSession.forbid_sql_after_commit = True

    created = client.post(
        "/api/v1/admin/content/news",
        headers={CSRF_HEADER_NAME: csrf},
        json=_news_payload(slug="no-refresh"),
    )
    updated = client.patch(
        "/api/v1/admin/content/news/1",
        headers={CSRF_HEADER_NAME: csrf},
        json={"title": "Updated"},
    )

    assert created.status_code == 201
    assert updated.status_code == 200
    FailingSession.forbid_sql_after_commit = False


@pytest.mark.parametrize(
    "method, path, payload, setup",
    [
        (
            "post",
            "/api/v1/admin/content/news",
            {
                "slug": "refresh-fail",
                "title": "Title",
                "excerpt": "Excerpt",
                "body": "Body",
            },
            None,
        ),
        (
            "patch",
            "/api/v1/admin/content/news/1",
            {"title": "Still original"},
            lambda client, csrf: client.post(
                "/api/v1/admin/content/news",
                headers={CSRF_HEADER_NAME: csrf},
                json=_news_payload(slug="original"),
            ),
        ),
    ],
)
def test_pre_commit_refresh_failure_rolls_back(
    method: str,
    path: str,
    payload: dict[str, Any],
    setup,
    tmp_path: Path,
) -> None:
    client, session_factory = _client(tmp_path, authenticated=True)
    csrf = _csrf(client)
    if setup is not None:
        setup(client, csrf)
    FailingSession.fail_refresh = True

    response = client.request(method.upper(), path, headers={CSRF_HEADER_NAME: csrf}, json=payload)

    FailingSession.fail_refresh = False
    assert response.status_code == 503
    assert response.json() == {"detail": "Content administration temporarily unavailable"}
    with session_factory() as session:
        if method == "post":
            assert session.query(NewsPost).filter_by(slug="refresh-fail").one_or_none() is None
        else:
            assert session.query(NewsPost).filter_by(slug="original").one().title == "Title"


def test_admin_content_validation_privacy_and_strict_booleans(tmp_path: Path) -> None:
    client, _ = _client(tmp_path, pages=[_page("about")], authenticated=True)
    csrf = _csrf(client)

    cases = [
        (
            "post",
            "/api/v1/admin/content/news",
            {
                "slug": "privacy",
                "title": "Title",
                "excerpt": "Excerpt",
                "body": "SECRET-NEWS-BODY",
                "is_published": "true",
            },
        ),
        (
            "patch",
            "/api/v1/admin/content/pages/about",
            {"content": "SECRET-PAGE-CONTENT", "is_published": "false"},
        ),
        (
            "post",
            "/api/v1/admin/content/videos",
            {
                "title": "Title",
                "description": "SECRET-VIDEO-DESCRIPTION",
                "source_url": "https://rutube.ru/video/0123456789abcdef0123456789abcdef/",
                "published_at": "2026-08-22T00:00:00Z",
            },
        ),
    ]

    for method, path, payload in cases:
        response = client.request(method.upper(), path, headers={CSRF_HEADER_NAME: csrf}, json=payload)
        assert response.status_code == 422
        assert response.json() == {"detail": "Invalid admin content request"}
        assert "SECRET-" not in response.text
        assert "input" not in response.text
        assert "published_at" not in response.text


def test_admin_content_read_and_write_db_failures_are_generic(tmp_path: Path) -> None:
    client, session_factory = _client(tmp_path, pages=[_page("about")], authenticated=True)
    csrf = _csrf(client)
    session_factory.class_.fail_execute = True
    read = client.get("/api/v1/admin/content/pages")
    session_factory.class_.fail_execute = False
    session_factory.class_.fail_commit = True
    write = client.patch(
        "/api/v1/admin/content/pages/about",
        headers={CSRF_HEADER_NAME: csrf},
        json={"title": "Changed"},
    )

    assert read.status_code == 503
    assert write.status_code == 503
    assert read.json() == {"detail": "Content administration temporarily unavailable"}
    assert write.json() == {"detail": "Content administration temporarily unavailable"}
    assert "lookup" not in read.text
    assert "commit" not in write.text


def test_no_new_tables_were_added() -> None:
    assert set(Base.metadata.tables) == {
        "pages",
        "news_posts",
        "videos",
        "candidate_applications",
        "application_consents",
        "email_outbox",
        "admin_users",
        "admin_sessions",
    }
    assert Path("alembic/versions/20260823_0005_email_outbox_delivery_state.py").exists()


def _client(
    tmp_path: Path,
    *,
    pages: list[Page] | None = None,
    authenticated: bool = False,
) -> tuple[TestClient, Any]:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(
        engine,
        tables=[
            Page.__table__,
            NewsPost.__table__,
            Video.__table__,
        ],
    )
    session_factory = sessionmaker(bind=engine, class_=FailingSession, expire_on_commit=False)
    session_factory.fail_execute = False
    session_factory.fail_commit = False
    with session_factory() as session:
        for page in pages or []:
            session.add(page)
        session.commit()

    app = create_app(_settings())
    app.dependency_overrides[get_db] = lambda: session_factory()
    if authenticated:
        app.dependency_overrides[get_db] = lambda: session_factory()
        app.dependency_overrides[get_authenticated_admin] = _fake_get_authenticated_admin
        app.dependency_overrides[require_admin_csrf] = _fake_require_admin_csrf
    return TestClient(app), session_factory


class FailingSession(Session):
    fail_execute = False
    fail_commit = False
    fail_refresh = False
    forbid_sql_after_commit = False

    def execute(self, *args: Any, **kwargs: Any) -> Any:
        if self.fail_execute or (self.forbid_sql_after_commit and self._commit_succeeded):
            raise SQLAlchemyError("lookup")
        return super().execute(*args, **kwargs)

    def commit(self) -> None:
        if self.fail_commit:
            raise SQLAlchemyError("commit")
        super().commit()
        self._commit_succeeded = True

    def refresh(self, instance: Any, *args: Any, **kwargs: Any) -> None:
        if self.fail_refresh:
            raise SQLAlchemyError("refresh")
        return super().refresh(instance, *args, **kwargs)

    _commit_succeeded = False


def _settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+psycopg://user:pass@localhost:5432/astrea",
        APP_ENV="test",
    )


async def _fake_get_authenticated_admin() -> AuthenticatedAdmin:
    return _fake_admin()


async def _fake_require_admin_csrf(request: Request) -> AuthenticatedAdmin:
    header = request.headers.get(CSRF_HEADER_NAME)
    cookie = request.cookies.get(CSRF_COOKIE_NAME)
    if header != _csrf_token() or cookie != _csrf_token():
        raise HTTPException(status_code=403, detail="Invalid admin CSRF token")
    return _fake_admin()


def _csrf(client: TestClient) -> str:
    client.cookies.set(CSRF_COOKIE_NAME, _csrf_token(), path="/")
    return _csrf_token()


def _csrf_token() -> str:
    return "astrea-admin-csrf-token"


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z"))


def _fake_admin() -> AuthenticatedAdmin:
    return AuthenticatedAdmin(
        user=SimpleNamespace(username="astrea.admin"),
        session=SimpleNamespace(),
    )


def _news_payload(
    *,
    slug: str = "first-news",
    title: str = "Title",
    image_url: str | None = None,
    is_published: bool = False,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "excerpt": "Excerpt",
        "body": "Body",
        "image_url": image_url,
        "is_published": is_published,
    }


def _payload_for(path: str) -> dict[str, Any]:
    if "/videos" in path:
        return {
            "title": "Video",
            "description": "Description",
            "source_url": "https://rutube.ru/video/0123456789abcdef0123456789abcdef/",
        }
    if "/pages" in path:
        return {"title": "Page", "content": "Content"}
    return _news_payload()


def _page(
    key: str,
    *,
    is_published: bool = True,
    updated_at: datetime | None = None,
) -> Page:
    page = Page(key=key, title="Title", content="Content", is_published=is_published)
    page.created_at = datetime(2026, 8, 22, tzinfo=UTC)
    page.updated_at = updated_at or datetime(2026, 8, 22, tzinfo=UTC)
    return page
