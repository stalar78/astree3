import pytest

from app.models.news import NewsPost
from app.models.page import Page
from app.services.identifiers import IdentifierValidationError


@pytest.mark.parametrize("slug", ["astrea-news", "news-2026", "a"])
def test_valid_news_slug_accepted(slug: str) -> None:
    post = NewsPost(slug=slug, title="Title", excerpt="Excerpt", body="Body")

    assert post.slug == slug


@pytest.mark.parametrize(
    "slug",
    ["Bad-Slug", "bad_slug", "bad slug", "-leading", "trailing-", "double--dash", ""],
)
def test_malformed_news_slug_rejected(slug: str) -> None:
    with pytest.raises(IdentifierValidationError):
        NewsPost(slug=slug, title="Title", excerpt="Excerpt", body="Body")


@pytest.mark.parametrize("key", ["about", "lodges_saint_petersburg", "faq"])
def test_valid_page_key_accepted(key: str) -> None:
    page = Page(key=key, title="Title", content="Content")

    assert page.key == key


@pytest.mark.parametrize(
    "key",
    ["Bad_Key", "bad-key", "bad key", "_leading", "trailing_", "double__underscore", ""],
)
def test_malformed_page_key_rejected(key: str) -> None:
    with pytest.raises(IdentifierValidationError):
        Page(key=key, title="Title", content="Content")
