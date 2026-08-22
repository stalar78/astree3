from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import create_app
from tests.fakes import FakeSession, make_news, make_page, make_video


def test_page_endpoint_returns_published_page() -> None:
    client = _client(FakeSession(pages=[make_page("about", True)]))

    response = client.get("/api/v1/pages/about")

    assert response.status_code == 200
    assert response.json() == {"key": "about", "title": "Title", "content": "Plain text"}


def test_page_endpoint_returns_404_for_unpublished_or_missing() -> None:
    client = _client(FakeSession(pages=[make_page("about", False)]))

    assert client.get("/api/v1/pages/about").status_code == 404
    assert client.get("/api/v1/pages/missing").status_code == 404


def test_news_endpoint_lists_published_only_and_validates_limit() -> None:
    client = _client(
        FakeSession(
            news=[
                make_news("older", datetime(2026, 1, 1, tzinfo=UTC), True, id=1),
                make_news("draft", datetime(2026, 3, 1, tzinfo=UTC), False, id=3),
                make_news("newer", datetime(2026, 2, 1, tzinfo=UTC), True, id=2),
            ]
        )
    )

    response = client.get("/api/v1/news?limit=1&offset=0")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["newer"]
    assert client.get("/api/v1/news?limit=101").status_code == 422


def test_news_endpoint_detail_and_slug_validation() -> None:
    client = _client(FakeSession(news=[make_news("live-post", None, True, id=1), make_news("draft-post", None, False, id=2)]))

    assert client.get("/api/v1/news/live-post").status_code == 200
    assert client.get("/api/v1/news/draft-post").status_code == 404
    assert client.get("/api/v1/news/missing-post").status_code == 404
    assert client.get("/api/v1/news/Bad_Slug").status_code == 422


def test_video_endpoints_return_published_only() -> None:
    client = _client(FakeSession(videos=[make_video(1, None, False), make_video(2, None, True)]))

    list_response = client.get("/api/v1/videos")

    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [2]
    assert client.get("/api/v1/videos/2").status_code == 200
    assert client.get("/api/v1/videos/1").status_code == 404
    assert client.get("/api/v1/videos/404").status_code == 404


def _client(fake_session: FakeSession) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: fake_session
    return TestClient(app)
