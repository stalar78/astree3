from datetime import UTC, datetime

from app.services import public_content
from tests.fakes import FakeSession, make_news, make_page, make_video


def test_published_page_returned() -> None:
    db = FakeSession(pages=[make_page("about", True)])

    page = public_content.get_published_page(db, "about")

    assert page is not None
    assert page.key == "about"


def test_unpublished_page_not_returned() -> None:
    db = FakeSession(pages=[make_page("about", False)])

    assert public_content.get_published_page(db, "about") is None


def test_missing_page_not_returned() -> None:
    db = FakeSession(pages=[make_page("about", True)])

    assert public_content.get_published_page(db, "contacts") is None


def test_news_list_returns_published_only_newest_first() -> None:
    older = make_news("older", datetime(2026, 1, 1, tzinfo=UTC), True, id=1)
    draft = make_news("draft", datetime(2026, 3, 1, tzinfo=UTC), False, id=3)
    newer = make_news("newer", datetime(2026, 2, 1, tzinfo=UTC), True, id=2)
    db = FakeSession(news=[older, draft, newer])

    posts = public_content.list_published_news(db)

    assert [post.slug for post in posts] == ["newer", "older"]


def test_news_limit_offset_behavior() -> None:
    posts = [
        make_news("first", datetime(2026, 3, 1, tzinfo=UTC), True, id=3),
        make_news("second", datetime(2026, 2, 1, tzinfo=UTC), True, id=2),
        make_news("third", datetime(2026, 1, 1, tzinfo=UTC), True, id=1),
    ]
    db = FakeSession(news=posts)

    result = public_content.list_published_news(db, limit=1, offset=1)

    assert [post.slug for post in result] == ["second"]


def test_news_detail_by_slug_excludes_drafts_and_missing() -> None:
    db = FakeSession(news=[make_news("draft", None, False, id=1), make_news("live", None, True, id=2)])

    assert public_content.get_published_news_by_slug(db, "live") is not None
    assert public_content.get_published_news_by_slug(db, "draft") is None
    assert public_content.get_published_news_by_slug(db, "missing") is None


def test_videos_list_and_detail_return_published_only() -> None:
    db = FakeSession(videos=[make_video(1, None, False), make_video(2, None, True)])

    assert [video.id for video in public_content.list_published_videos(db)] == [2]
    assert public_content.get_published_video(db, 2) is not None
    assert public_content.get_published_video(db, 1) is None
    assert public_content.get_published_video(db, 404) is None
