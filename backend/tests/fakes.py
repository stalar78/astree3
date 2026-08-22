from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.models.news import NewsPost
from app.models.page import Page
from app.models.video import Video


@dataclass
class FakeScalarResult:
    items: list[Any]

    def all(self) -> list[Any]:
        return self.items


@dataclass
class FakeResult:
    items: list[Any]
    one_or_none: Any = None

    def scalar_one_or_none(self) -> Any:
        return self.one_or_none

    def scalars(self) -> FakeScalarResult:
        return FakeScalarResult(self.items)


class FakeSession:
    def __init__(self, pages: list[Page] | None = None, news: list[NewsPost] | None = None, videos: list[Video] | None = None):
        self.pages = pages or []
        self.news = news or []
        self.videos = videos or []
        self.last_statement = None

    def execute(self, statement: Any) -> FakeResult:
        self.last_statement = statement
        entity = statement.column_descriptions[0].get("entity")

        if entity is Page:
            key = _where_value(statement, "key")
            page = next((item for item in self.pages if item.key == key and item.is_published), None)
            return FakeResult([], page)

        if entity is NewsPost and _where_value(statement, "slug") is not None:
            slug = _where_value(statement, "slug")
            post = next((item for item in self.news if item.slug == slug and item.is_published), None)
            return FakeResult([], post)

        if entity is NewsPost:
            offset = _limit_offset_value(statement, "_offset_clause", 0)
            limit = _limit_offset_value(statement, "_limit_clause", len(self.news))
            items = [item for item in self.news if item.is_published]
            items.sort(
                key=lambda item: (item.published_at or datetime.min.replace(tzinfo=UTC), item.id),
                reverse=True,
            )
            return FakeResult(items[offset : offset + limit])

        if entity is Video and _where_value(statement, "id") is not None:
            video_id = _where_value(statement, "id")
            video = next((item for item in self.videos if item.id == video_id and item.is_published), None)
            return FakeResult([], video)

        if entity is Video:
            offset = _limit_offset_value(statement, "_offset_clause", 0)
            limit = _limit_offset_value(statement, "_limit_clause", len(self.videos))
            items = [item for item in self.videos if item.is_published]
            items.sort(
                key=lambda item: (item.published_at or datetime.min.replace(tzinfo=UTC), item.id),
                reverse=True,
            )
            return FakeResult(items[offset : offset + limit])

        raise AssertionError(f"Unexpected statement: {statement}")


def make_page(key: str = "about", is_published: bool = True) -> Page:
    return Page(key=key, title="Title", content="Plain text", is_published=is_published)


def make_news(slug: str, published_at: datetime | None, is_published: bool = True, id: int = 1) -> NewsPost:
    return NewsPost(
        id=id,
        slug=slug,
        title=f"Title {slug}",
        excerpt="Excerpt",
        body="Body",
        is_published=is_published,
        published_at=published_at,
    )


def make_video(id: int, published_at: datetime | None, is_published: bool = True) -> Video:
    video_id = f"{id:032x}"
    return Video(
        id=id,
        title=f"Video {id}",
        description="Description",
        source_url=f"https://rutube.ru/video/{video_id}/",
        provider="rutube",
        is_published=is_published,
        published_at=published_at,
    )


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
